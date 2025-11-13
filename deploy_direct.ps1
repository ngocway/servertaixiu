# Deploy trực tiếp lên VPS qua SCP (không qua Git)
$VPS_IP = "97.74.83.97"
$VPS_USER = "myadmin"
$VPS_PATH = "~/screenshot-analyzer"

Write-Host "[Direct Deploy] Copying files to VPS..." -ForegroundColor Cyan

# Copy file đã thay đổi lên VPS
scp -r app/main.py ${VPS_USER}@${VPS_IP}:${VPS_PATH}/app/main.py 2>&1 | Out-Null

if ($LASTEXITCODE -ne 0) {
    Write-Host "[Direct Deploy] Failed! Check SSH connection." -ForegroundColor Red
    exit 1
}

Write-Host "[Direct Deploy] Restarting service on VPS..." -ForegroundColor Cyan

# Restart service trên VPS
ssh ${VPS_USER}@${VPS_IP} "cd ${VPS_PATH} && pkill -f 'uvicorn.*main:app' || true && nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > /dev/null 2>&1 &" 2>&1 | Out-Null

Write-Host "[Direct Deploy] Done! Server: http://${VPS_IP}:8000/admin" -ForegroundColor Green







