@echo off
net session >nul 2>&1
if errorlevel 1 (
  echo Can chay file nay bang quyen Administrator: chuot phai uninstall.bat, chon Run as administrator.
  pause
  exit /b 1
)
start "" /wait "%~dp0cs-agent.exe" --uninstall
