# 🚀 Quick Start - Deploy lên VPS

## Thông tin Server

- **Domain**: `lukistar.space`
- **VPS IP**: `97.74.83.97`
- **Username**: `myadmin`

## 🎯 Cách nhanh nhất: Dùng Git (Khuyến nghị)

### Setup Git auto-deploy (1 lần)

**Trên VPS**:
```bash
ssh myadmin@97.74.83.97

# Chạy script setup Git
# (Xem GIT_DEPLOY.md để copy script hoặc chạy setup_git.sh)
```

**Trên máy local (Windows)**:
```bash
cd d:\Testthu

# Khởi tạo Git (nếu chưa có)
git init
git add .
git commit -m "Initial commit"

# Thêm remote VPS
git remote add vps myadmin@97.74.83.97:~/screenshot-analyzer.git

# Push code (sẽ tự động setup và deploy)
git push vps main
```

### Update code (mỗi lần thay đổi)

```bash
# Chỉ cần 3 lệnh này!
git add .
git commit -m "Mô tả thay đổi"
git push vps main

# VPS tự động update và restart service ✅
```

## 📦 Cách 2: Upload thủ công (không dùng Git)

### 1. Upload code lên VPS

```bash
# Từ máy local, upload toàn bộ code lên VPS
scp -r . myadmin@97.74.83.97:~/screenshot-analyzer/
```

### 2. SSH vào VPS và chạy setup

```bash
# Kết nối VPS
ssh myadmin@97.74.83.97

# Chạy script setup tự động
cd ~/screenshot-analyzer
chmod +x setup_vps.sh
./setup_vps.sh
```

### 3. Khởi động server

```bash
# Khởi động service
sudo systemctl start screenshot-analyzer

# Kiểm tra status
sudo systemctl status screenshot-analyzer
```

## ✅ Xong! Kiểm tra

Mở trình duyệt hoặc dùng curl:

```bash
# Health check
curl http://97.74.83.97:8000/health

# Admin dashboard
# Mở: http://97.74.83.97:8000/admin
```

## 📝 Quản lý Service

```bash
# Xem logs
sudo journalctl -u screenshot-analyzer -f

# Restart
sudo systemctl restart screenshot-analyzer

# Stop
sudo systemctl stop screenshot-analyzer
```

## 🌐 Test API

```bash
# Gửi screenshot để test
curl -X POST "http://97.74.83.97:8000/analyze/green-dots?save_log=true" \
  -F "image=@screenshot.png"
```

## 📖 Xem thêm

- Chi tiết đầy đủ: `DEPLOY.md`
- Hướng dẫn API: `README.md`

