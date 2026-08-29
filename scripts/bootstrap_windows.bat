@echo off
cd /d D:\AI_worker
python ai_worker.py doctor
if errorlevel 1 exit /b 1
python ai_worker.py bootstrap
