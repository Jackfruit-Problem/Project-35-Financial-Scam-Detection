@echo off
title FSDIRAS shortcut
cd /d "%~dp0"

echo.
echo   Putting an FSDIRAS shortcut on your Desktop...
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\shortcut.ps1" -Target "%~dp0Run FSDIRAS.bat"

echo.
ping -n 5 127.0.0.1 >nul
exit /b 0
