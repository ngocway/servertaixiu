# 🚀 Hướng dẫn Auto Setup

Tôi đã tạo các script tự động để bạn có thể setup Git deploy mà **KHÔNG CẦN** cung cấp password qua chat.

## ⚠️ Quan trọng về Bảo mật

**KHÔNG nên** chia sẻ password VPS qua chat hoặc lưu vào file code!

**Thay vào đó**, dùng một trong các cách sau:

### Cách 1: SSH Key (Khuyến nghị - An toàn nhất)

1. **Tạo SSH key trên máy local** (nếu chưa có):
```bash
# Trong Git Bash hoặc PowerShell
ssh-keygen -t rsa -b 4096
# Nhấn Enter để dùng default, Enter để không đặt passphrase (hoặc đặt tùy ý)
```

2. **Copy public key lên VPS**:
```bash
# Xem public key
cat ~/.ssh/id_rsa.pub
# Hoặc trên Windows:
type %USERPROFILE%\.ssh\id_rsa.pub

# Copy nội dung, sau đó SSH vào VPS:
ssh myadmin@97.74.83.97

# Trên VPS, thêm public key:
mkdir -p ~/.ssh
nano ~/.ssh/authorized_keys
# Paste public key vào, save (Ctrl+O, Enter, Ctrl+X)
chmod 600 ~/.ssh/authorized_keys
chmod 700 ~/.ssh
```

3. **Sau khi setup SSH key, các script sẽ tự động login không cần password!**

### Cách 2: Dùng script interactive (Nhập password khi chạy)

**Chạy script**:
```bash
# Double-click: setup_with_password.bat
```

Script sẽ yêu cầu nhập password **khi chạy**, không lưu vào file.

### Cách 3: Nhập password trực tiếp khi SSH

Khi script chạy `ssh myadmin@97.74.83.97`, bạn sẽ thấy prompt nhập password.

## 📋 Các Script có sẵn

### 1. `setup_with_password.bat` ⭐ (Khuyến nghị)

**Script an toàn** - yêu cầu nhập password khi chạy, không lưu password vào file.

**Cách dùng**:
```bash
# Double-click file hoặc chạy:
.\setup_with_password.bat
```

Script sẽ:
- ✅ Setup Git trên local
- ✅ Kết nối VPS (yêu cầu nhập password)
- ✅ Setup Git trên VPS
- ✅ Push code lần đầu

### 2. `auto_setup_complete.bat`

**Script tự động hoàn chỉnh** - setup tất cả mọi thứ.

**Cách dùng**:
```bash
.\auto_setup_complete.bat
```

### 3. `setup_git_local.bat`

**Chỉ setup Git trên local**, không setup VPS.

**Cách dùng**:
```bash
.\setup_git_local.bat
```

## 🎯 Các bước thực hiện

### Option A: Dùng SSH Key (Tốt nhất)

1. **Setup SSH key** (xem hướng dẫn ở trên)

2. **Chạy script setup**:
```bash
.\setup_with_password.bat
```
(Vì đã có SSH key, sẽ không cần nhập password)

3. **Done!** ✅

### Option B: Dùng Password (Vẫn an toàn)

1. **Chạy script**:
```bash
.\setup_with_password.bat
```

2. **Khi được hỏi, nhập password VPS**

3. **Done!** ✅

### Option C: Manual từng bước

Nếu muốn tự làm từng bước, xem `GIT_DEPLOY.md`

## ✅ Sau khi setup

**Mỗi lần update code**:
```bash
git add .
git commit -m "Mô tả thay đổi"
git push vps main
```

**VPS tự động update và restart service!** 🎉

## 🔍 Kiểm tra

```bash
# Health check
curl http://97.74.83.97:8000/health

# Admin dashboard
# Mở: http://97.74.83.97:8000/admin
```

## ❓ Troubleshooting

### SSH không kết nối được

**Giải pháp**: Setup SSH key (xem Cách 1 ở trên)

### Script bị lỗi "Permission denied"

**Giải pháp**: 
- Kiểm tra SSH key đã setup chưa
- Hoặc nhập password đúng khi script chạy

### Git push không tự động deploy

**Kiểm tra trên VPS**:
```bash
ssh myadmin@97.74.83.97
cat ~/screenshot-analyzer.git/hooks/post-receive
ls -la ~/screenshot-analyzer.git/hooks/post-receive
# Phải có quyền execute (x)
```

## 💡 Tips

1. **Setup SSH key một lần** → Tất cả script sau đó không cần password
2. **Test connection trước**: `ssh myadmin@97.74.83.97` để test
3. **Kiểm tra logs**: `sudo journalctl -u screenshot-analyzer -f` trên VPS

