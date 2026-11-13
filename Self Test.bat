@echo off
call "%~dp0windows\launch.bat" --self-test
type "%~dp0selftest.log"
pause
