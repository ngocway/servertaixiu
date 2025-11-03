@echo off
chcp 65001 >nul
cls
echo ═══════════════════════════════════════════════════
echo   🔍 KIỂM TRA CẤU HÌNH CORS TRÊN SERVER
echo ═══════════════════════════════════════════════════
echo.

echo [BƯỚC 1] Kiểm tra OPTIONS preflight request...
echo ──────────────────────────────────────────────────
curl -v -X OPTIONS http://lukistar.space/upload ^
  -H "Origin: chrome-extension://test" ^
  -H "Access-Control-Request-Method: POST" ^
  -H "Access-Control-Request-Headers: Content-Type" 2>&1 | findstr /i "access-control HTTP/"
echo.
echo.

echo [BƯỚC 2] Kiểm tra POST request headers...
echo ──────────────────────────────────────────────────
curl -s -I -X POST http://lukistar.space/upload ^
  -H "Origin: chrome-extension://test" ^
  -H "Content-Type: application/json" | findstr /i "access-control HTTP/"
echo.
echo.

echo ═══════════════════════════════════════════════════
echo   📋 KẾT QUẢ
echo ═══════════════════════════════════════════════════
echo.
echo ✅ Nếu thấy các dòng sau, CORS đã cấu hình ĐÚNG:
echo    ✓ Access-Control-Allow-Origin: *
echo    ✓ Access-Control-Allow-Methods: GET, POST, OPTIONS...
echo    ✓ Access-Control-Allow-Headers: *
echo.
echo ❌ Nếu KHÔNG thấy các dòng trên, cần kiểm tra:
echo    1. Nginx config đã được cập nhật chưa
echo    2. Nginx đã restart chưa: sudo systemctl restart nginx
echo    3. FastAPI server đang chạy chưa
echo.
echo 💡 Hoặc mở Chrome DevTools (F12) → Network tab
echo    → Test upload từ extension → Xem Response Headers
echo ═══════════════════════════════════════════════════
pause

