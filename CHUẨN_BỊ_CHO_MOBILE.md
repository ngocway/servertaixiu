# 📱 CHUẨN BỊ CHO MOBILE APP - CHECKLIST

## ✅ SERVER ĐÃ SẴNSÀNG

**Status:** ✅ HOÀN THÀNH  
**API:** ✅ 5 endpoints sẵn sàng  
**Database:** ✅ Khởi tạo xong  
**Documentation:** ✅ Đầy đủ  

---

## 📋 CHECKLIST CHO BẠN (DEV)

### 1. Chuẩn Bị Screenshots (5-10 phút)

Cần chụp 2 loại ảnh từ game:

#### ☐ Screenshot 1: Popup Lịch Sử
```
Mô tả:
- Popup có tiêu đề "LỊCH SỬ CƯỢC"
- Bảng 5 cột
- Có ít nhất 2-3 dòng

Cách chụp:
1. Mở game
2. Tap nút "Lịch sử" hoặc icon tương tự
3. Popup hiện ra
4. Screenshot
5. Lưu: "popup_history.jpg"
```

#### ☐ Screenshot 2: Màn Hình Cược (Có Số Tiền)
```
Mô tả:
- Màn hình chính game
- Có chữ TÀI và XỈU
- Số giây trong vòng tròn (vd: 42)
- Số tiền màu trắng dưới TÀI/XỈU (vd: 2,000)

Cách chụp:
1. Đặt cược bất kỳ (vd: 2000)
2. Sau khi text "Đặt cược thành công!" xuất hiện
3. Screenshot ngay (trong 3s)
4. Lưu: "betting_screen_with_money.jpg"
```

#### ☐ Thông Tin Device
```
- Độ phân giải màn hình: _____x_____ px
  (Settings → Display → Screen resolution)
  
Ví dụ: 1080x2400, 1080x2340, 1440x3200...
```

---

### 2. Xác Định Tọa Độ Crop (10-15 phút)

**LƯU Ý:** Bạn CHỈ CẦN làm nếu muốn CHỈNH SỬA tỷ lệ crop mặc định.

#### Tỷ lệ mặc định (đã hard-code):
```
Vùng số tiền:
- X: 25% từ trái
- Y: 55% từ trên
- Width: 15%
- Height: 5%

Vùng số giây:
- X: 45% từ trái (giữa)
- Y: 45% từ trên (giữa)
- Width: 10%
- Height: 8%

→ Có thể dùng luôn, không cần adjust!
```

#### Nếu muốn adjust (optional):

**Tool:** Paint / Photoshop / https://www.pixelmap.amcharts.com/

**Cách làm:**
1. Mở "betting_screen_with_money.jpg"
2. Dùng Rectangle Select tool
3. Chọn vùng số tiền (số trắng "2,000")
4. Xem tọa độ: X, Y, Width, Height
5. Tính tỷ lệ:
   - xRatio = X / screenWidth
   - yRatio = Y / screenHeight
   - widthRatio = Width / screenWidth
   - heightRatio = Height / screenHeight
6. Update trong Constants.kt

---

### 3. Test Server API (5 phút)

#### ☐ Test với curl:

```bash
# Test analyze với popup history
curl -X POST https://lukistar.space/api/mobile/analyze \
  -F "file=@popup_history.jpg" \
  -F "device_name=TestPhone" \
  -F "betting_method=Tài"

# Kết quả mong đợi:
# → JSON với multiplier
# → session_id chính xác
# → win_loss = Thắng/Thua/null
```

```bash
# Test analyze với màn hình cược
curl -X POST https://lukistar.space/api/mobile/analyze \
  -F "file=@betting_screen.jpg" \
  -F "device_name=TestPhone" \
  -F "betting_method=Tài"

# Kết quả mong đợi:
# → JSON với seconds, bet_amount
# → session_id = null (không đọc từ màn hình)
# → note: "Session ID không chính xác..."
```

```bash
# Test verify-quick
curl -X POST https://lukistar.space/api/mobile/verify-quick \
  -F "file=@betting_screen_with_money.jpg" \
  -F "device_name=TestPhone" \
  -F "expected_amount=2000"

# Kết quả mong đợi:
# → verified: true/false
# → confidence: 0-1
# → detected_amount vs expected_amount
```

---

### 4. Xác Định 6 Tọa Độ TAP (10-15 phút)

#### Cách tìm tọa độ tap:

**Option 1: Developer Options (Khuyến nghị)**
```
1. Settings → About Phone → Tap "Build number" 7 lần
2. Settings → Developer Options
3. Bật "Show taps" và "Pointer location"
4. Mở game
5. Tap vào mỗi nút
6. Xem tọa độ hiện ở góc trên màn hình
7. Note lại (x, y) cho 6 nút
```

**Option 2: ADB + Layout Inspector**
```
1. Connect device qua ADB
2. Android Studio → Tools → Layout Inspector
3. Capture screen
4. Click vào từng nút
5. Xem coordinates
```

#### ☐ 6 Tọa Độ Cần Tìm:

```
1. Mở popup lịch sử: (x: ____, y: ____)
2. Đóng popup lịch sử: (x: ____, y: ____)
3. Mở cược Tài: (x: ____, y: ____)
4. Mở cược Xỉu: (x: ____, y: ____)
5. Đặt 1K: (x: ____, y: ____)
6. Đặt cược: (x: ____, y: ____)
```

**Tips:**
- Tap vài lần để đảm bảo tọa độ chính xác
- Test từng nút riêng lẻ
- Note lại screenshot có đánh dấu vị trí

---

### 5. Generate Android App (5 phút)

#### ☐ Bước thực hiện:

```
1. Mở Android Studio
2. Tools → Gemini
3. Copy TOÀN BỘ nội dung file: GEMINI_PROMPT_FINAL.md
4. Paste vào Gemini chat
5. Gemini sẽ generate code (3-5 phút)
6. Review code
7. Build project
```

---

### 6. Setup App (10 phút)

#### ☐ Sau khi build xong:

```
1. Install APK lên device
2. Mở app
3. Settings → Accessibility → Bật "Auto Betting Service"
4. App request Screen Capture permission → Allow
5. Nhập Device Name (vd: "PhoneA")
6. Chọn Betting Method từ dropdown ("Tài" hoặc "Xỉu")
7. Nhập 6 tọa độ (format: x:y)
   - Mở popup lịch sử: 100:200
   - Đóng popup: 100:300
   - Mở Tài: 300:500
   - Mở Xỉu: 600:500
   - Đặt 1K: 450:700
   - Đặt cược: 450:800
8. Ấn "💾 Lưu Tọa Độ"
9. Toast: "✅ Đã lưu tọa độ"
```

---

### 7. Test Thử (15 phút)

#### ☐ Test Mode:

```
1. Bật switch "🧪 Test Mode"
2. Mở game Tài Xỉu
3. Ấn "▶️ Bắt Đầu"
4. Xem logs trong app:
   - [HH:mm:ss] Giây: 42
   - [HH:mm:ss] Tap Mở popup...
   - [HH:mm:ss] Captured popup
   - [HH:mm:ss] Multiplier: 4.0
   - [HH:mm:ss] Sẽ cược: 4000
   - [HH:mm:ss] Tap Mở Tài...
   - [HH:mm:ss] Tap 1K lần 1/4...
   - ...
5. Verify: Không tap thật (Test Mode)
6. Check logs đầy đủ
```

#### ☐ Test Thật:

```
1. Tắt "Test Mode"
2. Mở game
3. Ấn "▶️ Bắt Đầu"
4. Quan sát:
   - App tự tap mở popup
   - Tự chụp ảnh
   - Tự đóng popup
   - Đợi... (upload + server analyze)
   - Tự tap cược (nếu multiplier > 0)
   - Tự verify
5. Check trong game: Đã cược đúng chưa?
6. Mở popup lịch sử: Dòng đầu có số tiền đúng không?
```

---

### 8. Monitor & Debug (Ongoing)

#### ☐ Xem Admin Dashboard:
```
URL: https://lukistar.space/admin
Click: "📱 Run Mobile"

Xem:
- Số thiết bị đang hoạt động
- Tổng số phân tích
- Lịch sử 100 records
- Verification status
- Mismatches (nếu có)
```

#### ☐ Check Logs Server:
```bash
# Xem logs real-time
tail -f /home/myadmin/screenshot-analyzer/server.log | grep "Mobile"

# Xem verification logs
tail -f /home/myadmin/screenshot-analyzer/server.log | grep "Verify"

# Xem errors
tail -f /home/myadmin/screenshot-analyzer/server.log | grep "Error"
```

#### ☐ Check Database:
```bash
# Vào server
ssh myadmin@lukistar.space

# Query history
sqlite3 /home/myadmin/screenshot-analyzer/logs.db \
  "SELECT * FROM mobile_analysis_history ORDER BY created_at DESC LIMIT 5"

# Query mismatches
sqlite3 /home/myadmin/screenshot-analyzer/logs.db \
  "SELECT * FROM bet_mismatches ORDER BY detected_at DESC LIMIT 5"
```

---

## 🎯 EXPECTED RESULTS

### Chu kỳ 1 (lần đầu):
```
[20:00] WorkManager trigger
[20:00] Wait until giây 50-55...
[20:01] Giây 52 → Capture popup
[20:03] Upload popup → Analyze
[20:05] Nhận: multiplier = 1 (hoặc 0)
[20:06] Nếu > 0: Execute betting
[20:08] Quick verify → confidence 1.0
[20:09] Done
[20:20] Trigger lại (20 phút sau)
```

### Chu kỳ 2-N (tiếp theo):
```
[20:20] Trigger
[20:21] Capture popup
[20:23] Nhận multiplier (dựa vào kết quả vòng 1)
[20:25] Execute + Verify
[20:27] Done
[20:40] Trigger lại...
```

---

## 📞 TROUBLESHOOTING

### Vấn đề 1: App không tap
```
Nguyên nhân:
- Accessibility Service chưa bật

Giải pháp:
- Settings → Accessibility → Bật service
```

### Vấn đề 2: OCR sai số tiền
```
Nguyên nhân:
- Tỷ lệ crop sai
- Font game đặc biệt

Giải pháp:
- Adjust Constants.MONEY_X_RATIO, etc.
- Chụp screenshot crop area để verify
```

### Vấn đề 3: Multiplier = 0 mãi
```
Nguyên nhân:
- Server không đọc được kết quả
- Ảnh mờ

Giải pháp:
- Xem logs server
- Check ChatGPT response
- Chụp ảnh rõ hơn
```

### Vấn đề 4: Verify fail
```
Nguyên nhân:
- Tọa độ tap sai
- Timing sai

Giải pháp:
- Test từng nút riêng
- Check timing (giây còn lại)
- Xem verification logs
```

---

## 🎁 FILES ĐÍNH KÈM

```
✅ GEMINI_PROMPT_FINAL.md
   → Copy paste vào Gemini để generate app

✅ MOBILE_API_COMPLETE.md
   → API documentation đầy đủ

✅ SERVER_UPDATES_SUMMARY.md
   → Tổng kết thay đổi server

✅ RUN_MOBILE_GUIDE.md
   → Hướng dẫn sử dụng

✅ CHUẨN_BỊ_CHO_MOBILE.md (file này)
   → Checklist từng bước
```

---

## ⏱️ TIMELINE ƯỚC TÍNH

```
┌─────────────────────────────────────────┐
│ 1. Chuẩn bị screenshots: 5-10 phút     │
├─────────────────────────────────────────┤
│ 2. Xác định tọa độ crop: 0 phút        │
│    (Dùng mặc định)                      │
├─────────────────────────────────────────┤
│ 3. Test server API: 5 phút             │
├─────────────────────────────────────────┤
│ 4. Xác định 6 tọa độ tap: 10-15 phút   │
├─────────────────────────────────────────┤
│ 5. Gemini generate app: 5 phút         │
├─────────────────────────────────────────┤
│ 6. Build & install: 5 phút             │
├─────────────────────────────────────────┤
│ 7. Setup app: 10 phút                  │
├─────────────────────────────────────────┤
│ 8. Test thử: 15 phút                   │
└─────────────────────────────────────────┘

TỔNG: ~60-75 phút (1 tiếng)
```

---

## 🚀 BƯỚC TIẾP THEO

### Ngay Bây Giờ:

1. ☐ Chụp 2 screenshots từ game
2. ☐ Test server API với screenshots đó
3. ☐ Note độ phân giải màn hình
4. ☐ Xác định 6 tọa độ tap

### Sau Đó:

5. ☐ Copy prompt từ GEMINI_PROMPT_FINAL.md
6. ☐ Paste vào Gemini → Generate app
7. ☐ Build & Install
8. ☐ Setup & Test

### Cuối Cùng:

9. ☐ Run thật với game
10. ☐ Monitor qua Admin Dashboard
11. ☐ Adjust nếu cần

---

## 📝 NOTES

### Server URL (Đã sẵn sàng):
```
Base: https://lukistar.space/

Endpoints:
✅ POST /api/mobile/analyze
✅ POST /api/mobile/verify-quick
✅ POST /api/mobile/verify-popup
✅ GET  /api/mobile/history
✅ GET  /api/mobile/device-state/{device}
```

### Admin Dashboard:
```
https://lukistar.space/admin
→ Click "📱 Run Mobile"
→ Xem stats, history, mismatches
```

### Support:
```
- Đọc: MOBILE_API_COMPLETE.md (API docs)
- Đọc: RUN_MOBILE_GUIDE.md (User guide)
- Logs: tail -f server.log | grep Mobile
```

---

## ✅ SERVER STATUS

```
Service: ✅ Active
Endpoints: ✅ Ready (5/5)
Database: ✅ Initialized
Prompts: ✅ Updated
Verification: ✅ Implemented
Anti-detection: ✅ Supported
Documentation: ✅ Complete
```

---

**BẠN ĐÃ SẴN SÀNG TẠO MOBILE APP!** 🎉

**Bước đầu tiên: Chụp 2 screenshots và test API** 📸✨

