@echo off
rem Tests of errors in the startup script (Windows).
pushd "%~dp0.."

echo === Test 1: unknown command ===
python -m src.main --vfs vfs\minimal.json ^
    --script startup\error_unknown.txt
echo Exit code: %ERRORLEVEL%

echo.
echo === Test 2: unclosed quote ===
python -m src.main --vfs vfs\minimal.json ^
    --script startup\error_syntax.txt
echo Exit code: %ERRORLEVEL%

echo.
echo === Test 3: wrong arguments of cd ===
python -m src.main --vfs vfs\minimal.json ^
    --script startup\error_arguments.txt
echo Exit code: %ERRORLEVEL%

echo.
echo === Test 4: wrong arguments of exit ===
python -m src.main --script startup\error_exit.txt
echo Exit code: %ERRORLEVEL%

echo.
echo === Test 5: startup script does not exist ===
python -m src.main --vfs vfs\minimal.json ^
    --script startup\missing.txt
echo Exit code: %ERRORLEVEL%
popd