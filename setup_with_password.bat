@echo off
REM Script setup với password (An toàn hơn - yêu cầu nhập password mỗi lần)

echo ========================================
echo   Setup Git Deploy with Password
echo ========================================
echo.
echo ⚠️  DO NOT ENTER PASSWORD IN FILE!
echo    Script will prompt for password when needed
echo.

set VPS_IP=97.74.83.97
set VPS_USER=myadmin

echo [Step 1/3] Setup Git on local...
if not exist .git (
    git init
    echo ✅ Git repo initialized
) else (
    echo ✅ Git repo already exists
)

REM Setup Git user config if not set
git config user.name >nul 2>&1
if errorlevel 1 (
    echo ⚙️  Setting Git user config...
    git config user.name "Screenshot Analyzer"
    git config user.email "admin@lukistar.space"
    echo ✅ Git config set
)

git remote get-url vps >nul 2>&1
if errorlevel 1 (
    git remote add vps %VPS_USER%@%VPS_IP%:~/screenshot-analyzer.git
    echo ✅ Remote VPS added
) else (
    echo ✅ Remote VPS already exists
)
echo.

echo [Step 2/3] Setup Git on VPS...
echo.
echo 🔐 You will need to enter VPS password for user: %VPS_USER%
echo 📝 Or if SSH key is already setup, it will login automatically
echo.
echo Press Enter to continue...
pause >nul

REM Tạo script setup cho VPS
(
echo #!/bin/bash
echo mkdir -p ~/screenshot-analyzer.git
echo cd ~/screenshot-analyzer.git
echo git init --bare
echo.
echo cat ^> hooks/post-receive ^<^< 'EOF'
echo #!/bin/bash
echo WORK_TREE=$HOME/screenshot-analyzer
echo GIT_DIR=$HOME/screenshot-analyzer.git
echo echo "🔄 Receiving new code, starting deploy..."
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
echo echo "✅ Deploy completed!"
echo EOF
echo chmod +x hooks/post-receive
echo echo "✅ Git setup completed!"
) > temp_setup.sh

echo 📤 Uploading setup script to VPS...
scp temp_setup.sh %VPS_USER%@%VPS_IP%:~/temp_setup.sh
if errorlevel 1 (
    echo ❌ Upload failed! Check SSH connection.
    del temp_setup.sh 2>nul
    pause
    exit /b 1
)

echo 🔄 Running setup script on VPS...
ssh %VPS_USER%@%VPS_IP% "bash ~/temp_setup.sh && rm ~/temp_setup.sh"
if errorlevel 1 (
    echo ❌ Setup failed on VPS!
    del temp_setup.sh 2>nul
    pause
    exit /b 1
)

del temp_setup.sh 2>nul
echo ✅ Git setup on VPS completed!
echo.

echo [Step 3/3] Commit and push code (first time)...
git add .

REM Check if there are any changes to commit
git diff --cached --quiet 2>nul
if errorlevel 1 (
    echo 📝 Committing changes...
    git commit -m "Initial commit - Screenshot Analyzer Server"
    echo ✅ Changes committed
) else (
    REM Check if repository has any commits
    git rev-parse --verify HEAD >nul 2>&1
    if errorlevel 1 (
        echo ⚠️  No changes staged, but repository has no commits yet
        echo 📝 Creating initial commit...
        git commit -m "Initial commit - Screenshot Analyzer Server" --allow-empty
        echo ✅ Initial commit created
    ) else (
        echo ⚠️  No changes to commit
    )
)

echo.
echo 📤 Pushing code to VPS...
echo    (Will automatically setup and deploy on VPS)
echo.

REM Try different branch names
git branch -M main 2>nul
git push -u vps main 2>nul
if errorlevel 1 (
    git branch -M master 2>nul
    git push -u vps master 2>nul
    if errorlevel 1 (
        echo ❌ Push failed! No commits to push.
        echo 💡 Make sure files are committed first.
        echo.
        echo Try manually:
        echo   git add .
        echo   git commit -m "Initial commit"
        echo   git push -u vps main
        pause
        exit /b 1
    )
)

echo.
echo ========================================
echo   ✅ Completed!
echo ========================================
echo.
echo 🌐 Check:
echo    http://%VPS_IP%:8000/health
echo    http://%VPS_IP%:8000/admin
echo.
pause

