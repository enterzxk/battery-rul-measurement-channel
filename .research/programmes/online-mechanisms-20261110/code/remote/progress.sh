#!/bin/bash
D=/home/user/dline/data/cycling_parts
S=10208088439
B=$(du -sb "$D" 2>/dev/null | cut -f1)
[ -z "$B" ] && B=0
N=$(ls "$D" 2>/dev/null | wc -l)
echo "downloaded_bytes=$B"
echo "percent=$(python3 -c "print(f'{100*$B/$S:.2f}')")"
echo "parts_present=$N (of 153)"
echo "rate_check:"
echo "  part files:"; ls -l "$D" 2>/dev/null | head -n 4
if [ -f /home/user/dline/prog/logs/fetch_par.log ]; then
  echo "  log tail:"; tail -n 3 /home/user/dline/prog/logs/fetch_par.log
fi
