@echo off
REM Script sửa post-receive hook trên VPS

set VPS_IP=97.74.83.97
set VPS_USER=myadmin

echo Fixing post-receive hook on VPS...

REM Create correct hook file
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
echo fi
echo source venv/bin/activate
echo pip install -r requirements.txt --quiet
echo sudo systemctl restart screenshot-analyzer 2>/dev/null || echo "Service not configured yet"
echo echo "Deploy completed!"
) > temp_hook_fix.sh

echo Uploading fixed hook...
scp temp_hook_fix.sh %VPS_USER%@%VPS_IP%:~/temp_hook_fix.sh
ssh %VPS_USER%@%VPS_IP% "cat ~/temp_hook_fix.sh > ~/screenshot-analyzer.git/hooks/post-receive && chmod +x ~/screenshot-analyzer.git/hooks/post-receive && rm ~/temp_hook_fix.sh"

del temp_hook_fix.sh

echo ✅ Hook fixed!
echo.
echo Triggering deployment...
git push vps main --force

echo.
echo ✅ Done!
pause

