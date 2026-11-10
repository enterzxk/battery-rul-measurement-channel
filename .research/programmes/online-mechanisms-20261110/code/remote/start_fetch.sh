#!/bin/bash
# Stage F · stop any in-flight fetch and start the parallel chunked download.
set -u
DEST=/home/user/dline/data
# kill by PID file / process scan that cannot match this script's own cmdline
for p in $(pgrep -f "ndownloader.figshare.com/files/43777470" 2>/dev/null); do
  [ "$p" != "$$" ] && kill -9 "$p" 2>/dev/null
done
for p in $(pgrep -f "fetch_cycling" 2>/dev/null); do
  [ "$p" != "$$" ] && kill -9 "$p" 2>/dev/null
done
sleep 2
rm -f "$DEST/Cycling_json.zip"
mkdir -p "$DEST/cycling_parts"

echo "=== official small files ==="
cd "$DEST" || exit 1
curl -sSL --fail -o process_data.py  https://ndownloader.figshare.com/files/43754835 || echo "process_data FAILED"
curl -sSL --fail -o capacity_fade.zip https://ndownloader.figshare.com/files/43755582 || echo "capacity_fade FAILED"
ls -l process_data.py capacity_fade.zip 2>/dev/null
echo "md5 process_data.py : $(md5sum process_data.py 2>/dev/null | awk '{print $1}')  (official ccb61a35ffb6f2e17b2d55b336f170c8)"

echo "=== launching parallel download ==="
nohup setsid bash /home/user/dline/fetch_par.sh > /home/user/dline/prog/logs/fetch_par.log 2>&1 &
echo "launched pid $!"
sleep 60
echo "=== progress after 60s ==="
du -sb "$DEST/cycling_parts" 2>/dev/null | awk '{printf "  %.1f MB\n", $1/1e6}'
ls "$DEST/cycling_parts" 2>/dev/null | wc -l
tail -n 5 /home/user/dline/prog/logs/fetch_par.log
