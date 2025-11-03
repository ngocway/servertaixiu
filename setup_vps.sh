#!/bin/bash
# Script setup VPS lần đầu (chạy trên VPS)
# Domain: lukistar.space
# VPS IP: 97.74.83.97

set -e

echo "🔧 Setup VPS cho Screenshot Analyzer Server..."

# Cập nhật system
echo "📦 Cập nhật system packages..."
sudo apt update
sudo apt upgrade -y

# Cài đặt Python và pip
echo "🐍 Cài đặt Python 3.10+..."
sudo apt install -y python3 python3-pip python3-venv

# Cài đặt nginx (optional, cho reverse proxy)
echo "🌐 Cài đặt Nginx (optional)..."
sudo apt install -y nginx || echo "⚠️ Nginx installation skipped"

# Tạo thư mục project
PROJECT_DIR="$HOME/screenshot-analyzer"
echo "📁 Tạo thư mục project: $PROJECT_DIR"
mkdir -p $PROJECT_DIR
mkdir -p $PROJECT_DIR/screenshots
mkdir -p $PROJECT_DIR/results
cd $PROJECT_DIR

# Tạo virtual environment
echo "🔨 Tạo virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Cài đặt dependencies
echo "📦 Cài đặt Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Tạo systemd service
echo "⚙️ Tạo systemd service..."
sudo tee /etc/systemd/system/screenshot-analyzer.service > /dev/null << 'EOF'
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
EOF

# Reload systemd và enable service
sudo systemctl daemon-reload
sudo systemctl enable screenshot-analyzer

# Mở firewall port (nếu cần)
echo "🔥 Cấu hình firewall..."
sudo ufw allow 8000/tcp || echo "⚠️ UFW not installed or already configured"
sudo ufw allow 22/tcp || echo "⚠️ SSH port already open"

echo ""
echo "✅ Setup hoàn tất!"
echo ""
echo "🚀 Khởi động server:"
echo "   sudo systemctl start screenshot-analyzer"
echo ""
echo "📊 Kiểm tra status:"
echo "   sudo systemctl status screenshot-analyzer"
echo ""
echo "📝 Xem logs:"
echo "   sudo journalctl -u screenshot-analyzer -f"

