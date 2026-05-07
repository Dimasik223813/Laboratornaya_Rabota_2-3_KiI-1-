import tkinter as tk
from tkinter import scrolledtext, ttk, filedialog, messagebox
import re
from collections import namedtuple

# Структура для хранения лексемы
Token = namedtuple('Token', ['type', 'value', 'line', 'position'])

class LexicalAnalyzer:
    """Лексический анализатор с использованием ДКА"""
    
    def __init__(self):
        # Ключевые слова
        self.keywords = {
            'if', 'else', 'while', 'for', 'do', 'switch', 'case', 'break',
            'continue', 'return', 'int', 'float', 'double', 'char', 'void',
            'struct', 'enum', 'typedef', 'const', 'static', 'extern', 'sizeof'
        }
        
        # Операторы
        self.operators = {
            '+', '-', '*', '/', '%', '=', '==', '!=', '<', '>', '<=', '>=',
            '&&', '||', '!', '&', '|', '^', '~', '<<', '>>', '+=', '-=',
            '*=', '/=', '%=', '++', '--', ';', ',', '(', ')', '{', '}', '[', ']'
        }
        
        # Разделители (игнорируются)
        self.delimiters = {' ', '\t', '\n', '\r'}
        
        # Типы лексем
        self.token_types = {
            'KEYWORD': 'Ключевое слово',
            'IDENTIFIER': 'Идентификатор',
            'NUMBER': 'Числовая константа',
            'STRING': 'Строковая константа',
            'CHAR': 'Символьная константа',
            'OPERATOR': 'Оператор',
            'COMMENT': 'Комментарий',
            'ERROR': 'ОШИБКА'
        }
        
        # Состояния ДКА (для чисел)
        self.states = {
            'START': 0,
            'NUMBER_INT': 1,
            'NUMBER_FLOAT': 2,
            'NUMBER_HEX': 3,
            'STRING': 4,
            'CHAR': 5,
            'COMMENT_LINE': 6,
            'COMMENT_BLOCK': 7,
            'ERROR': -1
        }
        
        self.tokens = []
        self.errors = []
    
    def is_letter(self, ch):
        """Проверка, является ли символ буквой или подчеркиванием"""
        return ch.isalpha() or ch == '_'
    
    def is_digit(self, ch):
        """Проверка, является ли символ цифрой"""
        return ch.isdigit()
    
    def is_hex_digit(self, ch):
        """Проверка, является ли символ шестнадцатеричной цифрой"""
        return ch.isdigit() or ch in 'abcdefABCDEF'
    
    def is_operator_char(self, ch):
        """Проверка, является ли символ частью оператора"""
        return ch in '+-*/%=<>!&|^~;:,(){}[]'
    
    def read_identifier(self, text, pos):
        """Чтение идентификатора или ключевого слова"""
        start = pos
        while pos < len(text) and (self.is_letter(text[pos]) or self.is_digit(text[pos])):
            pos += 1
        value = text[start:pos]
        
        # Проверка на ключевое слово
        if value in self.keywords:
            return 'KEYWORD', value, pos
        return 'IDENTIFIER', value, pos
    
    def read_number(self, text, pos, line, col_start):
        """Чтение числовой константы (ДКА)"""
        state = self.states['START']
        start = pos
        value = ''
        hex_mode = False
        
        while pos < len(text):
            ch = text[pos]
            
            if state == self.states['START']:
                if ch == '0' and pos + 1 < len(text) and text[pos + 1] in 'xX':
                    # Шестнадцатеричное число
                    state = self.states['NUMBER_HEX']
                    pos += 2
                    continue
                elif self.is_digit(ch):
                    state = self.states['NUMBER_INT']
                else:
                    break
            
            elif state == self.states['NUMBER_INT']:
                if self.is_digit(ch):
                    pass
                elif ch == '.':
                    state = self.states['NUMBER_FLOAT']
                elif ch in 'eE':
                    state = self.states['NUMBER_FLOAT']
                else:
                    break
            
            elif state == self.states['NUMBER_FLOAT']:
                if self.is_digit(ch):
                    pass
                elif ch in 'eE':
                    pass
                elif ch in '+-' and text[pos-1] in 'eE':
                    pass
                else:
                    break
            
            elif state == self.states['NUMBER_HEX']:
                if self.is_hex_digit(ch):
                    hex_mode = True
                else:
                    break
            
            pos += 1
        
        value = text[start:pos]
        
        # Проверка корректности
        if state == self.states['NUMBER_HEX'] and not hex_mode:
            self.errors.append(f"Ошибка: некорректное шестнадцатеричное число '{value}' на {line}:{col_start}")
            return 'ERROR', value, pos
        
        return 'NUMBER', value, pos
    
    def read_string(self, text, pos, line, col_start):
        """Чтение строковой константы"""
        start = pos
        pos += 1  # Пропускаем открывающую кавычку
        
        while pos < len(text):
            if text[pos] == '"':
                pos += 1
                value = text[start:pos]
                return 'STRING', value, pos
            elif text[pos] == '\n':
                self.errors.append(f"Ошибка: незакрытая строковая константа на {line}:{col_start}")
                return 'ERROR', text[start:pos], pos
            pos += 1
        
        self.errors.append(f"Ошибка: незакрытая строковая константа на {line}:{col_start}")
        return 'ERROR', text[start:pos], pos
    
    def read_char(self, text, pos, line, col_start):
        """Чтение символьной константы"""
        start = pos
        pos += 1  # Пропускаем открывающую кавычку
        
        if pos < len(text) and text[pos] != "'":
            if text[pos] == '\\' and pos + 1 < len(text):
                pos += 2
            else:
                pos += 1
        
        if pos < len(text) and text[pos] == "'":
            pos += 1
            value = text[start:pos]
            if len(value) > 3:  # Проверка длины символа
                self.errors.append(f"Ошибка: пустая символьная константа на {line}:{col_start}")
                return 'ERROR', value, pos
            return 'CHAR', value, pos
        
        self.errors.append(f"Ошибка: незакрытая символьная константа на {line}:{col_start}")
        return 'ERROR', text[start:pos], pos
    
    def read_operator(self, text, pos):
        """Чтение оператора"""
        # Проверка двухсимвольных операторов
        if pos + 1 < len(text) and text[pos:pos+2] in self.operators:
            return 'OPERATOR', text[pos:pos+2], pos + 2
        
        # Проверка односимвольных операторов
        if text[pos] in self.operators:
            return 'OPERATOR', text[pos], pos + 1
        
        return 'ERROR', text[pos], pos + 1
    
    def skip_comment_line(self, text, pos):
        """Пропуск однострочного комментария"""
        while pos < len(text) and text[pos] != '\n':
            pos += 1
        return pos
    
    def skip_comment_block(self, text, pos):
        """Пропуск блочного комментария"""
        start = pos
        while pos + 1 < len(text):
            if text[pos] == '*' and text[pos + 1] == '/':
                return pos + 2
            pos += 1
        self.errors.append(f"Ошибка: незакрытый блочный комментарий")
        return pos
    
    def analyze(self, text):
        """Основной метод анализа текста"""
        self.tokens = []
        self.errors = []
        
        if not text:
            self.errors.append("Ошибка: входной текст пуст")
            return self.tokens
        
        pos = 0
        line = 1
        col = 1
        text_len = len(text)
        
        while pos < text_len:
            ch = text[pos]
            start_col = col
            
            # Игнорируем разделители
            if ch in self.delimiters:
                if ch == '\n':
                    line += 1
                    col = 1
                else:
                    col += 1
                pos += 1
                continue
            
            # Однострочный комментарий
            if ch == '/' and pos + 1 < text_len and text[pos + 1] == '/':
                token_type = 'COMMENT'
                start_pos = pos
                pos = self.skip_comment_line(text, pos)
                value = text[start_pos:pos]
                self.tokens.append(Token(token_type, value, line, start_col))
                col += len(value)
                continue
            
            # Блочный комментарий
            if ch == '/' and pos + 1 < text_len and text[pos + 1] == '*':
                token_type = 'COMMENT'
                start_pos = pos
                pos = self.skip_comment_block(text, pos)
                value = text[start_pos:pos]
                # Обновляем строки и колонки
                for c in value:
                    if c == '\n':
                        line += 1
                        col = 1
                    else:
                        col += 1
                self.tokens.append(Token(token_type, value, line, col))
                continue
            
            # Идентификатор или ключевое слово
            if self.is_letter(ch):
                token_type, value, pos = self.read_identifier(text, pos)
                self.tokens.append(Token(token_type, value, line, start_col))
                col += len(value)
                continue
            
            # Числовая константа
            if self.is_digit(ch) or (ch == '0' and pos + 1 < text_len and text[pos + 1] in 'xX'):
                token_type, value, pos = self.read_number(text, pos, line, start_col)
                self.tokens.append(Token(token_type, value, line, start_col))
                col += len(value)
                continue
            
            # Строковая константа
            if ch == '"':
                token_type, value, pos = self.read_string(text, pos, line, start_col)
                self.tokens.append(Token(token_type, value, line, start_col))
                col += len(value)
                continue
            
            # Символьная константа
            if ch == "'":
                token_type, value, pos = self.read_char(text, pos, line, start_col)
                self.tokens.append(Token(token_type, value, line, start_col))
                col += len(value)
                continue
            
            # Оператор
            if self.is_operator_char(ch):
                token_type, value, pos = self.read_operator(text, pos)
                self.tokens.append(Token(token_type, value, line, start_col))
                col += len(value)
                continue
            
            # Неизвестный символ (ошибка)
            error_msg = f"Неизвестный символ '{ch}'"
            self.errors.append(f"{error_msg} на {line}:{start_col}")
            self.tokens.append(Token('ERROR', ch, line, start_col))
            pos += 1
            col += 1
        
        return self.tokens


class LexerGUI:
    """Графический интерфейс лексического анализатора"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Лексический анализатор")
        self.root.geometry("1200x750")
        
        self.analyzer = LexicalAnalyzer()
        
        self.setup_ui()
    
    def setup_ui(self):
        """Настройка пользовательского интерфейса"""
        
        # Верхняя панель с кнопками
        top_frame = tk.Frame(self.root)
        top_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Button(top_frame, text="Загрузить файл", command=self.load_file,
                  bg="#4CAF50", fg="white", font=("Arial", 10, "bold"),
                  padx=20, pady=5).pack(side=tk.LEFT, padx=5)
        
        tk.Button(top_frame, text="Очистить всё", command=self.clear_all,
                  bg="#f44336", fg="white", font=("Arial", 10, "bold"),
                  padx=20, pady=5).pack(side=tk.LEFT, padx=5)
        
        tk.Button(top_frame, text="Анализировать", command=self.analyze,
                  bg="#2196F3", fg="white", font=("Arial", 10, "bold"),
                  padx=20, pady=5).pack(side=tk.LEFT, padx=5)
        
        # Метка с информацией о варианте
        info_label = tk.Label(top_frame, text="Вариант: Си-подобный язык | ДКА для чисел",
                              font=("Arial", 9, "italic"), fg="gray")
        info_label.pack(side=tk.RIGHT, padx=10)
        
        # Основная область (фрейм с двумя колонками)
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Левая часть - ввод кода
        left_frame = tk.LabelFrame(main_frame, text="Входной код", font=("Arial", 10, "bold"))
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        self.input_text = scrolledtext.ScrolledText(left_frame, height=25, font=("Courier New", 10))
        self.input_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Правая часть - результаты
        right_frame = tk.LabelFrame(main_frame, text="Результаты анализа", font=("Arial", 10, "bold"))
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # Таблица лексем
        tree_frame = tk.Frame(right_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Создание таблицы
        columns = ("№", "Лексема", "Тип", "Строка", "Позиция")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            self.tree.heading(col, text=col)
            if col == "Лексема":
                self.tree.column(col, width=250)
            elif col == "Тип":
                self.tree.column(col, width=180)
            else:
                self.tree.column(col, width=70)
        
        # Scrollbar для таблицы
        tree_scroll = tk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Область ошибок
        error_frame = tk.LabelFrame(right_frame, text="Ошибки", font=("Arial", 9, "bold"), fg="red")
        error_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))
        
        self.error_text = scrolledtext.ScrolledText(error_frame, height=6, font=("Courier New", 9), fg="red")
        self.error_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Статусная строка
        self.status_bar = tk.Label(self.root, text="Готов к работе", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Добавим пример кода
        self.insert_example()
    
    def insert_example(self):
        """Вставка примера кода для демонстрации"""
        example_code = '''int main() {
    // Это комментарий
    int a = 10;
    float b = 3.14;
    char c = 'A';
    string s = "Hello, World!";
    
    if (a == 10) {
        a++;
        /* Блочный
           комментарий */
    }
    
    for (int i = 0; i < 10; i++) {
        a += i;
    }
    
    return 0;
}'''
        self.input_text.insert(1.0, example_code)
    
    def load_file(self):
        """Загрузка кода из файла"""
        filename = filedialog.askopenfilename(
            title="Выберите файл с кодом",
            filetypes=[("Текстовые файлы", "*.txt"), ("C/C++ файлы", "*.c"), ("Все файлы", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.input_text.delete(1.0, tk.END)
                self.input_text.insert(1.0, content)
                self.status_bar.config(text=f"Загружен файл: {filename}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось загрузить файл:\n{str(e)}")
    
    def clear_all(self):
        """Очистка всех полей"""
        self.input_text.delete(1.0, tk.END)
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.error_text.delete(1.0, tk.END)
        self.status_bar.config(text="Очищено")
    
    def analyze(self):
        """Запуск лексического анализа"""
        # Очистка предыдущих результатов
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.error_text.delete(1.0, tk.END)
        
        # Получение текста для анализа
        text = self.input_text.get(1.0, tk.END)
        
        if not text.strip():
            self.error_text.insert(1.0, "Ошибка: Введите код для анализа или загрузите файл!")
            self.status_bar.config(text="Ошибка: пустой ввод")
            return
        
        # Выполнение анализа
        try:
            tokens = self.analyzer.analyze(text)
            
            # Заполнение таблицы результатов
            for i, token in enumerate(tokens, 1):
                token_type_display = self.analyzer.token_types.get(token.type, token.type)
                
                self.tree.insert("", tk.END, values=(
                    i,
                    token.value,
                    token_type_display,
                    token.line,
                    token.position
                ))
                
                # Подсветка ошибок в таблице
                if token.type == 'ERROR':
                    last_item = self.tree.get_children()[-1]
                    self.tree.item(last_item, tags=('error',))
                    self.tree.tag_configure('error', background='#ffcccc')
            
            # Отображение ошибок
            if self.analyzer.errors:
                self.error_text.insert(1.0, "\n".join(self.analyzer.errors))
                self.status_bar.config(text=f"Анализ завершён. Найдено {len(self.analyzer.errors)} ошибок")
            else:
                self.error_text.insert(1.0, "Ошибок не обнаружено")
                self.status_bar.config(text=f"Анализ завершён успешно. Найдено {len(tokens)} лексем")
            
        except Exception as e:
            self.error_text.insert(1.0, f"Критическая ошибка при анализе:\n{str(e)}")
            self.status_bar.config(text="Ошибка выполнения анализа")


def main():
    """Запуск приложения"""
    root = tk.Tk()
    app = LexerGUI(root)
    
    # Установка иконки (опционально)
    try:
        root.iconbitmap(default='icon.ico')
    except:
        pass
    
    root.mainloop()


if __name__ == "__main__":
    main()