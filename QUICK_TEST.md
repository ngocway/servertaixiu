# 🚀 Quick Test - Xem trên trình duyệt

## Bước 1: Kiểm tra server đã chạy chưa

**SSH vào VPS** (đã có terminal mở):
```bash
# Đã có terminal mở rồi, tiếp tục...
```

**Kiểm tra service**:
```bash
sudo systemctl status screenshot-analyzer
```

### Nếu service đang chạy:
✅ Server đã chạy! Mở trình duyệt:
- **Admin Dashboard**: http://97.74.83.97:8000/admin
- **Health Check**: http://97.74.83.97:8000/health

### Nếu service chưa chạy hoặc chưa có:

**Option 1: Khởi động service (nếu đã setup)**
```bash
sudo systemctl start screenshot-analyzer
sudo systemctl enable screenshot-analyzer
sudo systemctl status screenshot-analyzer
```

**Option 2: Chạy server trực tiếp (để test nhanh)**
```bash
# Vào thư mục project (nếu code đã có trên VPS)
cd ~/screenshot-analyzer

# Nếu chưa có code, clone hoặc upload code trước
# Hoặc chạy script setup từ máy local

# Chạy server
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Bước 2: Mở trình duyệt

Sau khi server chạy, mở trình duyệt và truy cập:

### URLs:

1. **Admin Dashboard**:
   ```
   http://97.74.83.97:8000/admin
   ```

2. **Health Check**:
   ```
   http://97.74.83.97:8000/health
   ```
   (Sẽ hiện: `{"status":"ok"}`)

3. **API Documentation**:
   ```
   http://97.74.83.97:8000/docs
   ```
   (Swagger UI của FastAPI)

4. **Test API**:
   ```
   http://97.74.83.97:8000/api/stats
   ```

## Bước 3: Test API từ trình duyệt

**Health Check**:
- Mở: http://97.74.83.97:8000/health
- Kỳ vọng: `{"status":"ok"}`

**Stats API**:
- Mở: http://97.74.83.97:8000/api/stats
- Kỳ vọng: JSON với thống kê

**Admin Dashboard**:
- Mở: http://97.74.83.97:8000/admin
- Kỳ vọng: Giao diện admin với dashboard

## ⚠️ Troubleshooting

### Không truy cập được?

**1. Kiểm tra server có chạy không**:
```bash
# Trên VPS
curl http://localhost:8000/health
# Nếu không có output, server chưa chạy
```

**2. Kiểm tra firewall**:
```bash
# Mở port 8000
sudo ufw allow 8000/tcp
sudo ufw status
```

**3. Kiểm tra port có bị chiếm không**:
```bash
sudo netstat -tulpn | grep 8000
# Hoặc
sudo ss -tulpn | grep 8000
```

**4. Test từ VPS**:
```bash
# SSH vào VPS
curl http://localhost:8000/health

# Nếu hoạt động, vấn đề là firewall hoặc network
```

**5. Test từ máy local**:
```bash
# Từ máy Windows (PowerShell hoặc cmd)
curl http://97.74.83.97:8000/health

# Hoặc mở trình duyệt và truy cập URL
```

### Service không start

**Xem logs**:
```bash
sudo journalctl -u screenshot-analyzer -f
# Hoặc
sudo journalctl -u screenshot-analyzer -n 50
```

**Restart service**:
```bash
sudo systemctl restart screenshot-analyzer
sudo systemctl status screenshot-analyzer
```

### Lỗi "Connection refused"

**Có thể do**:
- Server chưa chạy
- Firewall chặn port 8000
- Server chỉ bind localhost thay vì 0.0.0.0

**Giải pháp**:
```bash
# Đảm bảo server chạy với --host 0.0.0.0
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Hoặc kiểm tra systemd service config
sudo nano /etc/systemd/system/screenshot-analyzer.service
# Đảm bảo có: --host 0.0.0.0
```

## ✅ Checklist nhanh

- [ ] Server đang chạy: `sudo systemctl status screenshot-analyzer`
- [ ] Port 8000 đã mở: `sudo ufw status`
- [ ] Test từ VPS: `curl http://localhost:8000/health`
- [ ] Test từ trình duyệt: http://97.74.83.97:8000/health
- [ ] Mở Admin: http://97.74.83.97:8000/admin

## 🎯 Nhanh nhất

**Nếu code đã có trên VPS và setup xong**:
```bash
# Trên VPS
sudo systemctl start screenshot-analyzer
sudo systemctl status screenshot-analyzer
```

**Sau đó mở trình duyệt**:
```
http://97.74.83.97:8000/admin
```

**Nếu chưa có code trên VPS**:
- Chạy script `setup_with_password.bat` từ máy local
- Hoặc upload code thủ công và setup

