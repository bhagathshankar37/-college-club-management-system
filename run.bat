@echo off
title College Club Management System
echo ====================================================
echo Starting College Club Management System...
echo ====================================================

set PYTHON_CMD="C:\Users\Dell\AppData\Local\Python\pythoncore-3.14-64\python.exe"

if exist %PYTHON_CMD% (
    %PYTHON_CMD% app.py
) else (
    python app.py || py app.py
)

pause
