# Script kiểm tra và fix lỗi VPS
$VPS_IP = "97.74.83.97"
$VPS_USER = "myadmin"
$VPS_PATH = "~/screenshot-analyzer"

Write-Host "=== Checking VPS Status ===" -ForegroundColor Cyan

# Check Python import
Write-Host "`n1. Testing Python imports..." -ForegroundColor Yellow
$importTest = ssh ${VPS_USER}@${VPS_IP} "cd ${VPS_PATH} && source venv/bin/activate && python3 -c 'import cv2; print(\"cv2 OK\")' 2>&1"
Write-Host $importTest

# Check if service exists
Write-Host "`n2. Checking service status..." -ForegroundColor Yellow
ssh ${VPS_USER}@${VPS_IP} "sudo systemctl status screenshot-analyzer --no-pager | head -5" 2>&1

# Check if port 8000 is listening
Write-Host "`n3. Checking port 8000..." -ForegroundColor Yellow
ssh ${VPS_USER}@${VPS_IP} "sudo netstat -tlnp | grep 8000 || echo 'Port 8000 not listening'" 2>&1

# Try to start manually
Write-Host "`n4. Attempting manual start..." -ForegroundColor Yellow
ssh ${VPS_USER}@${VPS_IP} "cd ${VPS_PATH} && source venv/bin/activate && timeout 3 python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000 2>&1 | head -10" 2>&1

Write-Host "`n=== Done ===" -ForegroundColor Cyan











