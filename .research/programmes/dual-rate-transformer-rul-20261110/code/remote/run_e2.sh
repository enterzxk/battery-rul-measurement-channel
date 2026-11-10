#!/bin/bash
set -u
cd /home/user/dline/prog/code || exit 1
. /home/user/dline/venv/bin/activate
export DLINE_PROTO=/home/user/dline/prog/protocol
export DLINE_OUT=/home/user/dline/prog/protocol
export OMP_NUM_THREADS=4
export PYTHONIOENCODING=utf-8
python -c "import torch;print('torch',torch.__version__,'cuda',torch.cuda.is_available())"
python -u E2_transformer.py cycles
echo "exit=$?"
