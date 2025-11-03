@echo off
REM Script tự động setup hoàn chỉnh (Windows)
REM Setup cả Git trên VPS và local

setlocal enabledelayedexpansion

echo ========================================
echo   Auto Setup Git Deploy - Complete
echo ========================================
echo.

set VPS_IP=97.74.83.97
set VPS_USER=myadmin
set VPS_REMOTE=%VPS_USER%@%VPS_IP%:~/screenshot-analyzer.git

echo [1/4] Checking Git...
git --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Git is not installed!
    echo 📥 Download Git from: https://git-scm.com/download/win
    echo.
    pause
    exit /b 1
)
echo ✅ Git is installed
echo.

echo [2/4] Checking SSH...
where ssh >nul 2>&1
if errorlevel 1 (
    echo ❌ SSH not found! Installing Git will include SSH.
    pause
    exit /b 1
)
echo ✅ SSH is available
echo.

echo [3/4] Setup Git on local...
if not exist .git (
    echo 📦 Initializing Git repository...
    git init
    echo ✅ Git repository initialized
) else (
    echo ✅ Git repository already exists
)

git remote get-url vps >nul 2>&1
if errorlevel 1 (
    echo 📡 Adding remote VPS...
    git remote add vps %VPS_REMOTE%
    echo ✅ Remote VPS added: %VPS_REMOTE%
) else (
    echo ✅ Remote VPS already exists
)
echo.

echo [4/4] Setup Git on VPS...
echo.
echo ⚠️  You will need to enter VPS password for setup
echo 📝 Or if SSH key is already setup, it will login automatically
echo.
echo 🔐 Press Enter to continue (or Ctrl+C to cancel)...
pause >nul

echo.
echo 🔄 Connecting to VPS and setting up Git...
echo.

REM Tạo script setup để chạy trên VPS
echo Creating temporary setup script...
(
echo mkdir -p ~/screenshot-analyzer.git
echo cd ~/screenshot-analyzer.git
echo git init --bare
echo.
echo cat ^> hooks/post-receive ^<^< 'EOF'
echo #!/bin/bash
echo WORK_TREE=$HOME/screenshot-analyzer
echo GIT_DIR=$HOME/screenshot-analyzer.git
echo.
echo echo "🔄 Receiving new code, starting deploy..."
echo.
echo mkdir -p $WORK_TREE
echo git --git-dir="$GIT_DIR" --work-tree="$WORK_TREE" checkout -f
echo.
echo cd "$WORK_TREE"
echo.
echo if [ ! -d "venv" ]; then
echo     echo "📦 Creating virtual environment..."
echo     python3 -m venv venv
echo     source venv/bin/activate
echo     pip install --upgrade pip
echo     pip install -r requirements.txt
echo.
echo     echo "⚙️ Creating systemd service..."
echo     sudo tee /etc/systemd/system/screenshot-analyzer.service ^> /dev/null ^<^< 'SERVICE_EOF'
echo [Unit]
echo Description=Screenshot Analyzer Server
echo After=network.target
echo.
echo [Service]
echo Type=simple
echo User=myadmin
echo WorkingDirectory=/home/myadmin/screenshot-analyzer
echo Environment="PATH=/home/myadmin/screenshot-analyzer/venv/bin:/usr/bin:/usr/local/bin"
echo ExecStart=/home/myadmin/screenshot-analyzer/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
echo Restart=always
echo RestartSec=10
echo.
echo [Install]
echo WantedBy=multi-user.target
echo SERVICE_EOF
echo.
echo     sudo systemctl daemon-reload
echo     sudo systemctl enable screenshot-analyzer
echo else
echo     echo "📦 Installing new dependencies..."
echo     source venv/bin/activate
echo     pip install -r requirements.txt --quiet
echo fi
echo.
echo echo "🔄 Restart service..."
echo sudo systemctl restart screenshot-analyzer
echo.
echo echo "✅ Deploy completed!"
echo EOF
echo.
echo chmod +x hooks/post-receive
echo echo "✅ Git setup completed on VPS!"
) > setup_vps_git.sh

REM Upload script to VPS and run
echo 📤 Uploading and running setup script on VPS...
scp setup_vps_git.sh %VPS_USER%@%VPS_IP%:~/setup_vps_git.sh
if errorlevel 1 (
    echo ❌ Failed to upload script! Check SSH connection.
    del setup_vps_git.sh 2>nul
    pause
    exit /b 1
)

ssh %VPS_USER%@%VPS_IP% "bash ~/setup_vps_git.sh && rm ~/setup_vps_git.sh"
if errorlevel 1 (
    echo ❌ Setup failed on VPS! Check password or SSH key.
    del setup_vps_git.sh 2>nul
    pause
    exit /b 1
)

del setup_vps_git.sh 2>nul
echo.

echo [5/5] Committing and pushing code (first time)...
git add .
git commit -m "Initial commit - Auto setup" 2>nul || echo ⚠️  No changes to commit

echo.
echo 📤 Pushing code to VPS (first time will setup everything)...
git push vps main 2>nul || git push vps master 2>nul || (
    echo ⚠️  No main/master branch. Push manually later.
    echo    git push vps HEAD:main
)

echo.
echo ========================================
echo   ✅ Setup completed!
echo ========================================
echo.
echo 📝 Next steps:
echo.
echo   1. Check server:
echo      curl http://%VPS_IP%:8000/health
echo.
echo   2. Open Admin Dashboard:
echo      http://%VPS_IP%:8000/admin
echo.
echo   3. Update code each time:
echo      git add .
echo      git commit -m "Description of changes"
echo      git push vps main
echo.
echo ========================================
pause

