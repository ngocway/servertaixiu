#!/bin/bash
# Script setup Git trên VPS để auto-deploy
# Chạy trên VPS

set -e

echo "🔧 Setup Git auto-deploy trên VPS..."

PROJECT_DIR="$HOME/screenshot-analyzer"
GIT_DIR="$HOME/screenshot-analyzer.git"

# Tạo bare repository
echo "📦 Tạo bare Git repository..."
mkdir -p $GIT_DIR
cd $GIT_DIR
git init --bare

# Tạo post-receive hook để auto-deploy
echo "⚙️ Tạo post-receive hook..."
cat > hooks/post-receive << 'HOOK_EOF'
#!/bin/bash
WORK_TREE=$HOME/screenshot-analyzer
GIT_DIR=$HOME/screenshot-analyzer.git

echo "🔄 Nhận code mới, bắt đầu deploy..."

# Checkout code vào working directory
git --git-dir="$GIT_DIR" --work-tree="$WORK_TREE" checkout -f

cd "$WORK_TREE"

echo "📦 Cài đặt dependencies mới (nếu có)..."
source venv/bin/activate
pip install -r requirements.txt --quiet

echo "🔄 Restart service..."
sudo systemctl restart screenshot-analyzer

echo "✅ Deploy hoàn tất!"
echo "📊 Kiểm tra status:"
sudo systemctl status screenshot-analyzer --no-pager -l
HOOK_EOF

chmod +x hooks/post-receive

echo "✅ Setup Git hoàn tất!"
echo ""
echo "📝 Hướng dẫn sử dụng:"
echo ""
echo "1. Trên máy local, thêm remote VPS:"
echo "   git remote add vps myadmin@97.74.83.97:~/screenshot-analyzer.git"
echo ""
echo "2. Push code lên VPS:"
echo "   git push vps main"
echo ""
echo "3. Code sẽ tự động deploy trên VPS!"

