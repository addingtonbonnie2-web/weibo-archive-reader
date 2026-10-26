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

where py >nul 2>nul
if %errorlevel%==0 (set "PY=py -3") else (set "PY=python")

start "" http://127.0.0.1:5055
%PY% run.py
pause
