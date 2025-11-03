#!/bin/bash
# Script tự động setup Git trên VPS
# Có thể dùng password hoặc SSH key

set -e

VPS_IP="97.74.83.97"
VPS_USER="myadmin"
VPS_DIR="~/screenshot-analyzer.git"
WORK_DIR="~/screenshot-analyzer"

echo "🚀 Auto Setup Git trên VPS..."
echo "VPS: $VPS_USER@$VPS_IP"
echo ""

# Hàm setup Git trên VPS
setup_git_on_vps() {
    local password=$1
    
    echo "📦 Đang setup Git trên VPS..."
    
    if [ -z "$password" ]; then
        echo "⚠️ Không có password, dùng SSH key..."
        ssh $VPS_USER@$VPS_IP << 'ENDSSH'
# Tạo bare repository
mkdir -p ~/screenshot-analyzer.git
cd ~/screenshot-analyzer.git
git init --bare

# Tạo post-receive hook
cat > hooks/post-receive << 'HOOK_EOF'
#!/bin/bash
WORK_TREE=$HOME/screenshot-analyzer
GIT_DIR=$HOME/screenshot-analyzer.git

echo "🔄 Nhận code mới, bắt đầu deploy..."

mkdir -p $WORK_TREE
git --git-dir="$GIT_DIR" --work-tree="$WORK_TREE" checkout -f

cd "$WORK_TREE"

if [ ! -d "venv" ]; then
    echo "📦 Tạo virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    
    # Tạo systemd service
    echo "⚙️ Tạo systemd service..."
    sudo tee /etc/systemd/system/screenshot-analyzer.service > /dev/null << 'SERVICE_EOF'
[Unit]
Description=Screenshot Analyzer Server
After=network.target

[Service]
Type=simple
User=myadmin
WorkingDirectory=/home/myadmin/screenshot-analyzer
Environment="PATH=/home/myadmin/screenshot-analyzer/venv/bin:/usr/bin:/usr/local/bin"
ExecStart=/home/myadmin/screenshot-analyzer/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICE_EOF

    sudo systemctl daemon-reload
    sudo systemctl enable screenshot-analyzer
else
    echo "📦 Cài đặt dependencies mới..."
    source venv/bin/activate
    pip install -r requirements.txt --quiet
fi

echo "🔄 Restart service..."
sudo systemctl restart screenshot-analyzer

echo "✅ Deploy hoàn tất!"
HOOK_EOF

chmod +x hooks/post-receive
echo "✅ Git setup hoàn tất trên VPS!"
ENDSSH
    else
        echo "🔐 Dùng password để setup..."
        sshpass -p "$password" ssh -o StrictHostKeyChecking=no $VPS_USER@$VPS_IP << 'ENDSSH'
# Tạo bare repository
mkdir -p ~/screenshot-analyzer.git
cd ~/screenshot-analyzer.git
git init --bare

# Tạo post-receive hook
cat > hooks/post-receive << 'HOOK_EOF'
#!/bin/bash
WORK_TREE=$HOME/screenshot-analyzer
GIT_DIR=$HOME/screenshot-analyzer.git

echo "🔄 Nhận code mới, bắt đầu deploy..."

mkdir -p $WORK_TREE
git --git-dir="$GIT_DIR" --work-tree="$WORK_TREE" checkout -f

cd "$WORK_TREE"

if [ ! -d "venv" ]; then
    echo "📦 Tạo virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    
    # Tạo systemd service
    echo "⚙️ Tạo systemd service..."
    sudo tee /etc/systemd/system/screenshot-analyzer.service > /dev/null << 'SERVICE_EOF'
[Unit]
Description=Screenshot Analyzer Server
After=network.target

[Service]
Type=simple
User=myadmin
WorkingDirectory=/home/myadmin/screenshot-analyzer
Environment="PATH=/home/myadmin/screenshot-analyzer/venv/bin:/usr/bin:/usr/local/bin"
ExecStart=/home/myadmin/screenshot-analyzer/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICE_EOF

    sudo systemctl daemon-reload
    sudo systemctl enable screenshot-analyzer
else
    echo "📦 Cài đặt dependencies mới..."
    source venv/bin/activate
    pip install -r requirements.txt --quiet
fi

echo "🔄 Restart service..."
sudo systemctl restart screenshot-analyzer

echo "✅ Deploy hoàn tất!"
HOOK_EOF

chmod +x hooks/post-receive
echo "✅ Git setup hoàn tất trên VPS!"
ENDSSH
    fi
}

# Kiểm tra xem có password không
if [ -z "$1" ]; then
    echo "⚠️ Không có password. Dùng SSH key hoặc nhập password:"
    read -s -p "Nhập password VPS (hoặc Enter để bỏ qua và dùng SSH key): " PASSWORD
    echo ""
    setup_git_on_vps "$PASSWORD"
else
    setup_git_on_vps "$1"
fi

echo ""
echo "✅ Setup Git trên VPS hoàn tất!"
echo ""
echo "📝 Tiếp theo:"
echo "   1. Setup Git trên local: chạy setup_git_local.bat"
echo "   2. Push code: git push vps main"

