# 📊 Session History API Documentation

## Tổng quan

Hệ thống quản lý và lưu trữ lịch sử các phiên cược từ screenshot. Tự động phân tích ảnh, trích xuất dữ liệu phiên và lưu vào database (tối đa 100 phiên gần nhất).

---

## 🎯 Tính năng chính

1. **Tự động phân tích screenshot** - Sử dụng ChatGPT Vision API để đọc dữ liệu từ ảnh
2. **Chống trùng lặp** - Kiểm tra số phiên để tránh lưu dữ liệu trùng
3. **Giới hạn 100 phiên** - Tự động xóa các phiên cũ, chỉ giữ 100 phiên gần nhất
4. **Giao diện web** - Hiển thị bảng dữ liệu đẹp, dễ sử dụng

---

## 📡 API Endpoints

### 1. Phân tích Screenshot và Lưu Phiên

**POST** `/api/sessions/analyze`

Upload screenshot và tự động phân tích, lưu phiên mới nhất vào database.

**Request:**
```bash
POST https://lukistar.space/api/sessions/analyze
Content-Type: multipart/form-data
Body: file=<image_file>
```

**Response Success:**
```json
{
  "success": true,
  "message": "Phân tích thành công: tìm thấy 4 phiên",
  "sessions_found": 4,
  "sessions_saved": 1,
  "latest_session": {
    "session_id": "631733590",
    "session_time": "04-11-2025 19:30:48",
    "bet_placed": "Tài",
    "result": "NaN",
    "total_bet": "1,000",
    "winnings": "-",
    "win_loss": "Thua"
  },
  "duplicate": false,
  "image_path": "mobile_images/sessions/session_20251104_193048.jpg",
  "ocr_text": "..."
}
```

**Response (Phiên đã tồn tại):**
```json
{
  "success": true,
  "message": "Phân tích thành công: tìm thấy 4 phiên",
  "sessions_found": 4,
  "sessions_saved": 0,
  "latest_session": {...},
  "duplicate": true
}
```

---

### 2. Lấy Lịch Sử Phiên

**GET** `/api/sessions/history?limit=100`

Lấy danh sách các phiên gần nhất (tối đa 100).

**Parameters:**
- `limit` (optional) - Số lượng phiên (mặc định: 100, tối đa: 100)

**Response:**
```json
{
  "success": true,
  "total_sessions": 50,
  "sessions": [
    {
      "id": 1,
      "session_id": "631733590",
      "session_time": "04-11-2025 19:30:48",
      "bet_placed": "Tài",
      "result": "NaN",
      "total_bet": "1,000",
      "winnings": "-",
      "win_loss": "Thua",
      "image_path": "mobile_images/sessions/session_20251104_193048.jpg",
      "created_at": "2025-11-04 19:30:50"
    },
    ...
  ]
}
```

---

### 3. Xóa Một Phiên

**DELETE** `/api/sessions/{session_id}`

Xóa một phiên theo session_id.

**Example:**
```bash
DELETE https://lukistar.space/api/sessions/631733590
```

**Response:**
```json
{
  "success": true,
  "message": "Đã xóa phiên 631733590"
}
```

---

### 4. Xóa Tất Cả Phiên

**DELETE** `/api/sessions/clear-all`

Xóa tất cả các phiên trong database (cẩn thận!).

**Response:**
```json
{
  "success": true,
  "message": "Đã xóa tất cả các phiên"
}
```

---

## 🖥️ Giao Diện Web

### URL: `https://lukistar.space/sessions`

**Tính năng:**
- ✅ Upload screenshot để phân tích
- ✅ Hiển thị bảng 100 phiên gần nhất
- ✅ Thống kê tổng số phiên
- ✅ Làm mới dữ liệu
- ✅ Xóa từng phiên hoặc xóa tất cả
- ✅ Responsive, đẹp mắt

**Cột trong bảng:**
1. **Phiên** - Số phiên (session_id)
2. **Thời gian** - Thời gian phiên (DD-MM-YYYY HH:MM:SS)
3. **Đặt cược** - Loại cược (Tài/Xỉu)
4. **Tổng cược** - Số tiền cược
5. **Thắng/Thua** - Kết quả (màu xanh: Thắng, màu đỏ: Thua)

---

## 📊 Database Schema

**Table:** `session_history`

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PRIMARY KEY | ID tự động tăng |
| `session_id` | TEXT UNIQUE | Số phiên (duy nhất) |
| `session_time` | TEXT | Thời gian phiên |
| `bet_placed` | TEXT | Loại cược (Tài/Xỉu) |
| `result` | TEXT | Kết quả (Tài/Xỉu/NaN) |
| `total_bet` | TEXT | Tổng cược |
| `winnings` | TEXT | Tiền thắng (+/-) |
| `win_loss` | TEXT | Thắng/Thua |
| `image_path` | TEXT | Đường dẫn ảnh |
| `created_at` | TIMESTAMP | Thời gian tạo |

**Indexes:**
- `idx_session_id` - Tìm kiếm nhanh theo session_id
- `idx_created_at` - Sắp xếp theo thời gian

---

## 🔄 Luồng Hoạt Động

1. **User upload screenshot** → API `/api/sessions/analyze`
2. **ChatGPT Vision** đọc text từ ảnh
3. **Parse text** thành danh sách sessions
4. **Tìm phiên mới nhất** (theo thời gian)
5. **Kiểm tra trùng lặp** (theo session_id)
6. **Lưu vào database** (nếu chưa tồn tại)
7. **Cleanup** - Xóa phiên cũ, chỉ giữ 100 phiên gần nhất
8. **Return response** với thông tin phiên

---

## 🎨 Ví dụ Sử dụng

### Python

```python
import requests

# Upload screenshot
url = "https://lukistar.space/api/sessions/analyze"
files = {'file': open('screenshot.jpg', 'rb')}

response = requests.post(url, files=files)
result = response.json()

if result['success']:
    print(f"Tìm thấy {result['sessions_found']} phiên")
    print(f"Phiên mới nhất: {result['latest_session']['session_id']}")
    
    if result['duplicate']:
        print("Phiên này đã tồn tại trong database")
    else:
        print("Đã lưu phiên mới!")
```

### JavaScript/React Native

```javascript
const uploadScreenshot = async (imageUri) => {
  const formData = new FormData();
  formData.append('file', {
    uri: imageUri,
    type: 'image/jpeg',
    name: 'screenshot.jpg'
  });

  const response = await fetch('https://lukistar.space/api/sessions/analyze', {
    method: 'POST',
    body: formData
  });

  const result = await response.json();
  
  if (result.success) {
    console.log('Sessions found:', result.sessions_found);
    console.log('Latest session:', result.latest_session);
  }
};
```

### cURL

```bash
# Upload screenshot
curl -X POST https://lukistar.space/api/sessions/analyze \
  -F "file=@screenshot.jpg"

# Lấy lịch sử
curl https://lukistar.space/api/sessions/history?limit=50

# Xóa phiên
curl -X DELETE https://lukistar.space/api/sessions/631733590
```

---

## ⚙️ Cấu hình

**Yêu cầu:**
- ✅ OpenAI API Key - Đặt trong file `.env`:
  ```
  OPENAI_API_KEY=sk-...
  ```

**Model sử dụng:** `gpt-4o`

**Temperature:** `0.1` (chính xác cao)

---

## ⚠️ Lưu Ý

1. **Chống trùng lặp:** Hệ thống kiểm tra `session_id`, nếu phiên đã tồn tại sẽ không lưu lại
2. **Giới hạn 100 phiên:** Tự động xóa phiên cũ khi vượt quá 100
3. **Phiên mới nhất:** Chỉ lưu phiên có thời gian mới nhất trong mỗi screenshot
4. **Format thời gian:** DD-MM-YYYY HH:MM:SS
5. **CORS:** API đã bật CORS, mobile app có thể gọi trực tiếp

---

## 🚀 Deployment

**Server:** VPS GoDaddy  
**Domain:** https://lukistar.space  
**Database:** SQLite (`logs.db`)  
**Status:** ✅ Running  

**Updated:** 2025-11-04

---

## 📱 Mobile Integration

Ứng dụng mobile có thể:
1. Chụp screenshot tự động
2. Upload lên `/api/sessions/analyze`
3. Nhận thông báo có phiên mới hoặc phiên trùng
4. Hiển thị lịch sử từ `/api/sessions/history`

---

## 🐛 Troubleshooting

**Lỗi: "OPENAI_API_KEY chưa được cấu hình"**
- Tạo file `.env` với `OPENAI_API_KEY=sk-...`

**Lỗi: "Không tìm thấy dữ liệu phiên nào"**
- Kiểm tra ảnh có rõ ràng không
- Đảm bảo ảnh là bảng lịch sử cược

**Phiên không được lưu (duplicate: true)**
- Phiên này đã tồn tại trong database
- Bình thường, hệ thống chống trùng lặp

---

## 📞 Hỗ Trợ

Nếu cần hỗ trợ, vui lòng liên hệ admin hoặc tạo issue trên GitHub.


