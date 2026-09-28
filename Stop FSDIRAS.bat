@echo off
title FSDIRAS shutdown
cd /d "%~dp0"

echo.
echo   Stopping FSDIRAS...
echo.

:: The real work is in tools\stop.ps1. Inlining it here was tried and does not
:: survive cmd's parsing -- caret continuations and redirection operators get
:: interpreted inside what should be one PowerShell string, and the script
:: silently stops halfway through.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\stop.ps1" -Root "%~dp0"

echo.
echo   You can close this window.
echo.
ping -n 6 127.0.0.1 >nul
exit /b 0
