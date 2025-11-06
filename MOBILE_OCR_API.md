# 📱 Mobile OCR API Documentation

## Endpoint cho Mobile App - Đọc Text Tự Động

### **URL Chính:**
```
POST https://lukistar.space/upload/mobile/ocr
```

---

## 📤 Request

### **Method:** 
`POST`

### **Content-Type:** 
`multipart/form-data`

### **Body Parameters:**
- `file` (required) - File ảnh chứa text cần đọc

**Hỗ trợ 2 cách gửi ảnh:**
1. **File binary** (Geelerk: `Encode as Base64 = No`)
2. **Base64 string** (Geelerk: `Encode as Base64 = Yes`)

---

## 📥 Response

### **Success Response (200):**

```json
{
  "success": true,
  "ocr_id": 15,
  "text": "Phiên|Thời gian|Đặt cược|Kết quả|Tổng cược|Tiền thắng|Thắng/Thua\n524124|03-11-2025 17:41:46|Tài|Tài|2,000|+1,960|Thắng\n524123|03-11-2025 17:40:45|Tài|Xỉu|1,000|-1,000|Thua",
  "image_path": "mobile_images/ocr/mobile_ocr_20251103_174530_123456.jpg",
  "message": "Đọc text thành công từ ảnh mobile (ID: 15)"
}
```

### **Error Response (400) - OpenAI từ chối:**

```json
{
  "detail": "OpenAI từ chối xử lý ảnh này.\n\nResponse từ ChatGPT: \"I'm sorry...\"\n\nNguyên nhân có thể:\n1. ⚠️ Ảnh chứa nội dung liên quan đến cờ bạc/game/casino\n2. ⚠️ Ảnh chứa nội dung nhạy cảm hoặc vi phạm policy\n3. ⚠️ Ảnh không rõ ràng hoặc bị lỗi\n\nGiải pháp:\n- Thử ảnh khác không liên quan đến game/cờ bạc\n- Đảm bảo ảnh rõ nét, không bị mờ\n- Thử crop ảnh để chỉ lấy phần text cần đọc"
}
```

### **Error Response (500) - Lỗi server:**

```json
{
  "detail": "OPENAI_API_KEY chưa được cấu hình..."
}
```

---

## 📱 Ví dụ sử dụng

### **JavaScript/React Native:**

```javascript
const uploadImageForOCR = async (imageUri) => {
  const formData = new FormData();
  formData.append('file', {
    uri: imageUri,
    type: 'image/jpeg',
    name: 'photo.jpg'
  });

  try {
    const response = await fetch('https://lukistar.space/upload/mobile/ocr', {
      method: 'POST',
      body: formData,
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });

    const result = await response.json();
    
    if (result.success) {
      console.log('Extracted Text:', result.text);
      console.log('OCR ID:', result.ocr_id);
    }
  } catch (error) {
    console.error('Error:', error);
  }
};
```

### **Python:**

```python
import requests

url = "https://lukistar.space/upload/mobile/ocr"
files = {'file': open('betting_history.jpg', 'rb')}

response = requests.post(url, files=files)
result = response.json()

if result['success']:
    print(f"Extracted Text:\n{result['text']}")
    print(f"Image saved at: {result['image_path']}")
```

### **cURL:**

```bash
curl -X POST https://lukistar.space/upload/mobile/ocr \
  -F "file=@betting_history.jpg"
```

### **Geelerk Automation (Base64):**

```
URL: https://lukistar.space/upload/mobile/ocr
Method: POST
Body: form-data
Field name: file
Field value: {image_base64}
Encode as Base64: Yes
```

---

## 📊 Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | Trạng thái thành công |
| `ocr_id` | integer | ID của kết quả OCR trong database |
| `text` | string | **Nội dung text đã đọc được** |
| `image_path` | string | Đường dẫn ảnh đã lưu trên server |
| `message` | string | Thông báo kết quả |

---

## 🎯 Đặc điểm của API

### **1. Tự động phân tích bảng cược:**
- API sử dụng ChatGPT Vision (model `gpt-4o`) để đọc text
- Tự động nhận diện bảng "LỊCH SỬ CƯỢC"
- Trả về dữ liệu có cấu trúc (pipe-separated format)

### **2. Lưu ảnh tự động:**
- Mọi ảnh upload từ mobile đều được lưu vào `mobile_images/ocr/`
- Có thể xem lại ảnh qua API: `/api/ocr/image/{ocr_id}`
- Tự động cleanup: chỉ giữ lại 10 kết quả mới nhất

### **3. Hỗ trợ nhiều định dạng:**
- JPG/JPEG
- PNG
- WebP
- GIF

---

## 🔄 So sánh giữa 2 Mobile APIs

| Feature | Pixel Detector API | **OCR API (MỚI)** |
|---------|-------------------|------------------|
| **URL** | `/upload/mobile` | `/upload/mobile/ocr` |
| **Mục đích** | Đếm pixel sáng/tối | **Đọc text từ ảnh** |
| **Yêu cầu** | Cần template trước | Không cần setup |
| **Response** | Thống kê số | **Text có cấu trúc** |
| **Chi phí** | Miễn phí | Dùng OpenAI API |
| **Tốc độ** | Nhanh (~1s) | Chậm hơn (~5-10s) |

---

## 🔐 Authentication

**Không cần:** API này không yêu cầu authentication. Mở cho mọi origin (CORS enabled).

---

## ⚠️ Lưu ý quan trọng

1. **OpenAI API Key:** Server phải có `OPENAI_API_KEY` trong file `.env`
2. **Chi phí:** Mỗi request tốn ~0.01-0.03 USD (tùy độ phức tạp của ảnh)
3. **Content Policy:** OpenAI có thể từ chối ảnh liên quan game/cờ bạc
4. **Timeout:** Request timeout là 60 giây
5. **Cleanup tự động:** Chỉ giữ 10 kết quả mới nhất (cả ảnh và database)
6. **File size:** Khuyến nghị < 5MB để xử lý nhanh

---

## 📍 API liên quan

### **Xem lịch sử OCR:**
```
GET https://lukistar.space/api/ocr/history?limit=10
```

**Response:**
```json
{
  "success": true,
  "total": 10,
  "history": [
    {
      "id": 15,
      "extracted_text": "...",
      "image_path": "mobile_images/ocr/mobile_ocr_20251103_174530_123456.jpg",
      "created_at": "2025-11-03 17:45:30"
    }
  ]
}
```

### **Xem ảnh đã upload:**
```
GET https://lukistar.space/api/ocr/image/15
```

Returns: Image file (JPEG/PNG/WebP)

---

## 🚀 Deployment

**Server:** VPS GoDaddy  
**Domain:** https://lukistar.space  
**Status:** ✅ Running  
**AI Model:** OpenAI GPT-4o Vision  
**Created:** 2025-11-03

---

## 💡 Use Cases

### **1. Mobile App tự động đọc lịch sử cược:**
```javascript
// User chụp màn hình game
takeScreenshot()
  .then(imageUri => uploadImageForOCR(imageUri))
  .then(result => {
    // Parse table data
    const rows = result.text.split('\n');
    displayBettingHistory(rows);
  });
```

### **2. Automation với Geelerk:**
```
1. Chụp màn hình game
2. POST ảnh đến /upload/mobile/ocr
3. Nhận text structured
4. Parse và xử lý tiếp
```

### **3. Batch processing nhiều ảnh:**
```python
import os
import requests

for image_file in os.listdir('screenshots/'):
    with open(f'screenshots/{image_file}', 'rb') as f:
        response = requests.post(
            'https://lukistar.space/upload/mobile/ocr',
            files={'file': f}
        )
        result = response.json()
        print(f"Processed {image_file}: {result['text'][:50]}...")
```

---

## 🎉 Kết luận

API này giúp **tự động hóa hoàn toàn** việc đọc text từ screenshot mobile mà không cần admin upload thủ công. Chỉ cần gửi ảnh, server sẽ tự động:
1. ✅ Nhận ảnh từ mobile
2. ✅ Lưu ảnh vào server
3. ✅ Gọi ChatGPT Vision để đọc text
4. ✅ Trả về kết quả có cấu trúc
5. ✅ Cleanup tự động

**Perfect for automation! 🚀**





