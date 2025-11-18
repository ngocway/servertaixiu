# Deploy nhanh - chỉ deploy file đã chỉnh sửa gần đây (trong 5 phút)
$VPS_IP = "97.74.83.97"
$VPS_USER = "myadmin"
$VPS_PATH = "~/screenshot-analyzer"

Write-Host "[Fast Deploy] Checking recently modified files..." -ForegroundColor Cyan

# Danh sách file có thể deploy
$filesToCheck = @(
    "app/main.py",
    "app/services/mobile_betting_service.py",
    "requirements.txt",
    "config.py"
)

# Kiểm tra file nào đã được chỉnh sửa trong 5 phút gần đây
$changedFiles = @()
$cutoffTime = (Get-Date).AddMinutes(-5)

foreach ($file in $filesToCheck) {
    if (Test-Path $file) {
        $fileInfo = Get-Item $file
        if ($fileInfo.LastWriteTime -gt $cutoffTime) {
            $changedFiles += $file
            Write-Host "  [OK] $file (modified $($fileInfo.LastWriteTime.ToString('HH:mm:ss')))" -ForegroundColor Green
        }
    }
}

# Nếu không có file nào thay đổi gần đây, hỏi user
if ($changedFiles.Count -eq 0) {
    Write-Host "  No files modified in last 5 minutes." -ForegroundColor Yellow
    $deployAll = Read-Host "Deploy all files anyway? (y/n)"
    if ($deployAll -eq "y" -or $deployAll -eq "Y") {
        $changedFiles = $filesToCheck | Where-Object { Test-Path $_ }
    } else {
        Write-Host "[Fast Deploy] Cancelled." -ForegroundColor Yellow
        exit 0
    }
}

if ($changedFiles.Count -eq 0) {
    Write-Host "[Fast Deploy] No files to deploy!" -ForegroundColor Yellow
    exit 0
}

Write-Host "[Fast Deploy] Deploying $($changedFiles.Count) file(s)..." -ForegroundColor Cyan

# Deploy với compression và parallel nếu có thể
$failedFiles = @()
foreach ($file in $changedFiles) {
    Write-Host "  -> $file" -ForegroundColor Gray -NoNewline
    
    $remoteDir = ""
    if ($file.Contains('/')) {
        $remoteDir = $file.Substring(0, $file.LastIndexOf('/'))
    }
    
    # Tạo thư mục nếu cần
    if ($remoteDir) {
        ssh -o ConnectTimeout=3 ${VPS_USER}@${VPS_IP} "mkdir -p ${VPS_PATH}/$remoteDir" 2>&1 | Out-Null
    }
    
    # Copy với compression
    scp -C -o ConnectTimeout=10 $file ${VPS_USER}@${VPS_IP}:${VPS_PATH}/$file 2>&1 | Out-Null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host " [OK]" -ForegroundColor Green
    } else {
        Write-Host " [FAILED]" -ForegroundColor Red
        $failedFiles += $file
    }
}

if ($failedFiles.Count -gt 0) {
    Write-Host "[Fast Deploy] Warning: Failed: $($failedFiles -join ', ')" -ForegroundColor Red
    exit 1
}

# Nếu requirements.txt được deploy, cài đặt dependencies
if ($changedFiles -contains "requirements.txt") {
    Write-Host "[Fast Deploy] Installing/updating dependencies..." -ForegroundColor Cyan
    ssh -o ConnectTimeout=10 ${VPS_USER}@${VPS_IP} "cd ${VPS_PATH} && source venv/bin/activate && pip install -r requirements.txt --quiet" 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[Fast Deploy] Dependencies updated successfully" -ForegroundColor Green
    } else {
        Write-Host "[Fast Deploy] Warning: Failed to install dependencies" -ForegroundColor Yellow
    }
}

Write-Host "[Fast Deploy] Restarting service..." -ForegroundColor Cyan
$restartCmd = "cd ${VPS_PATH} && sudo systemctl restart screenshot-analyzer 2>/dev/null || (pkill -f uvicorn.*main:app 2>/dev/null; nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > /dev/null 2>&1 &)"
ssh -o ConnectTimeout=5 ${VPS_USER}@${VPS_IP} $restartCmd 2>&1 | Out-Null

Write-Host "[Fast Deploy] Done! http://${VPS_IP}:8000/admin" -ForegroundColor Green

