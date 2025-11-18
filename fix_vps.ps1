# Script fix lỗi 502 trên VPS
$VPS_IP = "97.74.83.97"
$VPS_USER = "myadmin"
$VPS_PATH = "~/screenshot-analyzer"

Write-Host "[Fix VPS] Checking and fixing service..." -ForegroundColor Cyan

# Stop service
Write-Host "Stopping service..." -ForegroundColor Gray
ssh ${VPS_USER}@${VPS_IP} "sudo systemctl stop screenshot-analyzer" 2>&1 | Out-Null

# Install opencv-python
Write-Host "Installing opencv-python..." -ForegroundColor Gray
ssh ${VPS_USER}@${VPS_IP} "cd ${VPS_PATH} && source venv/bin/activate && pip install opencv-python==4.8.1.78" 2>&1 | Out-Null

# Install all requirements
Write-Host "Installing all requirements..." -ForegroundColor Gray
ssh ${VPS_USER}@${VPS_IP} "cd ${VPS_PATH} && source venv/bin/activate && pip install -r requirements.txt" 2>&1 | Out-Null

# Test import
Write-Host "Testing import..." -ForegroundColor Gray
$testResult = ssh ${VPS_USER}@${VPS_IP} "cd ${VPS_PATH} && source venv/bin/activate && python3 -c 'import cv2; import app.main; print(\"OK\")' 2>&1"
Write-Host $testResult

# Start service
Write-Host "Starting service..." -ForegroundColor Gray
ssh ${VPS_USER}@${VPS_IP} "sudo systemctl start screenshot-analyzer" 2>&1 | Out-Null

# Wait and check status
Start-Sleep -Seconds 3
Write-Host "Checking service status..." -ForegroundColor Gray
ssh ${VPS_USER}@${VPS_IP} "sudo systemctl status screenshot-analyzer --no-pager | head -10" 2>&1

Write-Host "[Fix VPS] Done! Check http://${VPS_IP}:8000/admin" -ForegroundColor Green












