Описание

Программа запускается в обычном терминале и ведет себя похоже на bash: показывает приглашение вида пользователь@компьютер:папка$, читает команду, разбирает ее и выполняет. Имя пользователя, имя компьютера и текущая папка берутся из настоящей системы.

Сейчас сделано три этапа:

этап 1 (REPL): цикл ввода команд, разбор аргументов в кавычках, команды-заглушки ls и cd, команда exit, сообщения об ошибках;
этап 2 (конфигурация): параметры командной строки --vfs и --script, вывод параметров при запуске, выполнение стартового скрипта;
этап 3 (VFS): загрузка виртуальной файловой системы из JSON-файла в память и служебная команда vfs-info.

Команды ls и cd пока ничего не делают, а только печатают свое имя и аргументы.

Для работы нужен Python 3.8 или новее. Сторонние библиотеки не нужны.

Структура
src/main.py        оболочка: команды, REPL, стартовый скрипт, параметры
src/vfs.py         загрузка VFS из JSON
tests/test_main.py тесты оболочки
tests/test_vfs.py  тесты VFS и команды vfs-info
vfs/               примеры VFS
startup/           стартовые скрипты для эмулятора
scripts/           скрипты Windows и Linux, которые запускают эмулятор
                   с разными параметрами
run.bat, run.sh    запуск эмулятора
Параметры запуска
python -m src.main [--vfs PATH] [--script PATH]
--vfs PATH - путь к JSON-файлу с VFS;
--script PATH - путь к стартовому скрипту;
-h, --help - справка.

Оба параметра можно не указывать. При запуске эмулятор всегда печатает, с какими параметрами он запущен (отладочный вывод), например:

[debug] Emulator parameters:
[debug]   VFS path:       vfs\minimal.json
[debug]   startup script: (not set)
[debug] VFS 'minimal' loaded into memory.

Если VFS не получилось загрузить (нет файла, ошибка в JSON, неправильный base64 и т.п.), печатается ошибка и программа завершается с кодом 1. Если передать неизвестный параметр, argparse выведет подсказку и программа завершится с кодом 2.

VFS

VFS хранится в JSON-файле. Файл читается один раз при запуске, после этого вся файловая система лежит в памяти в виде объектов Python. Сам JSON-файл программа не меняет и никуда не распаковывает.

Пример файла:

json
{
  "name": "example",
  "root": {
    "type": "dir",
    "children": {
      "readme.txt": {"type": "file", "content": "Hello!\n"},
      "data.bin": {
        "type": "file",
        "encoding": "base64",
        "content": "AAECAw=="
      },
      "docs": {"type": "dir", "children": {}}
    }
  }
}
name - имя VFS. Если его нет, берется имя файла без .json.
root - корневая папка, у нее обязательно "type": "dir".
type - dir для папки или file для файла.
children - содержимое папки: имя -> элемент. Можно не писать, тогда папка пустая.
content - содержимое файла. Можно не писать, тогда файл пустой.
encoding - text (по умолчанию) или base64. Base64 нужен для двоичных файлов, потому что в JSON можно хранить только текст.

Имя файла или папки не может быть пустым, содержать / или быть . или ...

Хеш SHA-256 считается по байтам JSON-файла. Если в файле поменять хотя бы один символ (даже перевод строки), хеш будет другим. Чтобы на Windows и Linux хеш получался одинаковый, в .gitattributes для .json задан перевод строки LF.

Примеры VFS в папке vfs:

minimal.json - пустая корневая папка;
several_files.json - четыре файла, два из них в base64;
three_levels.json - несколько уровней папок, например /home/user/documents/report.txt;
broken_json.json и broken_base64.json - испорченные файлы для проверки ошибок.
Стартовый скрипт

Это обычный текстовый файл, в котором на каждой строке записана одна команда эмулятора. Пустые строки и строки, которые начинаются с #, пропускаются.

Команды из скрипта выполняются по очереди. Перед каждой командой печатается приглашение и сама команда, а потом ее результат, так что на экране это выглядит так же, как если бы команды вводили руками.

Если какая-то команда завершилась с ошибкой, скрипт сразу останавливается, печатается номер строки с ошибкой и программа завершается с кодом 1. Если в скрипте есть exit, программа завершается с кодом 0. Если скрипт закончился, а exit в нем не было, эмулятор переходит в обычный интерактивный режим.

Скрипт startup/full_test.txt проверяет все команды всех этапов. Его нужно запускать с VFS, например с vfs\three_levels.json.

Команды
ls [аргументы] - заглушка, печатает ls: [аргументы];
cd [папка] - заглушка, печатает cd: [аргументы], принимает не больше одного аргумента;
vfs-info - печатает имя VFS, хеш SHA-256 и сколько в ней папок и файлов, аргументы не принимает;
exit - выход, аргументы не принимает.

Аргументы можно писать в двойных или одинарных кавычках, тогда текст с пробелами считается одним аргументом: ls "my folder".

Сообщения об ошибках:

Error: unknown command 'foo'.                  неизвестная команда
Error: invalid command syntax.                 не закрыта кавычка
Error: cd accepts at most one argument.        лишние аргументы у cd
Error: exit does not accept arguments.         аргументы у exit
Error: vfs-info does not accept arguments.     аргументы у vfs-info
Error: VFS is not loaded.                      vfs-info без --vfs
Error: startup script stopped at line N: ...   ошибка в стартовом скрипте
Error: cannot read startup script '...'.       нет файла скрипта
Error: cannot read VFS file '...'.             нет файла VFS
Error: VFS file '...' is not valid JSON.       ошибка в JSON
Error: file '...' contains invalid base64 data. неправильный base64
Error: node '...' has unknown type '...'.      неизвестный type в VFS

В интерактивном режиме после ошибки можно продолжать вводить команды.

Функции
src/main.py
build_prompt() - собирает приглашение. Использует getpass.getuser(), socket.gethostname() и os.getcwd(), домашнюю папку заменяет на ~.
parse_input(command_line) - делит строку на слова через shlex.split, поэтому правильно обрабатываются кавычки. Если кавычка не закрыта, выбрасывает CommandError.
print_stub(name, arguments) - печатает имя команды и аргументы.
command_ls, command_cd, command_exit, command_vfs_info - сами команды. Каждая принимает список аргументов и загруженную VFS (или None, если VFS не задана) и возвращает True, если работа продолжается, или False, если надо выйти. При ошибке выбрасывают CommandError.
COMMANDS - словарь, в котором имени команды соответствует ее функция.
execute_command(tokens, vfs) - находит команду в COMMANDS и вызывает ее. Если такой команды нет, выбрасывает CommandError.
execute_line(command_line, vfs) - разбирает строку и выполняет команду.
run_repl(vfs) - интерактивный режим. Ловит CommandError и печатает ошибку. Выход по exit или по концу ввода (Ctrl+Z и Enter в Windows, Ctrl+D в Linux), Ctrl+C просто показывает новое приглашение.
read_script(path) - читает файл скрипта, если файла нет, выбрасывает ScriptError.
is_script_command(line) - проверяет, что строка не пустая и не комментарий.
run_script(path, vfs) - выполняет стартовый скрипт и останавливается на первой ошибке (выбрасывает ScriptError с номером строки).
parse_arguments(argv) - разбирает параметры через argparse.
describe_parameter(value), print_config(args) - отладочный вывод параметров.
load_vfs_if_set(path) - загружает VFS, если путь передан.
main(argv) - точка входа, возвращает код завершения.
src/vfs.py
VfsFile - файл: имя и содержимое в байтах.
VfsDirectory - папка: имя и словарь children с вложенными файлами и папками.
Vfs - загруженная VFS: имя, хеш SHA-256 и корневая папка.
VfsError - ошибка загрузки VFS.
load_vfs(path) - главная функция модуля. Читает файл, считает хеш, разбирает JSON и строит дерево папок и файлов.
read_vfs_file(path) - читает файл как байты.
parse_json(raw_data, path) - разбирает JSON.
build_node, build_directory, build_file - создают папку или файл по описанию из JSON. build_directory вызывает build_node для каждого вложенного элемента, поэтому вложенность может быть любой.
decode_content(content, encoding, path) - переводит содержимое файла в байты (из обычного текста или из base64).
check_name(name, path) - проверяет имя файла или папки.
join_path(parent_path, name) - собирает путь для сообщений об ошибках.
default_vfs_name(path) - имя VFS по имени файла.
count_nodes(directory) - считает папки и файлы внутри папки.

Константы (настройки):

MAX_CD_ARGUMENTS = 1 - сколько аргументов можно передать в cd;
EXIT_SUCCESS = 0, EXIT_FAILURE = 1 - коды завершения;
COMMENT_PREFIX = "#" - с чего начинается комментарий в скрипте;
NOT_SET = "(not set)" - что печатать, если параметр не задан;
TYPE_DIRECTORY = "dir", TYPE_FILE = "file" - типы элементов VFS;
ENCODING_TEXT = "text", ENCODING_BASE64 = "base64" - способы записи содержимого файла;
PATH_SEPARATOR = "/" - разделитель пути в VFS;
RESERVED_NAMES = (".", "..") - запрещенные имена.
Запуск

Сборка не нужна. Запускать нужно из корня проекта.

Windows:

run.bat
run.bat --vfs vfs\three_levels.json --script startup\full_test.txt

Linux:

./run.sh
./run.sh --vfs vfs/three_levels.json --script startup/full_test.txt

Или напрямую:

python -m src.main --vfs vfs\three_levels.json --script startup\full_test.txt

Скрипты для проверки лежат в папке scripts (есть .bat для Windows и .sh для Linux). После каждого запуска эмулятора они печатают код завершения.

test_params - справка, запуск без параметров, только --vfs, только --script, оба параметра сразу, скрипт без exit, неизвестный параметр;
test_script_errors - разные ошибки в стартовом скрипте и несуществующий файл скрипта;
test_vfs - минимальная VFS, VFS с несколькими файлами, VFS с несколькими уровнями папок, полный тест всех команд, vfs-info в интерактивном режиме;
test_vfs_errors - нет файла VFS, ошибка в JSON, неправильный base64, vfs-info без VFS и с аргументами.
scripts\test_vfs.bat
scripts\test_vfs_errors.bat
Тесты
python -m unittest discover -s tests -v

В test_main.py проверяются разбор строки с кавычками, все команды и их ошибки, разбор параметров, отладочный вывод, работа стартового скрипта и коды завершения. В test_vfs.py проверяется загрузка всех примеров VFS, хеш SHA-256, то что исходный файл не меняется, текст и base64, ошибки загрузки и команда vfs-info.

Примеры

Полный тест всех команд. Скрипт останавливается на ошибке, поэтому последняя строка (ls never-executed) не выполняется:

> python -m src.main --vfs vfs\three_levels.json --script startup\full_test.txt
[debug] Emulator parameters:
[debug]   VFS path:       vfs\three_levels.json
[debug]   startup script: startup\full_test.txt
[debug] VFS 'three_levels' loaded into memory.
Asus@DESKTOP-O7G7B6J:~\OneDrive\Desktop\os-emulator$ vfs-info
VFS name: three_levels
SHA-256: 3d6611e60e4bd263a3c3cd5834d6abc9d2dfb07f32ed87e7a05073b47a7ecbf3
Directories: 5, files: 5
Asus@DESKTOP-O7G7B6J:~\OneDrive\Desktop\os-emulator$ ls
ls: []
Asus@DESKTOP-O7G7B6J:~\OneDrive\Desktop\os-emulator$ ls home etc
ls: ['home', 'etc']
Asus@DESKTOP-O7G7B6J:~\OneDrive\Desktop\os-emulator$ ls "my folder" 'other folder'
ls: ['my folder', 'other folder']
Asus@DESKTOP-O7G7B6J:~\OneDrive\Desktop\os-emulator$ cd
cd: []
Asus@DESKTOP-O7G7B6J:~\OneDrive\Desktop\os-emulator$ cd home
cd: ['home']
Asus@DESKTOP-O7G7B6J:~\OneDrive\Desktop\os-emulator$ cd "Program Files"
cd: ['Program Files']
Asus@DESKTOP-O7G7B6J:~\OneDrive\Desktop\os-emulator$ cd one two
Error: startup script stopped at line 21: cd accepts at most one argument.

Минимальная VFS:

> python -m src.main --vfs vfs\minimal.json --script startup\vfs_info.txt
[debug] Emulator parameters:
[debug]   VFS path:       vfs\minimal.json
[debug]   startup script: startup\vfs_info.txt
[debug] VFS 'minimal' loaded into memory.
Asus@DESKTOP-O7G7B6J:~\OneDrive\Desktop\os-emulator$ vfs-info
VFS name: minimal
SHA-256: 5d43d80ea89c2bceeadfe166650ba5a4896c9046b69bd43b954cce8ef3eec689
Directories: 0, files: 0
Asus@DESKTOP-O7G7B6J:~\OneDrive\Desktop\os-emulator$ exit

Интерактивный режим с VFS из нескольких файлов:

> python -m src.main --vfs vfs\several_files.json
[debug] Emulator parameters:
[debug]   VFS path:       vfs\several_files.json
[debug]   startup script: (not set)
[debug] VFS 'several_files' loaded into memory.
Asus@DESKTOP-O7G7B6J:~\OneDrive\Desktop\os-emulator$ vfs-info
VFS name: several_files
SHA-256: cb88e13c33e4033bcdedc305d614bf2784cdb8224a340f9b933b74408b0bb31a
Directories: 0, files: 4
Asus@DESKTOP-O7G7B6J:~\OneDrive\Desktop\os-emulator$ vfs-info now
Error: vfs-info does not accept arguments.
Asus@DESKTOP-O7G7B6J:~\OneDrive\Desktop\os-emulator$ ls "my folder"
ls: ['my folder']
Asus@DESKTOP-O7G7B6J:~\OneDrive\Desktop\os-emulator$ foo
Error: unknown command 'foo'.
Asus@DESKTOP-O7G7B6J:~\OneDrive\Desktop\os-emulator$ exit

Ошибки загрузки VFS:

> python -m src.main --vfs vfs\broken_json.json
[debug] Emulator parameters:
[debug]   VFS path:       vfs\broken_json.json
[debug]   startup script: (not set)
Error: VFS file 'vfs\broken_json.json' is not valid JSON.

> python -m src.main --vfs vfs\broken_base64.json
[debug] Emulator parameters:
[debug]   VFS path:       vfs\broken_base64.json
[debug]   startup script: (not set)
Error: file '/image.bin' contains invalid base64 data.

> python -m src.main --vfs vfs\missing.json
[debug] Emulator parameters:
[debug]   VFS path:       vfs\missing.json
[debug]   startup script: (not set)
Error: cannot read VFS file 'vfs\missing.json'.

vfs-info без VFS:

> python -m src.main --script startup\vfs_info.txt
[debug] Emulator parameters:
[debug]   VFS path:       (not set)
[debug]   startup script: startup\vfs_info.txt
Asus@DESKTOP-O7G7B6J:~\OneDrive\Desktop\os-emulator$ vfs-info
Error: startup script stopped at line 2: VFS is not loaded.