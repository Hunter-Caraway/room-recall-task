@echo off
rem Finds the Python that comes with PsychoPy Standalone and stores it in PSYPY.
rem If PsychoPy is installed somewhere unusual, put the full path to its python.exe
rem on the first line of psychopy_python.txt next to these files.
set "PSYPY="
if exist "%~dp0psychopy_python.txt" set /p PSYPY=<"%~dp0psychopy_python.txt"
if defined PSYPY if exist "%PSYPY%" goto :eof
for %%P in (
  "%ProgramFiles%\PsychoPy\python.exe"
  "%LOCALAPPDATA%\Programs\PsychoPy\python.exe"
  "%ProgramFiles%\PsychoPy3\python.exe"
  "%ProgramFiles(x86)%\PsychoPy\python.exe"
) do if exist %%P set "PSYPY=%%~P" & goto :eof
echo PsychoPy was not found. Install PsychoPy Standalone 2026.2.5 (Python 3.11 version),
echo or write the full path to PsychoPy's python.exe in psychopy_python.txt.
set "PSYPY="
