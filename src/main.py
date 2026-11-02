
"""Минимальный прототип консольного эмулятора ОС."""

import getpass
import os
import shlex
import socket


MAX_CD_ARGUMENTS = 1


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
    """Разбирает строку команды с учётом кавычек."""
    return shlex.split(command_line)


def print_stub(name, arguments):
    """Выводит имя команды-заглушки и её аргументы."""
    print(f"{name}: {arguments}")


def execute_command(tokens):
    """Выполняет команду и возвращает состояние REPL."""
    if not tokens:
        return True

    name = tokens[0]
    arguments = tokens[1:]

    if name == "exit":
        if arguments:
            print("Error: exit does not accept arguments.")
            return True
        return False

    if name == "ls":
        print_stub(name, arguments)
        return True

    if name == "cd":
        if len(arguments) > MAX_CD_ARGUMENTS:
            print("Error: cd accepts at most one argument.")
            return True
        print_stub(name, arguments)
        return True

    print(f"Error: unknown command '{name}'.")
    return True


def run():
    """Запускает интерактивный цикл командной оболочки."""
    while True:
        try:
            command_line = input(build_prompt())
        except EOFError:
            print()
            break

        try:
            tokens = parse_input(command_line)
        except ValueError:
            print("Error: invalid command syntax.")
            continue

        if not execute_command(tokens):
            break


if __name__ == "__main__":
    run()
