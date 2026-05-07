import re
from typing import Optional, Union, List, Tuple


class Node:
    """Узел синтаксического дерева"""
    def __init__(self, value: str, left: Optional['Node'] = None, right: Optional['Node'] = None):
        self.value = value
        self.left = left
        self.right = right

    def __repr__(self):
        return f"Node({self.value})"


class ExpressionParser:
    """Класс для преобразования арифметических выражений"""
    
    # Приоритеты операторов
    PRECEDENCE = {'+': 1, '-': 1, '*': 2, '/': 2, '^': 3}
    
    def __init__(self, expression: str = ""):
        self.expression = expression.replace(" ", "")
        self.postfix_form = ""
        self.prefix_form = ""
        self.syntax_tree = None
    
    def is_operator(self, char: str) -> bool:
        """Проверяет, является ли символ оператором"""
        return char in self.PRECEDENCE
    
    def is_operand(self, char: str) -> bool:
        """Проверяет, является ли символ операндом (буква или цифра)"""
        return char.isalnum()
    
    def infix_to_postfix(self, expression: Optional[str] = None) -> str:
        """
        Преобразование инфиксной формы в постфиксную (Обратная польская запись)
        Алгоритм сортировочной станции Дейкстры
        """
        if expression is None:
            expression = self.expression
        
        output = []
        stack = []
        i = 0
        
        while i < len(expression):
            char = expression[i]
            
            # Если операнд (цифра или буква)
            if self.is_operand(char):
                # Поддерживаем многозначные числа и переменные
                operand = ""
                while i < len(expression) and self.is_operand(expression[i]):
                    operand += expression[i]
                    i += 1
                output.append(operand)
                continue
            
            # Если открывающая скобка
            elif char == '(':
                stack.append(char)
            
            # Если закрывающая скобка
            elif char == ')':
                while stack and stack[-1] != '(':
                    output.append(stack.pop())
                if stack and stack[-1] == '(':
                    stack.pop()
            
            # Если оператор
            elif self.is_operator(char):
                while (stack and stack[-1] != '(' and
                       self.PRECEDENCE.get(stack[-1], 0) >= self.PRECEDENCE.get(char, 0)):
                    output.append(stack.pop())
                stack.append(char)
            
            i += 1
        
        # Выталкиваем оставшиеся операторы
        while stack:
            output.append(stack.pop())
        
        self.postfix_form = ' '.join(output)
        return self.postfix_form
    
    def infix_to_prefix(self, expression: Optional[str] = None) -> str:
        """
        Преобразование инфиксной формы в префиксную (Польская запись)
        """
        if expression is None:
            expression = self.expression
        
        # Переворачиваем выражение и меняем скобки
        reversed_expr = expression[::-1]
        reversed_expr = reversed_expr.replace('(', 'temp')
        reversed_expr = reversed_expr.replace(')', '(')
        reversed_expr = reversed_expr.replace('temp', ')')
        
        # Используем преобразование в постфикс для перевернутого выражения
        output = []
        stack = []
        i = 0
        
        while i < len(reversed_expr):
            char = reversed_expr[i]
            
            if self.is_operand(char):
                operand = ""
                while i < len(reversed_expr) and self.is_operand(reversed_expr[i]):
                    operand += reversed_expr[i]
                    i += 1
                output.append(operand[::-1])  # Возвращаем в нормальный порядок
                continue
            
            elif char == '(':
                stack.append(char)
            
            elif char == ')':
                while stack and stack[-1] != '(':
                    output.append(stack.pop())
                if stack and stack[-1] == '(':
                    stack.pop()
            
            elif self.is_operator(char):
                while (stack and stack[-1] != '(' and
                       self.PRECEDENCE.get(stack[-1], 0) > self.PRECEDENCE.get(char, 0)):
                    output.append(stack.pop())
                stack.append(char)
            
            i += 1
        
        while stack:
            output.append(stack.pop())
        
        # Переворачиваем результат
        prefix_result = ' '.join(output[::-1])
        self.prefix_form = prefix_result
        return self.prefix_form
    
    def build_tree_from_postfix(self, postfix_expr: Optional[str] = None) -> Node:
        """
        Построение синтаксического дерева из постфиксной формы
        """
        if postfix_expr is None:
            if not self.postfix_form:
                self.infix_to_postfix()
            postfix_expr = self.postfix_form
        
        tokens = postfix_expr.split()
        stack = []
        
        for token in tokens:
            if self.is_operand(token):
                stack.append(Node(token))
            elif self.is_operator(token):
                if len(stack) < 2:
                    raise ValueError("Недостаточно операндов для оператора")
                right = stack.pop()
                left = stack.pop()
                stack.append(Node(token, left, right))
        
        if len(stack) != 1:
            raise ValueError("Некорректное выражение")
        
        self.syntax_tree = stack[0]
        return self.syntax_tree
    
    def build_tree_from_prefix(self, prefix_expr: Optional[str] = None) -> Node:
        """
        Построение синтаксического дерева из префиксной формы
        """
        if prefix_expr is None:
            if not self.prefix_form:
                self.infix_to_prefix()
            prefix_expr = self.prefix_form
        
        tokens = prefix_expr.split()[::-1]  # Переворачиваем для удобства
        stack = []
        
        for token in tokens:
            if self.is_operand(token):
                stack.append(Node(token))
            elif self.is_operator(token):
                if len(stack) < 2:
                    raise ValueError("Недостаточно операндов для оператора")
                left = stack.pop()
                right = stack.pop()
                stack.append(Node(token, left, right))
        
        if len(stack) != 1:
            raise ValueError("Некорректное выражение")
        
        self.syntax_tree = stack[0]
        return self.syntax_tree
    
    def print_tree(self, node: Optional[Node] = None, level: int = 0, prefix: str = "Root: ") -> None:
        """
        Вывод синтаксического дерева на экран (рекурсивный обход)
        """
        if node is None:
            node = self.syntax_tree
            if node is None:
                print("Синтаксическое дерево не построено.")
                return
        
        indent = "    " * level
        if level == 0:
            print(f"\n{indent}{prefix}{node.value}")
        else:
            print(f"{indent}├── {node.value}")
        
        if node.left:
            self.print_tree(node.left, level + 1, "L: ")
        if node.right:
            self.print_tree(node.right, level + 1, "R: ")
    
    def visualize_tree(self, node: Optional[Node] = None) -> None:
        """Визуализация дерева в древовидном формате"""
        if node is None:
            node = self.syntax_tree
            if node is None:
                print("Синтаксическое дерево не построено.")
                return
        
        lines = []
        self._build_tree_string(node, 0, True, lines)
        print("\n" + "\n".join(lines))
    
    def _build_tree_string(self, node: Node, depth: int, is_last: bool, lines: List[str]) -> None:
        """Вспомогательный метод для построения строкового представления дерева"""
        if node is None:
            return
        
        current_line = "    " * depth
        if depth > 0:
            current_line += "└── " if is_last else "├── "
        current_line += node.value
        lines.append(current_line)
        
        children = []
        if node.left:
            children.append(node.left)
        if node.right:
            children.append(node.right)
        
        for i, child in enumerate(children):
            self._build_tree_string(child, depth + 1, i == len(children) - 1, lines)
    
    def evaluate_tree(self, node: Optional[Node] = None, variables: Optional[dict] = None) -> float:
        """
        Вычисление значения выражения по синтаксическому дереву
        
        Args:
            node: текущий узел
            variables: словарь значений переменных
        """
        if node is None:
            node = self.syntax_tree
        
        if variables is None:
            variables = {}
        
        if node.left is None and node.right is None:
            # Лист - операнд
            if node.value.isdigit():
                return float(node.value)
            else:
                # Переменная
                return float(variables.get(node.value, 0))
        
        left_val = self.evaluate_tree(node.left, variables) if node.left else 0
        right_val = self.evaluate_tree(node.right, variables) if node.right else 0
        
        operations = {
            '+': lambda a, b: a + b,
            '-': lambda a, b: a - b,
            '*': lambda a, b: a * b,
            '/': lambda a, b: a / b if b != 0 else float('inf'),
            '^': lambda a, b: a ** b
        }
        
        if node.value in operations:
            return operations[node.value](left_val, right_val)
        else:
            raise ValueError(f"Неподдерживаемый оператор: {node.value}")
    
    def get_expression_from_file(self, filename: str) -> bool:
        """Считывание выражения из файла"""
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                expression = file.readline().strip()
                if expression:
                    self.expression = expression.replace(" ", "")
                    return True
                else:
                    print("Файл пуст.")
                    return False
        except FileNotFoundError:
            print(f"Файл '{filename}' не найден.")
            return False
        except Exception as e:
            print(f"Ошибка при чтении файла: {e}")
            return False
    
    def process_expression(self) -> None:
        """Обработка выражения: генерация всех форм и дерева"""
        print(f"\n{'='*60}")
        print(f"Исходное выражение: {self.expression}")
        print(f"{'='*60}")
        
        try:
            # Генерация постфиксной формы
            postfix = self.infix_to_postfix()
            print(f"\nПостфиксная форма (ОПЗ): {postfix}")
            
            # Генерация префиксной формы
            prefix = self.infix_to_prefix()
            print(f"Префиксная форма (ПЗ): {prefix}")
            
            # Построение дерева из постфиксной формы
            tree = self.build_tree_from_postfix()
            print(f"\nСинтаксическое дерево (из постфиксной формы):")
            self.visualize_tree()
            
            print(f"\nПодробное представление дерева:")
            self.print_tree()
            
            # Возможность вычислить выражение
            choice = input("\nХотите вычислить выражение? (y/n): ").lower()
            if choice == 'y':
                # Сбор значений переменных
                variables = self._collect_variables()
                result = self.evaluate_tree(variables=variables)
                print(f"\nРезультат вычисления: {result}")
                
        except Exception as e:
            print(f"Ошибка при обработке выражения: {e}")


class ConsoleInterface:
    """Консольный пользовательский интерфейс"""
    
    @staticmethod
    def show_menu() -> None:
        """Отображение главного меню"""
        print("\n" + "="*60)
        print("     ГЕНЕРАТОР СИНТАКСИЧЕСКОГО ДЕРЕВА")
        print("     АРИФМЕТИЧЕСКИХ ВЫРАЖЕНИЙ")
        print("="*60)
        print("\n1. Ввести выражение с клавиатуры")
        print("3. Выход")
        print("-"*60)
    
    @staticmethod
    def get_expression_from_input() -> str:
        """Получение выражения от пользователя"""
        print("\nВведите арифметическое выражение (поддерживаются +, -, *, /, ^):")
        print("Примеры: a+b*c, (a+b)*c-d, x^2+2*x+1")
        expression = input(">>> ").strip()
        return expression
    
    @staticmethod
    def run() -> None:
        """Запуск программы"""
        parser = ExpressionParser()
        
        while True:
            ConsoleInterface.show_menu()
            choice = input("Выберите действие (1-3): ").strip()
            
            if choice == '1':
                expression = ConsoleInterface.get_expression_from_input()
                if expression:
                    parser.expression = expression.replace(" ", "")
                    parser.process_expression()
                else:
                    print("Выражение не введено.")
            
            elif choice == '2':
                filename = input("Введите имя файла: ").strip()
                if parser.get_expression_from_file(filename):
                    parser.process_expression()
            
            elif choice == '3':
                print("\nДо свидания!")
                break
            
            else:
                print("Неверный выбор. Попробуйте снова.")


def main():
    """Точка входа в программу"""
    # Дополнительные тесты
    test_expressions = [
        "a+b*c",
        "(a+b)*c-d",
        "x^2+2*x+1",
        "a*b+c/d",
        "((a+b)*c-d)/e"
    ]
    
    print("\n" + "="*60)
    print("     ДЕМОНСТРАЦИЯ РАБОТЫ ПРОГРАММЫ")
    print("="*60)
    
    # Демонстрация на тестовых примерах
    print("\n--- ТЕСТОВЫЕ ПРИМЕРЫ ---")
    for expr in test_expressions:
        print(f"\n\nОбработка выражения: {expr}")
        parser = ExpressionParser(expr)
        try:
            postfix = parser.infix_to_postfix()
            prefix = parser.infix_to_prefix()
            tree = parser.build_tree_from_postfix()
            
            print(f"  Постфиксная форма: {postfix}")
            print(f"  Префиксная форма: {prefix}")
            print("  Синтаксическое дерево:")
            parser.visualize_tree()
            
        except Exception as e:
            print(f"  Ошибка: {e}")
    
    # Запуск интерактивного режима
    print("\n\n" + "="*60)
    print("     ИНТЕРАКТИВНЫЙ РЕЖИМ")
    print("="*60)
    ConsoleInterface.run()


if __name__ == "__main__":
    main()