@echo off
REM Script kiểm tra nhanh xem code đã deploy chưa

set VPS_IP=97.74.83.97
set VPS_USER=myadmin

echo ========================================
echo   Quick Deployment Verification
echo ========================================
echo.

echo [1/3] Checking if code exists on VPS...
ssh %VPS_USER%@%VPS_IP% "test -d ~/screenshot-analyzer/app" 2>nul
if errorlevel 1 (
    echo ❌ Code NOT deployed yet
    echo.
    echo 💡 Run: .\deploy_complete.bat
    goto :end
) else (
    echo ✅ Code directory exists on VPS
)

echo.
echo [2/3] Checking main files...
ssh %VPS_USER%@%VPS_IP% "test -f ~/screenshot-analyzer/app/main.py" 2>nul
if errorlevel 1 (
    echo ❌ app/main.py NOT found
) else (
    echo ✅ app/main.py exists
)

ssh %VPS_USER%@%VPS_IP% "test -f ~/screenshot-analyzer/requirements.txt" 2>nul
if errorlevel 1 (
    echo ❌ requirements.txt NOT found
) else (
    echo ✅ requirements.txt exists
)

echo.
echo [3/3] Checking if server is running...
curl -s -o nul -w "%%{http_code}" http://%VPS_IP%:8000/health 2>nul | find "200" >nul
if errorlevel 1 (
    echo ❌ Server is NOT running
    echo.
    echo 💡 Start server:
    echo    SSH to VPS: ssh %VPS_USER%@%VPS_IP%
    echo    Then run: cd ~/screenshot-analyzer
    echo    Then run: uvicorn app.main:app --host 0.0.0.0 --port 8000
) else (
    echo ✅ Server is RUNNING!
    echo.
    echo 📊 Testing health endpoint...
    curl -s http://%VPS_IP%:8000/health
    echo.
    echo.
    echo ✅✅✅ DEPLOY SUCCESSFUL! ✅✅✅
    echo.
    echo 🌐 Open in browser:
    echo    http://%VPS_IP%:8000/admin
    echo    http://%VPS_IP%:8000/health
    echo.
    start http://%VPS_IP%:8000/admin
)

:end
echo.
pause

