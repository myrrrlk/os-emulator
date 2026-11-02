"""Тесты для консольного эмулятора ОС."""

import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout

from src.main import (
    EXIT_FAILURE,
    EXIT_SUCCESS,
    CommandError,
    ScriptError,
    execute_command,
    main,
    parse_arguments,
    parse_input,
    run_script,
)


def capture_output(function, *args):
    """Вызывает функцию и возвращает её результат и вывод."""
    output = io.StringIO()
    with redirect_stdout(output):
        result = function(*args)
    return result, output.getvalue()


class ScriptFileMixin:
    """Создаёт временные файлы стартовых скриптов."""

    def make_script(self, text):
        """Сохраняет текст скрипта во временный файл."""
        handle, path = tempfile.mkstemp(suffix=".txt")
        with os.fdopen(handle, "w", encoding="utf-8") as script_file:
            script_file.write(text)
        self.addCleanup(os.remove, path)
        return path


class TestParser(unittest.TestCase):
    """Проверяет работу парсера команд."""

    def test_quoted_arguments(self):
        """Проверяет обработку аргументов в кавычках."""
        result = parse_input('ls "my folder"')
        self.assertEqual(result, ["ls", "my folder"])

    def test_single_quotes(self):
        """Проверяет обработку одинарных кавычек."""
        result = parse_input("cd 'Program Files'")
        self.assertEqual(result, ["cd", "Program Files"])

    def test_invalid_quotes(self):
        """Проверяет обработку незакрытых кавычек."""
        with self.assertRaises(CommandError):
            parse_input('ls "my folder')


class TestCommands(unittest.TestCase):
    """Проверяет выполнение команд."""

    def test_empty_input(self):
        """Проверяет, что пустой ввод не завершает работу."""
        self.assertTrue(execute_command([]))

    def test_ls_command(self):
        """Проверяет вывод команды ls."""
        _, output = capture_output(execute_command, ["ls", "folder"])
        self.assertEqual(output.strip(), "ls: ['folder']")

    def test_cd_command(self):
        """Проверяет вывод команды cd."""
        _, output = capture_output(execute_command, ["cd", "folder"])
        self.assertEqual(output.strip(), "cd: ['folder']")

    def test_cd_invalid_arguments(self):
        """Проверяет неверное количество аргументов cd."""
        with self.assertRaises(CommandError):
            execute_command(["cd", "one", "two"])

    def test_unknown_command(self):
        """Проверяет обработку неизвестной команды."""
        with self.assertRaisesRegex(CommandError, "unknown command"):
            execute_command(["unknown"])

    def test_exit_command(self):
        """Проверяет завершение работы командой exit."""
        self.assertFalse(execute_command(["exit"]))

    def test_exit_invalid_arguments(self):
        """Проверяет неверные аргументы exit."""
        with self.assertRaises(CommandError):
            execute_command(["exit", "now"])


class TestArguments(unittest.TestCase):
    """Проверяет разбор параметров командной строки."""

    def test_no_arguments(self):
        """Проверяет значения по умолчанию."""
        args = parse_arguments([])
        self.assertIsNone(args.vfs)
        self.assertIsNone(args.script)

    def test_all_arguments(self):
        """Проверяет разбор обоих параметров."""
        args = parse_arguments(["--vfs", "a.json", "--script", "b.txt"])
        self.assertEqual(args.vfs, "a.json")
        self.assertEqual(args.script, "b.txt")


class TestScript(ScriptFileMixin, unittest.TestCase):
    """Проверяет выполнение стартового скрипта."""

    def test_script_shows_input_and_output(self):
        """Проверяет, что выводятся и команда, и результат."""
        path = self.make_script("ls docs\n")
        _, output = capture_output(run_script, path)
        self.assertIn("$ ls docs", output)
        self.assertIn("ls: ['docs']", output)

    def test_script_skips_comments(self):
        """Проверяет пропуск пустых строк и комментариев."""
        path = self.make_script("# comment\n\nls\n")
        _, output = capture_output(run_script, path)
        self.assertNotIn("comment", output)

    def test_script_without_exit(self):
        """Проверяет, что без exit работа продолжается."""
        path = self.make_script("ls\n")
        result, _ = capture_output(run_script, path)
        self.assertTrue(result)

    def test_script_with_exit(self):
        """Проверяет, что exit в скрипте завершает работу."""
        path = self.make_script("ls\nexit\nls never\n")
        result, output = capture_output(run_script, path)
        self.assertFalse(result)
        self.assertNotIn("never", output)

    def test_script_stops_on_error(self):
        """Проверяет остановку скрипта на первой ошибке."""
        path = self.make_script("ls\nfoo\nls never\n")
        output = io.StringIO()
        with redirect_stdout(output):
            with self.assertRaisesRegex(ScriptError, "line 2"):
                run_script(path)
        self.assertNotIn("never", output.getvalue())

    def test_missing_script(self):
        """Проверяет ошибку при отсутствии файла скрипта."""
        with self.assertRaisesRegex(ScriptError, "cannot read"):
            run_script("no_such_script.txt")


class TestMain(ScriptFileMixin, unittest.TestCase):
    """Проверяет точку входа эмулятора."""

    def test_debug_output(self):
        """Проверяет отладочный вывод параметров."""
        path = self.make_script("exit\n")
        argv = ["--vfs", "my.json", "--script", path]
        _, output = capture_output(main, argv)
        self.assertIn("VFS path:       my.json", output)
        self.assertIn(f"startup script: {path}", output)

    def test_successful_script(self):
        """Проверяет код завершения после успешного скрипта."""
        path = self.make_script("ls\nexit\n")
        result, _ = capture_output(main, ["--script", path])
        self.assertEqual(result, EXIT_SUCCESS)

    def test_failed_script(self):
        """Проверяет сообщение и код завершения при ошибке."""
        path = self.make_script("cd one two\n")
        result, output = capture_output(main, ["--script", path])
        self.assertEqual(result, EXIT_FAILURE)
        self.assertIn("Error: startup script stopped at line 1", output)

    def test_missing_vfs(self):
        """Проверяет код завершения, если VFS не загружается."""
        argv = ["--vfs", "no_such_vfs.json"]
        result, output = capture_output(main, argv)
        self.assertEqual(result, EXIT_FAILURE)
        self.assertIn("Error: cannot read VFS file", output)
        
if __name__ == "__main__":
    unittest.main()