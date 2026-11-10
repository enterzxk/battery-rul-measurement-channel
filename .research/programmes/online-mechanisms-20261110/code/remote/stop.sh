#!/bin/bash
# stop any running line-D batch and clean its logs
pkill -f "run_dline.sh" 2>/dev/null
pkill -f "python -u D" 2>/dev/null
sleep 2
rm -f /home/user/dline/prog/logs/D*.log /home/user/dline/prog/logs/runner.log
echo "stopped. remaining:"
ps -ef | grep "[p]ython -u D" | wc -l
echo "protocol contents:"
ls -l /home/user/dline/prog/protocol
