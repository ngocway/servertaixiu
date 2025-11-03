@echo off
chcp 65001 >nul
echo ========================================
echo 🔍 KIỂM TRA CORS CONFIGURATION
echo ========================================
echo.

echo [1/3] Kiểm tra OPTIONS preflight request...
echo.
curl -s -X OPTIONS http://lukistar.space/upload ^
  -H "Origin: chrome-extension://test" ^
  -H "Access-Control-Request-Method: POST" ^
  -H "Access-Control-Request-Headers: Content-Type" ^
  -w "\n\n✅ Status Code: %%{http_code}\n" -o nul
echo.

echo [2/3] Kiểm tra response headers từ Nginx...
echo.
curl -s -I -X OPTIONS http://lukistar.space/upload ^
  -H "Origin: chrome-extension://test" ^
  -H "Access-Control-Request-Method: POST" | findstr /i "access-control HTTP"
echo.

echo [3/3] Kiểm tra POST request (giả lập Chrome extension)...
echo.
curl -s -X POST http://lukistar.space/upload ^
  -H "Origin: chrome-extension://test" ^
  -H "Content-Type: application/json" ^
  -d "{}" ^
  -w "\n✅ Status Code: %%{http_code}\n" | findstr /i "status error"
echo.

echo ========================================
echo 📋 KẾT QUẢ KIỂM TRA:
echo.
echo ✅ Nếu thấy các headers sau là OK:
echo    - Access-Control-Allow-Origin: *
echo    - Access-Control-Allow-Methods: ...
echo    - Access-Control-Allow-Headers: ...
echo.
echo ❌ Nếu không thấy headers trên, cần kiểm tra lại:
echo    1. Nginx config: /etc/nginx/sites-available/screenshot-analyzer
echo    2. FastAPI CORS middleware trong app/main.py
echo    3. Restart Nginx: sudo systemctl restart nginx
echo ========================================
pause

