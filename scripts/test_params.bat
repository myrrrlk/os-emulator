@echo off
rem Tests of the emulator command line parameters (Windows).
pushd "%~dp0.."

echo === Test 1: help ===
python -m src.main --help
echo Exit code: %ERRORLEVEL%

echo.
echo === Test 2: no parameters ===
echo exit | python -m src.main
echo Exit code: %ERRORLEVEL%

echo.
echo === Test 3: only --vfs ===
echo exit | python -m src.main --vfs vfs\minimal.json
echo Exit code: %ERRORLEVEL%

echo.
echo === Test 4: only --script ===
python -m src.main --script startup\basic.txt
echo Exit code: %ERRORLEVEL%

echo.
echo === Test 5: --vfs and --script ===
python -m src.main --vfs vfs\minimal.json --script startup\basic.txt
echo Exit code: %ERRORLEVEL%

echo.
echo === Test 6: script without exit, then interactive mode ===
echo exit | python -m src.main --vfs vfs\minimal.json ^
    --script startup\no_exit.txt
echo Exit code: %ERRORLEVEL%

echo.
echo === Test 7: unknown parameter ===
python -m src.main --unknown
echo Exit code: %ERRORLEVEL%
popd