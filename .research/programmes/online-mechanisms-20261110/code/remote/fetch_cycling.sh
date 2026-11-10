#!/bin/bash
# Stage F · fetch the official ISU-ILCC Cycling_json.zip (10.2 GB) on campus-h3.
# Official metadata (figshare API, article 22582234, v2, published 2023-12-21):
#   name    Cycling_json.zip
#   url     https://ndownloader.figshare.com/files/43777470
#   md5     27ac156b31f7c35d4f27a78267c0dd56
#   size    10208088439
# Resumable. Verifies size and md5 before declaring success. Never writes to git.
set -u
DEST=/home/user/dline/data
URL="https://ndownloader.figshare.com/files/43777470"
EXPECT_SIZE=10208088439
EXPECT_MD5=27ac156b31f7c35d4f27a78267c0dd56
OUT="$DEST/Cycling_json.zip"
LOG=/home/user/dline/prog/logs

mkdir -p "$DEST" "$LOG"
cd "$DEST" || exit 1
echo "=== free space ==="; df -h "$DEST" | tail -n 2

if [ -f "$OUT" ]; then
  CUR=$(stat -c %s "$OUT")
  echo "existing file: $CUR bytes (expect $EXPECT_SIZE)"
else
  CUR=0
fi

if [ "$CUR" -ne "$EXPECT_SIZE" ]; then
  echo "=== downloading (resumable) ==="
  # -C - resumes; retry with backoff; fail loudly on HTTP errors
  curl -L -C - --fail --retry 8 --retry-delay 10 --retry-all-errors \
       --connect-timeout 30 --speed-time 120 --speed-limit 1024 \
       -o "$OUT" "$URL"
  echo "curl exit=$?"
fi

echo "=== integrity ==="
SIZE=$(stat -c %s "$OUT" 2>/dev/null || echo 0)
echo "size: $SIZE (expect $EXPECT_SIZE)"
if [ "$SIZE" -ne "$EXPECT_SIZE" ]; then
  echo "SIZE MISMATCH -> NOT a valid archive"; exit 2
fi
MD5=$(md5sum "$OUT" | awk '{print $1}')
echo "md5: $MD5 (expect $EXPECT_MD5)"
if [ "$MD5" != "$EXPECT_MD5" ]; then
  echo "MD5 MISMATCH -> NOT a valid archive"; exit 3
fi
echo "OK: archive verified against the official figshare manifest"
echo "=== listing (first 20 entries) ==="
python3 - <<'PY'
import zipfile
z = zipfile.ZipFile('/home/user/dline/data/Cycling_json.zip')
ns = z.namelist()
print("entries:", len(ns))
for n in ns[:20]:
    print("  ", n, z.getinfo(n).file_size)
PY
