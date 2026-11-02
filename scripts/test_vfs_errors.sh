#!/bin/sh
# Tests of VFS errors (Linux / macOS).
cd "$(dirname "$0")/.." || exit 1

echo "=== Test 1: VFS file does not exist ==="
python3 -m src.main --vfs vfs/missing.json --script startup/vfs_info.txt
echo "Exit code: $?"

echo
echo "=== Test 2: VFS file is not valid JSON ==="
python3 -m src.main --vfs vfs/broken_json.json \
    --script startup/vfs_info.txt
echo "Exit code: $?"

echo
echo "=== Test 3: VFS file contains invalid base64 ==="
python3 -m src.main --vfs vfs/broken_base64.json \
    --script startup/vfs_info.txt
echo "Exit code: $?"

echo
echo "=== Test 4: vfs-info without a loaded VFS ==="
python3 -m src.main --script startup/vfs_info.txt
echo "Exit code: $?"

echo
echo "=== Test 5: vfs-info with arguments ==="
python3 -m src.main --vfs vfs/minimal.json \
    --script startup/error_vfs_info.txt
echo "Exit code: $?"