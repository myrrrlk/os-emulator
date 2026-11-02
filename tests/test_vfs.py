"""Тесты виртуальной файловой системы и команды vfs-info."""

import hashlib
import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout

from src.main import CommandError, execute_command
from src.vfs import (
    VfsDirectory,
    VfsError,
    VfsFile,
    count_nodes,
    load_vfs,
)


PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXAMPLES_DIR = os.path.join(PROJECT_DIR, "vfs")


def example_path(name):
    """Возвращает путь к примеру VFS из папки vfs."""
    return os.path.join(EXAMPLES_DIR, name)


class VfsFileMixin:
    """Создаёт временные JSON-файлы VFS."""

    def make_vfs(self, text):
        """Сохраняет текст во временный JSON-файл."""
        handle, path = tempfile.mkstemp(suffix=".json")
        with os.fdopen(handle, "w", encoding="utf-8") as vfs_file:
            vfs_file.write(text)
        self.addCleanup(os.remove, path)
        return path

    def make_vfs_from(self, document):
        """Сохраняет объект Python как JSON-файл VFS."""
        return self.make_vfs(json.dumps(document))


class TestLoadExamples(unittest.TestCase):
    """Проверяет загрузку примеров VFS из репозитория."""

    def test_minimal(self):
        """Проверяет минимальную VFS с пустым корнем."""
        vfs = load_vfs(example_path("minimal.json"))
        self.assertEqual(vfs.name, "minimal")
        self.assertEqual(count_nodes(vfs.root), (0, 0))

    def test_several_files(self):
        """Проверяет VFS с несколькими файлами."""
        vfs = load_vfs(example_path("several_files.json"))
        self.assertEqual(count_nodes(vfs.root), (0, 4))

    def test_three_levels(self):
        """Проверяет VFS с тремя и более уровнями вложенности."""
        vfs = load_vfs(example_path("three_levels.json"))
        documents = (vfs.root.children["home"].children["user"]
                     .children["documents"])
        self.assertIsInstance(documents, VfsDirectory)
        self.assertIsInstance(documents.children["report.txt"], VfsFile)

    def test_sha256_of_file_data(self):
        """Проверяет, что хеш считается по байтам файла."""
        path = example_path("three_levels.json")
        with open(path, "rb") as vfs_file:
            expected = hashlib.sha256(vfs_file.read()).hexdigest()
        self.assertEqual(load_vfs(path).sha256, expected)

    def test_file_is_not_modified(self):
        """Проверяет, что загрузка не изменяет исходный файл."""
        path = example_path("several_files.json")
        with open(path, "rb") as vfs_file:
            before = vfs_file.read()
        load_vfs(path)
        with open(path, "rb") as vfs_file:
            self.assertEqual(vfs_file.read(), before)


class TestFileContent(VfsFileMixin, unittest.TestCase):
    """Проверяет декодирование содержимого файлов."""

    def load_single_file(self, description):
        """Загружает VFS с одним файлом и возвращает его данные."""
        path = self.make_vfs_from({"root": {
            "type": "dir", "children": {"f": description}}})
        return load_vfs(path).root.children["f"].data

    def test_text_content(self):
        """Проверяет текстовое содержимое файла."""
        data = self.load_single_file({"type": "file", "content": "hi"})
        self.assertEqual(data, b"hi")

    def test_base64_content(self):
        """Проверяет двоичное содержимое в base64."""
        data = self.load_single_file({
            "type": "file", "encoding": "base64", "content": "AAEC"})
        self.assertEqual(data, b"\x00\x01\x02")

    def test_default_name(self):
        """Проверяет имя VFS по имени файла, если поля name нет."""
        path = self.make_vfs_from({"root": {"type": "dir"}})
        expected = os.path.splitext(os.path.basename(path))[0]
        self.assertEqual(load_vfs(path).name, expected)


class TestLoadErrors(VfsFileMixin, unittest.TestCase):
    """Проверяет ошибки загрузки VFS."""

    def assert_vfs_error(self, document, pattern):
        """Проверяет, что загрузка документа вызывает VfsError."""
        path = self.make_vfs_from(document)
        with self.assertRaisesRegex(VfsError, pattern):
            load_vfs(path)

    def test_missing_file(self):
        """Проверяет отсутствующий файл VFS."""
        with self.assertRaisesRegex(VfsError, "cannot read"):
            load_vfs("no_such_vfs.json")

    def test_invalid_json(self):
        """Проверяет файл с неверным JSON."""
        path = self.make_vfs("{ not json")
        with self.assertRaisesRegex(VfsError, "not valid JSON"):
            load_vfs(path)

    def test_invalid_base64(self):
        """Проверяет неверные данные base64."""
        self.assert_vfs_error({"root": {"type": "dir", "children": {
            "f": {"type": "file", "encoding": "base64",
                  "content": "@@@"}}}}, "invalid base64")

    def test_root_is_file(self):
        """Проверяет, что корень VFS должен быть каталогом."""
        self.assert_vfs_error(
            {"root": {"type": "file"}}, "root must be a directory")

    def test_missing_root(self):
        """Проверяет отсутствие корня VFS."""
        self.assert_vfs_error({"name": "x"}, "must be a JSON object")

    def test_unknown_type(self):
        """Проверяет неизвестный тип элемента."""
        self.assert_vfs_error({"root": {"type": "link"}}, "unknown type")

    def test_invalid_name(self):
        """Проверяет недопустимое имя файла."""
        self.assert_vfs_error({"root": {"type": "dir", "children": {
            "a/b": {"type": "file"}}}}, "invalid name")


class TestVfsInfo(unittest.TestCase):
    """Проверяет служебную команду vfs-info."""

    def test_vfs_info_output(self):
        """Проверяет вывод имени и хеша SHA-256."""
        vfs = load_vfs(example_path("three_levels.json"))
        output = io.StringIO()
        with redirect_stdout(output):
            execute_command(["vfs-info"], vfs)
        self.assertIn("VFS name: three_levels", output.getvalue())
        self.assertIn(f"SHA-256: {vfs.sha256}", output.getvalue())

    def test_vfs_info_without_vfs(self):
        """Проверяет vfs-info без загруженной VFS."""
        with self.assertRaisesRegex(CommandError, "not loaded"):
            execute_command(["vfs-info"])

    def test_vfs_info_with_arguments(self):
        """Проверяет vfs-info с лишними аргументами."""
        vfs = load_vfs(example_path("minimal.json"))
        with self.assertRaises(CommandError):
            execute_command(["vfs-info", "extra"], vfs)


if __name__ == "__main__":
    unittest.main()