#!/bin/bash
# Stage E3 · full temporal policy replay, 18 (T,N,ratio) cells in parallel.
# c_insp does not enter: at matched N it is a constant in every arm, so it
# cancels from every paired delta (Codex ruling; also algebraically obvious).
set -u
cd /home/user/dline/prog/code || exit 1
. /home/user/dline/venv/bin/activate
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2 PYTHONIOENCODING=utf-8
export DLINE_PROTO=/home/user/dline/prog/protocol
export DLINE_RES=/home/user/dline/prog/results
export DLINE_RAW_ISU=/home/user/dline/data/RPT_json.zip
LOGS=/home/user/dline/prog/logs
mkdir -p "$LOGS"

echo "caching cells once..."
python -u E3a_cache.py > "$LOGS/E3a_cache.log" 2>&1 || { echo "cache FAILED"; tail -n 20 "$LOGS/E3a_cache.log"; exit 1; }
tail -n 2 "$LOGS/E3a_cache.log"

pids=""
for T in 56 63; do
  for N in 1 2 3; do
    for R in 2.0 5.0 10.0; do
      tag="T${T}_N${N}_r${R}"
      nohup python -u E3b_replay.py "$T" "$N" "$R" > "$LOGS/E3b_${tag}.log" 2>&1 &
      pids="$pids $!"
    done
  done
done
echo "launched:$pids"
wait
echo "=== replay finished ==="
for f in "$LOGS"/E3b_*.log; do
  st="ok"; grep -q "Traceback" "$f" && st="FAILED"
  echo "$(basename "$f") $st"
done
ls -l /home/user/dline/prog/protocol/E3_T*.json 2>/dev/null | wc -l
