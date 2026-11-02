
"""Тесты для консольного эмулятора ОС."""

import io
import unittest
from contextlib import redirect_stdout

from src.main import execute_command, parse_input


class TestParser(unittest.TestCase):
    """Проверяет работу парсера команд."""

    def test_quoted_arguments(self):
        """Проверяет обработку аргументов в кавычках."""
        result = parse_input('ls "my folder"')
        self.assertEqual(result, ["ls", "my folder"])

    def test_invalid_quotes(self):
        """Проверяет обработку незакрытых кавычек."""
        with self.assertRaises(ValueError):
            parse_input('ls "my folder')


class TestCommands(unittest.TestCase):
    """Проверяет выполнение команд."""

    def test_ls_command(self):
        """Проверяет вывод команды ls."""
        output = io.StringIO()
        with redirect_stdout(output):
            execute_command(["ls", "folder"])
        self.assertEqual(output.getvalue().strip(),
                         "ls: ['folder']")

    def test_cd_command(self):
        """Проверяет вывод команды cd."""
        output = io.StringIO()
        with redirect_stdout(output):
            execute_command(["cd", "folder"])
        self.assertEqual(output.getvalue().strip(),
                         "cd: ['folder']")

    def test_cd_invalid_arguments(self):
        """Проверяет неверное количество аргументов cd."""
        output = io.StringIO()
        with redirect_stdout(output):
            execute_command(["cd", "one", "two"])
        self.assertIn("Error", output.getvalue())

    def test_unknown_command(self):
        """Проверяет обработку неизвестной команды."""
        output = io.StringIO()
        with redirect_stdout(output):
            execute_command(["unknown"])
        self.assertIn("unknown command", output.getvalue())

    def test_exit_command(self):
        """Проверяет завершение REPL."""
        self.assertFalse(execute_command(["exit"]))

    def test_exit_invalid_arguments(self):
        """Проверяет неверные аргументы exit."""
        output = io.StringIO()
        with redirect_stdout(output):
            result = execute_command(["exit", "now"])
        self.assertTrue(result)
        self.assertIn("Error", output.getvalue())


if __name__ == "__main__":
    unittest.main()
