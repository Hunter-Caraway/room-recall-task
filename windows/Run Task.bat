@echo off
cd /d "%~dp0"
call "%~dp0find_python.bat"
if not defined PSYPY (pause & exit /b 1)
"%PSYPY%" run_task.py 
if errorlevel 1 pause
