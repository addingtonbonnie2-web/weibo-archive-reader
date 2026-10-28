@echo off
chcp 936 >nul
title Weibo Archive Reader
cd /d "%~dp0"

echo ==================================================
echo   Weibo Archive Reader
echo ==================================================
echo.
echo Browser will open at http://127.0.0.1:5055
echo Keep this window open. Press Ctrl+C to stop.
echo.

rem If a reader is already running, stop it first.
rem Otherwise the new one cannot bind the port and the browser keeps showing old pages.
netstat -ano | findstr ":5055" | findstr LISTENING >nul
if not errorlevel 1 (
  echo A reader is already running on port 5055. Stopping it first...
  for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":5055" ^| findstr LISTENING') do taskkill /f /pid %%p >nul 2>&1
  timeout /t 2 >nul 2>&1
)

where py >nul 2>nul
if %errorlevel%==0 (set "PY=py -3") else (set "PY=python")

start "" http://127.0.0.1:5055
%PY% run.py
pause
