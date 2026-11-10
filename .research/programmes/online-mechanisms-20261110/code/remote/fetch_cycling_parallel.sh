#!/bin/bash
# Stage F · parallel chunked fetch of the official ISU-ILCC Cycling_json.zip.
# figshare throttles per connection (measured: 63 KB/s single, 496 KB/s at 8),
# so fetch fixed-size byte ranges with a bounded worker pool, resuming each
# chunk from its current size, then concatenate and verify against the official
# manifest md5. Never writes into the git repository.
set -u
DEST=/home/user/dline/data
PARTS="$DEST/cycling_parts"
URL="https://ndownloader.figshare.com/files/43777470"
S=10208088439
EXPECT_MD5=27ac156b31f7c35d4f27a78267c0dd56
CHUNK=$((64 * 1024 * 1024))          # 64 MB per chunk
JOBS=32
OUT="$DEST/Cycling_json.zip"
LOG=/home/user/dline/prog/logs

mkdir -p "$DEST" "$PARTS" "$LOG"

NCHUNKS=$(( (S + CHUNK - 1) / CHUNK ))
echo "total $S bytes -> $NCHUNKS chunks of $CHUNK, $JOBS workers"

fetch_chunk() {
  local i=$1
  local start=$(( i * CHUNK ))
  local end=$(( start + CHUNK - 1 ))
  [ "$end" -ge "$S" ] && end=$(( S - 1 ))
  local want=$(( end - start + 1 ))
  local part="$PARTS/part_$(printf '%05d' "$i")"
  local tries=0
  while :; do
    local have=0
    [ -f "$part" ] && have=$(stat -c %s "$part")
    [ "$have" -ge "$want" ] && return 0
    curl -sSL --fail --connect-timeout 30 --speed-time 180 --speed-limit 512 \
         -r $(( start + have ))-${end} "$URL" >> "$part" 2>/dev/null
    have=$(stat -c %s "$part" 2>/dev/null || echo 0)
    [ "$have" -ge "$want" ] && return 0
    tries=$(( tries + 1 ))
    if [ "$tries" -ge 40 ]; then
      echo "CHUNK $i FAILED after $tries tries (have $have / want $want)" >&2
      return 1
    fi
    sleep $(( tries < 5 ? 2 : 10 ))
  done
}
export -f fetch_chunk
export URL S CHUNK PARTS

echo "=== fetching ==="
seq 0 $(( NCHUNKS - 1 )) | xargs -P "$JOBS" -I{} bash -c 'fetch_chunk {}'
rc=$?
echo "xargs rc=$rc"

echo "=== assembling ==="
if [ "$rc" -ne 0 ]; then echo "some chunks failed; not assembling"; exit 4; fi
: > "$OUT"
for i in $(seq 0 $(( NCHUNKS - 1 ))); do
  cat "$PARTS/part_$(printf '%05d' "$i")" >> "$OUT"
done

echo "=== integrity ==="
GOT=$(stat -c %s "$OUT")
echo "size $GOT (expect $S)"
[ "$GOT" -ne "$S" ] && { echo "SIZE MISMATCH"; exit 2; }
MD5=$(md5sum "$OUT" | awk '{print $1}')
echo "md5 $MD5 (expect $EXPECT_MD5)"
[ "$MD5" != "$EXPECT_MD5" ] && { echo "MD5 MISMATCH"; exit 3; }
echo "OK: verified against the official figshare manifest"
rm -rf "$PARTS"
python3 - <<'PY'
import zipfile
z = zipfile.ZipFile('/home/user/dline/data/Cycling_json.zip')
ns = z.namelist()
print("entries:", len(ns))
for n in ns[:8]:
    print("  ", n, z.getinfo(n).file_size)
PY
