#!/bin/bash
# Script cài đặt auto-start cho Screenshot Analyzer Server

echo "=================================================="
echo "  CÀI ĐẶT AUTO-START CHO SERVER"
echo "=================================================="
echo ""

# Kiểm tra quyền sudo
if ! sudo -v; then
    echo "❌ Cần quyền sudo để cài đặt systemd service"
    exit 1
fi

echo "📝 Bước 1: Copy service file..."
sudo cp /tmp/screenshot-analyzer.service /etc/systemd/system/

echo "🔄 Bước 2: Reload systemd..."
sudo systemctl daemon-reload

echo "⏹️  Bước 3: Dừng process cũ..."
pkill -f "uvicorn app.main:app"
sleep 2

echo "✅ Bước 4: Enable service (tự động khởi động khi boot)..."
sudo systemctl enable screenshot-analyzer

echo "🚀 Bước 5: Start service..."
sudo systemctl start screenshot-analyzer

echo ""
echo "⏳ Đợi 3 giây..."
sleep 3

echo ""
echo "=================================================="
echo "  KIỂM TRA TRẠNG THÁI"
echo "=================================================="

# Kiểm tra status
if sudo systemctl is-active --quiet screenshot-analyzer; then
    echo "✅ Service đang chạy!"
else
    echo "❌ Service KHÔNG chạy!"
    echo ""
    echo "Xem lỗi:"
    sudo systemctl status screenshot-analyzer
    exit 1
fi

# Kiểm tra port
if netstat -tlnp 2>/dev/null | grep -q ":8000" || ss -tlnp 2>/dev/null | grep -q ":8000"; then
    echo "✅ Port 8000 đang listen!"
else
    echo "❌ Port 8000 KHÔNG listen!"
fi

echo ""
echo "=================================================="
echo "  CÁC LỆNH HỮU ÍCH"
echo "=================================================="
echo ""
echo "Xem status:"
echo "  sudo systemctl status screenshot-analyzer"
echo ""
echo "Xem logs realtime:"
echo "  sudo journalctl -u screenshot-analyzer -f"
echo "  hoặc"
echo "  tail -f /home/myadmin/screenshot-analyzer/server.log"
echo ""
echo "Restart service:"
echo "  sudo systemctl restart screenshot-analyzer"
echo ""
echo "Stop service:"
echo "  sudo systemctl stop screenshot-analyzer"
echo ""
echo "Disable auto-start:"
echo "  sudo systemctl disable screenshot-analyzer"
echo ""
echo "=================================================="
echo "✅ HOÀN TẤT! Server sẽ tự động khởi động khi reboot"
echo "🌐 Truy cập: https://lukistar.space/admin"
echo "=================================================="

