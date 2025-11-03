@echo off
chcp 65001 >nul
cls
echo ═══════════════════════════════════════════════════
echo   ✅ KIỂM TRA CORS HEADERS - OPTIONS VÀ POST
echo ═══════════════════════════════════════════════════
echo.

echo [1/2] Kiểm tra OPTIONS preflight request...
echo ──────────────────────────────────────────────────
curl -v -X OPTIONS http://lukistar.space/upload ^
  -H "Origin: chrome-extension://test" ^
  -H "Access-Control-Request-Method: POST" ^
  -H "Access-Control-Request-Headers: Content-Type" 2>&1 | findstr /i "access-control HTTP/"
echo.
echo.

echo [2/2] Kiểm tra POST request headers...
echo ──────────────────────────────────────────────────
curl -v -X POST http://lukistar.space/upload ^
  -H "Origin: chrome-extension://test" ^
  -H "Content-Type: application/json" ^
  -d "{}" 2>&1 | findstr /i "access-control HTTP/" | head -10
echo.
echo.

echo ═══════════════════════════════════════════════════
echo   📋 KẾT QUẢ
echo ═══════════════════════════════════════════════════
echo.
echo ✅ CẦN THẤY CHO CẢ OPTIONS VÀ POST:
echo    ✓ Access-Control-Allow-Origin: *
echo    ✓ Access-Control-Allow-Methods: GET, POST, OPTIONS...
echo    ✓ Access-Control-Allow-Headers: *
echo.
echo 💡 Nếu cả 2 đều có headers trên → CORS đã cấu hình ĐÚNG
echo    Nếu thiếu → Kiểm tra lại Nginx và FastAPI code
echo ═══════════════════════════════════════════════════
pause

