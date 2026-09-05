@echo off
cd /d "%~dp0"
python -u main.py >> logs\authenticator.log 2>&1
