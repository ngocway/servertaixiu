# Hướng dẫn Deploy lên VPS

## Thông tin Server

- **Domain**: `lukistar.space`
- **VPS IP**: `97.74.83.97`
- **VPS Hostname**: `97.83.74.97.host.secureserver.net`
- **OS**: Ubuntu 22.04
- **Location**: Asia (Singapore)
- **Username**: `myadmin`

## DNS Configuration

Domain đã được cấu hình:
- ✅ A record `@` → `97.74.83.97`
- ✅ CNAME `www` → `lukistar.space`

## Các bước deploy

### 1. Kết nối VPS

```bash
ssh myadmin@97.74.83.97
```

### 2. Setup lần đầu (chạy trên VPS)

```bash
# Clone hoặc upload code lên VPS
cd ~
mkdir -p screenshot-analyzer
cd screenshot-analyzer

# Chạy script setup
chmod +x setup_vps.sh
./setup_vps.sh
```

Script sẽ tự động:
- Cài đặt Python 3.10+
- Tạo virtual environment
- Cài đặt dependencies
- Tạo systemd service
- Cấu hình firewall

### 3. Upload code lên VPS

Từ máy local:

```bash
# Nếu code đã có trên VPS, bỏ qua bước này
# Nếu cần upload, sử dụng scp:
scp -r . myadmin@97.74.83.97:~/screenshot-analyzer/
```

### 4. Khởi động server

```bash
sudo systemctl start screenshot-analyzer
sudo systemctl enable screenshot-analyzer
sudo systemctl status screenshot-analyzer
```

### 5. Kiểm tra

```bash
# Kiểm tra server đang chạy
curl http://localhost:8000/health

# Hoặc từ bên ngoài
curl http://97.74.83.97:8000/health
```

### 6. Cấu hình Nginx (tùy chọn)

Nếu muốn truy cập qua domain mà không cần port:

```bash
# Cài đặt Nginx
sudo apt install -y nginx

# Copy config
sudo cp nginx_config.conf /etc/nginx/sites-available/screenshot-analyzer

# Tạo symlink
sudo ln -s /etc/nginx/sites-available/screenshot-analyzer /etc/nginx/sites-enabled/

# Kiểm tra config
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

Sau đó có thể truy cập:
- `http://lukistar.space`
- `http://www.lukistar.space`

## URLs sau khi deploy

- **API trực tiếp**: `http://97.74.83.97:8000`
- **Admin Dashboard**: `http://97.74.83.97:8000/admin`
- **Health Check**: `http://97.74.83.97:8000/health`
- **API Analyze**: `http://97.74.83.97:8000/analyze/green-dots`

Nếu dùng Nginx:
- **API**: `http://lukistar.space`
- **Admin**: `http://lukistar.space/admin`

## Test API

Gửi screenshot để test:

```bash
curl -X POST "http://97.74.83.97:8000/analyze/green-dots?save_log=true" \
  -F "image=@screenshot.png"
```

## Quản lý Service

```bash
# Xem status
sudo systemctl status screenshot-analyzer

# Xem logs realtime
sudo journalctl -u screenshot-analyzer -f

# Restart service
sudo systemctl restart screenshot-analyzer

# Stop service
sudo systemctl stop screenshot-analyzer

# Start service
sudo systemctl start screenshot-analyzer
```

## Troubleshooting

### Server không khởi động

```bash
# Kiểm tra logs
sudo journalctl -u screenshot-analyzer -n 50

# Kiểm tra port có bị chiếm không
sudo netstat -tulpn | grep 8000

# Kiểm tra Python environment
cd ~/screenshot-analyzer
source venv/bin/activate
python --version
pip list
```

### Firewall chặn port

```bash
# Mở port 8000
sudo ufw allow 8000/tcp
sudo ufw status
```

### Nginx không hoạt động

```bash
# Kiểm tra config
sudo nginx -t

# Xem logs
sudo tail -f /var/log/nginx/error.log

# Restart Nginx
sudo systemctl restart nginx
```

### Permission issues

```bash
# Đảm bảo user myadmin có quyền
sudo chown -R myadmin:myadmin ~/screenshot-analyzer
sudo chmod -R 755 ~/screenshot-analyzer
```

## Backup

```bash
# Backup database
cp ~/screenshot-analyzer/logs.db ~/backup-logs-$(date +%Y%m%d).db

# Backup screenshots
tar -czf ~/backup-screenshots-$(date +%Y%m%d).tar.gz ~/screenshot-analyzer/screenshots/
```

## Update code

```bash
# Stop service
sudo systemctl stop screenshot-analyzer

# Backup
cp -r ~/screenshot-analyzer ~/screenshot-analyzer-backup-$(date +%Y%m%d)

# Update code (upload file mới hoặc git pull)
cd ~/screenshot-analyzer
# ... update code ...

# Cài đặt dependencies mới (nếu có)
source venv/bin/activate
pip install -r requirements.txt

# Start lại service
sudo systemctl start screenshot-analyzer
```

