# 📱 PROMPT CHO GEMINI - ANDROID AUTO BETTING APP

## 🎯 PASTE TOÀN BỘ PROMPT NÀY VÀO GEMINI

---

```
Tạo một Android project hoàn chỉnh bằng KOTLIN với kiến trúc MVVM:

═══════════════════════════════════════════════════════════════════
📋 LUỒNG XỬ LÝ TỔNG QUAN (ĐỌC KỸ TRƯỚC KHI CODE)
═══════════════════════════════════════════════════════════════════

**PHASE 1: SETUP BAN ĐẦU**
```
User mở app → Nhập thông tin:
├─ Device name: "PhoneA"
├─ Dropdown chọn: "Tài" hoặc "Xỉu"
└─ 6 tọa độ (format x:y):
   ├─ Mở popup lịch sử: "100:200"
   ├─ Đóng popup lịch sử: "100:300"
   ├─ Mở cược Tài: "300:500"
   ├─ Mở cược Xỉu: "600:500"
   ├─ Đặt 1K: "450:700"
   └─ Đặt cược: "450:800"

User ấn "💾 Lưu Tọa Độ"
→ Save vào SharedPreferences
→ Toast: "✅ Đã lưu"

User ấn "▶️ Bắt Đầu"
→ Check Accessibility Service (nếu chưa → Dialog hướng dẫn bật)
→ Schedule WorkManager (trigger mỗi 20 phút)
→ UI: Button "Dừng" enabled, Status = "Đang chạy"
```

**PHASE 2: CHU KỲ 20 PHÚT (Tự động lặp lại)**
```
[00:00] WorkManager trigger
        ↓
[00:01] Start BettingForegroundService
        Show notification: "Đang chạy auto betting..."
        ↓
[00:02] Execute logic - Đợi đến giây ideal (50-55)
        Loop: Capture screen → OCR số giây
        │
        ├─ Nếu giây 0-5 (DANGER ZONE): Đợi vòng mới (delay 6s)
        ├─ Nếu giây 6-10: Quá sát, skip vòng này
        ├─ Nếu giây > 55: Đợi đến 50-55
        └─ Nếu giây 50-55: ✅ Perfect! Continue
        ↓
[00:05] Giây = 52 → Bắt đầu capture popup
        ↓
[00:05] CAPTURE POPUP LỊCH SỬ:
        ├─ Tap "Mở popup" (với random offset ±2px)
        ├─ Delay random: 1700-2300ms
        ├─ Screenshot popup → Save "popup_timestamp.jpg"
        ├─ Tap "Đóng popup" (với random offset)
        └─ Delay random: 300-700ms
        ↓
[00:08] UPLOAD LÊN SERVER:
        POST https://lukistar.space/api/mobile/analyze
        ├─ file: popup screenshot
        ├─ device_name: "PhoneA"
        └─ betting_method: "Tài"
        ↓
[00:10] SERVER XỬ LÝ (3-5 giây):
        ├─ ChatGPT OCR dòng đầu popup
        ├─ Extract: Phiên, Số lượng, Kết quả (+/-/-)
        ├─ Map: Positive→Thắng, Negative→Thua, Pending→null
        ├─ Calculate multiplier theo 5 quy tắc
        └─ Check device state (lose_streak, rest_mode)
        ↓
[00:13] NHẬN JSON TỪ SERVER:
        {
          "multiplier": 4.0,
          "win_loss": "Thua",
          "verification": { "required": false },
          "device_state": { "lose_streak": 2, "rest_mode": false }
        }
        ↓
[00:13] QUYẾT ĐỊNH:
        ├─ Nếu multiplier = 0: 
        │  → Skip, không cược
        │  → Log: "Nghỉ vòng này"
        │  → Stop service
        │  → Đợi 20 phút tiếp
        │
        └─ Nếu multiplier > 0 (vd: 4.0):
           → betAmount = 1000 × 4 = 4000
           → tapCount = 4 lần
           → Continue Phase 3
```

**PHASE 3: THỰC HIỆN CƯỢC (Nếu multiplier > 0)**
```
[00:14] CHECK VÀ RESET SỐ TIỀN:
        ├─ Capture screen → OCR số tiền hiện tại
        ├─ Nếu currentMoney > 0:
        │  ├─ Tap nút đối diện (Tài→Xỉu hoặc ngược lại)
        │  ├─ Delay random: 300-700ms
        │  ├─ Tap lại nút đúng
        │  ├─ Delay random: 300-700ms
        │  └─ Verify: OCR lại → Phải = 0
        └─ Nếu = 0: OK, tiếp tục
        ↓
[00:15] TAP MỞ CƯỢC (Tài hoặc Xỉu):
        ├─ Chọn tọa độ: openBetTaiX/Y hoặc openBetXiuX/Y
        ├─ Tap với random offset: (300±2, 500±2)
        ├─ Log: "Tap Mở Tài (301, 502)"
        └─ Delay random: 1500-2500ms
        ↓
[00:17] LOOP TAP "1K" VỚI REAL-TIME VERIFY:
        For i = 1 to 4:
           ├─ Safety check (giây >= 6)
           ├─ Tap "1K" (450±2, 700±2)
           ├─ Delay random: 700-1300ms (vd: 892ms)
           ├─ Capture screen
           ├─ OCR số tiền → detected
           ├─ expected = i × 1000 (vd: lần 1 = 1000)
           ├─ Verify: detected == expected?
           │  ├─ YES: ✅ Continue
           │  └─ NO: ⚠️ Retry 1 lần
           │     ├─ Delay random: 300-700ms
           │     ├─ Tap lại "1K"
           │     ├─ OCR lại
           │     └─ Nếu vẫn sai: ❌ Dừng, return false
           └─ Next i...
        
        Kết quả sau loop:
        ├─ Lần 1: 1000 ✅
        ├─ Lần 2: 2000 ✅
        ├─ Lần 3: 3000 ✅
        └─ Lần 4: 4000 ✅
        ↓
[00:22] TAP "ĐẶT CƯỢC":
        ├─ Tap với random offset: (450±2, 800±2)
        ├─ Log: "Tap Đặt cược (451, 802)"
        └─ Delay random: 1600-2400ms (vd: 2187ms)
```

**PHASE 4: VERIFICATION (Kiểm tra cược đúng chưa)**
```
[00:24] QUICK VERIFICATION:
        ├─ Capture screen sau khi tap "Đặt cược"
        ├─ Save: "verify_timestamp.jpg"
        ├─ POST https://lukistar.space/api/mobile/verify-quick
        │  ├─ file: screenshot
        │  ├─ device_name: "PhoneA"
        │  └─ expected_amount: 4000
        ↓
[00:26] Server OCR số tiền:
        ├─ ChatGPT đọc: "Số lượng: 4000"
        ├─ detected_amount = 4000
        ├─ expected_amount = 4000
        ├─ Match? YES ✅
        └─ Confidence = 1.0 (100%)
        ↓
[00:27] Nhận response:
        {
          "verified": true,
          "confidence": 1.0,
          "detected_amount": 4000,
          "expected_amount": 4000,
          "needs_popup_verify": false
        }
        ↓
[00:27] QUYẾT ĐỊNH:
        ├─ Nếu verified = true && confidence >= 0.85:
        │  → ✅ VERIFIED! Done!
        │  → Log: "✅ Quick verify OK"
        │  → Skip popup verify
        │  → Update notification: "✅ Cược thành công: 4000"
        │  → Stop service
        │  → PHASE 5 (chờ 20 phút)
        │
        └─ Nếu confidence < 0.85:
           → ⚠️ Không chắc chắn
           → Continue Phase 4B (Popup verify)
```

**PHASE 4B: POPUP VERIFY (Fallback - nếu quick verify không chắc)**
```
[00:28] MỞ POPUP LẦN 2 (để verify chắc chắn):
        ├─ Tap "Mở popup lịch sử"
        ├─ Delay: 1700-2300ms
        ├─ Capture popup
        ├─ Tap "Đóng popup"
        └─ Save: "popup_verify_timestamp.jpg"
        ↓
[00:30] POST https://lukistar.space/api/mobile/verify-popup
        ├─ file: popup screenshot
        ├─ device_name: "PhoneA"
        ├─ expected_amount: 4000
        ├─ expected_method: "Tài"
        └─ current_session: ""
        ↓
[00:32] Server OCR dòng đầu popup:
        ├─ Extract: Phiên #526653, Số lượng 4000, Kết quả "-"
        ├─ Verify: amount_match, method_match, pending_status
        └─ Confidence = 1.0 (100%)
        ↓
[00:33] Nhận response:
        {
          "verified": true,
          "confidence": 1.0,
          "amount_match": true,
          "method_match": true,
          "status": "pending_result"
        }
        ↓
[00:33] Result: ✅ CONFIRMED 100%
        → Update notification: "✅ Verified: 4000 Tài"
        → Log: "✅ Popup verify: true"
        → Stop service
```

**PHASE 5: ĐỢI CHU KỲ TIẾP THEO**
```
[00:34] Service stopped
        Notification: "✅ Cược thành công: 4000"
        ↓
[00:34 - 00:54] Chờ (20 phút)
        WorkManager đang đợi...
        ↓
[00:54] WorkManager trigger lại
        → Quay lại PHASE 2
        → Loop vô tận cho đến khi user ấn "⏹️ Dừng"
```

**ERROR SCENARIOS (Xử lý khi có lỗi)**
```
Scenario 1: OCR số tiền sai trong loop tap 1K
[00:17] Tap 1K lần 2
[00:18] OCR: detected = 1000, expected = 2000 ❌
        → Retry: Tap lại lần 2
        → Delay random
        → OCR lại: 2000 ✅
        → Continue

Scenario 2: Retry vẫn fail
[00:18] Retry OCR: detected = 1000, expected = 2000 ❌
        → Log: "❌ Retry FAIL, dừng cược"
        → return false
        → Stop service
        → Notification: "❌ Lỗi: Verify failed"

Scenario 3: Quick verify confidence thấp
[00:27] confidence = 0.6 < 0.85
        → Log: "⚠️ Confidence thấp, cần popup verify"
        → Execute PHASE 4B (popup verify)
        → Verify 100% chắc chắn

Scenario 4: Popup verify mismatch
[00:33] detected_amount = 2000, expected = 4000
        → Server log mismatch to database
        → Response: verified = false, mismatch_details = "..."
        → Mobile alert: "⚠️ Cược sai: 2000 thay vì 4000"
        → Log error
        → Continue (accept actual amount)

Scenario 5: Giây quá ít (đang DANGER ZONE)
[00:02] Giây = 3 (trong 0-5)
        → Log: "⚠️ DANGER ZONE, đợi vòng mới"
        → Delay 6000ms
        → Loop lại check giây

Scenario 6: Server timeout
[00:10] POST /analyze → timeout 60s
        → Retry 1 lần
        → Nếu vẫn fail: Skip vòng này
        → Log error
        → Đợi 20 phút tiếp
```

**TEST MODE FLOW (Không tap thật)**
```
User bật switch "🧪 Test Mode"
User ấn "▶️ Bắt Đầu"
        ↓
App chạy logic NHƯNG:
├─ KHÔNG tap thật (skip tapAt())
├─ CHỈ log actions:
│  ├─ "[15:30:05] Would tap Mở popup (100, 200)"
│  ├─ "[15:30:07] Would capture popup"
│  ├─ "[15:30:09] Would upload to server"
│  ├─ "[15:30:12] Simulated multiplier: 4.0"
│  ├─ "[15:30:14] Would tap Mở Tài (300, 500)"
│  ├─ "[15:30:16] Would tap 1K x4 lần"
│  └─ "[15:30:20] Would tap Đặt cược"
├─ Hiển thị đầy đủ logs trong TextView
└─ User verify flow đúng chưa

→ Dùng để TEST TRƯỚC KHI chạy thật!
```

═══════════════════════════════════════════════════════════════════
📋 THÔNG TIN DỰ ÁN
═══════════════════════════════════════════════════════════════════

Package: com.autobet.taixiu
App Name: Auto Betting TaiXiu
Min SDK: 24 (Android 7.0)
Target SDK: 34
Language: Kotlin
Architecture: MVVM + Repository Pattern

Dependencies:
- Retrofit 2.9.0 + OkHttp 4.11.0 (HTTP client)
- Kotlin Coroutines (async)
- WorkManager 2.8.0 (background tasks 20 phút)
- Google ML Kit Text Recognition 16.0.0 (OCR local - FREE)
- Coil (image loading)
- AndroidX Lifecycle (ViewModel, LiveData)
- Material Components

═══════════════════════════════════════════════════════════════════
📋 CONSTANTS - TỌA ĐỘ & TIMING
═══════════════════════════════════════════════════════════════════

File: utils/Constants.kt

```kotlin
object Constants {
    // SharedPreferences
    const val PREFS_NAME = "AutoBettingPrefs"
    const val KEY_DEVICE_NAME = "device_name"
    const val KEY_BETTING_METHOD = "betting_method"
    const val KEY_COORD_OPEN_HISTORY_X = "coord_open_history_x"
    const val KEY_COORD_OPEN_HISTORY_Y = "coord_open_history_y"
    const val KEY_COORD_CLOSE_HISTORY_X = "coord_close_history_x"
    const val KEY_COORD_CLOSE_HISTORY_Y = "coord_close_history_y"
    const val KEY_COORD_OPEN_TAI_X = "coord_open_tai_x"
    const val KEY_COORD_OPEN_TAI_Y = "coord_open_tai_y"
    const val KEY_COORD_OPEN_XIU_X = "coord_open_xiu_x"
    const val KEY_COORD_OPEN_XIU_Y = "coord_open_xiu_y"
    const val KEY_COORD_BET_1K_X = "coord_bet_1k_x"
    const val KEY_COORD_BET_1K_Y = "coord_bet_1k_y"
    const val KEY_COORD_PLACE_BET_X = "coord_place_bet_x"
    const val KEY_COORD_PLACE_BET_Y = "coord_place_bet_y"
    const val KEY_IS_AUTO_RUNNING = "is_auto_running"
    
    // Timing (giây) - QUAN TRỌNG
    const val IDEAL_CAPTURE_MIN = 50     // Giây ideal để capture
    const val IDEAL_CAPTURE_MAX = 55
    const val MIN_SAFE_SECONDS = 30       // Tối thiểu để an toàn
    const val DANGER_ZONE_MAX = 5         // Giây 0-5: BỊ CHẶN cược
    const val MIN_SECONDS_START_BET = 6   // Phải >= 6 giây mới bắt đầu
    const val MIN_SECONDS_COMPLETE = 10   // Cần ít nhất 10s buffer
    
    // Verification
    const val CONFIDENCE_THRESHOLD = 0.85
    const val HIGH_MULTIPLIER_THRESHOLD = 8
    
    // Anti-Detection: Random Offset
    const val ENABLE_RANDOM_OFFSET = true
    const val RANDOM_OFFSET_MIN = -2
    const val RANDOM_OFFSET_MAX = 2
    
    // Anti-Detection: Random Delays (ms)
    const val DELAY_1K_BASE = 1000L
    const val DELAY_1K_VARIATION = 300L        // → 700-1300ms
    
    const val DELAY_OPEN_BET_BASE = 2000L
    const val DELAY_OPEN_BET_VARIATION = 500L  // → 1500-2500ms
    
    const val DELAY_PLACE_BET_BASE = 2000L
    const val DELAY_PLACE_BET_VARIATION = 400L // → 1600-2400ms
    
    const val DELAY_ACTION_BASE = 500L
    const val DELAY_ACTION_VARIATION = 200L    // → 300-700ms
    
    const val DELAY_POPUP_BASE = 2000L
    const val DELAY_POPUP_VARIATION = 300L     // → 1700-2300ms
    
    // OCR Crop Areas (tỷ lệ %)
    // Vùng số tiền cược (số trắng dưới TÀI/XỈU)
    const val MONEY_X_RATIO = 0.25f
    const val MONEY_Y_RATIO = 0.55f
    const val MONEY_WIDTH_RATIO = 0.15f
    const val MONEY_HEIGHT_RATIO = 0.05f
    
    // Vùng số giây (vòng tròn giữa)
    const val SECONDS_X_RATIO = 0.45f
    const val SECONDS_Y_RATIO = 0.45f
    const val SECONDS_WIDTH_RATIO = 0.1f
    const val SECONDS_HEIGHT_RATIO = 0.08f
    
    // WorkManager
    const val WORK_INTERVAL_MINUTES = 20L
    const val WORK_NAME = "auto_betting_worker"
    
    // Notification
    const val NOTIFICATION_CHANNEL_ID = "auto_betting_channel"
    const val NOTIFICATION_ID = 1001
}
```

═══════════════════════════════════════════════════════════════════
📋 RANDOM HELPER - ANTI-DETECTION
═══════════════════════════════════════════════════════════════════

File: utils/RandomHelper.kt

```kotlin
import kotlin.random.Random

object RandomHelper {
    
    /**
     * Random pixel offset: -2 đến +2
     */
    fun getRandomPixelOffset(): Int {
        return Random.nextInt(Constants.RANDOM_OFFSET_MIN, Constants.RANDOM_OFFSET_MAX + 1)
    }
    
    /**
     * Random delay với base + variation
     */
    fun getRandomDelay(baseMs: Long, variationMs: Long): Long {
        val variation = Random.nextLong(-variationMs, variationMs + 1)
        return maxOf(100, baseMs + variation)
    }
    
    /**
     * Delay giữa các tap 1K: 700-1300ms
     */
    fun getRandom1KDelay(): Long {
        return getRandomDelay(Constants.DELAY_1K_BASE, Constants.DELAY_1K_VARIATION)
    }
    
    /**
     * Delay sau mở cược: 1500-2500ms
     */
    fun getRandomAfterOpenBetDelay(): Long {
        return getRandomDelay(Constants.DELAY_OPEN_BET_BASE, Constants.DELAY_OPEN_BET_VARIATION)
    }
    
    /**
     * Delay sau tap "Đặt cược": 1600-2400ms
     */
    fun getRandomAfterPlaceBetDelay(): Long {
        return getRandomDelay(Constants.DELAY_PLACE_BET_BASE, Constants.DELAY_PLACE_BET_VARIATION)
    }
    
    /**
     * Delay giữa các action: 300-700ms
     */
    fun getRandomBetweenActionDelay(): Long {
        return getRandomDelay(Constants.DELAY_ACTION_BASE, Constants.DELAY_ACTION_VARIATION)
    }
    
    /**
     * Delay popup: 1700-2300ms
     */
    fun getRandomPopupDelay(): Long {
        return getRandomDelay(Constants.DELAY_POPUP_BASE, Constants.DELAY_POPUP_VARIATION)
    }
    
    /**
     * Human-like pause (10% chance): 3-5s
     */
    fun getHumanLikePause(): Long {
        return if (Random.nextDouble() < 0.1) {
            Random.nextLong(3000, 5001)
        } else {
            getRandomBetweenActionDelay()
        }
    }
}
```

═══════════════════════════════════════════════════════════════════
📋 API SERVICE - RETROFIT
═══════════════════════════════════════════════════════════════════

File: data/api/ApiService.kt

```kotlin
import okhttp3.MultipartBody
import okhttp3.RequestBody
import retrofit2.Response
import retrofit2.http.*
import com.google.gson.JsonObject

interface ApiService {
    
    @Multipart
    @POST("api/mobile/analyze")
    suspend fun analyzeImage(
        @Part file: MultipartBody.Part,
        @Part("device_name") deviceName: RequestBody,
        @Part("betting_method") bettingMethod: RequestBody
    ): Response<JsonObject>
    
    @Multipart
    @POST("api/mobile/verify-quick")
    suspend fun verifyQuick(
        @Part file: MultipartBody.Part,
        @Part("device_name") deviceName: RequestBody,
        @Part("expected_amount") expectedAmount: RequestBody
    ): Response<JsonObject>
    
    @Multipart
    @POST("api/mobile/verify-popup")
    suspend fun verifyPopup(
        @Part file: MultipartBody.Part,
        @Part("device_name") deviceName: RequestBody,
        @Part("expected_amount") expectedAmount: RequestBody,
        @Part("expected_method") expectedMethod: RequestBody,
        @Part("current_session") currentSession: RequestBody
    ): Response<JsonObject>
    
    @GET("api/mobile/history")
    suspend fun getHistory(
        @Query("limit") limit: Int = 50
    ): Response<JsonObject>
    
    @GET("api/mobile/device-state/{device_name}")
    suspend fun getDeviceState(
        @Path("device_name") deviceName: String
    ): Response<JsonObject>
}
```

File: data/api/ApiClient.kt

```kotlin
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit

object ApiClient {
    private const val BASE_URL = "https://lukistar.space/"
    private const val TIMEOUT_SECONDS = 60L
    
    private val loggingInterceptor = HttpLoggingInterceptor().apply {
        level = HttpLoggingInterceptor.Level.BODY
    }
    
    private val okHttpClient = OkHttpClient.Builder()
        .addInterceptor(loggingInterceptor)
        .connectTimeout(TIMEOUT_SECONDS, TimeUnit.SECONDS)
        .readTimeout(TIMEOUT_SECONDS, TimeUnit.SECONDS)
        .writeTimeout(TIMEOUT_SECONDS, TimeUnit.SECONDS)
        .build()
    
    private val retrofit = Retrofit.Builder()
        .baseUrl(BASE_URL)
        .client(okHttpClient)
        .addConverterFactory(GsonConverterFactory.create())
        .build()
    
    val apiService: ApiService = retrofit.create(ApiService::class.java)
}
```

═══════════════════════════════════════════════════════════════════
📋 OCR HELPER - ML KIT
═══════════════════════════════════════════════════════════════════

File: utils/OCRHelper.kt

```kotlin
import android.content.Context
import android.graphics.Bitmap
import com.google.mlkit.vision.common.InputImage
import com.google.mlkit.vision.text.TextRecognition
import com.google.mlkit.vision.text.latin.TextRecognizerOptions
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlin.coroutines.resume

class OCRHelper(private val context: Context) {
    
    private val recognizer = TextRecognition.getClient(TextRecognizerOptions.DEFAULT_OPTIONS)
    
    /**
     * OCR vùng số tiền cược
     */
    suspend fun detectMoneyAmount(fullScreenshot: Bitmap): Int {
        val cropped = cropMoneyArea(fullScreenshot)
        val text = performOCR(cropped)
        return parseMoneyText(text)
    }
    
    /**
     * OCR vùng số giây đếm ngược
     */
    suspend fun detectSecondsRemaining(fullScreenshot: Bitmap): Int {
        val cropped = cropSecondsArea(fullScreenshot)
        val text = performOCR(cropped)
        return text.trim().filter { it.isDigit() }.toIntOrNull() ?: -1
    }
    
    /**
     * Crop vùng số tiền (25%, 55%, 15%, 5%)
     */
    private fun cropMoneyArea(bitmap: Bitmap): Bitmap {
        val x = (bitmap.width * Constants.MONEY_X_RATIO).toInt()
        val y = (bitmap.height * Constants.MONEY_Y_RATIO).toInt()
        val w = (bitmap.width * Constants.MONEY_WIDTH_RATIO).toInt()
        val h = (bitmap.height * Constants.MONEY_HEIGHT_RATIO).toInt()
        return Bitmap.createBitmap(bitmap, x, y, w, h)
    }
    
    /**
     * Crop vùng số giây (45%, 45%, 10%, 8%)
     */
    private fun cropSecondsArea(bitmap: Bitmap): Bitmap {
        val x = (bitmap.width * Constants.SECONDS_X_RATIO).toInt()
        val y = (bitmap.height * Constants.SECONDS_Y_RATIO).toInt()
        val w = (bitmap.width * Constants.SECONDS_WIDTH_RATIO).toInt()
        val h = (bitmap.height * Constants.SECONDS_HEIGHT_RATIO).toInt()
        return Bitmap.createBitmap(bitmap, x, y, w, h)
    }
    
    /**
     * Perform OCR với ML Kit
     */
    private suspend fun performOCR(bitmap: Bitmap): String = suspendCancellableCoroutine { cont ->
        val inputImage = InputImage.fromBitmap(bitmap, 0)
        
        recognizer.process(inputImage)
            .addOnSuccessListener { visionText ->
                cont.resume(visionText.text)
            }
            .addOnFailureListener { e ->
                android.util.Log.e("OCRHelper", "OCR failed", e)
                cont.resume("")
            }
    }
    
    /**
     * Parse text thành số tiền
     * Input: "1,000" hoặc "2.000" hoặc "1 000"
     * Output: 1000
     */
    private fun parseMoneyText(text: String): Int {
        val cleaned = text.replace(",", "").replace(".", "").replace(" ", "")
        val numbers = cleaned.filter { it.isDigit() }
        return numbers.toIntOrNull() ?: 0
    }
}
```

═══════════════════════════════════════════════════════════════════
📋 AUTO TAP SERVICE - ACCESSIBILITY
═══════════════════════════════════════════════════════════════════

File: service/AutoTapAccessibilityService.kt

```kotlin
import android.accessibilityservice.AccessibilityService
import android.accessibilityservice.GestureDescription
import android.graphics.Path
import android.util.Log
import android.view.accessibility.AccessibilityEvent

class AutoTapAccessibilityService : AccessibilityService() {
    
    companion object {
        private var instance: AutoTapAccessibilityService? = null
        
        fun getInstance(): AutoTapAccessibilityService? = instance
        fun isEnabled(): Boolean = instance != null
    }
    
    override fun onServiceConnected() {
        super.onServiceConnected()
        instance = this
        Log.d("AutoTap", "Service connected")
    }
    
    override fun onAccessibilityEvent(event: AccessibilityEvent?) {}
    override fun onInterrupt() {}
    
    override fun onDestroy() {
        super.onDestroy()
        instance = null
    }
    
    /**
     * Tap với random offset ±2 pixels
     */
    fun tapAt(x: Int, y: Int, useRandomOffset: Boolean = true): Boolean {
        val finalX = if (useRandomOffset) {
            x + RandomHelper.getRandomPixelOffset()
        } else {
            x
        }
        
        val finalY = if (useRandomOffset) {
            y + RandomHelper.getRandomPixelOffset()
        } else {
            y
        }
        
        Log.d("AutoTap", "Tap at ($x,$y) → ($finalX,$finalY)")
        
        val path = Path().apply { moveTo(finalX.toFloat(), finalY.toFloat()) }
        val gesture = GestureDescription.Builder()
            .addStroke(GestureDescription.StrokeDescription(path, 0, 100))
            .build()
        
        return dispatchGesture(gesture, null, null)
    }
}
```

File: res/xml/accessibility_service_config.xml

```xml
<?xml version="1.0" encoding="utf-8"?>
<accessibility-service xmlns:android="http://schemas.android.com/apk/res/android"
    android:accessibilityEventTypes="typeAllMask"
    android:accessibilityFeedbackType="feedbackGeneric"
    android:canPerformGestures="true"
    android:description="@string/accessibility_description" />
```

═══════════════════════════════════════════════════════════════════
📋 EXECUTE BETTING USE CASE - LOGIC CHÍNH
═══════════════════════════════════════════════════════════════════

File: domain/usecase/ExecuteBettingUseCase.kt

```kotlin
class ExecuteBettingUseCase(
    private val context: Context,
    private val repository: BettingRepository,
    private val ocrHelper: OCRHelper,
    private val screenCapture: ScreenCaptureService
) {
    
    suspend fun execute(config: BettingConfig): Result<String> = withContext(Dispatchers.IO) {
        try {
            log("═══ BẮT ĐẦU CHU KỲ CƯỢC ═══")
            
            // STEP 1: Đợi đến giây 50-55
            val currentSeconds = waitUntilIdealCaptureTime()
            log("✅ Giây: $currentSeconds")
            
            // STEP 2: Capture popup lịch sử
            val popupScreenshot = captureHistoryPopup(config)
            log("✅ Captured popup")
            
            // STEP 3: Upload lên server
            val analysisResult = repository.analyzeHistoryImage(
                popupScreenshot,
                config.deviceName,
                config.bettingMethod
            )
            
            if (!analysisResult.isSuccess) {
                return@withContext Result.failure(Exception("Lỗi phân tích"))
            }
            
            val data = analysisResult.getOrNull()!!
            val multiplier = data.getAsJsonPrimitive("multiplier")?.asDouble ?: 0.0
            log("✅ Multiplier: $multiplier")
            
            // STEP 4: Check multiplier
            if (multiplier <= 0) {
                log("⏸️ Multiplier = 0, NGHỈ vòng này")
                return@withContext Result.success("Nghỉ (multiplier = 0)")
            }
            
            val betAmount = (1000 * multiplier).toInt()
            log("💰 Sẽ cược: $betAmount")
            
            // STEP 5: Thực hiện cược với multi-layer verify
            val success = executeBettingActions(config, multiplier.toInt(), betAmount)
            
            if (success) {
                Result.success("Cược thành công: $betAmount")
            } else {
                Result.failure(Exception("Cược thất bại"))
            }
            
        } catch (e: Exception) {
            log("❌ Lỗi: ${e.message}")
            Result.failure(e)
        }
    }
    
    /**
     * Đợi đến giây ideal (50-55)
     */
    private suspend fun waitUntilIdealCaptureTime(): Int {
        while (true) {
            val screenshot = screenCapture.captureScreen() ?: continue
            val seconds = ocrHelper.detectSecondsRemaining(screenshot)
            
            if (seconds < 0) {
                delay(1000)
                continue
            }
            
            log("⏱️ Giây: $seconds")
            
            // DANGER ZONE: 0-5 (BỊ CHẶN)
            if (seconds in 0..Constants.DANGER_ZONE_MAX) {
                log("⚠️ DANGER ZONE (giây $seconds), đợi vòng mới...")
                delay(6000)
                continue
            }
            
            // Quá ít (6-10): Không đủ thời gian
            if (seconds <= 10) {
                log("⚠️ Giây quá ít, skip vòng này")
                delay((seconds + 5) * 1000L)
                continue
            }
            
            // Ideal: 50-55
            if (seconds in Constants.IDEAL_CAPTURE_MIN..Constants.IDEAL_CAPTURE_MAX) {
                return seconds
            }
            
            // > 55: Đợi đến 50-55
            if (seconds > Constants.IDEAL_CAPTURE_MAX) {
                val waitTime = (seconds - Constants.IDEAL_CAPTURE_MAX) * 1000L
                delay(waitTime)
                continue
            }
            
            // 30-50: OK
            if (seconds > Constants.MIN_SAFE_SECONDS) {
                return seconds
            }
            
            // < 30: Skip
            delay((seconds + 10) * 1000L)
        }
    }
    
    /**
     * Capture popup lịch sử
     */
    private suspend fun captureHistoryPopup(config: BettingConfig): File {
        val service = AutoTapAccessibilityService.getInstance()
            ?: throw Exception("Accessibility Service chưa bật")
        
        val coords = config.coordinates
        
        // Tap mở popup (với random offset)
        log("📱 Tap Mở popup (${coords.openHistoryPopupX}, ${coords.openHistoryPopupY})")
        service.tapAt(coords.openHistoryPopupX, coords.openHistoryPopupY)
        delay(RandomHelper.getRandomPopupDelay())
        
        // Capture
        val screenshot = screenCapture.captureScreen()
            ?: throw Exception("Không capture được popup")
        
        // Tap đóng popup
        log("📱 Tap Đóng popup")
        service.tapAt(coords.closeHistoryPopupX, coords.closeHistoryPopupY)
        delay(RandomHelper.getRandomBetweenActionDelay())
        
        return saveToFile(screenshot, "popup_${System.currentTimeMillis()}.jpg")
    }
    
    /**
     * Thực hiện actions cược với real-time verification
     */
    private suspend fun executeBettingActions(
        config: BettingConfig,
        tapCount: Int,
        expectedAmount: Int
    ): Boolean {
        val service = AutoTapAccessibilityService.getInstance()
            ?: throw Exception("Accessibility Service chưa bật")
        
        val coords = config.coordinates
        val isTai = (config.bettingMethod == "Tài")
        
        // STEP 1: Check và reset số tiền
        val currentMoney = checkCurrentMoney()
        if (currentMoney > 0) {
            log("⚠️ Số tiền: $currentMoney, reset về 0")
            resetMoney(config, isTai)
        }
        
        // STEP 2: Tap "Mở cược Tài/Xỉu"
        val betX = if (isTai) coords.openBetTaiX else coords.openBetXiuX
        val betY = if (isTai) coords.openBetTaiY else coords.openBetXiuY
        
        log("📱 Tap Mở ${config.bettingMethod} ($betX, $betY)")
        service.tapAt(betX, betY)
        delay(RandomHelper.getRandomAfterOpenBetDelay())
        
        // STEP 3: Loop tap "1K" với verify từng bước
        for (i in 1..tapCount) {
            // Safety check
            if (!safetyCheck()) {
                log("❌ Safety check failed")
                return false
            }
            
            log("📱 Tap 1K lần $i/$tapCount")
            service.tapAt(coords.bet1KX, coords.bet1KY)
            
            val delay1K = RandomHelper.getRandom1KDelay()
            log("⏱️ Delay ${delay1K}ms")
            delay(delay1K)
            
            // Verify ngay
            val screenshot = screenCapture.captureScreen()
            if (screenshot != null) {
                val detected = ocrHelper.detectMoneyAmount(screenshot)
                val expected = i * 1000
                
                if (detected == expected) {
                    log("✅ Verify OK: $detected")
                } else {
                    log("⚠️ Verify FAIL: $detected != $expected, retry...")
                    delay(RandomHelper.getRandomBetweenActionDelay())
                    service.tapAt(coords.bet1KX, coords.bet1KY)
                    delay(RandomHelper.getRandom1KDelay())
                    
                    val retry = screenCapture.captureScreen()
                    val retryMoney = retry?.let { ocrHelper.detectMoneyAmount(it) } ?: 0
                    
                    if (retryMoney != expected) {
                        log("❌ Retry FAIL, dừng")
                        return false
                    }
                    log("✅ Retry OK: $retryMoney")
                }
            }
        }
        
        // STEP 4: Tap "Đặt cược"
        log("📱 Tap Đặt cược")
        service.tapAt(coords.placeBetX, coords.placeBetY)
        delay(RandomHelper.getRandomAfterPlaceBetDelay())
        
        // STEP 5: Quick verification
        val afterScreenshot = screenCapture.captureScreen()
        if (afterScreenshot != null) {
            val verifyResult = repository.verifyQuick(
                saveToFile(afterScreenshot, "verify_${System.currentTimeMillis()}.jpg"),
                config.deviceName,
                expectedAmount
            )
            
            if (verifyResult.isSuccess) {
                val data = verifyResult.getOrNull()!!
                val verified = data.getAsJsonPrimitive("verified")?.asBoolean ?: false
                val confidence = data.getAsJsonPrimitive("confidence")?.asDouble ?: 0.0
                
                log("🔍 Quick verify: verified=$verified, confidence=$confidence")
                
                if (verified && confidence >= Constants.CONFIDENCE_THRESHOLD) {
                    log("✅ Quick verify OK")
                    return true
                } else {
                    log("⚠️ Confidence thấp, cần popup verify")
                    return verifyViaPopup(config, expectedAmount)
                }
            }
        }
        
        return false
    }
    
    /**
     * Reset số tiền về 0
     */
    private suspend fun resetMoney(config: BettingConfig, isTai: Boolean) {
        val service = AutoTapAccessibilityService.getInstance() ?: return
        val coords = config.coordinates
        
        // Tap nút đối diện
        val oppX = if (isTai) coords.openBetXiuX else coords.openBetTaiX
        val oppY = if (isTai) coords.openBetXiuY else coords.openBetTaiY
        
        log("📱 Reset: Tap nút đối diện")
        service.tapAt(oppX, oppY)
        delay(RandomHelper.getRandomBetweenActionDelay())
        
        // Tap lại nút đúng
        val corX = if (isTai) coords.openBetTaiX else coords.openBetXiuX
        val corY = if (isTai) coords.openBetTaiY else coords.openBetXiuY
        
        log("📱 Reset: Tap lại nút đúng")
        service.tapAt(corX, corY)
        delay(RandomHelper.getRandomBetweenActionDelay())
        
        log("✅ Reset done")
    }
    
    /**
     * Check số tiền hiện tại
     */
    private suspend fun checkCurrentMoney(): Int {
        val screenshot = screenCapture.captureScreen() ?: return 0
        return ocrHelper.detectMoneyAmount(screenshot)
    }
    
    /**
     * Safety check trước actions
     */
    private suspend fun safetyCheck(): Boolean {
        val screenshot = screenCapture.captureScreen() ?: return false
        val seconds = ocrHelper.detectSecondsRemaining(screenshot)
        
        if (seconds <= Constants.MIN_SECONDS_START_BET) {
            log("⚠️ Safety: Giây $seconds quá ít")
            return false
        }
        
        return true
    }
    
    /**
     * Verify qua popup (fallback)
     */
    private suspend fun verifyViaPopup(config: BettingConfig, expectedAmount: Int): Boolean {
        log("🔍 Popup verification...")
        
        try {
            val popupScreenshot = captureHistoryPopup(config)
            
            val result = repository.verifyPopup(
                popupScreenshot,
                config.deviceName,
                expectedAmount,
                config.bettingMethod,
                ""
            )
            
            val verified = result.getOrNull()
                ?.getAsJsonPrimitive("verified")?.asBoolean ?: false
            
            log("✅ Popup verify: $verified")
            return verified
            
        } catch (e: Exception) {
            log("❌ Popup verify error: ${e.message}")
            return false
        }
    }
    
    private fun saveToFile(bitmap: Bitmap, filename: String): File {
        val file = File(context.cacheDir, filename)
        FileOutputStream(file).use {
            bitmap.compress(Bitmap.CompressFormat.JPEG, 90, it)
        }
        return file
    }
    
    private fun log(msg: String) {
        Log.d("ExecuteBetting", msg)
        context.sendBroadcast(Intent("com.autobet.taixiu.LOG").apply {
            putExtra("message", msg)
        })
    }
}
```

═══════════════════════════════════════════════════════════════════
📋 MAIN ACTIVITY - UI
═══════════════════════════════════════════════════════════════════

File: presentation/MainActivity.kt

Layout cần có:
- EditText: Device name
- Dropdown: Betting method ("Tài", "Xỉu")
- 6 EditText: Tọa độ (format x:y)
  * Mở popup lịch sử
  * Đóng popup lịch sử
  * Mở cược Tài
  * Mở cược Xỉu
  * Đặt 1K
  * Đặt cược
- Button: "💾 Lưu Tọa Độ"
- Button: "▶️ Bắt Đầu" (start WorkManager)
- Button: "⏹️ Dừng" (cancel WorkManager)
- Switch: "🧪 Test Mode"
- TextView: Status
- TextView: Logs (ScrollView, auto-scroll bottom)

Logic:
- Save/Load từ SharedPreferences
- Parse "x:y" → Pair<Int, Int>
- Start/Stop WorkManager (20 phút)
- BroadcastReceiver nhận logs từ service
- Check Accessibility Service enabled
- Request MediaProjection permission

═══════════════════════════════════════════════════════════════════
📋 ANDROIDMANIFEST.XML
═══════════════════════════════════════════════════════════════════

```xml
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="com.autobet.taixiu">

    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.FOREGROUND_SERVICE" />
    <uses-permission android:name="android.permission.POST_NOTIFICATIONS" />
    <uses-permission android:name="android.permission.SYSTEM_ALERT_WINDOW" />

    <application
        android:allowBackup="true"
        android:icon="@mipmap/ic_launcher"
        android:label="Auto Betting"
        android:usesCleartextTraffic="true"
        android:theme="@style/Theme.Material3.DayNight">
        
        <activity
            android:name=".presentation.MainActivity"
            android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
        
        <service
            android:name=".service.BettingForegroundService"
            android:foregroundServiceType="mediaProjection" />
        
        <service
            android:name=".service.AutoTapAccessibilityService"
            android:permission="android.permission.BIND_ACCESSIBILITY_SERVICE"
            android:exported="true">
            <intent-filter>
                <action android:name="android.accessibilityservice.AccessibilityService" />
            </intent-filter>
            <meta-data
                android:name="android.accessibilityservice"
                android:resource="@xml/accessibility_service_config" />
        </service>
        
    </application>
</manifest>
```

═══════════════════════════════════════════════════════════════════
📋 LƯU Ý QUAN TRỌNG
═══════════════════════════════════════════════════════════════════

**1. Timing Critical:**
- DANGER ZONE: Giây 0-5 (BỊ CHẶN, text "Đã hết thời gian cược")
- Chỉ capture khi giây >= 10
- Chỉ bắt đầu cược khi giây >= 10
- Ideal: 50-55 giây

**2. Anti-Detection:**
- Mọi tap đều có random offset ±2 pixels
- Mọi delay đều random ±20-30%
- 10% chance có pause dài 3-5s

**3. Verification:**
- Quick verify: CHỈ check số tiền (confidence ~80%)
- Popup verify: Check đầy đủ (confidence 100%)
- Fallback: Nếu quick < 0.85 → popup verify

**4. OCR Crop Areas:**
- User KHÔNG cần nhập
- App tự crop dựa vào tỷ lệ % hard-coded
- Số tiền: 25% x, 55% y, 15% w, 5% h
- Số giây: 45% x, 45% y, 10% w, 8% h

**5. Error Handling:**
- Mọi exception đều log chi tiết
- Retry tối đa 2 lần
- Notification khi có lỗi critical

**6. Database:**
- Server tự động cleanup giữ 100 records
- Mobile không cần quan tâm

**7. Test Mode:**
- Switch "Test Mode" → Không tap thật
- Chỉ log actions
- Dùng để test flow

═══════════════════════════════════════════════════════════════════
📋 IMPLEMENTATION NOTES CHO GEMINI
═══════════════════════════════════════════════════════════════════

**QUAN TRỌNG - ĐỌC KỸ:**

1. **Repository Pattern:**
   - Tạo BettingRepository.kt để wrap API calls
   - Methods:
     * analyzeHistoryImage(file, device, method) → POST /analyze
     * verifyQuick(file, device, amount) → POST /verify-quick
     * verifyPopup(file, device, amount, method, session) → POST /verify-popup
   - Convert File → MultipartBody.Part
   - Parse JsonObject response

2. **ScreenCaptureService.kt:**
   - Dùng MediaProjection API
   - Method captureScreen() → Bitmap
   - Request permission trong MainActivity
   - Store MediaProjection instance

3. **BettingForegroundService.kt:**
   - Receive BettingConfig từ Intent
   - Create notification channel
   - Call ExecuteBettingUseCase.execute()
   - Update notification theo kết quả
   - stopSelf() khi xong

4. **PeriodicBettingWorker.kt:**
   - Check KEY_IS_AUTO_RUNNING từ SharedPreferences
   - Load config từ SharedPreferences
   - Start BettingForegroundService với config
   - Return Result.success()

5. **MainActivity Logic:**
   - onActivityResult: Nhận MediaProjection permission
   - Parse coordinates: "100:200" → Pair(100, 200)
   - Save/Load SharedPreferences
   - BroadcastReceiver: Nhận logs từ service, append vào TextView
   - Check Accessibility: AutoTapAccessibilityService.isEnabled()

6. **Error Handling:**
   - Try-catch mọi network calls
   - Try-catch mọi OCR operations
   - Try-catch mọi tap operations
   - Log chi tiết với timestamp
   - Show notification khi có error

7. **Test Mode:**
   - Check SharedPreferences KEY_TEST_MODE
   - Nếu true: Skip tapAt(), chỉ log "Would tap..."
   - Vẫn execute logic flow đầy đủ
   - User có thể verify flow trước khi run thật

8. **Logging:**
   - Format: "[HH:mm:ss] emoji message"
   - Broadcast intent "com.autobet.taixiu.LOG"
   - MainActivity receive và append vào TextView
   - Auto-scroll to bottom
   - Max lines: 100 (clear old nếu quá nhiều)

═══════════════════════════════════════════════════════════════════

YÊU CẦU CUỐI CÙNG:
- Code sạch, comments tiếng Việt chi tiết
- UI đẹp Material Design 3
- Error handling đầy đủ với try-catch
- Logs chi tiết trong TextView với timestamp
- Test mode để kiểm tra flow
- README.md hướng dẫn setup permissions (Accessibility + MediaProjection)
- Implement ĐÚNG theo luồng xử lý ở PHẦN ĐẦU
- Tất cả delays phải dùng RandomHelper
- Tất cả taps phải có random offset
- OCR phải crop đúng vùng theo tỷ lệ %
- Verify sau MỖI lần tap 1K
- Quick verify SAU KHI tap "Đặt cược"
- Popup verify CHỈ KHI confidence < 0.85

Bắt đầu tạo project ngay với ĐÚNG flow đã mô tả!
```

---

**Copy toàn bộ prompt này và paste vào Gemini trong Android Studio!** 🚀

