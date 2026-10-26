@echo off
chcp 936 >nul
title Step 4 - Push to GitHub
cd /d "%~dp0"
setlocal enabledelayedexpansion

echo ==================================================
echo   Step 4 : Push this folder to GitHub
echo ==================================================
echo.
echo Usage:  4-ÉÏ´«µ½GitHub.bat [repo-url] [user-name] [email]
echo   all three arguments are optional, you will be asked otherwise.
echo.

where git >nul 2>nul
if errorlevel 1 goto nogit

rem ---------- 1) privacy guard ----------
if exist "data\weibo.db" (
  echo [X] data\weibo.db exists in this folder.
  echo     That database holds other people's weibo posts.
  echo     Delete it first:   rmdir /s /q data
  echo.
  goto end
)
if exist "config.py" echo [!] config.py is in .gitignore and will not be pushed.
echo.

rem ---------- 2) init first: git config needs a repository ----------
if not exist ".git" (
  echo [1/5] git init
  git init -q
  git branch -M main
) else (
  echo [1/5] already a git repository
)

rem ---------- 3) identity ----------
set "GITNAME=%~2"
if not defined GITNAME (
  for /f "delims=" %%i in ('git config user.name 2^>nul') do set "GITNAME=%%i"
)
if not defined GITNAME (
  echo Git records an author name and email with every commit.
  set /p GITNAME=Your git user name: 
)
set "GITMAIL=%~3"
if not defined GITMAIL (
  for /f "delims=" %%i in ('git config user.email 2^>nul') do set "GITMAIL=%%i"
)
if not defined GITMAIL set /p GITMAIL=Your git email: 
if not defined GITNAME goto noident
if not defined GITMAIL goto noident
git config user.name "!GITNAME!"
git config user.email "!GITMAIL!"
echo [2/5] identity: !GITNAME! ^<!GITMAIL!^>

rem ---------- 4) repository url ----------
set "REPO=%~1"
if not defined REPO set "REPO=https://github.com/addingtonbonnie2-web/weibo-archive-reader.git"
if not defined REPO set "REPO=x"
echo.
echo Target repository:  !REPO!
if "%~1"=="" (
  echo Press Enter to accept, or paste another URL.
  set /p REPO_IN=Repository URL: 
  if defined REPO_IN set "REPO=!REPO_IN!"
)
echo.

rem ---------- 5) add / commit ----------
echo [3/5] git add
git add -A
if errorlevel 1 goto addfail

git status --short | findstr /i "data\\ config.py" >nul
if not errorlevel 1 (
  echo [X] data\ or config.py got staged. Run  git reset  and check .gitignore.
  goto end
)

echo [4/5] git commit
git commit -q -m "Update from local copy"
if errorlevel 1 echo      nothing new to commit, continue

rem ---------- 6) remote + push ----------
git remote get-url origin >nul 2>nul
if errorlevel 1 (
  git remote add origin "!REPO!"
) else (
  git remote set-url origin "!REPO!"
)

echo [5/5] git push
echo.
echo A browser window may open for login. If it asks for a password,
echo paste a Personal Access Token instead.
echo.
git push -u origin main
if errorlevel 1 goto pushfail

echo.
echo [OK] Pushed. Check the page:  !REPO!
goto end

:nogit
echo [X] git not found.
echo     Install Git for Windows: https://git-scm.com/download/win
echo     Then close this window and run the file again.
goto end

:noident
echo.
echo [X] Name or email is empty, nothing committed.
echo     Run this file again and fill both prompts, or set them once for all repos:
echo         git config --global user.name "your name"
echo         git config --global user.email "you@example.com"
goto end

:addfail
echo [X] git add failed, see the message above.
goto end

:pushfail
echo.
echo [X] Push failed. Likely causes:
echo     - the repository does not exist yet; create it on GitHub first
echo       New repository - name weibo-archive-reader - Public - do not add README
echo     - wrong URL
echo     - not logged in; retry and finish the browser login
goto end

:end
echo.
pause
