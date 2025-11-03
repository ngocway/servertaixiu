# 🚀 Deploy bằng Git - Auto Update

Hệ thống Git để tự động deploy code lên VPS. Khi bạn push code từ local, VPS sẽ tự động update và restart service.

## 📋 Chuẩn bị

### Bước 1: Setup Git trên VPS (chạy 1 lần)

**SSH vào VPS**:
```bash
ssh myadmin@97.74.83.97
```

**Chạy script setup**:
```bash
# Upload script setup_git.sh lên VPS (nếu chưa có)
# Hoặc copy nội dung script và chạy

# Tạo thư mục project
mkdir -p ~/screenshot-analyzer
cd ~/screenshot-analyzer

# Tạo bare repository
mkdir -p ~/screenshot-analyzer.git
cd ~/screenshot-analyzer.git
git init --bare

# Tạo post-receive hook
cat > hooks/post-receive << 'EOF'
#!/bin/bash
WORK_TREE=$HOME/screenshot-analyzer
GIT_DIR=$HOME/screenshot-analyzer.git

echo "🔄 Nhận code mới, bắt đầu deploy..."

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
```

### Bước 2: Setup Git trên máy local

**Khởi tạo Git repo** (nếu chưa có):
```bash
cd d:\Testthu

# Khởi tạo Git repo
git init

# Thêm tất cả files
git add .

# Commit lần đầu
git commit -m "Initial commit"
```

**Thêm remote VPS**:
```bash
# Thêm remote VPS
git remote add vps myadmin@97.74.83.97:~/screenshot-analyzer.git

# Xem remote
git remote -v
```

## 🚀 Deploy

### Push code lên VPS (tự động deploy)

```bash
# Thêm và commit thay đổi
git add .
git commit -m "Update code"

# Push lên VPS (sẽ tự động deploy)
git push vps main
```

Hoặc nếu branch khác:
```bash
git push vps master
# hoặc
git push vps HEAD:main
```

### Workflow thường dùng

1. **Sửa code trên local**
2. **Commit và push**:
   ```bash
   git add .
   git commit -m "Mô tả thay đổi"
   git push vps main
   ```
3. **VPS tự động update và restart service** ✅

## 📝 Quy trình làm việc

### Lần đầu setup:

```bash
# 1. Setup Git trên VPS (đã làm ở trên)

# 2. Setup Git trên local
cd d:\Testthu
git init
git add .
git commit -m "Initial commit"

# 3. Thêm remote VPS
git remote add vps myadmin@97.74.83.97:~/screenshot-analyzer.git

# 4. Push code lên VPS (lần đầu sẽ setup mọi thứ)
git push vps main

# 5. SSH vào VPS để setup service (lần đầu)
ssh myadmin@97.74.83.97
cd ~/screenshot-analyzer

# Tạo systemd service (nếu chưa có)
sudo nano /etc/systemd/system/screenshot-analyzer.service
# (Copy nội dung từ DEPLOY.md)
```

### Mỗi lần update code:

```bash
# 1. Sửa code trên local
# 2. Commit và push
git add .
git commit -m "Mô tả thay đổi"
git push vps main

# 3. Xong! VPS tự động update
```

## 🔍 Kiểm tra deploy

**Xem logs trên VPS**:
```bash
# SSH vào VPS
ssh myadmin@97.74.83.97

# Xem logs của lần deploy vừa rồi
tail -f ~/.ssh/authorized_keys  # (hoặc xem qua journalctl)
sudo journalctl -u screenshot-analyzer -f

# Kiểm tra service
sudo systemctl status screenshot-analyzer
```

## ⚙️ Troubleshooting

### Git push bị lỗi "Permission denied"

**Giải pháp**: Setup SSH key

**Trên máy local**:
```bash
# Tạo SSH key (nếu chưa có)
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"

# Copy public key
cat ~/.ssh/id_rsa.pub
# Hoặc trên Windows:
type %USERPROFILE%\.ssh\id_rsa.pub
```

**Trên VPS**:
```bash
# Thêm public key vào authorized_keys
mkdir -p ~/.ssh
echo "PASTE_PUBLIC_KEY_HERE" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
chmod 700 ~/.ssh
```

### Git push không tự động deploy

**Kiểm tra post-receive hook**:
```bash
# SSH vào VPS
ssh myadmin@97.74.83.97

# Kiểm tra hook
cat ~/screenshot-analyzer.git/hooks/post-receive

# Kiểm tra quyền
ls -la ~/screenshot-analyzer.git/hooks/post-receive
# Phải có quyền execute (x)
```

### Service không restart

**Kiểm tra logs**:
```bash
# SSH vào VPS
ssh myadmin@97.74.83.97

# Xem logs của hook
tail -f /tmp/post-receive.log  # (nếu hook có redirect logs)

# Restart thủ công
sudo systemctl restart screenshot-analyzer
sudo systemctl status screenshot-analyzer
```

## 🔄 Branch Management

Nếu muốn dùng nhiều branch:

```bash
# Push branch khác
git push vps feature-branch:main

# Hoặc setup nhiều remote
git remote add vps-prod myadmin@97.74.83.97:~/screenshot-analyzer-prod.git
git remote add vps-dev myadmin@97.74.83.97:~/screenshot-analyzer-dev.git
```

## 📦 Tối ưu

### Chỉ push code, không push database/screenshots

`.gitignore` đã được config để bỏ qua:
- `*.db`, `*.sqlite` (database)
- `screenshots/`, `results/` (files tạm)

### Backup trước khi deploy

Có thể thêm vào post-receive hook:
```bash
# Backup trước khi deploy
cp -r $WORK_TREE $WORK_TREE-backup-$(date +%Y%m%d-%H%M%S)
```

## ✅ Summary

1. **Setup 1 lần**: Git trên VPS với post-receive hook
2. **Làm việc hàng ngày**: 
   - Sửa code local
   - `git add . && git commit -m "..." && git push vps main`
   - VPS tự động update ✅

