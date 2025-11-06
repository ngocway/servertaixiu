# 📱 MOBILE API - DOCUMENTATION ĐẦY ĐỦ

## ✅ CẬP NHẬT HOÀN CHỈNH

Server đã được code lại 100% với:
- ✅ 2 Prompts riêng biệt (Popup vs Màn hình cược)
- ✅ 3 Endpoints verification (analyze, verify-quick, verify-popup)
- ✅ Logic tính hệ số cược đầy đủ (5 quy tắc + nghỉ 3 phiên)
- ✅ Database lưu lịch sử + verification logs + mismatches
- ✅ Confidence scoring
- ✅ Mismatch handling
- ✅ Device state management

---

## 📡 API ENDPOINTS

### 1. POST `/api/mobile/analyze` ⭐ MAIN ENDPOINT

**Mục đích:** Phân tích ảnh từ mobile (popup lịch sử HOẶC màn hình cược)

**Request:**
```bash
POST https://lukistar.space/api/mobile/analyze
Content-Type: multipart/form-data

Parameters:
- file: Screenshot image (JPG/PNG)
- device_name: Tên thiết bị (vd: "PhoneA")
- betting_method: "Tài" hoặc "Xỉu"
```

**Response nếu POPUP LỊCH SỬ:**
```json
{
  "device_name": "PhoneA",
  "betting_method": "Tài",
  "image_type": "HISTORY",
  "session_id": "#526653",
  "session_time": "05-11-2025 04:48:56",
  "bet_amount": 2000,
  "win_loss": "Thua",
  "multiplier": 4.0,
  "verification": {
    "required": false,
    "threshold": 0.85,
    "reason": null
  },
  "device_state": {
    "lose_streak": 2,
    "rest_mode": false,
    "rest_counter": 0
  }
}
```

**Response nếu MÀN HÌNH CƯỢC:**
```json
{
  "device_name": "PhoneA",
  "betting_method": "Tài",
  "image_type": "BETTING",
  "session_id": null,
  "seconds": 42,
  "bet_amount": 2000,
  "bet_status": "Đã cược",
  "note": "Session ID không chính xác từ màn hình cược - dùng popup để verify"
}
```

---

### 2. POST `/api/mobile/verify-quick` ⚡ QUICK VERIFY

**Mục đích:** Verify nhanh sau khi tap "Đặt cược" (chỉ check số tiền)

**Request:**
```bash
POST https://lukistar.space/api/mobile/verify-quick
Content-Type: multipart/form-data

Parameters:
- file: Screenshot màn hình sau khi tap "Đặt cược"
- device_name: "PhoneA"
- expected_amount: 4000
```

**Response:**
```json
{
  "verified": true,
  "confidence": 1.0,
  "detected_amount": 4000,
  "expected_amount": 4000,
  "needs_popup_verify": false,
  "screenshot_path": "mobile_images/verify_quick/..."
}
```

**Nếu FAIL:**
```json
{
  "verified": false,
  "confidence": 0.3,
  "detected_amount": 2000,
  "expected_amount": 4000,
  "needs_popup_verify": true,
  "screenshot_path": "..."
}
```

---

### 3. POST `/api/mobile/verify-popup` 🔍 POPUP VERIFY

**Mục đích:** Verify chắc chắn 100% qua popup lịch sử (fallback)

**Request:**
```bash
POST https://lukistar.space/api/mobile/verify-popup
Content-Type: multipart/form-data

Parameters:
- file: Screenshot popup lịch sử
- device_name: "PhoneA"
- expected_amount: 4000
- expected_method: "Tài"
- current_session: "#526653" (optional)
```

**Response:**
```json
{
  "verified": true,
  "confidence": 1.0,
  "session_match": true,
  "amount_match": true,
  "method_match": true,
  "status": "pending_result",
  "detected_session": "#526653",
  "detected_amount": 4000,
  "detected_method": "Tài",
  "mismatch_details": null,
  "screenshot_path": "..."
}
```

**Nếu MISMATCH:**
```json
{
  "verified": false,
  "confidence": 0.33,
  "session_match": true,
  "amount_match": false,
  "method_match": true,
  "status": "pending_result",
  "detected_session": "#526653",
  "detected_amount": 2000,
  "detected_method": "Tài",
  "mismatch_details": "Expected 4000, got 2000",
  "screenshot_path": "..."
}
```

---

### 4. GET `/api/mobile/history` 📜 LỊCH SỬ

**Request:**
```bash
GET https://lukistar.space/api/mobile/history?limit=50
```

**Response:**
```json
{
  "success": true,
  "total": 25,
  "history": [
    {
      "id": 1,
      "device_name": "PhoneA",
      "betting_method": "Tài",
      "session_id": "#526653",
      "image_type": "HISTORY",
      "bet_amount": 2000,
      "win_loss": "Thua",
      "multiplier": 4.0,
      "created_at": "2025-11-05 15:30:00"
    }
  ]
}
```

---

### 5. GET `/api/mobile/device-state/{device_name}` 🔧 DEVICE STATE

**Request:**
```bash
GET https://lukistar.space/api/mobile/device-state/PhoneA
```

**Response:**
```json
{
  "success": true,
  "state": {
    "device_name": "PhoneA",
    "lose_streak_count": 2,
    "rest_mode": false,
    "rest_counter": 0,
    "last_lost_bet_amount": 0,
    "betting_method": "Tài",
    "last_session_id": "#526653"
  }
}
```

---

## 🔄 WORKFLOW CHO MOBILE APP

### **Workflow 1: Lấy Multiplier (Mỗi 20 phút)**

```
1. Chờ đến giây 50-55
2. Tap "Mở popup lịch sử"
3. Capture popup screenshot
4. Tap "Đóng popup"
5. POST /api/mobile/analyze
   - file: popup screenshot
   - device_name: "PhoneA"
   - betting_method: "Tài"
6. Nhận JSON response:
   - multiplier: 4.0
   - verification.required: false
   - device_state.lose_streak: 2
7. Nếu multiplier > 0:
   → Tiếp tục Workflow 2
   Nếu multiplier = 0:
   → Skip, đợi 20 phút
```

---

### **Workflow 2: Thực Hiện Cược (Nếu multiplier > 0)**

```
1. Check giây còn lại >= 10
2. Reset số tiền (nếu cần)
3. Tap "Mở cược Tài/Xỉu"
4. Delay random (1500-2500ms)
5. Loop tap "1K" x multiplier:
   - Tap "1K" với random offset ±2px
   - Delay random (700-1300ms)
   - OCR verify số tiền sau mỗi lần tap
   - Nếu sai → retry
6. Tap "Đặt cược"
7. Delay random (1600-2400ms)
8. Tiếp tục Workflow 3 (Quick Verify)
```

---

### **Workflow 3: Quick Verify (Sau khi cược)**

```
1. Capture màn hình
2. POST /api/mobile/verify-quick
   - file: screenshot
   - device_name: "PhoneA"
   - expected_amount: 4000
3. Nhận response:
   - verified: true
   - confidence: 1.0
   - needs_popup_verify: false
4. Nếu verified = true && confidence >= 0.85:
   → ✅ Done, đợi 20 phút
   Nếu confidence < 0.85:
   → Tiếp tục Workflow 4
```

---

### **Workflow 4: Popup Verify (Fallback - Nếu cần)**

```
1. Tap "Mở popup lịch sử"
2. Delay 2000ms
3. Capture popup
4. Tap "Đóng popup"
5. POST /api/mobile/verify-popup
   - file: popup screenshot
   - device_name: "PhoneA"
   - expected_amount: 4000
   - expected_method: "Tài"
6. Nhận response:
   - verified: true
   - confidence: 1.0
   - amount_match: true
   - method_match: true
7. Nếu verified = true:
   → ✅ CONFIRMED
   Nếu verified = false:
   → ❌ Alert, log mismatch
```

---

## 🎯 DECISION TREE

```
Nhận multiplier từ /analyze
    ↓
multiplier = 0?
├─ YES → Skip, đợi 20 phút
└─ NO → Continue
    ↓
Thực hiện cược với random offset + delays
    ↓
Quick verify (/verify-quick)
    ↓
confidence >= 0.85?
├─ YES → Done ✅
└─ NO → Popup verify (/verify-popup)
    ↓
verified = true?
├─ YES → Done ✅
└─ NO → Alert + Log mismatch ❌
```

---

## 📊 PROMPTS CHI TIẾT

### **Prompt 1: Detection (Loại ảnh)**
```
Detect xem là POPUP LỊCH SỬ hay MÀN HÌNH CƯỢC

POPUP:
- Có tiêu đề "LỊCH SỬ CƯỢC"
- Bảng 5 cột
- Nhiều dòng

MÀN HÌNH:
- Chữ TÀI XỈU lớn
- Vòng tròn số giây
- Nút 1K, 10K...
```

### **Prompt 2: Popup Lịch Sử (Nếu detect HISTORY)**
```
Đọc CHỈ dòng ĐẦU TIÊN:

Format:
Phiên: #[số]
Thời gian: DD-MM-YYYY HH:MM:SS
Tổng cược: [số]
Tiền thắng: [+số / -số / -]
Chi tiết: Đặt Tài/Xỉu...

Lưu ý:
- Tiền thắng = "-" → Đang chờ
- Tiền thắng = "+số" → Thắng
- Tiền thắng = "-số" → Thua
```

### **Prompt 3: Màn Hình Cược (Nếu detect BETTING)**
```
Đọc:
Giây: [số vàng trong vòng tròn]
Tiền cược: [số trắng dưới TÀI/XỈU]
Trạng thái: Đã cược / Chưa cược

KHÔNG đọc số phiên (không chính xác)
```

### **Prompt 4: Quick Verify**
```
Đọc số tiền đã cược:
Tiền cược: [số]

Chỉ 1 dòng, siêu ngắn gọn.
```

### **Prompt 5: Popup Verify**
```
Đọc dòng đầu popup:
Phiên: #[số]
Tổng cược: [số]
Tiền thắng: [+/-/- ]
Chi tiết: Đặt Tài/Xỉu...
```

---

## 🧮 LOGIC TÍNH HỆ SỐ CƯỢC

### Quy Tắc 1: Chưa có kết quả
```python
if win_loss is None:
    return 0.0
```

### Quy Tắc 2: Server lỗi
```python
if not win_loss or win_loss not in ['Thắng', 'Thua']:
    return 0.0
```

### Quy Tắc 3: Thắng
```python
if win_loss == 'Thắng':
    multiplier = 1.0
    lose_streak_count = 0  # Reset
    return 1.0
```

### Quy Tắc 4: Thua
```python
if win_loss == 'Thua':
    lose_streak_count += 1
    multiplier = (bet_amount * 2) / 1000
    return multiplier

# Ví dụ:
# Thua 1000 → (1000 * 2) / 1000 = 2
# Thua 2000 → (2000 * 2) / 1000 = 4
# Thua 4000 → (4000 * 2) / 1000 = 8
```

### Quy Tắc 5: Thua 4 liên tiếp → Nghỉ 3 phiên
```python
if lose_streak_count >= 4:
    rest_mode = True
    rest_counter = 0
    last_lost_bet_amount = bet_amount
    multiplier = (bet_amount * 2) / 1000
    # Nhưng 3 phiên sau sẽ trả về 0

# Trong rest_mode:
if rest_mode:
    rest_counter += 1
    
    if rest_counter >= 3:
        # Hết nghỉ
        rest_mode = False
        multiplier = (last_lost_bet_amount * 2) / 1000
    else:
        # Vẫn nghỉ
        multiplier = 0.0
```

---

## 📊 DATABASE TABLES

### Table: `mobile_device_states`
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
```sql
id INTEGER PRIMARY KEY
device_name TEXT
betting_method TEXT
session_id TEXT
image_type TEXT (HISTORY/BETTING)
seconds_remaining INTEGER
bet_amount INTEGER
bet_status TEXT
win_loss TEXT (Thắng/Thua/null)
multiplier REAL
image_path TEXT
chatgpt_response TEXT
verification_method TEXT (quick/popup/none)
confidence_score REAL (0-1)
verified_at TIMESTAMP
mismatch_detected BOOLEAN
actual_bet_amount INTEGER
retry_count INTEGER
verification_screenshot_path TEXT
error_message TEXT
created_at TIMESTAMP

Limit: 100 records (auto cleanup)
```

### Table: `bet_verification_logs`
```sql
id INTEGER PRIMARY KEY
device_name TEXT
session_id TEXT
verification_type TEXT (quick/popup)
expected_amount INTEGER
detected_amount INTEGER
confidence REAL
match_status BOOLEAN
screenshot_path TEXT
chatgpt_response TEXT
created_at TIMESTAMP
```

### Table: `bet_mismatches`
```sql
id INTEGER PRIMARY KEY
device_name TEXT
session_id TEXT
expected_amount INTEGER
actual_amount INTEGER
expected_method TEXT
actual_method TEXT
detected_at TIMESTAMP
resolved BOOLEAN
resolution_action TEXT
```

---

## 🎯 CONFIDENCE SCORING

### Quick Verify (Màn hình cược):
```
Checks:
✅ Số tiền khớp → +1 point

Confidence:
- 1/1 passed = 1.0 (100%)
- 0/1 passed = 0.0 (0%)

Threshold: 0.85
→ Nếu < 0.85 → needs_popup_verify = true
```

### Popup Verify (Popup lịch sử):
```
Checks:
✅ Số tiền khớp → +1 point
✅ Method khớp (Tài/Xỉu) → +1 point
✅ Status = pending ("-") → +1 point

Confidence:
- 3/3 passed = 1.0 (100%) ✅ VERIFIED
- 2/3 passed = 0.67 (67%) ⚠️ Warning
- 1/3 passed = 0.33 (33%) ❌ Failed

Threshold: 0.8
```

---

## ⚠️ MISMATCH HANDLING

### Khi phát hiện mismatch:

**Server tự động:**
1. Log vào `bet_mismatches` table
2. Log vào `bet_verification_logs`
3. Gọi `handle_mismatch()` method
4. (Optional) Gửi alert (nếu config)

**Response vẫn trả về:**
```json
{
  "verified": false,
  "mismatch_details": "Expected 4000, got 2000",
  "detected_amount": 2000,
  "actual_amount": 2000
}
```

**Mobile nhận được và:**
- Log error
- Alert user
- Có thể retry hoặc skip

---

## 🛡️ ANTI-DETECTION FEATURES (Mobile)

Đã được integrate vào prompt Android:

### 1. Random Pixel Offset
```kotlin
tapAt(x, y) → tapAt(x±2, y±2)
```

### 2. Random Delays
```kotlin
Base: 1000ms → Actual: 700-1300ms
Base: 2000ms → Actual: 1500-2500ms
```

### 3. Human-like Pauses
```kotlin
10% chance → Long pause 3-5s
```

---

## ⏱️ TIMING GUIDELINES

### Capture Time:
```
✅ Ideal: Giây 50-55
✅ Safe: Giây 30-55
⚠️ Warning: Giây 10-30
❌ Danger: Giây 0-10 (bao gồm 0-5 bị chặn)
```

### Action Time:
```
✅ Start betting: Giây >= 10
⚠️ Complete betting: Cần ít nhất 10s buffer
❌ KHÔNG tap: Giây <= 5 (bị chặn)
```

### Verification Time:
```
Quick verify: Giây 38-35 (sau tap "Đặt cược")
Popup verify: Giây 30-25 (nếu cần)
```

---

## 📝 EXAMPLE USE CASE

### Scenario: Mobile auto-betting

```
[Giây 55] POST popup screenshot → /analyze
Response: multiplier = 4, win_loss = "Thua"

[Giây 48] Nhận multiplier = 4
Decision: Cược 4000

[Giây 45] Check giây = 45 >= 10 ✅
[Giây 45] Tap Tài (300+random, 500+random)
[Giây 43] Tap 1K lần 1 (random offset)
[Giây 42] OCR: 1000 ✅
[Giây 41] Tap 1K lần 2
[Giây 40] OCR: 2000 ✅
[Giây 39] Tap 1K lần 3
[Giây 38] OCR: 3000 ✅
[Giây 37] Tap 1K lần 4
[Giây 36] OCR: 4000 ✅
[Giây 35] Tap "Đặt cược"
[Giây 33] Delay random

[Giây 33] POST screenshot → /verify-quick
Response: verified = true, confidence = 1.0

[Giây 32] Done ✅, đợi 20 phút
```

---

## 🚨 ERROR SCENARIOS

### Scenario 1: Quick verify fail
```
confidence < 0.85
→ needs_popup_verify = true
→ Mobile thực hiện Workflow 4 (popup verify)
```

### Scenario 2: Popup verify mismatch
```
Expected: 4000
Detected: 2000
→ Server log mismatch
→ Mobile alert user
→ Có thể retry vòng sau
```

### Scenario 3: Giây quá ít
```
Giây = 5
→ DANGER ZONE
→ Mobile skip, không tap
→ Đợi vòng sau
```

### Scenario 4: Server timeout
```
ChatGPT > 30s
→ Timeout exception
→ Mobile retry 1 lần
→ Nếu vẫn fail → skip vòng này
```

---

## ✅ TESTING

### Test với curl:

**Test analyze (popup):**
```bash
curl -X POST https://lukistar.space/api/mobile/analyze \
  -F "file=@popup_history.jpg" \
  -F "device_name=TestPhone" \
  -F "betting_method=Tài"
```

**Test verify-quick:**
```bash
curl -X POST https://lukistar.space/api/mobile/verify-quick \
  -F "file=@after_bet.jpg" \
  -F "device_name=TestPhone" \
  -F "expected_amount=4000"
```

**Test verify-popup:**
```bash
curl -X POST https://lukistar.space/api/mobile/verify-popup \
  -F "file=@popup_verify.jpg" \
  -F "device_name=TestPhone" \
  -F "expected_amount=4000" \
  -F "expected_method=Tài"
```

---

## 🎓 BEST PRACTICES

### 1. Always check seconds before action
```kotlin
if (seconds <= 10) {
    skip()
}
```

### 2. Use random offsets
```kotlin
tapAt(x + random(-2, 2), y + random(-2, 2))
```

### 3. Verify after each critical action
```kotlin
tap1K()
delay(random)
verify() // OCR số tiền
```

### 4. Fallback to popup verify when unsure
```kotlin
if (confidence < 0.85 || multiplier >= 8) {
    popupVerify()
}
```

### 5. Log everything
```kotlin
log("Every action, every result, every error")
```

---

## 📞 SUPPORT

### Admin Dashboard:
```
https://lukistar.space/admin → "📱 Run Mobile"
```

### Xem logs:
```bash
tail -f /home/myadmin/screenshot-analyzer/server.log | grep "Mobile"
```

### Check database:
```bash
sqlite3 logs.db "SELECT * FROM mobile_analysis_history ORDER BY created_at DESC LIMIT 10"
```

---

**Server đã sẵn sàng! Mobile có thể bắt đầu gửi request!** 🚀✅

