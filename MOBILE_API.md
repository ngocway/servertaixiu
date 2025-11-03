# 📱 Mobile API Documentation

## Endpoint cho Mobile App

### **URL Chính:**
```
POST https://lukistar.space/upload/mobile
```

---

## 📤 Request

### **Method:** 
`POST`

### **Content-Type:** 
`multipart/form-data`

### **Body Parameters:**
- `file` (required) - File ảnh cần phân tích

---

## 📥 Response

### **Success Response (200):**

```json
{
  "success": true,
  "analysis_id": 123,
  "template_id": 5,
  "template_name": "Template 13:52:44 3/11/2025",
  "total_positions": 560,
  "statistics": {
    "light_pixels": 156,
    "dark_pixels": 404
  },
  "message": "Phân tích thành công: 156 sáng, 404 tối"
}
```

### **Error Response (404) - Chưa có template:**

```json
{
  "detail": "Chưa có template. Vui lòng upload template trước."
}
```

### **Error Response (500) - Lỗi server:**

```json
{
  "detail": "Lỗi phân tích: ..."
}
```

---

## 📱 Ví dụ sử dụng

### **JavaScript/React Native:**

```javascript
const uploadImage = async (imageUri) => {
  const formData = new FormData();
  formData.append('file', {
    uri: imageUri,
    type: 'image/jpeg',
    name: 'photo.jpg'
  });

  try {
    const response = await fetch('https://lukistar.space/upload/mobile', {
      method: 'POST',
      body: formData,
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });

    const result = await response.json();
    
    if (result.success) {
      console.log('Pixel Sáng:', result.statistics.light_pixels);
      console.log('Pixel Tối:', result.statistics.dark_pixels);
    }
  } catch (error) {
    console.error('Error:', error);
  }
};
```

### **Python:**

```python
import requests

url = "https://lukistar.space/upload/mobile"
files = {'file': open('image.jpg', 'rb')}

response = requests.post(url, files=files)
result = response.json()

if result['success']:
    print(f"Pixel Sáng: {result['statistics']['light_pixels']}")
    print(f"Pixel Tối: {result['statistics']['dark_pixels']}")
```

### **cURL:**

```bash
curl -X POST https://lukistar.space/upload/mobile \
  -F "file=@image.jpg"
```

---

## 📊 Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | Trạng thái thành công |
| `analysis_id` | integer | ID của phân tích trong database |
| `template_id` | integer | ID template được sử dụng |
| `template_name` | string | Tên template |
| `total_positions` | integer | Tổng số vị trí đã phân tích |
| `statistics.light_pixels` | integer | **Số lượng pixel sáng** |
| `statistics.dark_pixels` | integer | **Số lượng pixel tối** |
| `message` | string | Thông báo kết quả |

---

## 🔄 So sánh với Extension API

| Feature | Mobile API | Extension API |
|---------|------------|---------------|
| **URL** | `/upload/mobile` | `/upload/raw` |
| **Mục đích** | Phân tích pixel sáng/tối | Screenshot tự động |
| **Response** | Thống kê pixel | Phân tích nốt xanh |
| **Đơn giản** | ✅ Rất đơn giản | 🔧 Phức tạp hơn |

---

## ⚠️ Lưu ý

1. **Phải có template trước:** Admin phải upload ảnh mẫu (có pixel màu #1AFF0D) trước khi mobile app có thể phân tích
2. **CORS:** API đã bật CORS cho mọi origin, mobile app có thể gọi trực tiếp
3. **File size:** Không giới hạn kích thước file ảnh (khuyến nghị < 5MB)
4. **Image format:** Hỗ trợ JPG, PNG, WebP, etc.

---

## 🚀 Deployment

**Server:** VPS GoDaddy  
**Domain:** https://lukistar.space  
**Status:** ✅ Running  
**Updated:** 2025-11-03

