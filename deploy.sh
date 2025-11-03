#!/bin/bash
# Script deploy server lên VPS GoDaddy
# Domain: lukistar.space
# VPS IP: 97.74.83.97

set -e

echo "🚀 Bắt đầu deploy Screenshot Analyzer Server..."

# Thông tin VPS
VPS_IP="97.74.83.97"
VPS_USER="myadmin"
DOMAIN="lukistar.space"
SERVER_PORT="8000"

echo "📋 Thông tin deploy:"
echo "   VPS IP: $VPS_IP"
echo "   Domain: $DOMAIN"
echo "   Port: $SERVER_PORT"

# Kiểm tra kết nối
echo ""
echo "🔍 Kiểm tra kết nối đến VPS..."
ssh -o ConnectTimeout=5 $VPS_USER@$VPS_IP "echo 'Kết nối thành công!'" || {
    echo "❌ Không thể kết nối đến VPS. Vui lòng kiểm tra SSH key và thông tin đăng nhập."
    exit 1
}

echo ""
echo "✅ Kết nối thành công!"

# Tạo thư mục trên VPS
echo ""
echo "📁 Tạo thư mục project trên VPS..."
ssh $VPS_USER@$VPS_IP << 'ENDSSH'
PROJECT_DIR="$HOME/screenshot-analyzer"
mkdir -p $PROJECT_DIR
mkdir -p $PROJECT_DIR/screenshots
mkdir -p $PROJECT_DIR/results
echo "✅ Thư mục đã tạo: $PROJECT_DIR"
ENDSSH

# Upload files (nếu cần)
echo ""
echo "📤 Upload files lên VPS..."
echo "   (Bỏ qua bước này nếu code đã có trên VPS)"
echo "   Sử dụng: scp -r . $VPS_USER@$VPS_IP:~/screenshot-analyzer/"

# Cài đặt dependencies
echo ""
echo "📦 Cài đặt dependencies..."
ssh $VPS_USER@$VPS_IP << 'ENDSSH'
cd ~/screenshot-analyzer
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo "✅ Dependencies đã được cài đặt"
ENDSSH

# Tạo systemd service
echo ""
echo "⚙️ Tạo systemd service..."
ssh $VPS_USER@$VPS_IP << 'ENDSSH'
PROJECT_DIR="$HOME/screenshot-analyzer"
SERVICE_FILE="/tmp/screenshot-analyzer.service"

cat > $SERVICE_FILE << 'EOF'
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

sudo mv $SERVICE_FILE /etc/systemd/system/screenshot-analyzer.service
sudo systemctl daemon-reload
sudo systemctl enable screenshot-analyzer
echo "✅ Systemd service đã được tạo"
ENDSSH

# Khởi động service
echo ""
echo "🔄 Khởi động server..."
ssh $VPS_USER@$VPS_IP << 'ENDSSH'
sudo systemctl restart screenshot-analyzer
sleep 2
sudo systemctl status screenshot-analyzer --no-pager
ENDSSH

echo ""
echo "✅ Deploy hoàn tất!"
echo ""
echo "🌐 Truy cập:"
echo "   API: http://$VPS_IP:$SERVER_PORT"
echo "   Admin: http://$VPS_IP:$SERVER_PORT/admin"
echo "   Domain: http://$DOMAIN:$SERVER_PORT (nếu đã cấu hình DNS)"
echo ""
echo "📝 Kiểm tra logs:"
echo "   sudo journalctl -u screenshot-analyzer -f"

