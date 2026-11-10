#!/bin/bash
cd /home/user/dline/prog || exit 1
tar -czf /home/user/dline/dline_results.tgz protocol logs
ls -l /home/user/dline/dline_results.tgz
echo "--- protocol ---"
ls -l protocol
