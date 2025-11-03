#!/bin/bash
WORK_TREE=$HOME/screenshot-analyzer
GIT_DIR=$HOME/screenshot-analyzer.git
echo "Receiving new code, starting deploy..."
mkdir -p $WORK_TREE
git --git-dir="$GIT_DIR" --work-tree="$WORK_TREE" checkout -f
cd "$WORK_TREE"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
fi
source venv/bin/activate
pip install -r requirements.txt --quiet
sudo systemctl restart screenshot-analyzer 2>/dev/null || echo "Service not configured yet"
echo "Deploy completed!"

