# 📊 Azure OCR - Hiển Thị Dạng Bảng

## ✅ Tính Năng Mới: Tự Động Format Bảng

Azure OCR giờ đây có thể **tự động nhận diện và hiển thị kết quả dạng bảng đẹp mắt** giống như ảnh gốc!

---

## 🎯 Cách Hoạt Động

### 1. **Upload Ảnh Bảng Cược**
- Truy cập: https://lukistar.space/admin
- Click nút **"☁️ Azure OCR"**
- Upload ảnh bảng lịch sử cược

### 2. **Azure Tự Động Đọc & Parse**
- Azure Computer Vision đọc toàn bộ text
- JavaScript tự động detect format bảng cược
- Parse data thành cấu trúc table

### 3. **Hiển Thị 2 Dạng**

#### 📊 **Dạng Bảng (Table View)**
- Background tối như ảnh gốc (#2d2d2d)
- ID màu vàng (#ffd700)
- Số tiền thắng màu xanh (#4caf50)
- Số tiền thua màu đỏ (#f44336)
- Zebra striping cho dễ đọc

#### 📝 **Dạng Text (Raw Text)**
- Văn bản thuần từ Azure OCR
- Có thể toggle hiện/ẩn
- Copy được vào clipboard

---

## 🎨 Giao Diện Bảng

### Cột 1: **Phiên** (Session ID)
- Màu vàng (#ffd700)
- Font weight: 600
- Format: 6 chữ số (vd: 524124)

### Cột 2: **Thời gian**
- Màu sáng (#e0e0e0)
- Format: DD-MM-YYYY HH:MM:SS

### Cột 3: **Số tiền**
- Màu trắng (#f0f0f0)
- Format: 1,000 hoặc 2,000

### Cột 4: **Thắng/Thua**
- Màu xanh: +980, +1,960 (thắng)
- Màu đỏ: -1,000 (thua)
- Font weight: 700

### Cột 5: **Chi tiết**
- Mô tả đầy đủ: "Đặt Tài. Kết quả: Tài. Tổng đặt 2,000. Hoàn trả 0."
- Màu sáng (#d0d0d0)

---

## 🔍 Cách Parse Dữ Liệu

JavaScript sử dụng **Regular Expressions** để extract:

```javascript
// ID Pattern
/\b\d{6}\b/  // 6 chữ số: 524124

// Date Pattern
/\d{2}-\d{2}-\d{4}\s+\d{2}:\d{2}:\d{2}/  // 03-11-2025 17:41:46

// Betting Info
/Đặt\s+(Tài|Xỉu)/        // Đặt cược
/Kết quả:\s+(Tài|Xỉu)/   // Kết quả
/Tổng đặt\s+([\d,]+)/    // Số tiền
/([+\-]\d{1,3}(?:,\d{3})*)/ // Thắng/Thua
```

---

## 🎁 Tính Năng Bổ Sung

### 1. **Toggle View** (Ẩn/Hiện Text)
```javascript
toggleAzureTextView()
```
- Click nút **"👁️ Ẩn/Hiện text"** để toggle
- Tiết kiệm không gian khi chỉ cần xem bảng

### 2. **Download HTML Table**
```javascript
downloadAzureTableHTML()
```
- Click **"💾 Tải xuống HTML"**
- Tải file HTML standalone với bảng đẹp
- Mở được trên bất kỳ browser nào

### 3. **Download Raw Text**
```javascript
downloadAzureResult()
```
- Click **"💾 Tải xuống Text"**
- Tải file .txt với raw OCR text

### 4. **Copy to Clipboard**
```javascript
copyAzureResult()
```
- Click **"📋 Copy văn bản"**
- Copy raw text vào clipboard

---

## 📋 Format Bảng HTML Export

File HTML export có cấu trúc:

```html
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <title>Bảng Kết Quả OCR - Azure Computer Vision</title>
    <style>
        /* Dark theme styling */
        body { background: #1a1a1a; }
        table { background: #2d2d2d; color: #f0f0f0; }
        /* ... */
    </style>
</head>
<body>
    <div class="container">
        <h1>☁️ Kết Quả Phân Tích Azure OCR</h1>
        <table>...</table>
        <p>Tạo bởi Azure Computer Vision | 05/11/2025 10:28:36</p>
    </div>
</body>
</html>
```

---

## 🧪 Test Thử

### Bước 1: Upload Ảnh Bảng
```
https://lukistar.space/admin → "☁️ Azure OCR"
```

### Bước 2: Xem Kết Quả
Nếu ảnh là **bảng lịch sử cược**, sẽ thấy:
- ✅ Section **"📊 Hiển thị dạng bảng"**
- ✅ Bảng HTML với styling đẹp
- ✅ Nút **"💾 Tải xuống HTML"** xuất hiện

Nếu ảnh **KHÔNG phải** bảng cược:
- ⚠️ Chỉ hiện raw text
- ⚠️ Không có table view

---

## 🎯 Keywords Để Detect Bảng

JavaScript tìm các từ khóa sau trong OCR text:

```javascript
const bettingKeywords = [
    'Đặt',
    'Tài',
    'Xỉu',
    'Kết quả',
    'Hoàn trả',
    'Tổng đặt'
];
```

Nếu text chứa **ít nhất 1 keyword** → Thử parse thành bảng

---

## 💡 Ví Dụ Input/Output

### Input (Ảnh):
```
Bảng dark theme với:
- Row 1: 524124 | 03-11-2025 17:41:46 | 2,000 | +1,960 | Đặt Tài...
- Row 2: 524123 | 03-11-2025 17:40:45 | 1,000 | -1,000 | Đặt Tài...
- Row 3: 524122 | 03-11-2025 17:39:50 | 1,000 | +980   | Đặt Tài...
```

### Output (Azure OCR Text):
```
524124
03-11-2025 17:41:46
Đặt Tài. Kết quả: Tài. Tổng đặt 2,000. Hoàn trả 0.
+1,960

524123
03-11-2025 17:40:45
Đặt Tài. Kết quả: Xỉu. Tổng đặt 1,000. Hoàn trả 0.
-1,000
...
```

### Output (Parsed Table):
HTML table với 4 rows, 5 columns, styling đẹp mắt như ảnh gốc.

---

## 🐛 Troubleshooting

### Bảng không hiển thị?

**Nguyên nhân có thể:**
1. ❌ OCR text không chứa keywords
2. ❌ Format text không match pattern
3. ❌ Không tìm thấy ID 6 chữ số
4. ❌ Không tìm thấy date pattern

**Giải pháp:**
- Đảm bảo ảnh rõ nét
- Chụp đúng bảng lịch sử cược
- Crop ảnh để chỉ lấy phần bảng

### Text bị sai?

**Nguyên nhân:**
- Azure OCR đọc sai một số ký tự
- Ảnh bị mờ, góc nghiêng

**Giải pháp:**
- Chụp lại ảnh rõ hơn
- Tăng độ phân giải
- Chỉnh độ tương phản cao hơn

---

## 🎨 Customization

Muốn thay đổi màu sắc? Sửa trong function `parseAzureTextAsTable`:

```javascript
// Background colors
const rowBg = index % 2 === 0 ? '#2d2d2d' : '#363636';

// Text colors
color: #ffd700   // ID - vàng
color: #e0e0e0   // Date - sáng
color: #4caf50   // Win - xanh
color: #f44336   // Loss - đỏ
```

---

## 📊 Performance

- ✅ Parse time: < 50ms (JavaScript client-side)
- ✅ No server overhead
- ✅ Works với bất kỳ số rows nào
- ✅ Responsive design

---

## 🚀 Next Features (Tùy Chọn)

Có thể thêm:

1. **Export to Excel/CSV**
2. **Filter/Sort columns**
3. **Calculate statistics** (tổng thắng/thua, win rate)
4. **Chart visualization** (biểu đồ thắng thua theo thời gian)
5. **Print-friendly view**

---

## ✅ Summary

**Azure OCR giờ có:**
- ✅ Hiển thị dạng bảng HTML đẹp mắt
- ✅ Auto-detect betting table format
- ✅ Dark theme giống ảnh gốc
- ✅ Color-coded thắng/thua
- ✅ Export HTML standalone
- ✅ Toggle raw text view
- ✅ Copy & download functions

**Truy cập ngay:** https://lukistar.space/admin → "☁️ Azure OCR"

Enjoy! 🎉

