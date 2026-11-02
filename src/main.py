"""Консольный эмулятор командной оболочки UNIX-подобной ОС."""

import argparse
import getpass
import os
import shlex
import socket
import sys


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


def command_ls(arguments):
    """Команда-заглушка ls: выводит своё имя и аргументы."""
    print_stub("ls", arguments)
    return True


def command_cd(arguments):
    """Команда-заглушка cd: принимает не более одного аргумента."""
    if len(arguments) > MAX_CD_ARGUMENTS:
        raise CommandError("cd accepts at most one argument.")
    print_stub("cd", arguments)
    return True


def command_exit(arguments):
    """Команда exit: сообщает, что работу нужно завершить."""
    if arguments:
        raise CommandError("exit does not accept arguments.")
    return False


COMMANDS = {
    "ls": command_ls,
    "cd": command_cd,
    "exit": command_exit,
}


def execute_command(tokens):
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
    return handler(arguments)


def execute_line(command_line):
    """Разбирает и выполняет одну строку ввода."""
    return execute_command(parse_input(command_line))


def run_repl():
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
            if not execute_line(command_line):
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


def run_script(path):
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
            if not execute_line(line):
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


def main(argv=None):
    """Точка входа: разбирает параметры, выполняет скрипт и REPL.

    Возвращает код завершения программы.
    """
    args = parse_arguments(argv)
    print_config(args)

    if args.script is not None:
        try:
            if not run_script(args.script):
                return EXIT_SUCCESS
        except ScriptError as error:
            print(f"Error: {error}")
            return EXIT_FAILURE

    run_repl()
    return EXIT_SUCCESS


if __name__ == "__main__":
    sys.exit(main())