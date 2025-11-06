# ✅ KHẮC PHỤC LỖI 502 HOÀN TẤT

## 📊 Tóm Tắt Vấn Đề

**Lỗi:** 502 Bad Gateway khi truy cập `https://lukistar.space/admin`

**Nguyên nhân:** FastAPI server (backend application) bị dừng, không chạy trên port 8000

**Nginx đang proxy đến:** `http://127.0.0.1:8000` nhưng không có gì đang listen

---

## ✅ Đã Khắc Phục

### 1. Khởi Động Lại Server ✓
Server đã được khởi động lại thành công bằng lệnh:
```bash
./restart-server.sh
```

**Hiện tại website đã hoạt động bình thường!**
- 🌐 Admin: https://lukistar.space/admin
- 🌐 API: https://lukistar.space/api

---

## ⚠️ QUAN TRỌNG: Cài Đặt Auto-Start

**HIỆN TẠI:** Server đang chạy thủ công → Sẽ bị dừng khi:
- Restart VPS
- Server bị crash
- Ai đó tắt terminal

**GIẢI PHÁP:** Cài đặt systemd service để tự động khởi động

### Chạy Lệnh Sau:
```bash
cd /home/myadmin/screenshot-analyzer
./setup-autostart.sh
```

**Lệnh này sẽ:**
- ✅ Tạo systemd service
- ✅ Tự động khởi động khi VPS reboot
- ✅ Tự động restart nếu server crash
- ✅ Logs được quản lý tốt hơn

---

## 🛠️ Các Script Đã Tạo

### 1. `check-502.sh`
Kiểm tra và chẩn đoán lỗi 502
```bash
./check-502.sh
```

### 2. `restart-server.sh`
Khởi động lại server nhanh
```bash
./restart-server.sh
```

### 3. `setup-autostart.sh`
Cài đặt tự động khởi động (QUAN TRỌNG!)
```bash
./setup-autostart.sh
```

---

## 📚 Tài Liệu Hữu Ích

### `502_error_troubleshooting.md`
Hướng dẫn chi tiết về:
- Tất cả nguyên nhân có thể gây lỗi 502
- Cách debug từng bước
- Tối ưu hiệu suất
- Monitoring và alerts

---

## 🔍 Kiểm Tra Trạng Thái

### Kiểm tra server có đang chạy không:
```bash
# Kiểm tra port 8000
sudo netstat -tlnp | grep :8000

# Kiểm tra process
ps aux | grep uvicorn

# Xem logs real-time
tail -f /home/myadmin/screenshot-analyzer/server.log
```

### Nếu cài đặt systemd service rồi:
```bash
# Xem status
sudo systemctl status screenshot-analyzer

# Restart
sudo systemctl restart screenshot-analyzer

# Xem logs
sudo journalctl -u screenshot-analyzer -f
```

---

## 🚨 Nếu Lại Gặp Lỗi 502

### Bước 1: Chạy script kiểm tra
```bash
cd /home/myadmin/screenshot-analyzer
./check-502.sh
```

### Bước 2: Khởi động lại server
```bash
./restart-server.sh
```

### Bước 3: Xem logs để tìm nguyên nhân
```bash
tail -50 server.log
```

### Bước 4: Nếu vẫn không được
```bash
# Kiểm tra nginx
sudo systemctl status nginx
sudo nginx -t

# Kiểm tra RAM/CPU
free -h
top

# Xem nginx error log
sudo tail -50 /var/log/nginx/error.log
```

---

## 💡 Nguyên Nhân Thường Gặp Khiến Server Bị Dừng

1. **Restart VPS** → Server không tự động khởi động
   - **Giải pháp:** Chạy `./setup-autostart.sh`

2. **Hết RAM** → Process bị kill
   - **Kiểm tra:** `free -h`
   - **Giải pháp:** Thêm SWAP hoặc upgrade RAM

3. **Code lỗi** → Application crash
   - **Kiểm tra:** `tail -50 server.log`
   - **Giải pháp:** Fix code và restart

4. **Ai đó chạy Ctrl+C** trong terminal
   - **Giải pháp:** Dùng systemd service thay vì chạy manual

5. **Dependency lỗi** → Import modules fail
   - **Kiểm tra:** Logs sẽ hiện import error
   - **Giải pháp:** `source venv/bin/activate && pip install -r requirements.txt`

---

## 📞 Quick Commands Cheat Sheet

```bash
# Khởi động lại nhanh
cd /home/myadmin/screenshot-analyzer && ./restart-server.sh

# Kiểm tra trạng thái
./check-502.sh

# Xem logs
tail -f server.log

# Xem 100 dòng log cuối
tail -100 server.log

# Kiểm tra port
sudo netstat -tlnp | grep :8000

# Kill server
pkill -f "uvicorn app.main:app"

# Start server manual
cd /home/myadmin/screenshot-analyzer
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Start server background
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 >> server.log 2>&1 &
```

---

## 🎯 Khuyến Nghị

### ✅ NÊN LÀM NGAY:
1. **Chạy `./setup-autostart.sh`** - Tránh lỗi 502 trong tương lai
2. **Theo dõi logs thường xuyên** - Phát hiện vấn đề sớm
3. **Backup code thường xuyên** - Git commit + push

### ✅ NÊN LÀM TRONG TƯƠNG LAI:
1. **Setup monitoring** - Email/SMS alert khi server down
2. **Tối ưu code** - Giảm thời gian xử lý request
3. **Tăng RAM** nếu hay gặp vấn đề out of memory
4. **Setup log rotation** - Tránh logs làm đầy disk

---

## 🎉 Kết Luận

✅ **Lỗi 502 đã được khắc phục**
✅ **Server đang chạy bình thường**
✅ **Có đầy đủ tools để debug trong tương lai**

⚠️ **QUAN TRỌNG:** Chạy `./setup-autostart.sh` để tránh lỗi lặp lại!

---

**Nếu cần hỗ trợ thêm, hãy:**
1. Chạy `./check-502.sh` và gửi output
2. Gửi 50 dòng cuối của `server.log`
3. Gửi nginx error log: `sudo tail -50 /var/log/nginx/error.log`

Chúc bạn vận hành website suôn sẻ! 🚀

