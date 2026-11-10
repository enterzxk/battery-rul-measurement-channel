#!/bin/bash
# Measure whether figshare throttles per-connection. Fetch the same 8 MB range
# with 1 connection, then with 8 parallel connections, and compare throughput.
URL="https://ndownloader.figshare.com/files/43777470"
TMP=/home/user/dline/_speedtest
mkdir -p "$TMP"; cd "$TMP" || exit 1

echo "=== 1 connection, 8 MB ==="
t0=$(date +%s)
curl -sSL --fail -r 0-8388607 -o one.bin "$URL"
t1=$(date +%s)
echo "  bytes=$(stat -c %s one.bin) secs=$((t1-t0)) rate=$(( 8388608 / (t1-t0+1) / 1024 )) KB/s"

echo "=== 8 parallel connections, 8 x 4 MB (disjoint ranges) ==="
t0=$(date +%s)
for i in 0 1 2 3 4 5 6 7; do
  s=$(( 100000000 + i*4194304 )); e=$(( s + 4194303 ))
  curl -sSL --fail -r ${s}-${e} -o p$i.bin "$URL" &
done
wait
t1=$(date +%s)
tot=$(du -cb p?.bin | tail -n1 | awk '{print $1}')
echo "  bytes=$tot secs=$((t1-t0)) rate=$(( tot / (t1-t0+1) / 1024 )) KB/s"

echo "=== tools ==="
which aria2c wget curl 2>/dev/null
rm -rf "$TMP"
