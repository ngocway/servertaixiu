# Deploy trực tiếp lên VPS qua SCP (chỉ deploy file thay đổi)
$VPS_IP = "97.74.83.97"
$VPS_USER = "myadmin"
$VPS_PATH = "~/screenshot-analyzer"

Write-Host "[Fast Deploy] Detecting changed files..." -ForegroundColor Cyan

# Danh sách file có thể deploy
$allPossibleFiles = @(
    "app/main.py",
    "app/services/mobile_betting_service.py",
    "requirements.txt",
    "config.py"
)

# Kiểm tra file nào đã thay đổi (so với Git HEAD)
$changedFiles = @()
foreach ($file in $allPossibleFiles) {
    if (Test-Path $file) {
        # Kiểm tra xem file có thay đổi không (so với HEAD)
        $gitStatus = git diff --name-only HEAD -- $file 2>&1
        $gitStatusUnstaged = git diff --name-only -- $file 2>&1
        
        if ($gitStatus -or $gitStatusUnstaged -or (git ls-files --error-unmatch $file 2>&1)) {
            # File đã thay đổi hoặc chưa được track
            $changedFiles += $file
        }
    }
}

# Nếu không có file nào thay đổi, kiểm tra file đã modified (không commit)
if ($changedFiles.Count -eq 0) {
    $modifiedFiles = git diff --name-only 2>&1
    $untrackedFiles = git ls-files --others --exclude-standard 2>&1
    
    foreach ($file in $allPossibleFiles) {
        if ($modifiedFiles -match [regex]::Escape($file) -or $untrackedFiles -match [regex]::Escape($file)) {
            if (Test-Path $file) {
                $changedFiles += $file
            }
        }
    }
}

# Nếu vẫn không có, deploy tất cả file quan trọng (fallback)
if ($changedFiles.Count -eq 0) {
    Write-Host "  No changes detected, deploying all important files..." -ForegroundColor Yellow
    $changedFiles = $allPossibleFiles | Where-Object { Test-Path $_ }
}

if ($changedFiles.Count -eq 0) {
    Write-Host "[Fast Deploy] No files to deploy!" -ForegroundColor Yellow
    exit 0
}

Write-Host "[Fast Deploy] Found $($changedFiles.Count) file(s) to deploy:" -ForegroundColor Green
foreach ($file in $changedFiles) {
    Write-Host "  - $file" -ForegroundColor Gray
}

Write-Host "[Fast Deploy] Copying files to VPS..." -ForegroundColor Cyan

# Copy file với compression và chỉ copy file thay đổi
$failedFiles = @()
foreach ($file in $changedFiles) {
    Write-Host "  Copying $file..." -ForegroundColor Gray -NoNewline
    $remoteDir = $file.Substring(0, $file.LastIndexOf('/'))
    
    # Tạo thư mục remote nếu cần
    if ($remoteDir) {
        ssh -o Compression=yes -o CompressionLevel=9 ${VPS_USER}@${VPS_IP} "mkdir -p ${VPS_PATH}/$remoteDir" 2>&1 | Out-Null
    }
    
    # Copy với compression để nhanh hơn
    scp -C -o Compression=yes $file ${VPS_USER}@${VPS_IP}:${VPS_PATH}/$file 2>&1 | Out-Null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host " ✓" -ForegroundColor Green
    } else {
        Write-Host " ✗" -ForegroundColor Red
        $failedFiles += $file
    }
}

if ($failedFiles.Count -gt 0) {
    Write-Host "[Fast Deploy] Warning: Failed to copy $($failedFiles.Count) file(s)" -ForegroundColor Yellow
    foreach ($file in $failedFiles) {
        Write-Host "  - $file" -ForegroundColor Red
    }
}

Write-Host "[Fast Deploy] Restarting service on VPS..." -ForegroundColor Cyan

# Restart service trên VPS (sử dụng systemd nếu có, nếu không thì dùng nohup)
$restartResult = ssh -o Compression=yes ${VPS_USER}@${VPS_IP} "cd ${VPS_PATH} && sudo systemctl restart screenshot-analyzer 2>/dev/null || (pkill -f 'uvicorn.*main:app' 2>/dev/null; nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > /dev/null 2>&1 &)" 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "[Fast Deploy] Done! Server: http://${VPS_IP}:8000/admin" -ForegroundColor Green
} else {
    Write-Host "[Fast Deploy] Warning: Service restart may have failed" -ForegroundColor Yellow
    Write-Host "[Fast Deploy] Server: http://${VPS_IP}:8000/admin" -ForegroundColor Green
}







