# 🔍 Cách Kiểm Tra SSH Key Đã Hoạt Động Chưa

## 🚀 Cách 1: Dùng Script (Dễ nhất)

### Kiểm tra đầy đủ:
```bash
.\check_ssh_key.bat
```
Script này sẽ kiểm tra:
- ✅ SSH key có trên máy local chưa
- ✅ SSH key có hoạt động không (có cần password không)
- ✅ Key đã được cài trên VPS chưa

### Kiểm tra nhanh:
```bash
.\test_ssh.bat
```
Script này test nhanh xem SSH key có hoạt động không.

## 🧪 Cách 2: Test Thủ Công

### Test 1: SSH vào VPS
```bash
ssh myadmin@97.74.83.97
```

**Kết quả:**
- ✅ **KHÔNG hỏi password** → SSH key đang hoạt động! 🎉
- ❌ **Vẫn hỏi password** → SSH key chưa hoạt động

### Test 2: Test với lệnh cụ thể
```bash
ssh myadmin@97.74.83.97 "echo 'Test OK'"
```

**Kết quả:**
- ✅ In ra `Test OK` mà **không hỏi password** → OK!
- ❌ Hỏi password → Chưa OK

### Test 3: Kiểm tra file key
```bash
# Kiểm tra key có trên máy local không
type %USERPROFILE%\.ssh\id_rsa.pub

# Nếu thấy output (bắt đầu với ssh-rsa) → Key có
# Nếu lỗi "file not found" → Key chưa tạo
```

## 📋 Checklist

### ✅ SSH Key đã hoạt động nếu:

1. **File key tồn tại:**
   ```bash
   type %USERPROFILE%\.ssh\id_rsa.pub
   ```
   → Có output (ssh-rsa ...) ✅

2. **SSH không hỏi password:**
   ```bash
   ssh myadmin@97.74.83.97
   ```
   → Vào VPS ngay, không hỏi password ✅

3. **Script test pass:**
   ```bash
   .\test_ssh.bat
   ```
   → Hiện "SSH Key is WORKING!" ✅

### ❌ SSH Key chưa hoạt động nếu:

1. **Không có file key:**
   ```bash
   type %USERPROFILE%\.ssh\id_rsa.pub
   ```
   → Lỗi "file not found" ❌

2. **SSH vẫn hỏi password:**
   ```bash
   ssh myadmin@97.74.83.97
   ```
   → Vẫn hỏi password ❌

3. **Script test fail:**
   ```bash
   .\test_ssh.bat
   ```
   → Hiện "SSH key NOT working" ❌

## 🔧 Nếu SSH Key Chưa Hoạt Động

### Bước 1: Setup SSH Key
```bash
.\setup_ssh_key.bat
```

### Bước 2: Kiểm tra lại
```bash
.\test_ssh.bat
```

### Bước 3: Nếu vẫn không hoạt động

**Setup thủ công:**

1. **Xem public key:**
   ```bash
   type %USERPROFILE%\.ssh\id_rsa.pub
   ```
   Copy toàn bộ output

2. **SSH vào VPS** (nhập password lần cuối):
   ```bash
   ssh myadmin@97.74.83.97
   ```

3. **Trên VPS, setup key:**
   ```bash
   mkdir -p ~/.ssh
   chmod 700 ~/.ssh
   nano ~/.ssh/authorized_keys
   ```
   - Paste public key vào
   - Save: Ctrl+O, Enter, Ctrl+X
   - Set quyền:
     ```bash
     chmod 600 ~/.ssh/authorized_keys
     exit
     ```

4. **Test lại:**
   ```bash
   ssh myadmin@97.74.83.97
   ```
   → Không hỏi password = OK! ✅

## ✅ Kết Quả Mong Đợi

**Khi SSH key đã hoạt động:**
- ✅ `ssh myadmin@97.74.83.97` → Vào VPS ngay, không hỏi password
- ✅ `.\test_ssh.bat` → Hiện "SSH Key is WORKING!"
- ✅ `.\deploy_no_password.bat` → Deploy không hỏi password
- ✅ Tất cả script deploy đều không hỏi password

**Khi SSH key chưa hoạt động:**
- ❌ `ssh myadmin@97.74.83.97` → Vẫn hỏi password
- ❌ `.\test_ssh.bat` → Hiện "SSH key NOT working"
- ❌ Script deploy vẫn hỏi password nhiều lần

## 🎯 Quick Test

**Cách nhanh nhất:**
```bash
.\test_ssh.bat
```

Nếu thấy "SSH Key is WORKING!" → Xong! 🎉

Nếu thấy "SSH key NOT working" → Chạy `.\setup_ssh_key.bat`

