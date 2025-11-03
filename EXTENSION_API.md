# 📸 Extension Upload API

## API Endpoints cho Chrome Extension

### 1. Upload Screenshot

**POST** `http://lukistar.space/upload`

**Request:**
- Method: `POST`
- Content-Type: `multipart/form-data`
- Field name: `image` (file ảnh)

**Query Parameters:**
- `auto_analyze` (default: `true`) - Tự động phân tích nốt xanh sau khi upload

**Response:**
```json
{
  "status": "success",
  "message": "Screenshot uploaded successfully",
  "filename": "screenshot_20241031_103000_123.png",
  "log_id": 123,
  "analysis": {
    "total": 5,
    "white": 2,
    "black": 3,
    "positions": [
      {
        "number": 1,
        "x": 880,
        "y": 502,
        "classification": "TRẮNG"
      }
    ]
  },
  "auto_analyze": true
}
```

**Ví dụ upload từ extension:**
```javascript
const formData = new FormData();
formData.append('image', blob, 'screenshot.png');

fetch('http://lukistar.space/upload?auto_analyze=true', {
    method: 'POST',
    body: formData
})
.then(response => response.json())
.then(data => console.log(data));
```

### 2. Upload không phân tích (chỉ lưu ảnh)

**POST** `http://lukistar.space/upload?auto_analyze=false`

Chỉ lưu screenshot, không phân tích nốt xanh.

**Response:**
```json
{
  "status": "success",
  "message": "Screenshot uploaded successfully",
  "filename": "screenshot_20241031_103000_123.png",
  "log_id": null,
  "analysis": null,
  "auto_analyze": false
}
```

### 3. Lấy danh sách Screenshots

**GET** `http://lukistar.space/api/screenshots`

**Query Parameters:**
- `limit` (default: 50)
- `offset` (default: 0)

**Response:**
```json
{
  "screenshots": [
    {
      "id": 1,
      "timestamp": "20241031_103000_123",
      "screenshot_filename": "screenshot_20241031_103000_123.png",
      "total_dots": 5,
      "white_count": 2,
      "black_count": 3,
      "created_at": "2024-10-31T10:30:00.123",
      "screenshot_url": "/api/screenshots/1/image",
      "file_exists": true,
      "file_size": 245678
    }
  ],
  "total": 100,
  "limit": 50,
  "offset": 0
}
```

### 4. Xem Screenshot Image

**GET** `http://lukistar.space/api/screenshots/{screenshot_id}/image`

Trả về file ảnh screenshot.

### 5. Xóa Screenshot

**DELETE** `http://lukistar.space/api/screenshots/{screenshot_id}`

Xóa screenshot và log liên quan.

## Cấu hình Extension

### Server URL:
```
http://lukistar.space/upload
```

### Auth Header (nếu cần):
- Header Name: `Authorization` (optional)
- Header Value: `Bearer <token>` (optional)

**Lưu ý:** Hiện tại server chưa yêu cầu authentication, có thể thêm sau nếu cần.

## Giao diện Quản lý Screenshots

Truy cập: `http://lukistar.space/admin`

Click vào tab **"🖼️ Screenshots"** để:
- ✅ Xem danh sách tất cả screenshots đã upload
- ✅ Xem preview thumbnail
- ✅ Xem chi tiết screenshot và kết quả phân tích
- ✅ Tải JSON kết quả
- ✅ Xóa screenshot

## Test API

**Upload test:**
```bash
curl -X POST "http://lukistar.space/upload" \
  -F "image=@screenshot.png"
```

**List screenshots:**
```bash
curl http://lukistar.space/api/screenshots
```

## Workflow

1. **Extension upload screenshot** → `POST /upload`
2. **Server tự động phân tích** (nếu `auto_analyze=true`)
3. **Server lưu ảnh và kết quả** vào database
4. **Admin xem trong dashboard** → `http://lukistar.space/admin` → Tab "Screenshots"


