#!/bin/bash
cd /home/user/dline/prog/code || exit 1
. /home/user/dline/venv/bin/activate
export PYTHONIOENCODING=utf-8
echo "=== python ==="; python -V
python - <<'PY'
mods = ["numpy","scipy","sklearn","pandas","lightgbm","catboost","xgboost","torch","pyarrow"]
for m in mods:
    try:
        mod = __import__(m)
        print("  ok   %-10s %s" % (m, getattr(mod,"__version__","?")))
    except Exception as e:
        print("  MISS %-10s %s" % (m, type(e).__name__))
PY
echo "=== torch cuda ==="
python -c "import torch;print('torch',torch.__version__,'cuda',torch.cuda.is_available(),torch.cuda.device_count())" 2>&1 | tail -2
echo "=== gpu ==="
nvidia-smi --query-gpu=name,memory.total,memory.used --format=csv,noheader 2>/dev/null
echo "=== key tables ==="
for f in F4_clock_table.csv F7_intervals.csv F6_admission_dod.csv F3_condition_exposure.csv; do
  if [ -f "/home/user/dline/prog/protocol/$f" ]; then
    echo "  $f  $(stat -c %s /home/user/dline/prog/protocol/$f) bytes"
  fi
done
echo "=== results dir ==="
ls /home/user/dline/prog/results/ 2>/dev/null | head
