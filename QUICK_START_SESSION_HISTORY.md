# 🚀 Quick Start - Session History Feature

## Tính năng đã hoàn thành ✅

Hệ thống quản lý lịch sử phiên cược từ screenshot đã sẵn sàng sử dụng!

---

## 📋 Chức năng

✅ **Tự động đọc dữ liệu từ ảnh** - Sử dụng ChatGPT Vision API  
✅ **Lưu phiên mới nhất** - Chỉ lưu phiên có thời gian mới nhất  
✅ **Chống trùng lặp** - Kiểm tra số phiên để tránh lưu dữ liệu trùng  
✅ **Giới hạn 100 phiên** - Tự động xóa phiên cũ, chỉ giữ 100 phiên gần nhất  
✅ **Giao diện web đẹp** - Hiển thị bảng dữ liệu với các cột: Phiên, Thời gian, Đặt cược, Tổng cược, Thắng/Thua  

---

## 🌐 Truy cập giao diện

### URL: `https://lukistar.space/sessions`

**Hoặc local:**
- `http://localhost:8000/sessions` (nếu chạy trên máy local)

---

## 📤 Cách sử dụng

### 1. Upload Screenshot

1. Mở trang `https://lukistar.space/sessions`
2. Click vào **"Chọn tập tin"** để chọn screenshot
3. Click **"Phân tích"**
4. Đợi hệ thống phân tích (3-5 giây)
5. Xem kết quả:
   - ✅ Nếu phiên mới → Lưu vào database và hiển thị trong bảng
   - ⚠️ Nếu phiên đã tồn tại → Thông báo phiên trùng, không lưu lại

### 2. Xem Lịch Sử

- Bảng tự động tải 100 phiên gần nhất
- Phiên mới nhất ở trên cùng
- Thắng (màu xanh) / Thua (màu đỏ)

### 3. Làm Mới Dữ Liệu

- Click nút **"🔄 Làm mới"** để reload dữ liệu

### 4. Xóa Phiên

- Click **"Xóa"** ở cột "Hành động" để xóa 1 phiên
- Click **"🗑️ Xóa tất cả"** để xóa toàn bộ (cẩn thận!)

---

## 🔧 API Endpoints

### Phân tích Screenshot
```bash
POST /api/sessions/analyze
Content-Type: multipart/form-data
Body: file=<screenshot.jpg>
```

### Lấy Lịch Sử
```bash
GET /api/sessions/history?limit=100
```

### Xóa Phiên
```bash
DELETE /api/sessions/{session_id}
```

### Xóa Tất Cả
```bash
DELETE /api/sessions/clear-all
```

---

## 📊 Bảng Hiển Thị

| Cột | Mô tả |
|-----|-------|
| **Phiên** | Số phiên (session_id) |
| **Thời gian** | Thời gian phiên (DD-MM-YYYY HH:MM:SS) |
| **Đặt cược** | Loại cược (Tài/Xỉu) |
| **Tổng cược** | Số tiền cược |
| **Thắng/Thua** | Kết quả (Thắng: xanh, Thua: đỏ) |
| **Hành động** | Nút xóa phiên |

---

## 💾 Database

**Table:** `session_history`
- Lưu trong file: `logs.db`
- Tối đa: 100 phiên gần nhất
- Tự động cleanup khi vượt quá 100

---

## 🎯 Ví dụ Sử dụng

### Từ Mobile App (React Native)

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
    if (result.sessions_saved > 0) {
      alert('Đã lưu phiên mới!');
    } else {
      alert('Phiên này đã tồn tại.');
    }
  }
};
```

### Từ Python

```python
import requests

# Upload screenshot
files = {'file': open('screenshot.jpg', 'rb')}
response = requests.post('https://lukistar.space/api/sessions/analyze', files=files)
result = response.json()

print(f"Tìm thấy: {result['sessions_found']} phiên")
print(f"Phiên mới nhất: {result['latest_session']['session_id']}")
```

---

## ⚙️ Cấu hình

### Yêu cầu:
1. **OpenAI API Key** - Để sử dụng ChatGPT Vision API
   - Tạo file `.env` trong thư mục gốc:
   ```
   OPENAI_API_KEY=sk-...
   ```

2. **Python Dependencies** - Đã có sẵn trong `requirements.txt`

---

## 🧪 Testing

Tất cả các chức năng đã được test:
- ✅ Parse OCR text
- ✅ Add session (lưu phiên mới)
- ✅ Duplicate detection (kiểm tra trùng)
- ✅ Get recent sessions (lấy lịch sử)
- ✅ Delete session (xóa phiên)
- ✅ Clear all (xóa tất cả)
- ✅ 100 sessions limit (giới hạn 100 phiên)

---

## 📱 Integration với Mobile App

Mobile app có thể:
1. Chụp screenshot tự động
2. Upload lên API `/api/sessions/analyze`
3. Nhận response:
   - `sessions_found`: Số phiên tìm thấy
   - `sessions_saved`: Số phiên đã lưu (0 hoặc 1)
   - `duplicate`: true/false (phiên đã tồn tại?)
   - `latest_session`: Thông tin phiên mới nhất

---

## 🔍 Chi tiết kỹ thuật

### Files đã tạo/sửa:
1. ✅ `app/services/session_service.py` - Service quản lý session
2. ✅ `app/main.py` - Thêm 4 endpoints mới + 1 page UI
3. ✅ `SESSION_HISTORY_API.md` - Documentation đầy đủ

### Endpoints:
- `POST /api/sessions/analyze` - Phân tích screenshot
- `GET /api/sessions/history` - Lấy lịch sử
- `DELETE /api/sessions/{session_id}` - Xóa 1 phiên
- `DELETE /api/sessions/clear-all` - Xóa tất cả
- `GET /sessions` - Giao diện web

### Database:
- Table: `session_history` (trong `logs.db`)
- Indexes: `idx_session_id`, `idx_created_at`
- Auto cleanup: Chỉ giữ 100 phiên gần nhất

---

## 🎉 Sẵn sàng sử dụng!

Hệ thống đã hoàn thiện và sẵn sàng. Truy cập ngay:

👉 **https://lukistar.space/sessions**

Hoặc đọc API docs:

👉 **SESSION_HISTORY_API.md**

---

## 📞 Hỗ trợ

Nếu cần hỗ trợ, vui lòng liên hệ admin.

**Updated:** 2025-11-04


