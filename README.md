# os-emulator

Эмулятор командной строки UNIX-подобной ОС на Python.
Учебный проект по дисциплине "Архитектура вычислительных машин и систем".

## Описание

Программа запускается в обычном терминале и ведет себя похоже на bash:
показывает приглашение вида `пользователь@компьютер:папка$`, читает
команду, разбирает ее и выполняет. Имя пользователя, имя компьютера и
текущая папка берутся из настоящей системы.

Сейчас сделано два этапа:

- этап 1 (REPL): цикл ввода команд, разбор аргументов в кавычках,
  команды-заглушки `ls` и `cd`, команда `exit`, сообщения об ошибках;
- этап 2 (конфигурация): параметры командной строки `--vfs` и `--script`,
  вывод параметров при запуске, выполнение стартового скрипта.

Команды `ls` и `cd` пока ничего не делают, а только печатают свое имя и
аргументы. Путь к VFS на этом этапе только запоминается и выводится,
загружать VFS эмулятор будет на следующем этапе.

Для работы нужен Python 3.8 или новее. Сторонние библиотеки не нужны.

## Структура

```
src/main.py        код эмулятора
tests/test_main.py тесты
startup/           стартовые скрипты для эмулятора
scripts/           скрипты Windows и Linux, которые запускают эмулятор
                   с разными параметрами
run.bat, run.sh    запуск эмулятора
```

## Параметры запуска

```
python -m src.main [--vfs PATH] [--script PATH]
```

- `--vfs PATH` - путь к файлу VFS;
- `--script PATH` - путь к стартовому скрипту;
- `-h`, `--help` - справка.

Оба параметра можно не указывать. При запуске эмулятор всегда печатает,
с какими параметрами он запущен (отладочный вывод), например:

```
[debug] Emulator parameters:
[debug]   VFS path:       (not set)
[debug]   startup script: startup\basic.txt
```

Если передать неизвестный параметр, argparse выведет подсказку и программа
завершится с кодом 2.

## Стартовый скрипт

Это обычный текстовый файл, в котором на каждой строке записана одна
команда эмулятора. Пустые строки и строки, которые начинаются с `#`,
пропускаются.

Команды из скрипта выполняются по очереди. Перед каждой командой
печатается приглашение и сама команда, а потом ее результат, так что
на экране это выглядит так же, как если бы команды вводили руками.

Если какая-то команда завершилась с ошибкой, скрипт сразу
останавливается, печатается номер строки с ошибкой и программа
завершается с кодом 1. Если в скрипте есть `exit`, программа завершается
с кодом 0. Если скрипт закончился, а `exit` в нем не было, эмулятор
переходит в обычный интерактивный режим.

## Команды

- `ls [аргументы]` - заглушка, печатает `ls: [аргументы]`;
- `cd [папка]` - заглушка, печатает `cd: [аргументы]`, принимает не больше
  одного аргумента;
- `exit` - выход, аргументы не принимает.

Аргументы можно писать в двойных или одинарных кавычках, тогда текст с
пробелами считается одним аргументом: `ls "my folder"`.

Сообщения об ошибках:

```
Error: unknown command 'foo'.                  неизвестная команда
Error: invalid command syntax.                 не закрыта кавычка
Error: cd accepts at most one argument.        лишние аргументы у cd
Error: exit does not accept arguments.         аргументы у exit
Error: startup script stopped at line N: ...   ошибка в стартовом скрипте
Error: cannot read startup script '...'.       нет файла скрипта
```

В интерактивном режиме после ошибки можно продолжать вводить команды.

## Функции

Все функции находятся в `src/main.py`.

- `build_prompt()` - собирает приглашение. Использует `getpass.getuser()`,
  `socket.gethostname()` и `os.getcwd()`, домашнюю папку заменяет на `~`.
- `parse_input(command_line)` - делит строку на слова через `shlex.split`,
  поэтому правильно обрабатываются кавычки. Если кавычка не закрыта,
  выбрасывает `CommandError`.
- `print_stub(name, arguments)` - печатает имя команды и аргументы.
- `command_ls`, `command_cd`, `command_exit` - сами команды. Каждая
  принимает список аргументов и возвращает `True`, если работа
  продолжается, или `False`, если надо выйти. При ошибке выбрасывают
  `CommandError`.
- `COMMANDS` - словарь, в котором имени команды соответствует ее функция.
- `execute_command(tokens)` - находит команду в `COMMANDS` и вызывает ее.
  Если такой команды нет, выбрасывает `CommandError`.
- `execute_line(command_line)` - разбирает строку и выполняет команду.
- `run_repl()` - интерактивный режим. Ловит `CommandError` и печатает
  ошибку. Выход по `exit` или по концу ввода (Ctrl+Z и Enter в Windows,
  Ctrl+D в Linux), Ctrl+C просто показывает новое приглашение.
- `read_script(path)` - читает файл скрипта, если файла нет, выбрасывает
  `ScriptError`.
- `is_script_command(line)` - проверяет, что строка не пустая и не
  комментарий.
- `run_script(path)` - выполняет стартовый скрипт и останавливается на
  первой ошибке (выбрасывает `ScriptError` с номером строки).
- `parse_arguments(argv)` - разбирает параметры через `argparse`.
- `describe_parameter(value)`, `print_config(args)` - отладочный вывод
  параметров.
- `main(argv)` - точка входа, возвращает код завершения.

Константы (настройки):

- `MAX_CD_ARGUMENTS = 1` - сколько аргументов можно передать в `cd`;
- `EXIT_SUCCESS = 0`, `EXIT_FAILURE = 1` - коды завершения;
- `COMMENT_PREFIX = "#"` - с чего начинается комментарий в скрипте;
- `NOT_SET = "(not set)"` - что печатать, если параметр не задан.

## Запуск

Сборка не нужна. Запускать нужно из корня проекта.

Windows:

```
run.bat
run.bat --vfs vfs\minimal.json --script startup\basic.txt
```

Linux:

```
./run.sh
./run.sh --vfs vfs/minimal.json --script startup/basic.txt
```

Или напрямую:

```
python -m src.main --script startup\basic.txt
```

Скрипты для проверки параметров лежат в папке `scripts`:

- `test_params.bat` / `test_params.sh` - справка, запуск без параметров,
  только `--vfs`, только `--script`, оба параметра сразу, скрипт без
  `exit`, неизвестный параметр;
- `test_script_errors.bat` / `test_script_errors.sh` - разные ошибки в
  стартовом скрипте и несуществующий файл скрипта.

После каждого запуска они печатают код завершения.

```
scripts\test_params.bat
scripts\test_script_errors.bat
```

## Тесты

```
python -m unittest discover -s tests -v
```

Проверяются разбор строки с кавычками, все команды и их ошибки, разбор
параметров, отладочный вывод, работа стартового скрипта и коды
завершения.

## Примеры

Справка:

```
PS C:\Users\Asus\OneDrive\Desktop\os-emulator> python -m src.main --help
usage: os-emulator [-h] [--vfs PATH] [--script PATH]

Emulator of a UNIX-like OS shell.

options:
  -h, --help     show this help message and exit
  --vfs PATH     path to the physical location of the VFS
  --script PATH  path to the startup script
```

Интерактивный режим:

```
PS C:\Users\Asus\OneDrive\Desktop\os-emulator> python -m src.main
[debug] Emulator parameters:
[debug]   VFS path:       (not set)
[debug]   startup script: (not set)
Asus@DESKTOP-O7G7B6J:~\OneDrive\Desktop\os-emulator$ ls
ls: []
Asus@DESKTOP-O7G7B6J:~\OneDrive\Desktop\os-emulator$ ls "my folder" docs
ls: ['my folder', 'docs']
Asus@DESKTOP-O7G7B6J:~\OneDrive\Desktop\os-emulator$ cd "Program Files"
cd: ['Program Files']
Asus@DESKTOP-O7G7B6J:~\OneDrive\Desktop\os-emulator$ cd one two
Error: cd accepts at most one argument.
Asus@DESKTOP-O7G7B6J:~\OneDrive\Desktop\os-emulator$ ls "my folder
Error: invalid command syntax.
Asus@DESKTOP-O7G7B6J:~\OneDrive\Desktop\os-emulator$ foo
Error: unknown command 'foo'.
Asus@DESKTOP-O7G7B6J:~\OneDrive\Desktop\os-emulator$ exit now
Error: exit does not accept arguments.
Asus@DESKTOP-O7G7B6J:~\OneDrive\Desktop\os-emulator$ exit
```

Стартовый скрипт без ошибок:

```
PS C:\Users\Asus\OneDrive\Desktop\os-emulator> python -m src.main --vfs vfs\minimal.json --script startup\basic.txt
[debug] Emulator parameters:
[debug]   VFS path:       vfs\minimal.json
[debug]   startup script: startup\basic.txt
Asus@DESKTOP-O7G7B6J:~\OneDrive\Desktop\os-emulator$ ls
ls: []
Asus@DESKTOP-O7G7B6J:~\OneDrive\Desktop\os-emulator$ ls src tests
ls: ['src', 'tests']
Asus@DESKTOP-O7G7B6J:~\OneDrive\Desktop\os-emulator$ ls "my folder" 'other folder'
ls: ['my folder', 'other folder']
Asus@DESKTOP-O7G7B6J:~\OneDrive\Desktop\os-emulator$ cd
cd: []
Asus@DESKTOP-O7G7B6J:~\OneDrive\Desktop\os-emulator$ cd docs
cd: ['docs']
Asus@DESKTOP-O7G7B6J:~\OneDrive\Desktop\os-emulator$ cd "Program Files"
cd: ['Program Files']
Asus@DESKTOP-O7G7B6J:~\OneDrive\Desktop\os-emulator$ exit
```

Ошибка в стартовом скрипте. Последняя строка скрипта (`ls never-executed`)
уже не выполняется:

```
PS C:\Users\Asus\OneDrive\Desktop\os-emulator> python -m src.main --script startup\error_unknown.txt
[debug] Emulator parameters:
[debug]   VFS path:       (not set)
[debug]   startup script: startup\error_unknown.txt
Asus@DESKTOP-O7G7B6J:~\OneDrive\Desktop\os-emulator$ ls
ls: []
Asus@DESKTOP-O7G7B6J:~\OneDrive\Desktop\os-emulator$ foo
Error: startup script stopped at line 3: unknown command 'foo'.
```

Файла скрипта нет:

```
PS C:\Users\Asus\OneDrive\Desktop\os-emulator> python -m src.main --script startup\missing.txt
[debug] Emulator parameters:
[debug]   VFS path:       (not set)
[debug]   startup script: startup\missing.txt
Error: cannot read startup script 'startup\missing.txt'.
```