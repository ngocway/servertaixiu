@echo off
REM Script kiểm tra code đã deploy lên VPS chưa

set VPS_IP=97.74.83.97
set VPS_USER=myadmin

echo ========================================
echo   Checking Deployment Status
echo ========================================
echo.

echo [1/5] Checking SSH connection...
ssh -o ConnectTimeout=5 %VPS_USER%@%VPS_IP% "echo 'SSH OK'" >nul 2>&1
if errorlevel 1 (
    echo ❌ Cannot connect to VPS!
    echo    Check: ssh %VPS_USER%@%VPS_IP%
    pause
    exit /b 1
)
echo ✅ SSH connection OK
echo.

echo [2/5] Checking Git repository on VPS...
ssh %VPS_USER%@%VPS_IP% "test -d ~/screenshot-analyzer.git" 2>nul
if errorlevel 1 (
    echo ❌ Git repository not found on VPS!
    echo    Run: setup_with_password.bat
    set GIT_SETUP=NO
) else (
    echo ✅ Git repository exists on VPS
    set GIT_SETUP=YES
)
echo.

echo [3/5] Checking project directory on VPS...
ssh %VPS_USER%@%VPS_IP% "test -d ~/screenshot-analyzer" 2>nul
if errorlevel 1 (
    echo ❌ Project directory not found!
    echo    Code hasn't been deployed yet
    set CODE_DEPLOYED=NO
) else (
    echo ✅ Project directory exists
    set CODE_DEPLOYED=YES
    
    echo.
    echo 📁 Checking files...
    ssh %VPS_USER%@%VPS_IP% "ls -la ~/screenshot-analyzer/ | head -10"
    echo.
    
    echo 📄 Checking main files...
    ssh %VPS_USER%@%VPS_IP% "test -f ~/screenshot-analyzer/app/main.py" 2>nul
    if errorlevel 1 (
        echo ⚠️  app/main.py not found
    ) else (
        echo ✅ app/main.py exists
    )
    
    ssh %VPS_USER%@%VPS_IP% "test -f ~/screenshot-analyzer/requirements.txt" 2>nul
    if errorlevel 1 (
        echo ⚠️  requirements.txt not found
    ) else (
        echo ✅ requirements.txt exists
    )
)
echo.

echo [4/5] Checking Python virtual environment...
ssh %VPS_USER%@%VPS_IP% "test -d ~/screenshot-analyzer/venv" 2>nul
if errorlevel 1 (
    echo ⚠️  Virtual environment not created yet
    set VENV_EXISTS=NO
) else (
    echo ✅ Virtual environment exists
    set VENV_EXISTS=YES
)
echo.

echo [5/5] Checking if server is running...
curl -s -o nul -w "%%{http_code}" http://%VPS_IP%:8000/health 2>nul | find "200" >nul
if errorlevel 1 (
    echo ❌ Server is not running!
    echo    Status: Offline
    set SERVER_RUNNING=NO
) else (
    echo ✅ Server is running!
    echo    Status: Online
    set SERVER_RUNNING=YES
    
    echo.
    echo 📊 Testing endpoints...
    curl -s http://%VPS_IP%:8000/health
    echo.
)

echo.
echo ========================================
echo   Summary
echo ========================================
echo.

if "%GIT_SETUP%"=="NO" (
    echo ❌ Git: Not setup
    echo    → Run: setup_with_password.bat
) else (
    echo ✅ Git: Setup
)

if "%CODE_DEPLOYED%"=="NO" (
    echo ❌ Code: Not deployed
    echo    → Run: deploy_now.bat
) else (
    echo ✅ Code: Deployed
)

if "%VENV_EXISTS%"=="NO" (
    echo ⚠️  Python venv: Not created
    echo    → Will be created on first deploy
) else (
    echo ✅ Python venv: Exists
)

if "%SERVER_RUNNING%"=="NO" (
    echo ❌ Server: Not running
    echo    → SSH to VPS and start: uvicorn app.main:app --host 0.0.0.0 --port 8000
    echo    → Or enable service: sudo systemctl start screenshot-analyzer
) else (
    echo ✅ Server: Running
    echo    → Access: http://%VPS_IP%:8000/admin
)

echo.
echo ========================================
pause

