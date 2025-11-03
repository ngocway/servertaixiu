@echo off
REM Script deploy nhanh - chỉ push code, không setup

set VPS_IP=97.74.83.97
set VPS_USER=myadmin

echo 🚀 Quick Deploy to VPS...
echo.

echo [1/2] Committing changes...
git add .
git commit -m "Update - %date% %time%" 2>nul || echo ⚠️  No changes to commit

echo.
echo [2/2] Pushing to VPS...
git push vps main 2>nul || git push vps master 2>nul || git push vps HEAD:main
if errorlevel 1 (
    echo ❌ Push failed!
    echo.
    echo 💡 Make sure:
    echo    - Git is setup on VPS (run setup_with_password.bat first)
    echo    - SSH connection works
    pause
    exit /b 1
)

echo.
echo ✅ Code pushed successfully!
echo 🔄 VPS is auto-updating...
echo.
echo 📊 Check status:
call check_deploy.bat

pause

