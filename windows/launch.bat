@echo off
rem Runs the task with the private Python in runtime\, setting it up on the first run.
rem Called by Run Task.bat and Run Baseline.bat; extra arguments go to run_task.py.
setlocal
cd /d "%~dp0.."
if not exist "run_task.py" (
  echo The task files are missing. If you opened this from inside the zip file,
  echo close it, right-click the zip, choose "Extract All", then open the extracted folder.
  pause
  exit /b 1
)
if not exist "runtime\ready.txt" (
  echo First run: setting up Python for the task in the "runtime" folder.
  echo This needs internet once and takes about a minute.
  powershell -NoProfile -ExecutionPolicy Bypass -File "windows\setup_runtime.ps1"
  if errorlevel 1 (
    echo.
    echo Setup failed. Check the internet connection and run this again.
    pause
    exit /b 1
  )
)
"runtime\python\python.exe" run_task.py --pygame %*
set "CODE=%ERRORLEVEL%"
if not "%CODE%"=="0" pause
exit /b %CODE%
