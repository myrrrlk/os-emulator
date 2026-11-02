@echo off
rem Tests of VFS errors (Windows).
pushd "%~dp0.."

echo === Test 1: VFS file does not exist ===
python -m src.main --vfs vfs\missing.json --script startup\vfs_info.txt
echo Exit code: %ERRORLEVEL%

echo.
echo === Test 2: VFS file is not valid JSON ===
python -m src.main --vfs vfs\broken_json.json ^
    --script startup\vfs_info.txt
echo Exit code: %ERRORLEVEL%

echo.
echo === Test 3: VFS file contains invalid base64 ===
python -m src.main --vfs vfs\broken_base64.json ^
    --script startup\vfs_info.txt
echo Exit code: %ERRORLEVEL%

echo.
echo === Test 4: vfs-info without a loaded VFS ===
python -m src.main --script startup\vfs_info.txt
echo Exit code: %ERRORLEVEL%

echo.
echo === Test 5: vfs-info with arguments ===
python -m src.main --vfs vfs\minimal.json ^
    --script startup\error_vfs_info.txt
echo Exit code: %ERRORLEVEL%
popd