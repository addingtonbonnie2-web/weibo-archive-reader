@echo off
chcp 936 >nul
title Step 2 - Create demo data
cd /d "%~dp0"

echo ==================================================
echo   Step 2 : Create demo data
echo ==================================================
echo.
echo This creates data\weibo.db with 20 fake posts,
echo so you can see the interface without any real data.
echo.

where py >nul 2>nul
if %errorlevel%==0 (set "PY=py -3") else (set "PY=python")

%PY% tools\make_demo_db.py
echo.
echo [OK] Next: 3-start-reader.bat
echo.
echo If you already have your own backup, copy weibo.db into the
echo data folder and skip this step. See README for details.
pause
