#!/bin/bash
# Line D · remote execution on campus-h3 (64 cores / 125 GB)
# Workspace rule (2026-11-10): no experiment may run on the Windows box.
# Every number reported from line D is produced by this script.
set -u
cd /home/user/dline/prog/code || exit 1
. /home/user/dline/venv/bin/activate
export OMP_NUM_THREADS=2
export OPENBLAS_NUM_THREADS=2
export MKL_NUM_THREADS=2
export PYTHONIOENCODING=utf-8
export DLINE_PROTO=/home/user/dline/prog/protocol
export DLINE_RES=/home/user/dline/prog/results
export DLINE_RAW_ISU=/home/user/dline/data/RPT_json.zip

LOGS=/home/user/dline/prog/logs
mkdir -p "$LOGS"
echo "cwd: $(pwd)"
echo "python: $(python -V 2>&1)"
python -c "import numpy,scipy,sklearn,pandas;print('libs',numpy.__version__,scipy.__version__,sklearn.__version__,pandas.__version__)"
echo "raw isu bytes: $(stat -c %s $DLINE_RAW_ISU)"
echo "git HEAD of code: $(cd /home/user/dline/prog && echo n/a)"

SCRIPTS="D1_deconfound D4_budget_curve D5_parsimony D7_stability D8_audit"
pids=""
for s in $SCRIPTS; do
  nohup python -u "$s.py" > "$LOGS/$s.log" 2>&1 &
  pids="$pids $!"
  echo "launched $s pid $!"
done
echo "waiting for:$pids"
wait
echo "=== batch finished ==="
: > "$LOGS/EXITCODES.txt"
for s in $SCRIPTS; do
  if grep -q "Traceback (most recent call last)" "$LOGS/$s.log"; then
    st="FAILED"
  else
    st="ok"
  fi
  echo "$s $st" | tee -a "$LOGS/EXITCODES.txt"
  tail -n 3 "$LOGS/$s.log"
done
