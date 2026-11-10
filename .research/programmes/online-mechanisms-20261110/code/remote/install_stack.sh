#!/bin/bash
# Stage G · install the modelling stack into the existing venv.
# lightgbm is needed first (Gate 1 E0/E1 baselines); torch is needed later for
# the Transformer stages, so it installs in the background.
set -u
cd /home/user/dline || exit 1
. /home/user/dline/venv/bin/activate
export PYTHONIOENCODING=utf-8
LOG=/home/user/dline/prog/logs
mkdir -p "$LOG"

echo "=== installing lightgbm (foreground, needed now) ==="
python -m pip install -q lightgbm 2>&1 | tail -5
python -c "import lightgbm;print('lightgbm', lightgbm.__version__)" 2>&1 | tail -2

echo "=== launching torch install in background ==="
nohup setsid bash -c '
  . /home/user/dline/venv/bin/activate
  python -m pip install torch --index-url https://download.pytorch.org/whl/cu124 \
    > /home/user/dline/prog/logs/torch_install.log 2>&1
  echo "TORCH_INSTALL_EXIT=$?" >> /home/user/dline/prog/logs/torch_install.log
' > /dev/null 2>&1 &
echo "torch install pid $!"

echo "=== disk ==="
df -h /home | tail -1
