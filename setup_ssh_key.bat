@echo off
REM Script setup SSH key để không cần nhập password nữa

set VPS_IP=97.74.83.97
set VPS_USER=myadmin

echo ========================================
echo   Setup SSH Key (No Password Required)
echo ========================================
echo.

echo [Step 1/4] Checking if SSH key exists...
if exist "%USERPROFILE%\.ssh\id_rsa.pub" (
    echo ✅ SSH public key found
    set KEY_EXISTS=YES
) else (
    echo ⚠️  SSH key not found
    echo 📦 Generating SSH key...
    
    echo.
    echo ⚠️  You will be asked to enter a passphrase
    echo    (Press Enter twice to skip passphrase - optional)
    echo.
    echo y | ssh-keygen -t rsa -b 4096 -f "%USERPROFILE%\.ssh\id_rsa" -C "screenshot-analyzer" -N ""
    if errorlevel 1 (
        echo ❌ Failed to generate SSH key
        pause
        exit /b 1
    )
    echo ✅ SSH key generated
    set KEY_EXISTS=YES
)

echo.
echo [Step 2/4] Displaying public key...
echo.
echo 📋 Copy the public key below:
echo ========================================
type "%USERPROFILE%\.ssh\id_rsa.pub"
echo ========================================
echo.

echo [Step 3/4] Installing SSH key on VPS...
echo.
echo ⚠️  You need to enter VPS password ONCE to install the key
echo.
echo 📝 Instructions:
echo    1. You will be asked for VPS password (this is the LAST time!)
echo    2. The key will be automatically installed
echo    3. After this, NO MORE passwords needed!
echo.
pause

echo.
echo 🔐 Connecting to VPS and installing key...
echo    (Enter VPS password when asked)
echo.

REM Install key using ssh-copy-id if available, otherwise manual method
where ssh-copy-id >nul 2>&1
if errorlevel 1 (
    REM Manual method - create .ssh directory and add key
    echo Creating .ssh directory on VPS...
    ssh %VPS_USER%@%VPS_IP% "mkdir -p ~/.ssh && chmod 700 ~/.ssh"
    
    echo Copying public key to VPS...
    type "%USERPROFILE%\.ssh\id_rsa.pub" | ssh %VPS_USER%@%VPS_IP% "cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"
) else (
    ssh-copy-id %VPS_USER%@%VPS_IP%
)

if errorlevel 1 (
    echo ❌ Failed to install SSH key
    echo.
    echo 💡 Manual installation:
    echo    1. Copy the public key shown above
    echo    2. SSH to VPS: ssh %VPS_USER%@%VPS_IP%
    echo    3. Run: mkdir -p ~/.ssh
    echo    4. Run: chmod 700 ~/.ssh
    echo    5. Run: nano ~/.ssh/authorized_keys
    echo    6. Paste the public key, save and exit
    echo    7. Run: chmod 600 ~/.ssh/authorized_keys
    pause
    exit /b 1
)

echo.
echo [Step 4/4] Testing SSH connection...
echo    (Should NOT ask for password now)
echo.
ssh -o BatchMode=yes %VPS_USER%@%VPS_IP% "echo 'SSH Key Working!'" 2>nul
if errorlevel 1 (
    echo ⚠️  SSH key test failed, but it might still work
    echo    Try manually: ssh %VPS_USER%@%VPS_IP%
) else (
    echo ✅ SSH key working! No password needed!
)

echo.
echo ========================================
echo   ✅ SSH Key Setup Completed!
echo ========================================
echo.
echo 🎉 From now on, you won't need to enter password!
echo.
echo 📝 Test it now:
echo    ssh %VPS_USER%@%VPS_IP%
echo.
echo 📝 Then run deploy script:
echo    .\deploy_complete.bat
echo    (Won't ask for password anymore!)
echo.
pause

