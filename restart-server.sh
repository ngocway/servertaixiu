#!/bin/bash
# Script khởi động lại server Screenshot Analyzer

echo "🔄 Khởi động lại Screenshot Analyzer Server..."

cd /home/myadmin/screenshot-analyzer

# Kill process cũ nếu có
pkill -f "uvicorn app.main:app" 2>/dev/null

# Activate virtual environment
source venv/bin/activate

# Khởi động server trong background với nohup
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 >> server.log 2>&1 &

echo "⏳ Đợi 3 giây để server khởi động..."
sleep 3

# Kiểm tra xem server đã chạy chưa
if netstat -tlnp 2>/dev/null | grep -q ":8000" || ss -tlnp 2>/dev/null | grep -q ":8000"; then
    echo "✅ Server đã khởi động thành công!"
    echo "🌐 Truy cập tại: https://lukistar.space/admin"
    echo ""
    echo "📊 Kiểm tra logs:"
    echo "   tail -f /home/myadmin/screenshot-analyzer/server.log"
else
    echo "❌ Server không khởi động được!"
    echo "📋 Xem logs:"
    tail -20 server.log
fi

