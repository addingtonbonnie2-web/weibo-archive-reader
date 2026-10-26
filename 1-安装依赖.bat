@echo off
chcp 936 >nul
title Step 1 - Install dependencies
cd /d "%~dp0"

echo ==================================================
echo   Step 1 : Install dependencies
echo ==================================================
echo.

where py >nul 2>nul
if %errorlevel%==0 (set "PY=py -3") else (set "PY=python")

%PY% -m pip install --upgrade pip
%PY% -m pip install -r requirements.txt
if errorlevel 1 goto fail

echo.
echo [OK] Done. Next: 2-make-demo-data.bat
pause
exit /b 0

:fail
echo.
echo [X] Install failed.
echo     Try running this file as administrator, or check your network.
echo     If you are in China, add a mirror:
echo       py -3 -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
pause
exit /b 1
