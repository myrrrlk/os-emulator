Общее описание

Программа представляет собой консольное приложение (CLI), которое эмулирует работу командной строки UNIX-подобной операционной системы. Эмулятор запускается в обычном терминале, выводит приглашение к вводу, читает команды пользователя, разбирает их и выполняет.

Текущий этап - Этап 1. REPL. Это минимальный прототип: диалог с пользователем уже работает, но команды ls и cd пока являются заглушками и только выводят своё имя и аргументы.

Цикл работы программы (REPL - Read, Eval, Print, Loop):

Вывести приглашение username@hostname:каталог$.
Прочитать строку, введённую пользователем.
Разобрать строку на команду и аргументы с учётом кавычек.
Выполнить команду или вывести сообщение об ошибке.
Повторять, пока не введена команда exit.
Требования
Python 3.8 или новее.
Сторонние библиотеки не нужны, используется только стандартная библиотека Python.
Структура проекта
os-emulator/
src/
__init__.py
main.py — исходный код эмулятора tests/
test_main.py   — автоматические тесты
.gitignore
README.md
run.bat  — запуск в Windows
run.sh   — запуск в Linux и macOS
Описание функций

Все функции находятся в файле src/main.py.

build_prompt()

Формирует строку приглашения на основе реальных данных ОС:

имя пользователя — getpass.getuser();
имя компьютера — socket.gethostname();
текущий каталог — os.getcwd().

Если текущий каталог совпадает с домашним, он отображается как ~. Если текущий каталог находится внутри домашнего, начало пути заменяется на ~. Иначе выводится полный путь.

Возвращает строку вида user@host:~/projects$ .

parse_input(command_line)

Разбирает введённую строку на список слов с помощью модуля shlex. Аргументы в кавычках считаются одним словом:

ls "my folder"   ["ls", "my folder"]

Если кавычка не закрыта, функция выбрасывает ValueError.

print_stub(name, arguments)

Выводит имя команды-заглушки и список её аргументов в формате имя: [аргументы].

execute_command(tokens)

Выполняет команду, переданную в виде списка токенов. Первый токен — имя команды, остальные — аргументы.

Возвращает:

True — продолжить работу REPL;
False — завершить работу (команда exit).

Пустой ввод игнорируется.

run()

Запускает основной цикл программы: выводит приглашение, читает ввод, вызывает parse_input и execute_command. Завершается по команде exit или по концу ввода (Ctrl+D в Linux/macOS, Ctrl+Z и Enter в Windows).

Настройки
Константа	Значение	Назначение
MAX_CD_ARGUMENTS	1	Максимальное число аргументов команды cd
Поддерживаемые команды
Команда	Описание
ls [аргументы]	Заглушка. Выводит имя и аргументы
cd [каталог]	Заглушка. Принимает не более 1 аргумента
exit	Завершает работу. Аргументы не принимает
Обработка ошибок
Ситуация	Сообщение
Неизвестная команда	Error: unknown command '<имя>'.
Незакрытая кавычка	Error: invalid command syntax.
У cd больше одного аргумента	Error: cd accepts at most one argument.
У exit есть аргументы	Error: exit does not accept arguments.

После сообщения об ошибке программа продолжает работу.

Сборка и запуск

Python — интерпретируемый язык, поэтому отдельная сборка не требуется.

Windows:

run.bat

Linux / macOS:

chmod +x run.sh
./run.sh

Запуск без скриптов (из корня проекта):

python src/main.py
Запуск тестов

Из корня проекта:

python -m unittest discover -s tests -v

Тесты проверяют:

разбор аргументов в кавычках;
ошибку при незакрытой кавычке;
вывод команд-заглушек ls и cd;
ошибку при лишних аргументах cd и exit;
обработку неизвестной команды;
завершение работы командой exit.
Примеры использования

Запуск и работа команд-заглушек:

Asus@DESKTOP-07G7B6J:~\OneDrive\Desktop\os-emulator$ ls
ls: []
sus@DESKTOP-07G7B6J:~\OneDrive\Desktop\os-emulator$ ls src tests
ls: ['src', 'tests']
sus@DESKTOP-07G7B6J:~\OneDrive\Desktop\os-emulator$ cd Documents
cd: ['Documents']

Аргументы в кавычках:

sus@DESKTOP-07G7B6J:~\OneDrive\Desktop\os-emulator$ ls "my folder"
ls: ['my folder']
sus@DESKTOP-07G7B6J:~\OneDrive\Desktop\os-emulator$ cd "Program Files"
cd: ['Program Files']]

Обработка ошибок:

sus@DESKTOP-07G7B6J:~\OneDrive\Desktop\os-emulator$ foo
Error: unknown command 'foo'.
sus@DESKTOP-07G7B6J:~\OneDrive\Desktop\os-emulator$ ls "my folder
Error: invalid command syntax.
sus@DESKTOP-07G7B6J:~\OneDrive\Desktop\os-emulator$ cd one two
Error: cd accepts at most one argument.
sus@DESKTOP-07G7B6J:~\OneDrive\Desktop\os-emulator$ exit now
Error: exit does not accept arguments.

Пустой ввод и завершение работы:

sus@DESKTOP-07G7B6J:~\OneDrive\Desktop\os-emulator$
sus@DESKTOP-07G7B6J:~\OneDrive\Desktop\os-emulator$ exit