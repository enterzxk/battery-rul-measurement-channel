#!/bin/bash
cd /home/user/dline || exit 1
echo "=== running processes ==="
ps -ef | grep "[r]un_dline" | head -n 5
ps -ef | grep "[p]ython -u D" | head -n 10
echo "=== runner.log ==="
if [ -f prog/logs/runner.log ]; then cat prog/logs/runner.log; else echo "(absent)"; fi
echo "=== log dir ==="
ls -l prog/logs 2>&1
echo "=== per-script tails ==="
for f in prog/logs/D*.log; do
  [ -e "$f" ] || continue
  echo "--- $f"
  tail -n 12 "$f"
done
echo "=== protocol outputs so far ==="
ls -l prog/protocol | tail -n 25
