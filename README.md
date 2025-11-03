# Screenshot Analyzer Server

Server FastAPI nhận screenshot từ tool khác, phân tích nốt xanh lá trên ảnh và phân loại ĐEN/TRẮNG theo độ sáng, với hệ thống quản lý log và giao diện admin.

## Tính năng

- ✅ Nhận screenshot từ tool khác qua API
- ✅ Tự động phân tích nốt xanh và phân loại ĐEN/TRẮNG
- ✅ Lưu trữ screenshots và kết quả phân tích vào database
- ✅ API trả về JSON kết quả theo ID
- ✅ Giao diện web admin để xem log, thống kê và tải kết quả
- ✅ **Git auto-deploy**: Push code từ local, VPS tự động update!

## Cài đặt

1) Cài Python 3.10+
2) Cài dependencies:

```bash
pip install -r requirements.txt
```

## Chạy server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Hoặc để deploy trên VPS:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

Mở health check:

```bash
curl http://localhost:8000/health
```

## API Endpoints

### 1. Phân tích screenshot (tự động lưu log)

**POST** `/analyze/green-dots`

- **Content-Type**: `multipart/form-data`
- **Field**: `image` (file ảnh)
- **Query Parameter**: `save_log` (default: `true`) - có lưu log hay không

**Response**:
```json
{
  "total": 5,
  "white": 2,
  "black": 3,
  "log_id": 123,
  "positions": [
    { "number": 1, "x": 880, "y": 502, "classification": "TRẮNG" },
    { "number": 2, "x": 850, "y": 505, "classification": "ĐEN" }
  ]
}
```

**Ví dụ sử dụng**:
```bash
curl -X POST "http://your-domain.com/analyze/green-dots?save_log=true" \
  -F "image=@screenshot.png"
```

### 2. Lấy danh sách logs

**GET** `/api/logs`

- **Query Parameters**:
  - `limit` (default: 100): Số lượng logs mỗi trang
  - `offset` (default: 0): Offset để phân trang
  - `order_by` (default: "created_at"): Sắp xếp theo field
  - `order_direction` (default: "DESC"): ASC hoặc DESC

**Response**:
```json
{
  "logs": [
    {
      "id": 1,
      "timestamp": "20241201_120000_123",
      "screenshot_filename": "screenshot_20241201_120000_123.png",
      "total_dots": 5,
      "white_count": 2,
      "black_count": 3,
      "created_at": "2024-12-01T12:00:00.123456"
    }
  ],
  "total": 100,
  "limit": 100,
  "offset": 0
}
```

### 3. Lấy chi tiết log

**GET** `/api/logs/{log_id}`

**Response**: Chi tiết đầy đủ của log bao gồm kết quả phân tích

### 4. Tải JSON kết quả

**GET** `/api/logs/{log_id}/result`

Trả về file JSON kết quả phân tích để download.

### 5. Xem screenshot

**GET** `/api/logs/{log_id}/screenshot`

Trả về file ảnh screenshot đã lưu.

### 6. Thống kê

**GET** `/api/stats`

**Response**:
```json
{
  "total_logs": 150,
  "total_dots_analyzed": 750,
  "total_white": 300,
  "total_black": 450
}
```

## Giao diện Admin

Truy cập: `http://your-domain.com/admin`

Giao diện web admin cung cấp:
- 📊 Dashboard thống kê tổng quan
- 📋 Danh sách logs với pagination
- 🔍 Tìm kiếm logs
- 📄 Xem chi tiết log (modal)
- 📥 Tải JSON kết quả
- 🖼️ Xem screenshot

## Cấu trúc thư mục

Sau khi chạy server, các thư mục sau sẽ được tạo tự động:

```
.
├── logs.db              # SQLite database chứa logs
├── screenshots/         # Thư mục lưu screenshots
│   └── screenshot_*.png
└── results/            # Thư mục lưu kết quả (nếu có)
```

## Ghi chú thuật toán

- Phát hiện nốt xanh lá dựa trên khoảng màu gần `#1AFF0D` (GREEN_DETECTION_CONFIG)
- Gom hàng theo y (ngưỡng 20px) và sắp xếp ziczac: hàng 1 phải→trái, hàng 2 trái→phải, ...
- Phân loại ĐEN/TRẮNG dựa vào luminance threshold 128

## Deploy trên VPS

### Thông tin VPS và Domain

- **Domain**: `lukistar.space`
- **VPS IP**: `97.74.83.97`
- **VPS Hostname**: `97.83.74.97.host.secureserver.net`
- **OS**: Ubuntu 22.04
- **Location**: Asia (Singapore)
- **Username**: `myadmin`

### Cách 1: Sử dụng script tự động

**Trên máy local** (nếu đã setup SSH):
```bash
chmod +x deploy.sh
./deploy.sh
```

**Trên VPS** (chạy lần đầu):
```bash
chmod +x setup_vps.sh
./setup_vps.sh
sudo systemctl start screenshot-analyzer
```

### Cách 2: Deploy thủ công

1. **Kết nối VPS**:
```bash
ssh myadmin@97.74.83.97
```

2. **Cài đặt dependencies**:
```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv
```

3. **Tạo project directory**:
```bash
mkdir -p ~/screenshot-analyzer
cd ~/screenshot-analyzer
```

4. **Upload code lên VPS** (từ máy local):
```bash
scp -r . myadmin@97.74.83.97:~/screenshot-analyzer/
```

5. **Setup Python environment**:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

6. **Tạo systemd service**:
```bash
sudo nano /etc/systemd/system/screenshot-analyzer.service
```

Nội dung file:
```ini
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
```

7. **Khởi động service**:
```bash
sudo systemctl daemon-reload
sudo systemctl enable screenshot-analyzer
sudo systemctl start screenshot-analyzer
sudo systemctl status screenshot-analyzer
```

8. **Mở firewall**:
```bash
sudo ufw allow 8000/tcp
sudo ufw reload
```

### Cấu hình Nginx (Optional - Reverse Proxy)

1. **Cài đặt Nginx**:
```bash
sudo apt install -y nginx
```

2. **Copy config**:
```bash
sudo cp nginx_config.conf /etc/nginx/sites-available/screenshot-analyzer
sudo ln -s /etc/nginx/sites-available/screenshot-analyzer /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

3. **Kiểm tra DNS đã trỏ đúng**:
   - A record `@` → `97.74.83.97` ✅ (đã cấu hình)
   - CNAME `www` → `lukistar.space` ✅ (đã cấu hình)

### Kiểm tra server

- **API trực tiếp**: `http://97.74.83.97:8000`
- **Admin dashboard**: `http://97.74.83.97:8000/admin`
- **Health check**: `http://97.74.83.97:8000/health`
- **Qua domain** (nếu dùng Nginx): `http://lukistar.space` hoặc `https://lukistar.space`

### Quản lý service

```bash
# Xem status
sudo systemctl status screenshot-analyzer

# Xem logs
sudo journalctl -u screenshot-analyzer -f

# Restart
sudo systemctl restart screenshot-analyzer

# Stop
sudo systemctl stop screenshot-analyzer

# Start
sudo systemctl start screenshot-analyzer
```
