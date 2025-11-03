@echo off
REM Script deploy không cần password (sử dụng SSH key)

set VPS_IP=97.74.83.97
set VPS_USER=myadmin

echo ========================================
echo   Deploy Without Password (SSH Key)
echo ========================================
echo.

echo [Step 1/5] Checking SSH key...
ssh -o BatchMode=yes -o ConnectTimeout=5 %VPS_USER%@%VPS_IP% "echo OK" >nul 2>&1
if errorlevel 1 (
    echo ❌ SSH key not setup!
    echo.
    echo 💡 Setup SSH key first:
    echo    .\setup_ssh_key.bat
    echo.
    pause
    exit /b 1
)
echo ✅ SSH key is working (no password needed!)
echo.

echo [Step 2/5] Checking Git config...
git config user.name >nul 2>&1
if errorlevel 1 (
    git config user.name "Screenshot Analyzer"
    git config user.email "admin@lukistar.space"
)
echo ✅ Git config OK
echo.

echo [Step 3/5] Checking Git setup on VPS...
ssh %VPS_USER%@%VPS_IP% "test -d ~/screenshot-analyzer.git" 2>nul
if errorlevel 1 (
    echo ⚠️  Git not setup on VPS
    echo 🔄 Setting up Git on VPS (no password needed!)...
    
    REM Create bare repository
    ssh %VPS_USER%@%VPS_IP% "mkdir -p ~/screenshot-analyzer.git"
    ssh %VPS_USER%@%VPS_IP% "cd ~/screenshot-analyzer.git && git init --bare"
    
    REM Create post-receive hook
    echo Creating post-receive hook...
    REM Create hook file locally first
    (
    echo #!/bin/bash
    echo WORK_TREE=$HOME/screenshot-analyzer
    echo GIT_DIR=$HOME/screenshot-analyzer.git
    echo echo "Receiving new code, starting deploy..."
    echo mkdir -p $WORK_TREE
    echo git --git-dir="$GIT_DIR" --work-tree="$WORK_TREE" checkout -f
    echo cd "$WORK_TREE"
    echo if [ ! -d "venv" ]; then
    echo     python3 -m venv venv
    echo     source venv/bin/activate
    echo     pip install --upgrade pip
    echo     pip install -r requirements.txt
    echo     sudo tee /etc/systemd/system/screenshot-analyzer.service ^> /dev/null ^<^< 'SERVICE_EOF'
    echo [Unit]
    echo Description=Screenshot Analyzer Server
    echo After=network.target
    echo [Service]
    echo Type=simple
    echo User=myadmin
    echo WorkingDirectory=/home/myadmin/screenshot-analyzer
    echo Environment="PATH=/home/myadmin/screenshot-analyzer/venv/bin:/usr/bin:/usr/local/bin"
    echo ExecStart=/home/myadmin/screenshot-analyzer/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
    echo Restart=always
    echo RestartSec=10
    echo [Install]
    echo WantedBy=multi-user.target
    echo SERVICE_EOF
    echo     sudo systemctl daemon-reload
    echo     sudo systemctl enable screenshot-analyzer
    echo else
    echo     source venv/bin/activate
    echo     pip install -r requirements.txt --quiet
    echo fi
    echo sudo systemctl restart screenshot-analyzer
    echo echo "Deploy completed!"
    ) > temp_post_receive.sh
    
    REM Upload and setup hook on VPS
    scp temp_post_receive.sh %VPS_USER%@%VPS_IP%:~/temp_post_receive.sh
    ssh %VPS_USER%@%VPS_IP% "cat ~/temp_post_receive.sh > ~/screenshot-analyzer.git/hooks/post-receive && rm ~/temp_post_receive.sh"
    del temp_post_receive.sh 2>nul
    
    ssh %VPS_USER%@%VPS_IP% "chmod +x ~/screenshot-analyzer.git/hooks/post-receive"
    echo ✅ Git setup completed on VPS!
) else (
    echo ✅ Git is already setup on VPS
)
echo.

REM Setup remote if not exists
git remote get-url vps >nul 2>&1
if errorlevel 1 (
    git remote add vps %VPS_USER%@%VPS_IP%:~/screenshot-analyzer.git
)

echo [Step 4/5] Committing changes...
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

echo [Step 5/5] Pushing to VPS (no password needed!)...
git branch -M main 2>nul
git push -u vps main
if errorlevel 1 (
    echo ❌ Push failed!
    echo.
    echo 💡 Check:
    echo    - Git is setup: ssh %VPS_USER%@%VPS_IP% "ls ~/screenshot-analyzer.git"
    echo    - There are commits: git log --oneline
    pause
    exit /b 1
)

echo.
echo ========================================
echo   ✅ Deploy Completed (No Password!)
echo ========================================
echo.
echo 🔍 Verifying...
curl -s http://%VPS_IP%:8000/health 2>nul
if errorlevel 1 (
    echo ⚠️  Server might not be running yet
) else (
    echo ✅ Server is running!
)

echo.
echo 🌐 Open in browser:
echo    http://%VPS_IP%:8000/admin
echo.
start http://%VPS_IP%:8000/admin 2>nul
pause

