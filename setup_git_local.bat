@echo off
REM Script setup Git trên máy local (Windows)
REM Chạy trong thư mục d:\Testthu

echo 🔧 Setting up Git on local machine...

REM Check if Git is installed
git --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Git is not installed!
    echo 📥 Download Git from: https://git-scm.com/download/win
    pause
    exit /b 1
)

echo ✅ Git is installed

REM Initialize Git repo (if not exists)
if not exist .git (
    echo 📦 Initializing Git repository...
    git init
    echo ✅ Git repository initialized
) else (
    echo ✅ Git repository already exists
)

REM Check if remote VPS exists
git remote get-url vps >nul 2>&1
if errorlevel 1 (
    echo 📡 Adding remote VPS...
    git remote add vps myadmin@97.74.83.97:~/screenshot-analyzer.git
    echo ✅ Remote VPS added
) else (
    echo ✅ Remote VPS already exists
)

REM Add files (if not committed)
git add .
if %errorlevel% equ 0 (
    echo ✅ Files added to staging
)

echo.
echo ✅ Git setup completed!
echo.
echo 📝 Common commands:
echo.
echo   1. Commit and push code:
echo      git add .
echo      git commit -m "Description of changes"
echo      git push vps main
echo.
echo   2. View status:
echo      git status
echo.
echo   3. View logs:
echo      git log --oneline
echo.
pause

