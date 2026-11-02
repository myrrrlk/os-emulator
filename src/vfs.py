"""Виртуальная файловая система (VFS), загружаемая из JSON-файла.

Вся VFS хранится в памяти. Исходный JSON-файл только читается
и никогда не изменяется.
"""

import base64
import binascii
import hashlib
import json
import os
from dataclasses import dataclass, field


TYPE_DIRECTORY = "dir"
TYPE_FILE = "file"
ENCODING_TEXT = "text"
ENCODING_BASE64 = "base64"
PATH_SEPARATOR = "/"
RESERVED_NAMES = (".", "..")


class VfsError(Exception):
    """Ошибка загрузки или структуры VFS."""


@dataclass
class VfsFile:
    """Файл VFS. Содержимое хранится в памяти в виде байтов."""

    name: str
    data: bytes


@dataclass
class VfsDirectory:
    """Каталог VFS со словарём вложенных файлов и каталогов."""

    name: str
    children: dict = field(default_factory=dict)


@dataclass
class Vfs:
    """Загруженная VFS: имя, хеш исходных данных и корневой каталог."""

    name: str
    sha256: str
    root: VfsDirectory


def read_vfs_file(path):
    """Читает JSON-файл VFS целиком как байты."""
    try:
        with open(path, "rb") as vfs_file:
            return vfs_file.read()
    except OSError as error:
        raise VfsError(f"cannot read VFS file '{path}'.") from error


def parse_json(raw_data, path):
    """Преобразует байты JSON-файла в объекты Python."""
    try:
        return json.loads(raw_data)
    except ValueError as error:
        raise VfsError(f"VFS file '{path}' is not valid JSON.") from error


def join_path(parent_path, name):
    """Соединяет путь родительского каталога и имя элемента."""
    return parent_path.rstrip(PATH_SEPARATOR) + PATH_SEPARATOR + name


def check_name(name, path):
    """Проверяет, что имя файла или каталога допустимо."""
    if not name or PATH_SEPARATOR in name or name in RESERVED_NAMES:
        raise VfsError(f"invalid name '{name}' in '{path}'.")


def decode_content(content, encoding, path):
    """Декодирует содержимое файла из JSON в байты."""
    if encoding == ENCODING_TEXT:
        return content.encode("utf-8")
    if encoding == ENCODING_BASE64:
        try:
            return base64.b64decode(content, validate=True)
        except binascii.Error as error:
            message = f"file '{path}' contains invalid base64 data."
            raise VfsError(message) from error
    raise VfsError(f"file '{path}' has unknown encoding '{encoding}'.")


def build_file(name, description, path):
    """Создаёт файл VFS из его описания в JSON."""
    content = description.get("content", "")
    if not isinstance(content, str):
        raise VfsError(f"content of file '{path}' must be a string.")
    encoding = description.get("encoding", ENCODING_TEXT)
    return VfsFile(name, decode_content(content, encoding, path))


def build_directory(name, description, path):
    """Создаёт каталог VFS и рекурсивно всё его содержимое."""
    children = description.get("children", {})
    if not isinstance(children, dict):
        raise VfsError(f"children of '{path}' must be a JSON object.")

    directory = VfsDirectory(name)
    for child_name, child_description in children.items():
        child_path = join_path(path, child_name)
        check_name(child_name, child_path)
        directory.children[child_name] = build_node(
            child_name, child_description, child_path)
    return directory


def build_node(name, description, path):
    """Создаёт файл или каталог VFS в зависимости от поля type."""
    if not isinstance(description, dict):
        raise VfsError(f"node '{path}' must be a JSON object.")

    node_type = description.get("type")
    if node_type == TYPE_DIRECTORY:
        return build_directory(name, description, path)
    if node_type == TYPE_FILE:
        return build_file(name, description, path)
    raise VfsError(f"node '{path}' has unknown type '{node_type}'.")


def default_vfs_name(path):
    """Возвращает имя VFS по имени файла без расширения."""
    return os.path.splitext(os.path.basename(path))[0]


def load_vfs(path):
    """Загружает VFS из JSON-файла в память.

    Хеш SHA-256 считается по байтам исходного файла.
    При любой ошибке выбрасывает VfsError.
    """
    raw_data = read_vfs_file(path)
    document = parse_json(raw_data, path)
    if not isinstance(document, dict):
        raise VfsError("VFS file must contain a JSON object.")

    name = document.get("name", default_vfs_name(path))
    if not isinstance(name, str) or not name:
        raise VfsError("VFS name must be a non-empty string.")

    root = build_node(PATH_SEPARATOR, document.get("root"),
                      PATH_SEPARATOR)
    if not isinstance(root, VfsDirectory):
        raise VfsError("VFS root must be a directory.")

    return Vfs(name, hashlib.sha256(raw_data).hexdigest(), root)


def count_nodes(directory):
    """Возвращает число каталогов и файлов внутри каталога.

    Сам каталог в подсчёт не входит.
    """
    directories = 0
    files = 0
    for child in directory.children.values():
        if isinstance(child, VfsDirectory):
            sub_directories, sub_files = count_nodes(child)
            directories += 1 + sub_directories
            files += sub_files
        else:
            files += 1
    return directories, files