@echo off
echo ========================================
echo Testing CORS Configuration
echo ========================================
echo.

echo [1] Testing OPTIONS preflight request...
echo.
curl -v -X OPTIONS http://lukistar.space/upload ^
  -H "Origin: chrome-extension://test" ^
  -H "Access-Control-Request-Method: POST" ^
  -H "Access-Control-Request-Headers: Content-Type" 2>&1 | findstr /i "access-control HTTP/1.1"
echo.
echo.

echo [2] Testing GET request with CORS headers...
echo.
curl -v -X GET http://lukistar.space/upload ^
  -H "Origin: chrome-extension://test" 2>&1 | findstr /i "access-control HTTP/1.1"
echo.
echo.

echo [3] Testing POST request (simulating Chrome extension)...
echo.
curl -v -X POST http://lukistar.space/upload ^
  -H "Origin: chrome-extension://test" ^
  -H "Content-Type: multipart/form-data" ^
  -F "image=@test_image.png" 2>&1 | findstr /i "access-control HTTP/1.1 status"
echo.
echo.

echo ========================================
echo Testing complete!
echo.
echo Expected results:
echo - HTTP/1.1 204 (for OPTIONS)
echo - Access-Control-Allow-Origin: *
echo - Access-Control-Allow-Methods: GET, POST, OPTIONS...
echo - Access-Control-Allow-Headers: Content-Type...
echo ========================================
pause

