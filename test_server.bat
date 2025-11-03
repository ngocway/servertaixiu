@echo off
REM Script test server từ máy local

set VPS_IP=97.74.83.97

echo ========================================
echo   Testing Server Connection
echo ========================================
echo.

echo [1/3] Testing health endpoint...
curl http://%VPS_IP%:8000/health 2>nul
if errorlevel 1 (
    echo ❌ Cannot connect to server!
    echo    Server might not be running
    echo.
) else (
    echo ✅ Server is running!
    echo.
)

echo [2/3] Opening admin dashboard in browser...
start http://%VPS_IP%:8000/admin

echo [3/3] Opening health check in browser...
start http://%VPS_IP%:8000/health

echo.
echo ========================================
echo   ✅ Testing completed!
echo ========================================
echo.
echo 🌐 URLs:
echo    - Admin: http://%VPS_IP%:8000/admin
echo    - Health: http://%VPS_IP%:8000/health
echo    - API Docs: http://%VPS_IP%:8000/docs
echo.
pause

