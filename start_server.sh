#!/bin/bash
# Script khởi động server trên VPS
# Chạy trên VPS

echo "🚀 Starting Screenshot Analyzer Server..."

PROJECT_DIR="$HOME/screenshot-analyzer"

# Kiểm tra thư mục project
if [ ! -d "$PROJECT_DIR" ]; then
    echo "❌ Project directory not found: $PROJECT_DIR"
    echo "📝 Run setup first or clone code to this directory"
    exit 1
fi

cd "$PROJECT_DIR"

# Kiểm tra virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Tạo thư mục cần thiết
mkdir -p screenshots results

echo "✅ Server starting..."
echo "🌐 Access at:"
echo "   - API: http://97.74.83.97:8000"
echo "   - Admin: http://97.74.83.97:8000/admin"
echo "   - Health: http://97.74.83.97:8000/health"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Khởi động server
uvicorn app.main:app --host 0.0.0.0 --port 8000

