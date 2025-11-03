@echo off
REM Script setup Nginx để dùng domain thay vì IP

set VPS_IP=97.74.83.97
set VPS_USER=myadmin
set DOMAIN=lukistar.space

echo ========================================
echo   Setup Nginx for Domain
echo ========================================
echo.

echo Installing Nginx on VPS...
ssh %VPS_USER%@%VPS_IP% "sudo apt update && sudo apt install -y nginx"

echo.
echo Creating Nginx config...
ssh %VPS_USER%@%VPS_IP% "sudo tee /etc/nginx/sites-available/screenshot-analyzer > /dev/null << 'EOF'
server {
    listen 80;
    server_name %DOMAIN% www.%DOMAIN%;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection \"upgrade\";
    }
    
    client_max_body_size 50M;
    
    proxy_connect_timeout 300s;
    proxy_send_timeout 300s;
    proxy_read_timeout 300s;
}
EOF
"

echo.
echo Enabling site...
ssh %VPS_USER%@%VPS_IP% "sudo ln -sf /etc/nginx/sites-available/screenshot-analyzer /etc/nginx/sites-enabled/"

echo.
echo Testing Nginx config...
ssh %VPS_USER%@%VPS_IP% "sudo nginx -t"

echo.
echo Reloading Nginx...
ssh %VPS_USER%@%VPS_IP% "sudo systemctl reload nginx"

echo.
echo Opening firewall port 80...
ssh %VPS_USER%@%VPS_IP% "sudo ufw allow 80/tcp && sudo ufw allow 443/tcp"

echo.
echo ========================================
echo   ✅ Nginx Setup Completed!
echo ========================================
echo.
echo 🌐 Access your server:
echo    http://%DOMAIN%
echo    http://%DOMAIN%/admin
echo    http://%DOMAIN%/health
echo.
echo 📝 Note: Make sure DNS A record for %DOMAIN% points to %VPS_IP%
echo.
pause

