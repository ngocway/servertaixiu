@echo off
REM Script deploy đơn giản - không cần password

set VPS_IP=97.74.83.97
set VPS_USER=myadmin

echo ========================================
echo   Simple Deploy to VPS
echo ========================================
echo.

echo [1/4] Checking SSH key...
ssh -o BatchMode=yes %VPS_USER%@%VPS_IP% "echo OK" >nul 2>&1
if errorlevel 1 (
    echo ❌ SSH key not working!
    pause
    exit /b 1
)
echo ✅ SSH key OK
echo.

echo [2/4] Checking Git...
git config user.name >nul 2>&1
if errorlevel 1 (
    git config user.name "Screenshot Analyzer"
    git config user.email "admin@lukistar.space"
)
echo ✅ Git config OK
echo.

echo [3/4] Committing changes...
git add .
git commit -m "Deploy - %date% %time%" 2>nul || git commit -m "Initial commit" --allow-empty
echo ✅ Committed
echo.

REM Setup remote if needed
git remote get-url vps >nul 2>&1
if errorlevel 1 (
    git remote add vps %VPS_USER%@%VPS_IP%:~/screenshot-analyzer.git
)

REM Setup Git on VPS if needed
ssh %VPS_USER%@%VPS_IP% "test -d ~/screenshot-analyzer.git" >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Setting up Git on VPS...
    ssh %VPS_USER%@%VPS_IP% "mkdir -p ~/screenshot-analyzer.git"
    ssh %VPS_USER%@%VPS_IP% "cd ~/screenshot-analyzer.git && git init --bare"
    
    REM Create simple post-receive hook
    echo Creating post-receive hook...
    echo #!/bin/bash > temp_hook.sh
    echo WORK_TREE=$HOME/screenshot-analyzer >> temp_hook.sh
    echo GIT_DIR=$HOME/screenshot-analyzer.git >> temp_hook.sh
    echo mkdir -p $WORK_TREE >> temp_hook.sh
    echo git --git-dir="$GIT_DIR" --work-tree="$WORK_TREE" checkout -f >> temp_hook.sh
    echo cd "$WORK_TREE" >> temp_hook.sh
    echo if [ ! -d "venv" ]; then >> temp_hook.sh
    echo     python3 -m venv venv >> temp_hook.sh
    echo     source venv/bin/activate >> temp_hook.sh
    echo     pip install -r requirements.txt >> temp_hook.sh
    echo     sudo systemctl daemon-reload >> temp_hook.sh
    echo     sudo systemctl enable screenshot-analyzer >> temp_hook.sh
    echo fi >> temp_hook.sh
    echo source venv/bin/activate >> temp_hook.sh
    echo pip install -r requirements.txt --quiet >> temp_hook.sh
    echo sudo systemctl restart screenshot-analyzer >> temp_hook.sh
    
    scp temp_hook.sh %VPS_USER%@%VPS_IP%:~/temp_hook.sh
    ssh %VPS_USER%@%VPS_IP% "cat ~/temp_hook.sh > ~/screenshot-analyzer.git/hooks/post-receive && chmod +x ~/screenshot-analyzer.git/hooks/post-receive && rm ~/temp_hook.sh"
    del temp_hook.sh
    echo ✅ Git setup on VPS
)
echo.

echo [4/4] Pushing to VPS...
git branch -M main 2>nul
git push -u vps main
if errorlevel 1 (
    echo ❌ Push failed!
    pause
    exit /b 1
)

echo.
echo ========================================
echo   ✅ Deploy Completed!
echo ========================================
echo.
echo 🌐 Check:
echo    http://%VPS_IP%:8000/admin
echo.
start http://%VPS_IP%:8000/admin 2>nul
pause

