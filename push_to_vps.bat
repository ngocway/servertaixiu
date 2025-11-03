@echo off
REM Script nhanh để push code lên VPS
REM Chạy trong thư mục d:\Testthu

echo 🚀 Pushing code to VPS...

REM Add all changes
git add .

REM Get message from parameter or use default
if "%1"=="" (
    set "commit_msg=Update code"
) else (
    set "commit_msg=%*"
)

REM Commit
git commit -m "%commit_msg%"
if errorlevel 1 (
    echo ⚠️ No changes to commit, or already committed
)

REM Push to VPS
echo 📤 Pushing to VPS...
git push vps main
if errorlevel 1 (
    echo ❌ Push failed! Check SSH connection.
    pause
    exit /b 1
)

echo.
echo ✅ Push successful!
echo 🔄 VPS is automatically updating and restarting service...
echo.
echo 📊 Check: http://97.74.83.97:8000/health
echo.
pause

