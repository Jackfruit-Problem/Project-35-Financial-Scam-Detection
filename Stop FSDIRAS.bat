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
set "PROJECT_ROOT=%~dp0"
set "PROJECT_ROOT=%PROJECT_ROOT:~0,-1%"
:: Stripped of its trailing backslash: a quoted argument ending in one
:: escapes its own closing quote and absorbs anything after it.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\stop.ps1" -Root "%PROJECT_ROOT%"

echo.
echo   You can close this window.
echo.
ping -n 6 127.0.0.1 >nul
exit /b 0
