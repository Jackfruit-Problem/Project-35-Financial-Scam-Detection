@echo off
setlocal EnableDelayedExpansion
title FSDIRAS launcher
cd /d "%~dp0"

echo.
echo   ============================================
echo     FSDIRAS - Financial Scam Detection System
echo   ============================================
echo.
echo   Starting up. The first run takes a few minutes
echo   while it installs things; after that, seconds.
echo.

set "VENV_PY=backend\.venv\Scripts\python.exe"

if exist "%VENV_PY%" goto :haveenv

:: ---------------------------------------------------------------- Python ---
:: Detection is done step by step rather than in one chained expression,
:: because cmd's parser handles && inside if-blocks badly enough to silently
:: pick the wrong interpreter.
echo   [1/5] Setting up Python ^(one time only^)...
set "BOOTSTRAP="

py -3.11 --version >nul 2>&1
if not errorlevel 1 set "BOOTSTRAP=py -3.11"

if not defined BOOTSTRAP (
    py -3 --version >nul 2>&1
    if not errorlevel 1 set "BOOTSTRAP=py -3"
)

if not defined BOOTSTRAP (
    python --version >nul 2>&1
    if not errorlevel 1 set "BOOTSTRAP=python"
)

if not defined BOOTSTRAP goto :nopython

!BOOTSTRAP! -m venv backend\.venv
if errorlevel 1 goto :venvfailed

echo   [2/5] Installing backend packages...
"%VENV_PY%" -m pip install --quiet --upgrade pip
"%VENV_PY%" -m pip install --quiet -r backend\requirements-dev.txt
if errorlevel 1 goto :pipfailed
goto :frontend

:haveenv
echo   [1/5] Python environment found.
echo   [2/5] Backend packages already installed.

:: -------------------------------------------------------------- Frontend ---
:frontend
if exist "frontend\node_modules" goto :havenode

echo   [3/5] Installing web interface packages ^(one time only^)...
where npm >nul 2>&1
if errorlevel 1 goto :nonode
pushd frontend
call npm install --no-fund --no-audit
popd
goto :data

:havenode
echo   [3/5] Web interface packages already installed.

:: ------------------------------------------------------------------ Data ---
:data
if exist "backend\fsdiras.db" goto :havedata
echo   [4/5] Creating the demo database...
pushd backend
".venv\Scripts\python.exe" scripts\seed_demo.py >nul
popd
goto :servers

:havedata
echo   [4/5] Database found.

:: --------------------------------------------------------------- Servers ---
:servers
echo   [5/5] Starting the system...

start "FSDIRAS API (do not close)" cmd /k "cd /d "%~dp0backend" && .venv\Scripts\python.exe -m uvicorn app.main:app --reload"
start "FSDIRAS Web (do not close)" cmd /k "cd /d "%~dp0frontend" && npm run dev"

:: The web app is useless until the API answers, so wait for it rather than
:: opening a browser onto a page that cannot load any of its data.
echo.
echo   Waiting for the system to come up...
set /a TRIES=0

:waitloop
set /a TRIES+=1
ping -n 3 127.0.0.1 >nul
curl -s -o nul -m 2 http://127.0.0.1:8000/health 2>nul
if not errorlevel 1 goto :ready
if !TRIES! lss 30 goto :waitloop
goto :timedout

:ready
ping -n 4 127.0.0.1 >nul
start "" http://localhost:5173

echo.
echo   ============================================
echo     Running. Your browser should have opened.
echo.
echo     Web app   http://localhost:5173
echo     API docs  http://localhost:8000/docs
echo.
echo     Sign in with any demo account:
echo       victim@fsdiras.example.com
echo       investigator@fsdiras.example.com
echo       officer@fsdiras.example.com
echo       admin@fsdiras.example.com
echo     Password for all:  password123
echo.
echo     To shut down, run "Stop FSDIRAS.bat" or
echo     close the two windows this opened.
echo   ============================================
echo.
echo   You can close THIS window now.
echo.
pause
exit /b 0

:nopython
echo.
echo   PROBLEM: Python is not installed, or not on your PATH.
echo.
echo   Install Python 3.11 or later from https://www.python.org/downloads/
echo   and tick "Add Python to PATH" during setup. Then run this again.
echo.
pause
exit /b 1

:nonode
echo.
echo   PROBLEM: Node.js is not installed, or not on your PATH.
echo   Install it from https://nodejs.org/ then run this again.
echo.
pause
exit /b 1

:venvfailed
echo.
echo   PROBLEM: could not create the Python environment.
echo   Delete the folder backend\.venv if it exists, then try again.
echo.
pause
exit /b 1

:pipfailed
echo.
echo   PROBLEM: could not install the backend packages.
echo   Check your internet connection and try again.
echo.
pause
exit /b 1

:timedout
echo.
echo   The system did not start within a minute. Look at the two windows
echo   titled "FSDIRAS API" and "FSDIRAS Web" - the error will be in one
echo   of them.
echo.
pause
exit /b 1
