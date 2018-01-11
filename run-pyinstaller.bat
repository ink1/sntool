@echo off
echo "Delete old build directories and recompile?"
echo
pause
rm -r build dist snq.spec
pyi-makespec --onefile --strip snq.py
pyinstaller --onefile snq.py

