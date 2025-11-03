# 🚀 Setup SSH Key - Không Cần Password Nữa

## ❌ Vấn đề

Script hiện tại cứ hỏi password nhiều lần khi deploy, rất bất tiện!

## ✅ Giải pháp: Setup SSH Key

Chỉ cần setup SSH key **1 LẦN**, sau đó **KHÔNG BAO GIỜ** phải nhập password nữa!

## 📋 Các bước

### Bước 1: Setup SSH Key (Chạy 1 lần)

```bash
.\setup_ssh_key.bat
```

Script sẽ:
1. ✅ Tạo SSH key (nếu chưa có)
2. ✅ Hiển thị public key
3. ⚠️  **Yêu cầu nhập password VPS 1 LẦN** (để cài key lên VPS)
4. ✅ Sau đó KHÔNG CẦN password nữa!

### Bước 2: Deploy code (Không cần password)

```bash
.\deploy_no_password.bat
```

Hoặc dùng các script khác:
```bash
.\deploy_complete.bat
.\quick_deploy.bat
```

**Tất cả sẽ không hỏi password nữa!** 🎉

## 🔍 Kiểm tra SSH Key đã hoạt động chưa

**Test thủ công:**
```bash
ssh myadmin@97.74.83.97
```

Nếu **KHÔNG** hỏi password → SSH key đã hoạt động! ✅

Nếu vẫn hỏi password → SSH key chưa setup đúng

## 🛠️ Troubleshooting

### SSH key vẫn không hoạt động

**Cách 1: Kiểm tra key đã copy đúng chưa**
```bash
# Trên máy local - xem public key
type %USERPROFILE%\.ssh\id_rsa.pub

# Trên VPS - kiểm tra authorized_keys
ssh myadmin@97.74.83.97 "cat ~/.ssh/authorized_keys"
```

**Cách 2: Setup lại thủ công**

1. **Copy public key**:
   ```bash
   type %USERPROFILE%\.ssh\id_rsa.pub
   ```
   Copy toàn bộ output (bắt đầu với `ssh-rsa ...`)

2. **SSH vào VPS** (nhập password lần cuối):
   ```bash
   ssh myadmin@97.74.83.97
   ```

3. **Trên VPS**, tạo thư mục và thêm key:
   ```bash
   mkdir -p ~/.ssh
   chmod 700 ~/.ssh
   nano ~/.ssh/authorized_keys
   ```
   - Paste public key vào
   - Save (Ctrl+O, Enter, Ctrl+X)
   - Set quyền:
     ```bash
     chmod 600 ~/.ssh/authorized_keys
     ```

4. **Test lại**:
   ```bash
   exit
   ssh myadmin@97.74.83.97
   ```
   Nếu không hỏi password → Thành công! ✅

### Không có file `~/.ssh/id_rsa.pub`

**Tạo SSH key mới:**
```bash
ssh-keygen -t rsa -b 4096
```
- Nhấn Enter để dùng default path
- Nhấn Enter để không đặt passphrase (hoặc đặt tùy ý)

## 📝 Summary

1. **Setup SSH key 1 lần**: `.\setup_ssh_key.bat` (cần password 1 lần)
2. **Sau đó**: Tất cả script deploy **KHÔNG CẦN password** nữa!
3. **Deploy**: `.\deploy_no_password.bat` hoặc các script khác

## 🎯 Workflow

**Lần đầu:**
```bash
.\setup_ssh_key.bat          # Setup SSH key (nhập password 1 lần)
.\deploy_no_password.bat     # Deploy (không cần password!)
```

**Các lần sau:**
```bash
.\quick_deploy.bat           # Deploy nhanh (không cần password!)
.\deploy_no_password.bat     # Deploy đầy đủ (không cần password!)
```

**Tất cả không hỏi password nữa!** 🎉

