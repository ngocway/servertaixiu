# 🪟 Hướng dẫn Setup trên Windows

## ⚡ Cách nhanh nhất: Git Auto-Deploy

### Bước 1: Cài Git (nếu chưa có)

Tải Git cho Windows: https://git-scm.com/download/win

Cài đặt và mở **Git Bash** hoặc **PowerShell**.

### Bước 2: Setup Git trên máy local

**Mở Git Bash hoặc PowerShell** trong thư mục `d:\Testthu`:

```bash
cd d:\Testthu

# Chạy script setup (hoặc chạy thủ công các lệnh bên dưới)
# Double-click: setup_git_local.bat
```

**Hoặc chạy thủ công**:
```bash
# Khởi tạo Git repo
git init

# Thêm tất cả files
git add .

# Commit lần đầu
git commit -m "Initial commit"

# Thêm remote VPS
git remote add vps myadmin@97.74.83.97:~/screenshot-analyzer.git

# Xem remote
git remote -v
```

### Bước 3: Setup Git trên VPS (1 lần)

**Mở Git Bash hoặc PowerShell**, SSH vào VPS:

```bash
ssh myadmin@97.74.83.97
```

**Trên VPS**, chạy script setup Git:

```bash
# Tạo bare repository
mkdir -p ~/screenshot-analyzer.git
cd ~/screenshot-analyzer.git
git init --bare

# Tạo post-receive hook để auto-deploy
cat > hooks/post-receive << 'EOF'
#!/bin/bash
WORK_TREE=$HOME/screenshot-analyzer
GIT_DIR=$HOME/screenshot-analyzer.git

echo "🔄 Nhận code mới, bắt đầu deploy..."

# Tạo working directory nếu chưa có
mkdir -p $WORK_TREE

# Checkout code
git --git-dir="$GIT_DIR" --work-tree="$WORK_TREE" checkout -f

cd "$WORK_TREE"

# Setup Python environment (lần đầu)
if [ ! -d "venv" ]; then
    echo "📦 Tạo virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    
    # Tạo systemd service (nếu chưa có)
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
    echo "📦 Cài đặt dependencies mới (nếu có)..."
    source venv/bin/activate
    pip install -r requirements.txt --quiet
fi

# Restart service
echo "🔄 Restart service..."
sudo systemctl restart screenshot-analyzer

echo "✅ Deploy hoàn tất!"
EOF

chmod +x hooks/post-receive

echo "✅ Git setup hoàn tất!"
```

### Bước 4: Push code lên VPS (lần đầu)

**Trên máy local**, trong Git Bash hoặc PowerShell:

```bash
cd d:\Testthu

# Push code lên VPS
git push vps main
```

Nếu branch tên khác:
```bash
git push vps master
# hoặc
git push vps HEAD:main
```

**Lần đầu push sẽ tự động**:
- ✅ Setup Python environment
- ✅ Cài đặt dependencies
- ✅ Tạo systemd service
- ✅ Khởi động server

### Bước 5: Test nhanh

**Trên máy local**, mở trình duyệt hoặc dùng curl:

```bash
# Health check
curl http://97.74.83.97:8000/health

# Hoặc mở trình duyệt:
# http://97.74.83.97:8000/admin
```

## 🔄 Workflow hàng ngày

### Mỗi lần thay đổi code:

**Cách 1: Dùng script nhanh** (Windows)
```bash
# Double-click: push_to_vps.bat
# Hoặc chạy trong PowerShell/Git Bash:
.\push_to_vps.bat "Mô tả thay đổi"
```

**Cách 2: Chạy thủ công**
```bash
cd d:\Testthu

# Thêm thay đổi
git add .

# Commit
git commit -m "Mô tả thay đổi"

# Push lên VPS (tự động deploy)
git push vps main
```

**Sau khi push**, VPS sẽ tự động:
- ✅ Update code
- ✅ Cài dependencies mới (nếu có)
- ✅ Restart service
- ✅ Server chạy code mới ngay lập tức!

## 📋 Checklist

### Setup lần đầu (1 lần):
- [ ] Cài Git trên Windows
- [ ] Khởi tạo Git repo trên local (`git init`)
- [ ] Commit code lần đầu (`git commit`)
- [ ] Thêm remote VPS (`git remote add vps ...`)
- [ ] SSH vào VPS và setup Git (`setup_git.sh` hoặc chạy thủ công)
- [ ] Push code lên VPS (`git push vps main`)

### Làm việc hàng ngày:
- [ ] Sửa code trên local
- [ ] `git add .`
- [ ] `git commit -m "..."`  
- [ ] `git push vps main`
- [ ] ✅ Done! Server tự động update

## 🔧 Troubleshooting

### SSH không kết nối được

**Cách 1: Dùng password**
```bash
ssh myadmin@97.74.83.97
# Nhập password khi được hỏi
```

**Cách 2: Setup SSH key** (khuyến nghị)

**Trên Windows (Git Bash)**:
```bash
# Tạo SSH key (nếu chưa có)
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"
# Nhấn Enter để dùng default path
# Nhấn Enter để không đặt password (hoặc đặt password tùy ý)

# Xem public key
cat ~/.ssh/id_rsa.pub
# Hoặc trên Windows:
type %USERPROFILE%\.ssh\id_rsa.pub
```

**Trên VPS**:
```bash
# SSH vào VPS
ssh myadmin@97.74.83.97

# Tạo thư mục .ssh nếu chưa có
mkdir -p ~/.ssh

# Thêm public key (paste nội dung từ máy local)
nano ~/.ssh/authorized_keys
# Paste public key vào, save (Ctrl+O, Enter, Ctrl+X)

# Set quyền
chmod 600 ~/.ssh/authorized_keys
chmod 700 ~/.ssh
```

### Git push bị lỗi

**Lỗi "Permission denied"**:
- Setup SSH key (xem ở trên)

**Lỗi "repository not found"**:
- Kiểm tra remote: `git remote -v`
- Đảm bảo đã setup Git trên VPS

**Lỗi "branch main không tồn tại"**:
```bash
# Push branch hiện tại
git push vps HEAD:main

# Hoặc đổi tên branch
git branch -M main
git push vps main
```

### VPS không tự động deploy

**Kiểm tra post-receive hook**:
```bash
# SSH vào VPS
ssh myadmin@97.74.83.97

# Kiểm tra hook
cat ~/screenshot-analyzer.git/hooks/post-receive

# Kiểm tra quyền (phải có x)
ls -la ~/screenshot-analyzer.git/hooks/post-receive

# Nếu không có quyền, chạy:
chmod +x ~/screenshot-analyzer.git/hooks/post-receive
```

**Test hook thủ công**:
```bash
# Trên VPS
cd ~/screenshot-analyzer.git
./hooks/post-receive
```

### Service không restart

**Kiểm tra logs**:
```bash
# SSH vào VPS
ssh myadmin@97.74.83.97

# Xem logs service
sudo journalctl -u screenshot-analyzer -f

# Kiểm tra status
sudo systemctl status screenshot-analyzer

# Restart thủ công nếu cần
sudo systemctl restart screenshot-analyzer
```

## ✅ Tips

1. **Dùng script nhanh**: Double-click `push_to_vps.bat` thay vì gõ lệnh
2. **Commit message rõ ràng**: Viết mô tả ngắn gọn về thay đổi
3. **Kiểm tra trước khi push**: `git status` để xem thay đổi
4. **Backup**: Git tự động backup qua version control

## 📖 Xem thêm

- Chi tiết Git deploy: `GIT_DEPLOY.md`
- Hướng dẫn deploy thủ công: `DEPLOY.md`
- API documentation: `README.md`

