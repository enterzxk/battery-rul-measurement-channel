#!/bin/bash
# G1c · target-axis control, run sequentially with capped threads.
set -u
cd /home/user/dline/prog/code || exit 1
. /home/user/dline/venv/bin/activate
export DLINE_PROTO=/home/user/dline/prog/protocol
export DLINE_OUT=/home/user/dline/prog/protocol
export OMP_NUM_THREADS=4
export PYTHONIOENCODING=utf-8
for t in days cycles ah; do
  echo "########## target = $t ##########"
  python -u G1c_target_axis.py "$t"
  echo "exit=$?"
done
echo "=== all targets done ==="
