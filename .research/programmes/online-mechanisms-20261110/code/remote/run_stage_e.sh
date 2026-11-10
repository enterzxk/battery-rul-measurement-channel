#!/bin/bash
# Stage E · remote execution on campus-h3 (workspace compute rule: nothing runs locally)
set -u
cd /home/user/dline/prog/code || exit 1
. /home/user/dline/venv/bin/activate
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2 PYTHONIOENCODING=utf-8
export DLINE_PROTO=/home/user/dline/prog/protocol
export DLINE_RES=/home/user/dline/prog/results
export DLINE_RAW_ISU=/home/user/dline/data/RPT_json.zip
LOGS=/home/user/dline/prog/logs
mkdir -p "$LOGS"

SCRIPTS="${*:-E0_probe}"
for s in $SCRIPTS; do
  echo "=== $s ==="
  python -u "$s.py" > "$LOGS/$s.log" 2>&1
  rc=$?
  echo "  exit=$rc  log=$LOGS/$s.log"
  tail -n 3 "$LOGS/$s.log"
done
