@echo off
chcp 936 >nul
title Step 0 - Check environment
cd /d "%~dp0"

echo ==================================================
echo   Step 0 : Check environment
echo ==================================================
echo.

where py >nul 2>nul
if %errorlevel%==0 (set "PY=py -3") else (set "PY=python")

%PY% --version
if errorlevel 1 goto nopy

echo.
echo Python found. Checking packages...
%PY% -c "import flask, PIL, jieba; print('packages OK')"
if errorlevel 1 (
  echo.
  echo [X] Packages missing. Please run: 1-install-dependencies.bat
) else (
  echo.
  echo [OK] Everything looks fine. Now run: 2-make-demo-data.bat
)
goto end

:nopy
echo.
echo [X] Python not found.
echo     Install Python 3.9+ from https://www.python.org/downloads/
echo     Remember to tick "Add python.exe to PATH" during install.
echo.

:end
pause
