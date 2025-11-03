@echo off
REM Script kiểm tra SSH key đã hoạt động chưa

set VPS_IP=97.74.83.97
set VPS_USER=myadmin

echo ========================================
echo   Checking SSH Key Status
echo ========================================
echo.

echo [1/3] Checking if SSH key exists on local...
if exist "%USERPROFILE%\.ssh\id_rsa.pub" (
    echo ✅ SSH public key found
    echo.
    echo 📋 Your public key:
    echo ========================================
    type "%USERPROFILE%\.ssh\id_rsa.pub"
    echo ========================================
    set KEY_EXISTS=YES
) else (
    echo ❌ SSH public key NOT found
    echo.
    echo 💡 Generate SSH key first:
    echo    .\setup_ssh_key.bat
    set KEY_EXISTS=NO
)
echo.

if "%KEY_EXISTS%"=="NO" (
    goto :end
)

echo [2/3] Testing SSH connection (should NOT ask password)...
echo.
echo 🔍 Testing: ssh %VPS_USER%@%VPS_IP% "echo SSH OK"
echo.
ssh -o BatchMode=yes -o ConnectTimeout=5 %VPS_USER%@%VPS_IP% "echo SSH OK" 2>nul
if errorlevel 1 (
    echo ❌ SSH key NOT working!
    echo    It will ask for password when connecting.
    echo.
    set SSH_WORKING=NO
) else (
    echo ✅ SSH key is WORKING!
    echo    No password needed!
    echo.
    set SSH_WORKING=YES
)
echo.

echo [3/3] Checking if key is installed on VPS...
ssh -o BatchMode=yes %VPS_USER%@%VPS_IP% "test -f ~/.ssh/authorized_keys && echo Key exists || echo Key missing" 2>nul
if errorlevel 1 (
    echo ⚠️  Cannot check (SSH not working yet)
) else (
    ssh -o BatchMode=yes %VPS_USER%@%VPS_IP% "grep -q 'ssh-rsa' ~/.ssh/authorized_keys 2>/dev/null && echo ✅ Key is installed on VPS || echo ⚠️  Key might not be installed"
)
echo.

echo ========================================
echo   Summary
echo ========================================
echo.

if "%KEY_EXISTS%"=="YES" (
    echo ✅ Local SSH key: Found
) else (
    echo ❌ Local SSH key: Missing
    echo    → Run: .\setup_ssh_key.bat
)

if "%SSH_WORKING%"=="YES" (
    echo ✅ SSH connection: Working (no password needed!)
    echo.
    echo 🎉 You can now use:
    echo    .\deploy_no_password.bat
    echo    .\quick_deploy.bat
    echo    All scripts will work without password!
) else (
    echo ❌ SSH connection: Not working (will ask password)
    echo.
    echo 💡 Setup SSH key:
    echo    1. Run: .\setup_ssh_key.bat
    echo    2. Enter VPS password when asked (LAST time!)
    echo    3. After that, no password needed!
)

:end
echo.
pause

