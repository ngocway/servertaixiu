@echo off
REM Script test nhanh SSH key

set VPS_IP=97.74.83.97
set VPS_USER=myadmin

echo ========================================
echo   Quick SSH Key Test
echo ========================================
echo.

echo Testing SSH connection...
echo Command: ssh %VPS_USER%@%VPS_IP% "echo 'SSH OK'"
echo.

REM Test với BatchMode (không interactive, chỉ dùng key)
ssh -o BatchMode=yes -o ConnectTimeout=5 %VPS_USER%@%VPS_IP% "echo 'SSH Key Working!'" 2>nul

if errorlevel 1 (
    echo.
    echo ❌ SSH key NOT working
    echo.
    echo 🔍 Details:
    echo    - SSH key might not be installed on VPS
    echo    - Or key file is missing
    echo.
    echo 💡 Fix it:
    echo    .\setup_ssh_key.bat
    echo.
    echo Or test manually:
    echo    ssh %VPS_USER%@%VPS_IP%
    echo    (If it asks password = SSH key NOT working)
) else (
    echo.
    echo ✅✅✅ SSH Key is WORKING! ✅✅✅
    echo.
    echo 🎉 No password needed!
    echo.
    echo 📝 You can now use:
    echo    - .\deploy_no_password.bat
    echo    - .\quick_deploy.bat
    echo    - .\check_deploy.bat
    echo.
    echo All will work WITHOUT password!
)

echo.
pause

