#!/bin/sh
# Tests of errors in the startup script (Linux / macOS).
cd "$(dirname "$0")/.." || exit 1

echo "=== Test 1: unknown command ==="
python3 -m src.main --vfs vfs/minimal.json \
    --script startup/error_unknown.txt
echo "Exit code: $?"

echo
echo "=== Test 2: unclosed quote ==="
python3 -m src.main --vfs vfs/minimal.json \
    --script startup/error_syntax.txt
echo "Exit code: $?"

echo
echo "=== Test 3: wrong arguments of cd ==="
python3 -m src.main --vfs vfs/minimal.json \
    --script startup/error_arguments.txt
echo "Exit code: $?"

echo
echo "=== Test 4: wrong arguments of exit ==="
python3 -m src.main --script startup/error_exit.txt
echo "Exit code: $?"

echo
echo "=== Test 5: startup script does not exist ==="
python3 -m src.main --vfs vfs/minimal.json \
    --script startup/missing.txt
echo "Exit code: $?"