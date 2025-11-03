# 📄 Template Image Matching System - Hướng dẫn sử dụng

## 🎯 Tổng quan

Hệ thống cho phép upload **1 ảnh mẫu duy nhất** chứa vị trí các nốt xanh. Tất cả screenshots từ Extension sẽ được tự động so sánh với template này.

## 🔐 Quy tắc quan trọng

⚠️ **CHỈ CHO PHÉP 1 TEMPLATE DUY NHẤT**
- Upload template mới = **XÓA** template cũ
- Không thể có nhiều templates cùng lúc
- Template luôn ở trạng thái "Active"

## 📋 Cách sử dụng

### 1️⃣ Upload Template

**Via Admin UI:**
```
1. Truy cập: https://lukistar.space/admin
2. Click tab "📄 Templates"
3. Click "🔄 Upload/Replace Template"
4. Điền thông tin:
   - Tên template
   - Mô tả (optional)
   - Chọn ảnh
   - ✓ Tự động detect nốt xanh (hoặc bỏ tick để manual)
5. Click "Upload"
```

**Via API:**
```bash
curl -X POST "https://lukistar.space/api/templates/upload?name=My+Template&auto_detect=true" \
  -F "image=@template.png"
```

### 2️⃣ Set Manual Dots (nếu auto-detect không chính xác)

```bash
curl -X PUT "https://lukistar.space/api/templates/{template_id}/dots" \
  -H "Content-Type: application/json" \
  -d '[
    {"number": 1, "x": 100, "y": 150},
    {"number": 2, "x": 200, "y": 150},
    {"number": 3, "x": 300, "y": 150}
  ]'
```

### 3️⃣ Upload Screenshot (Extension)

Screenshot sẽ **TỰ ĐỘNG** so sánh với template:

```javascript
// Extension upload
fetch('https://lukistar.space/upload/raw?auto_analyze=true', {
  method: 'POST',
  headers: {'Content-Type': 'image/jpeg'},
  body: imageBlob
})
```

**Response:**
```json
{
  "status": "success",
  "log_id": 123,
  "analysis": {
    "total": 50,
    "white": 30,
    "black": 20,
    "positions": [...]
  },
  "template_comparison": {
    "template_id": 1,
    "template_name": "Mẫu bảng A",
    "match_score": 96.0,
    "details": {
      "matched": 48,
      "missing": 2,
      "missing_dots": [5, 23],
      "extra": 0
    }
  }
}
```

## 📊 Match Score

**Công thức:**
```
match_score = (matched_dots / total_template_dots) × 100
```

**Ví dụ:**
- Template có 50 dots
- Screenshot khớp 48 dots
- Match score = 48/50 × 100 = **96%**

**Tolerance:** ±10 pixels (có thể điều chỉnh)

## 🎨 Template Format

**Yêu cầu:**
- Format: PNG, JPG, JPEG, WEBP
- Size: Tùy ý (khuyến nghị: resolution thật của screenshots)
- Chứa nốt xanh màu lime green (RGB: 0, 255, 0 hoặc gần đó)

**Lưu ý:**
- Nốt xanh càng sáng, càng dễ detect
- Kích thước nốt: tối thiểu 10x10 pixels
- Background: Tránh màu xanh lá

## 📁 Database Schema

**Table: template_images**
```sql
id                      INTEGER PRIMARY KEY
name                    TEXT
filename                TEXT
green_dots_positions    TEXT (JSON)
image_width             INTEGER
image_height            INTEGER
created_at              TIMESTAMP
is_active               INTEGER (luôn = 1)
description             TEXT
```

**Table: analysis_logs (updated)**
```sql
... (existing columns)
template_id             INTEGER
match_score             REAL
```

## 🔧 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/templates/upload` | Upload/Replace template |
| GET | `/api/templates` | List templates (max 1) |
| GET | `/api/templates/active` | Get current template |
| GET | `/api/templates/{id}` | Get template details |
| GET | `/api/templates/{id}/image` | Download template image |
| PUT | `/api/templates/{id}/dots` | Update dots positions |
| DELETE | `/api/templates/{id}` | Delete template |
| POST | `/api/templates/{id}/compare` | Manual comparison |

## 📈 Workflow

```
┌─────────────────────────────────────────────┐
│ 1. Admin upload template image             │
│    ↓                                        │
│ 2. System auto-detect green dots           │
│    (hoặc admin set manual)                  │
│    ↓                                        │
│ 3. Template saved (REPLACE nếu đã có cũ)   │
│    ↓                                        │
│ 4. Extension upload screenshot              │
│    ↓                                        │
│ 5. Server detect dots trong screenshot     │
│    ↓                                        │
│ 6. Compare với template                    │
│    - Check số lượng dots                   │
│    - Check vị trí (tolerance ±10px)        │
│    - Calculate match_score                 │
│    ↓                                        │
│ 7. Save result + match_score to DB         │
│    ↓                                        │
│ 8. Return to Extension với comparison      │
└─────────────────────────────────────────────┘
```

## ⚙️ Comparison Details

**Fields in comparison result:**

| Field | Description |
|-------|-------------|
| `matched` | Số dots khớp vị trí với template |
| `matched_dots` | Danh sách số thứ tự dots khớp |
| `missing` | Số dots trong template nhưng không có trong screenshot |
| `missing_dots` | Danh sách số thứ tự dots thiếu |
| `extra` | Số dots trong screenshot nhưng không có trong template |
| `extra_dots` | Danh sách số thứ tự dots thừa |

**Example:**
```json
{
  "matched": 48,
  "matched_dots": [1,2,3,4,6,7,8,...],
  "missing": 2,
  "missing_dots": [5, 23],
  "extra": 0,
  "extra_dots": []
}
```

## 🚨 Lưu ý khi sử dụng

### ✅ Nên làm:
- Upload template với ảnh có chất lượng tốt
- Đảm bảo nốt xanh rõ ràng
- Test template với 1-2 screenshots trước
- Kiểm tra match_score có hợp lý không

### ❌ Không nên:
- Upload template với resolution quá khác screenshots
- Dùng ảnh mờ hoặc nốt xanh không rõ
- Quên backup template cũ trước khi replace

## 📊 File Locations

```
/home/myadmin/screenshot-analyzer/
├── templates/
│   └── template_YYYYMMDD_HHMMSS_mmm.png  ← Chỉ 1 file
├── screenshots/
│   └── screenshot_*.{jpg,png}            ← Nhiều files
└── logs.db
    ├── template_images                   ← Max 1 row
    └── analysis_logs                     ← Có template_id, match_score
```

## 🎯 Use Cases

### Case 1: Setup ban đầu
```bash
# Upload template lần đầu
POST /api/templates/upload?name=Template+Chính&auto_detect=true
# Response: template_id = 1

# Extension upload screenshot
POST /upload/raw?auto_analyze=true
# Response: match_score = 100% (perfect match)
```

### Case 2: Replace template
```bash
# Upload template mới (auto-delete template cũ)
POST /api/templates/upload?name=Template+Mới&auto_detect=true
# Response: template_id = 2 (template cũ đã bị xóa)

# Screenshots tiếp theo sẽ so sánh với template mới
```

### Case 3: Xóa template
```bash
# Xóa template hiện tại
DELETE /api/templates/{id}

# Screenshots sau đó sẽ không có template comparison
```

## 🔍 Troubleshooting

**Q: Match score luôn = 0?**
- A: Check green dots có được detect không (xem analysis.total)
- A: Kiểm tra template có dots positions không (xem template details)

**Q: Upload template mới không xóa cũ?**
- A: Check server logs để xem error
- A: Verify quyền write vào thư mục templates/

**Q: Comparison details sai?**
- A: Điều chỉnh tolerance (default 10px)
- A: Check resolution screenshot có khớp template không

## 🎉 Tính năng đã hoàn thành

✅ Upload template (replace cũ tự động)  
✅ Auto-detect green dots  
✅ Manual edit dots positions  
✅ Auto-comparison khi upload screenshot  
✅ Match score calculation  
✅ Missing/Extra dots detection  
✅ Admin UI với Templates tab  
✅ API đầy đủ  
✅ HTTPS + CORS support  

## 📞 URLs

- **Admin:** https://lukistar.space/admin
- **API Docs:** https://lukistar.space/docs
- **Template Upload:** https://lukistar.space/api/templates/upload
- **Screenshot Upload:** https://lukistar.space/upload/raw



