# ✅ Azure OCR - Hướng Dẫn Sử Dụng

## 🎉 Đã Hoàn Thành!

Chức năng **Azure Computer Vision OCR** đã được thêm thành công vào Admin Dashboard!

---

## 📍 Vị Trí Nút

Trong Admin Dashboard, bạn sẽ thấy nút **"☁️ Azure OCR"** màu xanh Azure (gradient) nằm ngay sau nút **"📊 Lịch sử phiên"**.

Truy cập: **https://lukistar.space/admin**

---

## 🚀 Cách Sử Dụng

### Bước 1: Truy cập Admin Dashboard
```
https://lukistar.space/admin
```

### Bước 2: Click nút "☁️ Azure OCR"

### Bước 3: Chọn ảnh
- Click vào ô "Chọn ảnh"
- Chọn ảnh từ máy tính (hỗ trợ: JPG, PNG, BMP, GIF)
- Kích thước tối đa: 20MB
- Xem trước ảnh sẽ hiển thị ngay

### Bước 4: Bấm "🚀 Bắt đầu phân tích"
- Hệ thống sẽ upload ảnh lên server
- Server gửi ảnh đến Azure Computer Vision API
- Đợi 2-5 giây để Azure xử lý

### Bước 5: Xem kết quả
Kết quả sẽ hiển thị:
- ✅ **Ngôn ngữ phát hiện**: (vi, en, zh, etc.)
- ✅ **Độ tin cậy**: Phần trăm độ chính xác
- ✅ **Văn bản đã đọc**: Toàn bộ text được OCR

### Bước 6: Sao chép hoặc tải xuống
- **📋 Copy văn bản**: Copy vào clipboard
- **💾 Tải xuống**: Download file .txt
- **🔄 Phân tích ảnh khác**: Reset form để upload ảnh mới

---

## ⚙️ Cấu Hình Kỹ Thuật

### Azure Credentials Đã Cài Đặt:
```
AZURE_COMPUTER_VISION_KEY: EEaWyBtz0U7Aw1d30xm8uNdlQahX4IFU...
AZURE_COMPUTER_VISION_ENDPOINT: https://taixiu.cognitiveservices.azure.com/
Location: southeastasia
```

### API Endpoint:
```
POST https://lukistar.space/upload/azure-ocr
Content-Type: multipart/form-data
Body: file (image)
```

### Response Format:
```json
{
  "success": true,
  "ocr_id": 123,
  "text": "Extracted text content...",
  "language": "vi",
  "confidence": 0.98,
  "lines_count": 15,
  "image_path": "mobile_images/azure_ocr/...",
  "message": "Đọc text thành công bằng Azure Computer Vision"
}
```

---

## 🎯 Tính Năng

### ✅ Đã Implement:
1. **Nút Azure OCR** trong Admin Dashboard
2. **UI đẹp mắt** với màu sắc Azure brand
3. **Upload ảnh** với preview
4. **Integration Azure Computer Vision Read API 3.2**
5. **Hiển thị kết quả** chi tiết (language, confidence, text)
6. **Copy to clipboard** function
7. **Download text** as .txt file
8. **Database storage** - Lưu kết quả OCR vào SQLite
9. **Error handling** - Hiển thị lỗi rõ ràng
10. **Loading animation** - UX tốt khi đợi

### 🌟 Ưu Điểm So Với OCR Khác:
- ✅ **Độ chính xác cao hơn** OpenAI Vision (đặc biệt với tiếng Việt)
- ✅ **Không bị từ chối** do content policy (gambling, etc.)
- ✅ **Chi phí thấp hơn** OpenAI GPT-4 Vision
- ✅ **Hỗ trợ nhiều ngôn ngữ** tự động detect
- ✅ **Confidence score** cho từng dòng text

---

## 📁 Files Đã Tạo/Sửa

### 1. `/app/main.py`
- ✅ Thêm nút Azure OCR vào UI
- ✅ Thêm view Azure OCR với form upload
- ✅ Thêm JavaScript functions: `previewAzureImage`, `startAzureOCR`, `copyAzureResult`, `downloadAzureResult`, `resetAzureOCR`
- ✅ Thêm API endpoint `/upload/azure-ocr`
- ✅ Update `switchView` function

### 2. `/.env`
- ✅ Thêm `AZURE_COMPUTER_VISION_KEY`
- ✅ Thêm `AZURE_COMPUTER_VISION_ENDPOINT`

### 3. `/mobile_images/azure_ocr/` (folder tự động tạo)
- Lưu trữ ảnh đã upload

### 4. Database `logs.db`
- ✅ Table `azure_ocr_results` tự động tạo khi có OCR request đầu tiên

---

## 🔧 Quản Lý

### Restart Service (nếu cần):
```bash
sudo systemctl restart screenshot-analyzer
```

### Xem Logs:
```bash
# Service logs
sudo journalctl -u screenshot-analyzer -f

# Application logs
tail -f /home/myadmin/screenshot-analyzer/server.log
```

### Kiểm Tra Service:
```bash
sudo systemctl status screenshot-analyzer
```

### Update Azure Credentials (nếu cần):
```bash
cd /home/myadmin/screenshot-analyzer
nano .env

# Thêm/sửa:
AZURE_COMPUTER_VISION_KEY=your_new_key
AZURE_COMPUTER_VISION_ENDPOINT=your_new_endpoint

# Restart
sudo systemctl restart screenshot-analyzer
```

---

## 🧪 Test Thử

### Test qua Admin UI:
1. Truy cập: https://lukistar.space/admin
2. Click nút "☁️ Azure OCR"
3. Upload ảnh có text tiếng Việt
4. Xem kết quả

### Test qua API (curl):
```bash
curl -X POST https://lukistar.space/upload/azure-ocr \
  -F "file=@/path/to/image.jpg" \
  -H "Accept: application/json"
```

### Test qua Python:
```python
import requests

url = "https://lukistar.space/upload/azure-ocr"
files = {'file': open('image.jpg', 'rb')}

response = requests.post(url, files=files)
result = response.json()

print(f"Success: {result['success']}")
print(f"Text: {result['text']}")
print(f"Language: {result['language']}")
print(f"Confidence: {result['confidence']}")
```

---

## 🎨 UI/UX Features

### Design:
- 🎨 **Azure brand colors** (gradient #0078d4 → #00bcf2)
- 📱 **Responsive design** - Mobile friendly
- 🖼️ **Image preview** trước khi phân tích
- ⚡ **Loading animation** khi đang xử lý
- ✅ **Success section** với stats đẹp mắt
- ❌ **Error handling** với message rõ ràng

### User Flow:
1. Chọn ảnh → Preview hiện ngay
2. Click "Bắt đầu" → Loading animation
3. Kết quả hiện → Copy/Download dễ dàng
4. Reset → Phân tích ảnh khác

---

## 💡 Lưu Ý Quan Trọng

### 1. Azure Free Tier Limits:
- ✅ **5,000 transactions/tháng MIỄN PHÍ**
- ✅ Sau đó: $1/1,000 transactions
- ⚠️ Theo dõi usage tại: https://portal.azure.com

### 2. Supported Formats:
- ✅ JPG, JPEG
- ✅ PNG
- ✅ BMP
- ✅ GIF
- ⚠️ Max size: 20MB

### 3. OCR Quality:
- ✅ **Best**: Ảnh rõ nét, độ phân giải cao
- ✅ **Good**: Screenshot, scanned documents
- ⚠️ **Poor**: Ảnh mờ, góc nghiêng, chữ viết tay

### 4. Languages Supported:
- ✅ Vietnamese (vi)
- ✅ English (en)
- ✅ Chinese (zh-Hans, zh-Hant)
- ✅ 70+ languages khác
- 🤖 Auto-detect language

---

## 🐛 Troubleshooting

### Lỗi: "Azure credentials chưa được cấu hình"
**Giải pháp:**
```bash
cd /home/myadmin/screenshot-analyzer
./setup-azure-credentials.sh
sudo systemctl restart screenshot-analyzer
```

### Lỗi: "Lỗi từ Azure API (HTTP 401)"
**Nguyên nhân:** Azure key không đúng hoặc hết hạn

**Giải pháp:**
1. Kiểm tra key tại: https://portal.azure.com
2. Regenerate key nếu cần
3. Update vào .env
4. Restart service

### Lỗi: "Timeout waiting for Azure OCR result"
**Nguyên nhân:** Azure API quá chậm hoặc ảnh quá lớn

**Giải pháp:**
- Giảm kích thước ảnh
- Thử lại sau vài phút
- Kiểm tra internet connection

### UI không hiển thị nút Azure OCR
**Giải pháp:**
1. Clear browser cache (Ctrl+Shift+R)
2. Kiểm tra server đã restart chưa
3. Xem console error (F12)

---

## 📊 Monitoring

### Xem Database:
```bash
sqlite3 /home/myadmin/screenshot-analyzer/logs.db

# Xem 10 OCR results gần nhất
SELECT id, language, confidence, created_at 
FROM azure_ocr_results 
ORDER BY created_at DESC 
LIMIT 10;

# Xem text của result
SELECT extracted_text FROM azure_ocr_results WHERE id = 1;
```

### Check Azure Usage:
1. Truy cập: https://portal.azure.com
2. Vào resource "taixiu" (Computer Vision)
3. Metrics → Transactions
4. Xem usage chart

---

## 🎓 Best Practices

### 1. Tối Ưu Ảnh:
- Crop ảnh để chỉ lấy phần có text
- Độ phân giải: 300-600 DPI là tốt nhất
- Format: PNG cho text rõ nét, JPG cho ảnh chụp

### 2. Xử Lý Kết Quả:
- Check `confidence` score trước khi tin tưởng result
- Với confidence < 0.8, nên review lại
- Lưu ảnh gốc để review sau

### 3. Security:
- ⚠️ **KHÔNG share Azure key** ra ngoài
- ✅ Key được lưu trong .env (gitignore)
- ✅ Regenerate key định kỳ (3-6 tháng)

---

## 🚀 Next Steps (Tùy Chọn)

Nếu muốn mở rộng thêm:

### 1. History View:
- Thêm tab xem lịch sử OCR
- Hiển thị ảnh + text đã đọc
- Filter by date, language

### 2. Batch Processing:
- Upload nhiều ảnh cùng lúc
- Process hàng loạt
- Export combined results

### 3. Advanced Features:
- Table detection & extraction
- Handwriting recognition
- Business card parsing

---

## ✅ Checklist Hoàn Thành

- ✅ Nút Azure OCR trong UI
- ✅ Upload form với preview
- ✅ API endpoint hoàn chỉnh
- ✅ Azure credentials configured
- ✅ Database storage
- ✅ Error handling
- ✅ Copy/Download functions
- ✅ Loading states
- ✅ Responsive design
- ✅ Auto-start service configured
- ✅ Documentation complete

---

## 🎉 Kết Luận

Chức năng **Azure Computer Vision OCR** đã sẵn sàng sử dụng!

**Truy cập ngay:** https://lukistar.space/admin → Click nút "☁️ Azure OCR"

Chúc bạn sử dụng hiệu quả! 🚀

---

**Người tạo:** AI Assistant  
**Ngày:** 05-11-2025  
**Version:** 1.0

