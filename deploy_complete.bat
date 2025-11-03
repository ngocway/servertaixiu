@echo off
REM Script deploy hoàn chỉnh - kiểm tra và push code

set VPS_IP=97.74.83.97
set VPS_USER=myadmin

echo ========================================
echo   Complete Deploy to VPS
echo ========================================
echo.

echo [1/5] Checking Git config...
git config user.name >nul 2>&1
if errorlevel 1 (
    echo ⚙️  Setting Git config...
    git config user.name "Screenshot Analyzer"
    git config user.email "admin@lukistar.space"
    echo ✅ Git config set
) else (
    echo ✅ Git config OK
)
echo.

echo [2/5] Checking remote VPS...
git remote get-url vps >nul 2>&1
if errorlevel 1 (
    echo 📡 Adding remote VPS...
    git remote add vps %VPS_USER%@%VPS_IP%:~/screenshot-analyzer.git
    echo ✅ Remote added
) else (
    echo ✅ Remote exists
)
echo.

echo [3/5] Checking Git setup on VPS...
ssh -o ConnectTimeout=5 %VPS_USER%@%VPS_IP% "test -d ~/screenshot-analyzer.git" 2>nul
if errorlevel 1 (
    echo ⚠️  Git not setup on VPS!
    echo.
    echo 🔄 Running setup script first...
    call setup_with_password.bat
    goto :push_code
) else (
    echo ✅ Git is setup on VPS
)
echo.

:push_code
echo [4/5] Committing changes...
git add .
git diff --cached --quiet 2>nul
if errorlevel 1 (
    git commit -m "Update - %date% %time%"
    echo ✅ Changes committed
) else (
    git rev-parse --verify HEAD >nul 2>&1
    if errorlevel 1 (
        git commit -m "Initial commit - Screenshot Analyzer Server" --allow-empty
        echo ✅ Initial commit created
    ) else (
        echo ⚠️  No changes to commit
    )
)
echo.

echo [5/5] Pushing to VPS...
git branch -M main 2>nul
echo 📤 Pushing code to VPS...
git push -u vps main
if errorlevel 1 (
    echo ❌ Push failed!
    echo.
    echo 💡 Troubleshooting:
    echo    1. Make sure Git is setup on VPS: setup_with_password.bat
    echo    2. Check SSH connection: ssh %VPS_USER%@%VPS_IP%
    echo    3. Check if there are commits: git log --oneline
    pause
    exit /b 1
)

echo.
echo ========================================
echo   ✅ Deploy completed!
echo ========================================
echo.
echo 🔍 Verifying deployment...
call check_deploy.bat

echo.
echo 🌐 Access your server:
echo    - Admin: http://%VPS_IP%:8000/admin
echo    - Health: http://%VPS_IP%:8000/health
echo.
pause

