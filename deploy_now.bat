@echo off
REM Script deploy code lên VPS ngay lập tức

set VPS_IP=97.74.83.97
set VPS_USER=myadmin

echo ========================================
echo   Deploy Code to VPS
echo ========================================
echo.

echo [Step 1/4] Checking Git setup on local...
if not exist .git (
    echo WARNING: Git repository not initialized.
    echo Initializing Git repository...
    git init
    git add .
    git commit -m "Initial commit"
)

git remote get-url vps >nul 2>&1
if errorlevel 1 (
    echo Adding remote VPS...
    git remote add vps %VPS_USER%@%VPS_IP%:~/screenshot-analyzer.git
) else (
    echo Remote VPS configured
)
echo.

echo [Step 2/4] Checking if Git repository exists on VPS...
echo Checking VPS Git repository...
ssh %VPS_USER%@%VPS_IP% "test -d ~/screenshot-analyzer.git" 1>nul 2>nul
if errorlevel 1 goto repo_missing
echo Git repository is available on VPS.
goto deploy_code

:repo_missing
echo Git repository chưa được thiết lập trên VPS.
echo Vui lòng chạy setup_with_password.bat một lần để tạo repository, sau đó thử deploy lại.
pause
exit /b 1

:deploy_code
echo.
echo [Step 3/4] Committing local changes...
git add .
git commit -m "Deploy - %date% %time%" 2>nul || echo No new changes to commit

echo.
echo [Step 4/4] Pushing code to VPS...
echo Pushing to VPS (will auto-deploy)...
git push vps main 2>nul || git push vps master 2>nul || git push vps HEAD:main
if errorlevel 1 (
    echo Push failed!
    echo Troubleshooting:
    echo    1. Check SSH connection: ssh %VPS_USER%@%VPS_IP%
    echo    2. Run setup_with_password.bat to setup Git
    echo    3. Make sure code is committed: git add . && git commit -m "message"
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Deploy completed!
echo ========================================
echo.
echo Verifying deployment...
call check_deploy.bat

echo.
echo URLs:
echo    - Admin: http://%VPS_IP%:8000/admin
echo    - Health: http://%VPS_IP%:8000/health
echo.
pause

