# 📱 Run Mobile - Hệ Thống Tự Động Betting

## ✅ Đã Hoàn Thành!

Hệ thống **Run Mobile** đã được tích hợp hoàn chỉnh vào server, bao gồm:
- ✅ API nhận ảnh từ mobile
- ✅ Phân tích 2 loại ảnh (lịch sử cược & màn hình cược)
- ✅ Tính hệ số cược tự động theo chiến lược Martingale
- ✅ Quản lý state riêng biệt cho từng device
- ✅ Lưu lịch sử 100 ảnh gần nhất
- ✅ Admin dashboard để monitor

---

## 🚀 Truy Cập Admin Dashboard

```
https://lukistar.space/admin → Click "📱 Run Mobile"
```

---

## 📡 API Endpoint Cho Mobile

### POST: Gửi ảnh để phân tích
```
POST https://lukistar.space/api/mobile/analyze
Content-Type: multipart/form-data

Parameters:
- file: Screenshot image (JPG/PNG)
- device_name: Tên thiết bị (vd: "PhoneA", "PhoneB")
- betting_method: "Tài" hoặc "Xỉu"
```

### GET: Lấy lịch sử
```
GET https://lukistar.space/api/mobile/history?limit=50
```

### GET: Lấy state của device
```
GET https://lukistar.space/api/mobile/device-state/{device_name}
```

---

## 🎯 Luồng Hoạt Động

### 1. Mobile Gửi Ảnh
Mobile POST ảnh + metadata lên server:
```bash
curl -X POST https://lukistar.space/api/mobile/analyze \
  -F "file=@screenshot.jpg" \
  -F "device_name=PhoneA" \
  -F "betting_method=Tài"
```

### 2. Server Phân Tích
- ChatGPT Vision đọc ảnh
- Detect loại ảnh (HISTORY hoặc BETTING)
- Extract data (phiên, giây, tiền cược, kết quả)

### 3. Server Tính Hệ Số
Theo 5 quy tắc:
1. Chưa có kết quả → multiplier = 0
2. Server lỗi → multiplier = 0
3. Thắng → multiplier = 1, reset chuỗi thua
4. Thua → multiplier = (bet × 2) / 1000
5. Thua 4 liên tiếp → Nghỉ 3 phiên, multiplier = 0

### 4. Server Trả JSON
Mobile nhận JSON với đầy đủ thông tin

---

## 📊 JSON Response Format

### Loại 1: Ảnh Lịch Sử Cược
```json
{
  "device_name": "PhoneA",
  "betting_method": "Tài",
  "image_type": "HISTORY",
  "session_id": "#524124",
  "session_time": "03-11-2025 17:41:46",
  "bet_amount": 2000,
  "win_loss": "Thắng",
  "multiplier": 1.0
}
```

### Loại 2: Ảnh Màn Hình Cược
```json
{
  "device_name": "PhoneA",
  "betting_method": "Tài",
  "image_type": "BETTING",
  "session_id": "#523929",
  "seconds": 26,
  "bet_amount": 1000,
  "bet_status": "Đã cược"
}
```

---

## 🧮 Quy Tắc Tính Hệ Số Cược

### Quy Tắc 1: Phiên chưa có kết quả
```
win_loss = None → multiplier = 0
```

### Quy Tắc 2: Server lỗi
```
OCR lỗi / Không đọc được → multiplier = 0
```

### Quy Tắc 3: Kết quả Thắng
```
win_loss = "Thắng"
→ multiplier = 1
→ lose_streak_count = 0 (reset)
```

### Quy Tắc 4: Kết quả Thua
```
win_loss = "Thua"
→ multiplier = (bet_amount × 2) / 1000
→ lose_streak_count += 1

Ví dụ:
- Thua 1000 → multiplier = (1000 × 2) / 1000 = 2
- Thua 2000 → multiplier = (2000 × 2) / 1000 = 4
- Thua 4000 → multiplier = (4000 × 2) / 1000 = 8
```

### Quy Tắc 5: Thua 4 Liên Tiếp → Nghỉ 3 Phiên
```
lose_streak_count = 4
→ rest_mode = True
→ rest_counter = 0
→ last_lost_bet_amount = bet_amount_of_4th_loss

Trong 3 phiên kế tiếp:
→ multiplier = 0 (không cược)
→ rest_counter += 1

Sau 3 phiên nghỉ (rest_counter = 3):
→ rest_mode = False
→ multiplier = (last_lost_bet_amount × 2) / 1000
```

---

## 🔢 Ví Dụ Cụ Thể

### Scenario: PhoneA gửi ảnh lịch sử

| Ảnh | Phiên | Kết quả | Bet | Hệ số trả về | Giải thích |
|-----|-------|---------|-----|--------------|------------|
| 1 | #557 | Thua | 1000 | 2 | Thua lần 1 |
| 2 | #558 | Thua | 2000 | 4 | Thua lần 2 |
| 3 | #559 | Thua | 4000 | 8 | Thua lần 3 |
| 4 | #560 | Thua | 8000 | 16 | Thua lần 4 → bắt đầu nghỉ |
| 5 | - | - | - | 0 | Nghỉ phiên 1/3 |
| 6 | - | - | - | 0 | Nghỉ phiên 2/3 |
| 7 | - | - | - | 0 | Nghỉ phiên 3/3 |
| 8 | #564 | - | - | 16 | Hết nghỉ, tính từ bet phiên #560 |
| 9 | #565 | Thắng | 16000 | 1 | Thắng → reset |
| 10 | #566 | Thua | 1000 | 2 | Thua mới, bắt đầu lại |

---

## 💾 Database Structure

### Table: `mobile_device_states`
Lưu state của từng device:
```sql
device_name TEXT PRIMARY KEY
lose_streak_count INTEGER
rest_mode BOOLEAN
rest_counter INTEGER
last_lost_bet_amount INTEGER
betting_method TEXT
last_session_id TEXT
updated_at TIMESTAMP
```

### Table: `mobile_analysis_history`
Lưu lịch sử phân tích (max 100):
```sql
id INTEGER PRIMARY KEY
device_name TEXT
betting_method TEXT
session_id TEXT
image_type TEXT (HISTORY/BETTING)
seconds_remaining INTEGER
bet_amount INTEGER
bet_status TEXT
win_loss TEXT (Thắng/Thua)
multiplier REAL
image_path TEXT
chatgpt_response TEXT
created_at TIMESTAMP
```

---

## 🧪 Test API Bằng Curl

### Test Upload Ảnh Lịch Sử
```bash
curl -X POST https://lukistar.space/api/mobile/analyze \
  -F "file=@history_screenshot.jpg" \
  -F "device_name=PhoneA" \
  -F "betting_method=Tài"
```

### Test Upload Ảnh Màn Hình Cược
```bash
curl -X POST https://lukistar.space/api/mobile/analyze \
  -F "file=@betting_screen.jpg" \
  -F "device_name=PhoneA" \
  -F "betting_method=Xỉu"
```

### Lấy Lịch Sử
```bash
curl https://lukistar.space/api/mobile/history?limit=10
```

### Lấy State Device
```bash
curl https://lukistar.space/api/mobile/device-state/PhoneA
```

---

## 🎯 Cách Mobile Sử Dụng

### Python Example
```python
import requests

# Upload ảnh
url = "https://lukistar.space/api/mobile/analyze"
files = {'file': open('screenshot.jpg', 'rb')}
data = {
    'device_name': 'PhoneA',
    'betting_method': 'Tài'
}

response = requests.post(url, files=files, data=data)
result = response.json()

print(f"Image Type: {result['image_type']}")
print(f"Session: {result.get('session_id')}")
print(f"Multiplier: {result.get('multiplier')}")

# Sử dụng multiplier để tính tiền cược phiên tiếp theo
if 'multiplier' in result:
    next_bet = 1000 * result['multiplier']
    print(f"Tiền cược phiên sau: {next_bet}")
```

---

## 📱 Admin Dashboard Features

Truy cập: `https://lukistar.space/admin` → **"📱 Run Mobile"**

### Hiển thị:
1. **Stats Cards**: Số thiết bị, tổng phân tích
2. **API Endpoint**: Copy URL để dùng
3. **Lịch Sử Table**: 100 phân tích gần nhất với:
   - ID, Thiết bị
   - Loại ảnh (HISTORY/BETTING)
   - Phiên, Giây
   - Tiền cược
   - Kết quả (Thắng/Thua)
   - Hệ số cược
   - Thời gian

### Filter:
- 10 / 50 / 100 records
- Làm mới real-time

---

## 🎨 Color Coding

- **HISTORY**: Màu tím (#667eea)
- **BETTING**: Màu xanh (#28a745)
- **Thắng**: Màu xanh (#28a745)
- **Thua**: Màu đỏ (#dc3545)
- **Hệ số**: Màu tím đậm (#667eea)

---

## 🐛 Troubleshooting

### Mobile không nhận được JSON?
**Kiểm tra:**
- API endpoint đúng chưa
- Parameters đầy đủ (file, device_name, betting_method)
- Image format hợp lệ (JPG/PNG)

### Hệ số cược = 0 mãi?
**Nguyên nhân:**
- ChatGPT không đọc được kết quả
- Ảnh mờ hoặc không rõ
- Đang trong giai đoạn nghỉ 3 phiên

**Giải pháp:**
- Xem lịch sử trong Admin Dashboard
- Check state của device
- Chụp ảnh rõ hơn

### State không cập nhật?
**Reset state của device:**
```sql
DELETE FROM mobile_device_states WHERE device_name = 'PhoneA';
```

---

## 💡 Tips & Best Practices

### 1. Tên Thiết Bị
- Dùng tên duy nhất cho mỗi device
- Ví dụ: "PhoneA", "PhoneB", "TabletC"
- Không đổi tên trong quá trình chạy

### 2. Chụp Ảnh
- Rõ nét, không mờ
- Đầy đủ thông tin (phiên, giây, tiền)
- Crop bỏ phần không cần thiết

### 3. Timing
- Gửi ảnh lịch sử SAU KHI phiên kết thúc
- Gửi ảnh màn hình cược TRƯỚC KHI hết giờ

### 4. Monitor
- Xem lịch sử thường xuyên trong Admin
- Check state của device khi cần
- Backup data định kỳ

---

## 🔐 Security

### API Key
- OPENAI_API_KEY đã được cấu hình
- Không expose ra ngoài
- Mobile chỉ gửi ảnh, không cần key

### Rate Limiting
- OpenAI: 3,500 requests/minute
- Đủ cho nhiều devices đồng thời

### Data Privacy
- Ảnh được lưu local trên server
- Tự động cleanup giữ 100 ảnh gần nhất

---

## 📊 Monitoring & Analytics

### Admin Dashboard
Vào `https://lukistar.space/admin` → **"📱 Run Mobile"**

**Xem được:**
- Số thiết bị đang hoạt động
- Tổng số phân tích
- Lịch sử chi tiết từng phiên
- State của từng device

### Logs
```bash
# Xem server logs
tail -f /home/myadmin/screenshot-analyzer/server.log

# Xem mobile analyze logs
tail -f /home/myadmin/screenshot-analyzer/server.log | grep "Mobile Analyze"
```

---

## 🎓 Chiến Lược Martingale

### Cơ Bản
- Bắt đầu với bet = 1000
- Thắng → giữ nguyên 1000
- Thua → nhân đôi (2000, 4000, 8000...)

### Quy Tắc Đặc Biệt
- Thua 4 liên tiếp → Nghỉ 3 phiên
- Sau nghỉ → Cược lại với hệ số từ phiên thua thứ 4
- Thắng bất kỳ lúc nào → Reset về 1000

### Lợi Ích
- Tự động recovery sau thua
- Limit risk (nghỉ sau 4 thua)
- Không cảm tính

---

## 💰 Chi Phí Vận Hành

### ChatGPT Vision API
- **Model**: gpt-4o-mini
- **Cost per image**: ~$0.00012 (~3 VND)
- **1000 ảnh**: ~$0.12 (~3,000 VND)

### So sánh
- Azure OCR: $1.50/1000 ảnh
- ChatGPT: $0.12/1000 ảnh
- **Tiết kiệm**: $1.38/1000 ảnh (92% rẻ hơn!)

---

## 🔄 Workflow Đầy Đủ

```
Mobile chụp màn hình
        ↓
POST /api/mobile/analyze
   (file + device_name + betting_method)
        ↓
Server nhận ảnh → Lưu file
        ↓
ChatGPT Vision phân tích
        ↓
Detect loại ảnh (HISTORY / BETTING)
        ↓
Extract data (phiên, giây, tiền, kết quả)
        ↓
Load device state từ DB
        ↓
Tính hệ số cược (theo 5 quy tắc)
        ↓
Update device state
        ↓
Lưu lịch sử (limit 100)
        ↓
Trả JSON cho mobile
        ↓
Mobile nhận JSON → Xử lý tiếp
```

---

## 📝 Code Example Cho Mobile App

### Android (Kotlin)
```kotlin
val client = OkHttpClient()
val file = File("/path/to/screenshot.jpg")

val requestBody = MultipartBody.Builder()
    .setType(MultipartBody.FORM)
    .addFormDataPart("file", "screenshot.jpg",
        file.asRequestBody("image/jpeg".toMediaType()))
    .addFormDataPart("device_name", "PhoneA")
    .addFormDataPart("betting_method", "Tài")
    .build()

val request = Request.Builder()
    .url("https://lukistar.space/api/mobile/analyze")
    .post(requestBody)
    .build()

client.newCall(request).execute().use { response ->
    val json = JSONObject(response.body?.string())
    val multiplier = json.getDouble("multiplier")
    
    // Tính tiền cược phiên sau
    val nextBet = 1000 * multiplier
}
```

### iOS (Swift)
```swift
let url = URL(string: "https://lukistar.space/api/mobile/analyze")!
var request = URLRequest(url: url)
request.httpMethod = "POST"

let boundary = UUID().uuidString
request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")

var body = Data()
// Add file, device_name, betting_method...

URLSession.shared.dataTask(with: request) { data, response, error in
    if let data = data,
       let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
       let multiplier = json["multiplier"] as? Double {
        let nextBet = 1000 * multiplier
        // Use nextBet for next round
    }
}.resume()
```

---

## ✅ Checklist Hoàn Thành

- ✅ Nút "📱 Run Mobile" trong Admin Dashboard
- ✅ API POST `/api/mobile/analyze`
- ✅ API GET `/api/mobile/history`
- ✅ API GET `/api/mobile/device-state/{device}`
- ✅ Service quản lý state
- ✅ Database lưu lịch sử (limit 100)
- ✅ Logic tính hệ số cược (5 quy tắc)
- ✅ Detect 2 loại ảnh tự động
- ✅ ChatGPT Vision integration
- ✅ Admin UI để monitor
- ✅ Color coding & visualization
- ✅ Error handling đầy đủ

---

## 🎉 Sẵn Sàng Sử Dụng!

**Server:** ✅ Đang chạy  
**API:** ✅ Sẵn sàng nhận request  
**Admin Dashboard:** ✅ https://lukistar.space/admin → "📱 Run Mobile"

**Mobile có thể bắt đầu gửi ảnh ngay!** 🚀

---

**Tạo bởi:** AI Assistant  
**Ngày:** 05-11-2025  
**Version:** 1.0

