#!/bin/sh
# Tests of the emulator with different VFS (Linux / macOS).
cd "$(dirname "$0")/.." || exit 1

echo "=== Test 1: minimal VFS (empty root) ==="
python3 -m src.main --vfs vfs/minimal.json --script startup/vfs_info.txt
echo "Exit code: $?"

echo
echo "=== Test 2: VFS with several files (text and base64) ==="
python3 -m src.main --vfs vfs/several_files.json \
    --script startup/vfs_info.txt
echo "Exit code: $?"

echo
echo "=== Test 3: VFS with 3+ levels of files and directories ==="
python3 -m src.main --vfs vfs/three_levels.json \
    --script startup/vfs_info.txt
echo "Exit code: $?"

echo
echo "=== Test 4: full test of all commands ==="
python3 -m src.main --vfs vfs/three_levels.json \
    --script startup/full_test.txt
echo "Exit code: $?"

echo
echo "=== Test 5: VFS in interactive mode ==="
echo vfs-info | python3 -m src.main --vfs vfs/several_files.json
echo "Exit code: $?"