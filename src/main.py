"""Консольный эмулятор командной оболочки UNIX-подобной ОС."""

import argparse
import getpass
import os
import shlex
import socket
import sys

from src.vfs import VfsError, count_nodes, load_vfs


MAX_CD_ARGUMENTS = 1
EXIT_SUCCESS = 0
EXIT_FAILURE = 1
COMMENT_PREFIX = "#"
NOT_SET = "(not set)"


class CommandError(Exception):
    """Ошибка выполнения команды эмулятора."""


class ScriptError(Exception):
    """Ошибка выполнения стартового скрипта."""


def build_prompt():
    """Создаёт приглашение на основе данных текущей ОС."""
    username = getpass.getuser()
    hostname = socket.gethostname()
    current_dir = os.getcwd()
    home_dir = os.path.expanduser("~")

    if current_dir == home_dir:
        display_dir = "~"
    elif current_dir.startswith(home_dir + os.sep):
        display_dir = "~" + current_dir[len(home_dir):]
    else:
        display_dir = current_dir

    return f"{username}@{hostname}:{display_dir}$ "


def parse_input(command_line):
    """Разбирает строку команды с учётом кавычек.

    При незакрытой кавычке выбрасывает CommandError.
    """
    try:
        return shlex.split(command_line)
    except ValueError as error:
        raise CommandError("invalid command syntax.") from error


def print_stub(name, arguments):
    """Выводит имя команды-заглушки и её аргументы."""
    print(f"{name}: {arguments}")


def command_ls(arguments, vfs):
    """Команда-заглушка ls: выводит своё имя и аргументы.

    Параметр vfs пока не используется.
    """
    print_stub("ls", arguments)
    return True


def command_cd(arguments, vfs):
    """Команда-заглушка cd: принимает не более одного аргумента.

    Параметр vfs пока не используется.
    """
    if len(arguments) > MAX_CD_ARGUMENTS:
        raise CommandError("cd accepts at most one argument.")
    print_stub("cd", arguments)
    return True


def command_exit(arguments, vfs):
    """Команда exit: сообщает, что работу нужно завершить."""
    if arguments:
        raise CommandError("exit does not accept arguments.")
    return False


def command_vfs_info(arguments, vfs):
    """Служебная команда vfs-info: выводит имя и хеш SHA-256 VFS."""
    if arguments:
        raise CommandError("vfs-info does not accept arguments.")
    if vfs is None:
        raise CommandError("VFS is not loaded.")
    directories, files = count_nodes(vfs.root)
    print(f"VFS name: {vfs.name}")
    print(f"SHA-256: {vfs.sha256}")
    print(f"Directories: {directories}, files: {files}")
    return True


COMMANDS = {
    "ls": command_ls,
    "cd": command_cd,
    "exit": command_exit,
    "vfs-info": command_vfs_info,
}


def execute_command(tokens, vfs=None):
    """Выполняет команду, заданную списком токенов.

    Возвращает False, если работу нужно завершить, иначе True.
    При ошибке выбрасывает CommandError.
    """
    if not tokens:
        return True

    name = tokens[0]
    arguments = tokens[1:]
    handler = COMMANDS.get(name)
    if handler is None:
        raise CommandError(f"unknown command '{name}'.")
    return handler(arguments, vfs)


def execute_line(command_line, vfs=None):
    """Разбирает и выполняет одну строку ввода."""
    return execute_command(parse_input(command_line), vfs)


def run_repl(vfs=None):
    """Запускает интерактивный цикл командной оболочки.

    Если ввод перенаправлен из файла или канала, введённая строка
    повторяется на экране, чтобы вывод выглядел как диалог.
    """
    while True:
        try:
            command_line = input(build_prompt())
        except EOFError:
            print()
            break
        except KeyboardInterrupt:
            print()
            continue

        if not sys.stdin.isatty():
            print(command_line)

        try:
            if not execute_line(command_line, vfs):
                break
        except CommandError as error:
            print(f"Error: {error}")


def read_script(path):
    """Читает стартовый скрипт и возвращает список его строк."""
    try:
        with open(path, encoding="utf-8") as script_file:
            return script_file.read().splitlines()
    except (OSError, UnicodeDecodeError) as error:
        message = f"cannot read startup script '{path}'."
        raise ScriptError(message) from error


def is_script_command(line):
    """Проверяет, что строка скрипта не пустая и не комментарий."""
    stripped = line.strip()
    return bool(stripped) and not stripped.startswith(COMMENT_PREFIX)


def run_script(path, vfs=None):
    """Выполняет стартовый скрипт, имитируя диалог с пользователем.

    Перед каждой командой выводится приглашение и сама команда.
    Возвращает False, если скрипт выполнил exit, иначе True.
    На первой ошибке останавливается и выбрасывает ScriptError.
    """
    for number, line in enumerate(read_script(path), start=1):
        if not is_script_command(line):
            continue
        print(build_prompt() + line)
        try:
            if not execute_line(line, vfs):
                return False
        except CommandError as error:
            message = f"startup script stopped at line {number}: {error}"
            raise ScriptError(message) from error
    return True


def parse_arguments(argv=None):
    """Разбирает параметры командной строки эмулятора."""
    parser = argparse.ArgumentParser(
        prog="os-emulator",
        description="Emulator of a UNIX-like OS shell.",
    )
    parser.add_argument(
        "--vfs", metavar="PATH",
        help="path to the physical location of the VFS",
    )
    parser.add_argument(
        "--script", metavar="PATH",
        help="path to the startup script",
    )
    return parser.parse_args(argv)


def describe_parameter(value):
    """Возвращает значение параметра для отладочного вывода."""
    return NOT_SET if value is None else value


def print_config(args):
    """Выводит отладочную информацию о параметрах запуска."""
    print("[debug] Emulator parameters:")
    print(f"[debug]   VFS path:       {describe_parameter(args.vfs)}")
    print(f"[debug]   startup script: {describe_parameter(args.script)}")


def load_vfs_if_set(path):
    """Загружает VFS, если путь задан, иначе возвращает None."""
    if path is None:
        return None
    vfs = load_vfs(path)
    print(f"[debug] VFS '{vfs.name}' loaded into memory.")
    return vfs


def main(argv=None):
    """Точка входа эмулятора.

    Разбирает параметры, загружает VFS, выполняет стартовый скрипт
    и запускает REPL. Возвращает код завершения программы.
    """
    args = parse_arguments(argv)
    print_config(args)

    try:
        vfs = load_vfs_if_set(args.vfs)
        if args.script is not None and not run_script(args.script, vfs):
            return EXIT_SUCCESS
    except (VfsError, ScriptError) as error:
        print(f"Error: {error}")
        return EXIT_FAILURE

    run_repl(vfs)
    return EXIT_SUCCESS


if __name__ == "__main__":
    sys.exit(main())