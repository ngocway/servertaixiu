@echo off
REM Script deploy nhanh - chỉ commit và push, bỏ qua các bước kiểm tra

set VPS_IP=97.74.83.97
set VPS_USER=myadmin

echo [Quick Deploy] Committing and pushing...
git add . >nul 2>&1
git commit -m "Quick deploy - %date% %time%" >nul 2>&1
git push vps main 2>nul || git push vps master 2>nul || git push vps HEAD:main

if errorlevel 1 (
    echo Deploy failed! Run deploy_now.bat for detailed error.
    exit /b 1
)

echo [Quick Deploy] Done! Server: http://%VPS_IP%:8000/admin


























