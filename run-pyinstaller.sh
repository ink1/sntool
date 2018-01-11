#!/bin/bash
./run-clean.sh
# YOU NEED TO LOAD ONE OF THE TWO
#module load python/2.6.6 python/2.6.8
pyi-makespec --onefile --strip snq.py
pyinstaller --onefile snq.py
cp dist/snq /apps/sntool/snq
