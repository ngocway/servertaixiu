@echo off
REM Script fix và deploy ngay

echo ========================================
echo   Fix & Deploy to VPS
echo ========================================
echo.

echo [Step 1/4] Setting up Git config...
git config user.name "Screenshot Analyzer" 2>nul
git config user.email "admin@lukistar.space" 2>nul
echo ✅ Git config set
echo.

echo [Step 2/4] Adding all files...
git add .
echo ✅ Files added
echo.

echo [Step 3/4] Committing...
git commit -m "Initial commit - Screenshot Analyzer Server"
if errorlevel 1 (
    echo ⚠️  Commit failed or already committed
) else (
    echo ✅ Committed
)
echo.

echo [Step 4/4] Pushing to VPS...
set VPS_IP=97.74.83.97
set VPS_USER=myadmin

REM Check if remote exists
git remote get-url vps >nul 2>&1
if errorlevel 1 (
    echo 📡 Adding remote VPS...
    git remote add vps %VPS_USER%@%VPS_IP%:~/screenshot-analyzer.git
)

REM Rename branch to main if needed
git branch -M main 2>nul

REM Push
echo 📤 Pushing to VPS...
git push -u vps main
if errorlevel 1 (
    echo ❌ Push failed!
    echo.
    echo 💡 Make sure Git is setup on VPS:
    echo    Run: setup_with_password.bat first
    pause
    exit /b 1
)

echo.
echo ========================================
echo   ✅ Deploy completed!
echo ========================================
echo.
echo 🔍 Checking deployment...
call check_deploy.bat

pause

