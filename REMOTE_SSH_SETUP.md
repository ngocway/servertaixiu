# Hướng dẫn kết nối VPS qua Remote-SSH trong Cursor

## ✅ Đã cấu hình SSH Config

File SSH config đã được tạo tại: `C:\Users\ADMIN\.ssh\config`

Cấu hình:
```
Host lukistar-vps
    HostName 97.74.83.97
    User myadmin
    IdentityFile C:\Users\ADMIN\.ssh\id_rsa
    Port 22
```

## Cách sử dụng Remote-SSH trong Cursor

### Bước 1: Cài đặt Extension
1. Mở Cursor
2. Nhấn `Ctrl+Shift+X` để mở Extensions
3. Tìm kiếm "Remote - SSH" 
4. Cài đặt extension **Remote - SSH** (by Microsoft)

### Bước 2: Kết nối đến VPS
1. Nhấn `F1` hoặc `Ctrl+Shift+P` để mở Command Palette
2. Gõ: `Remote-SSH: Connect to Host...`
3. Chọn: `lukistar-vps` (alias đã cấu hình)
4. Cursor sẽ mở cửa sổ mới và kết nối đến VPS

### Bước 3: Mở thư mục dự án
Sau khi kết nối thành công:
1. Nhấn `F1` hoặc `Ctrl+Shift+P`
2. Gõ: `Open Folder...`
3. Nhập đường dẫn: `/home/myadmin/screenshot-analyzer`
4. Hoặc dùng: `~/screenshot-analyzer`

### Bước 4: Chọn platform
- Cursor có thể hỏi bạn chọn platform (Linux/Windows)
- Chọn: **Linux** (vì VPS chạy Ubuntu)

### Bước 5: Cài đặt Server trên VPS (lần đầu tiên)
- Cursor sẽ tự động cài đặt Remote-SSH server trên VPS lần đầu tiên kết nối
- Quá trình này mất vài phút, đợi cho đến khi hoàn thành

## Sử dụng Terminal trong Cursor

Sau khi kết nối:
- Mở Terminal: `Ctrl+` ` (backtick) hoặc `Terminal > New Terminal`
- Terminal sẽ tự động chạy trên VPS
- Bạn có thể chạy các lệnh Linux trực tiếp

## Lợi ích khi dùng Remote-SSH

1. ✅ **Chỉnh sửa code trực tiếp trên VPS** - Không cần pull/push
2. ✅ **Terminal tích hợp** - Chạy lệnh Linux ngay trong Cursor
3. ✅ **Debug trên server** - Debug Python code chạy trên VPS
4. ✅ **Quản lý files** - Xem và chỉnh sửa files trên VPS như local
5. ✅ **IntelliSense** - Code completion và syntax highlighting

## Troubleshooting

### Nếu không kết nối được:
1. Kiểm tra SSH key: `Test-Path C:\Users\ADMIN\.ssh\id_rsa`
2. Kiểm tra kết nối: `ssh lukistar-vps` (trong PowerShell)
3. Xem logs: `View > Output > Remote-SSH`

### Nếu yêu cầu password:
- SSH key có thể chưa được thêm vào VPS
- Chạy lại: `.\setup_ssh_key.bat`

### Nếu extension không hoạt động:
- Đảm bảo đã cài **Remote - SSH** (chính thức từ Microsoft)
- Restart Cursor

## Lưu ý

- ⚠️ **Lưu ý an toàn**: Khi chỉnh sửa code trên VPS qua Remote-SSH, code thay đổi NGAY trên server
- 💡 **Tip**: Nên commit code vào Git trước khi chỉnh sửa trên server, để có thể rollback nếu cần
- 🔄 **Git workflow**: Vẫn có thể dùng Git để đồng bộ code giữa local và VPS

## So sánh: Remote-SSH vs Git Push

| Remote-SSH | Git Push |
|------------|----------|
| ✅ Chỉnh sửa trực tiếp trên server | ✅ Code được version control |
| ✅ Phù hợp khi test nhanh | ✅ Phù hợp khi deploy production |
| ⚠️ Cần kết nối internet | ✅ Có thể deploy offline (cần push trước) |
| ⚠️ Thay đổi không tự động sync về local | ✅ Code sync giữa local và server |

## Các lệnh hữu ích khi đã kết nối

```bash
# Restart server
pkill -f 'uvicorn app.main:app'
cd ~/screenshot-analyzer
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 &

# Xem logs
tail -f ~/screenshot-analyzer/server.log

# Kiểm tra server
curl http://localhost:8000/health

# Xem process
ps aux | grep uvicorn
```








































