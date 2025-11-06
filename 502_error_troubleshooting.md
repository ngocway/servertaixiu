# Khắc Phục Lỗi 502 Bad Gateway - Hướng Dẫn Chi Tiết

## 🔍 Lỗi 502 Bad Gateway Là Gì?

Lỗi **502 Bad Gateway** xảy ra khi **nginx** (web server của bạn) không thể nhận được phản hồi hợp lệ từ **upstream server** (thường là application server như PHP-FPM, Node.js, Python, etc.)

Trong trường hợp của bạn: `nginx/1.18.0 (Ubuntu)` đang chạy nhưng không kết nối được với backend application.

---

## 🎯 Nguyên Nhân Chính

### 1. **Application Server Bị Crash/Dừng**
- PHP-FPM, Node.js, hoặc backend service không chạy
- Process bị kill do thiếu RAM
- Application bị lỗi và tự động dừng

### 2. **Timeout - Quá Thời Gian Chờ**
- Request xử lý quá lâu (query database chậm, API external timeout)
- Nginx timeout chờ backend response

### 3. **Cấu Hình Sai**
- Socket/Port không đúng trong nginx config
- Upstream server config sai địa chỉ
- Firewall chặn connection

### 4. **Quá Tải Tài Nguyên**
- RAM đầy
- CPU 100%
- Quá nhiều connections đồng thời

### 5. **Permission Issues**
- Socket file không có quyền đọc/ghi
- Nginx user không thể connect đến application socket

---

## 🛠️ Cách Khắc Phục Triệt Để

### BƯỚC 1: Kiểm Tra Application Server

```bash
# Kiểm tra PHP-FPM (nếu dùng PHP)
sudo systemctl status php8.1-fpm
# hoặc
sudo systemctl status php7.4-fpm

# Kiểm tra Node.js/PM2 (nếu dùng Node.js)
pm2 status
pm2 logs

# Kiểm tra Python/Gunicorn (nếu dùng Python)
sudo systemctl status gunicorn

# Kiểm tra các process đang chạy
ps aux | grep php-fpm
ps aux | grep node
ps aux | grep gunicorn
```

**Nếu service không chạy:**
```bash
# Khởi động lại service
sudo systemctl start php8.1-fpm
# hoặc
pm2 restart all
# hoặc
sudo systemctl start gunicorn
```

---

### BƯỚC 2: Kiểm Tra Nginx Error Logs

```bash
# Xem log lỗi nginx (quan trọng nhất!)
sudo tail -f /var/log/nginx/error.log

# Xem access log
sudo tail -f /var/log/nginx/access.log

# Xem toàn bộ log gần đây
sudo tail -100 /var/log/nginx/error.log
```

**Các lỗi thường gặp trong log:**
- `connect() failed (111: Connection refused)` → Backend không chạy
- `upstream timed out` → Backend xử lý quá chậm
- `no live upstreams` → Tất cả backend servers đều down
- `permission denied` → Lỗi phân quyền

---

### BƯỚC 3: Kiểm Tra Application Logs

```bash
# PHP-FPM logs
sudo tail -f /var/log/php8.1-fpm.log
sudo tail -f /var/log/php-fpm/error.log

# PM2/Node.js logs
pm2 logs --lines 100

# Gunicorn logs
sudo journalctl -u gunicorn -n 100

# Application specific logs (Laravel, Django, etc.)
tail -f /path/to/your/app/storage/logs/laravel.log
tail -f /path/to/your/app/logs/application.log
```

---

### BƯỚC 4: Kiểm Tra Tài Nguyên Server

```bash
# Kiểm tra RAM
free -h

# Kiểm tra CPU
top
# hoặc
htop

# Kiểm tra disk space
df -h

# Kiểm tra số connections
netstat -an | grep ESTABLISHED | wc -l
```

**Nếu hết RAM:**
```bash
# Thêm SWAP nếu chưa có
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Hoặc restart services để giải phóng RAM
sudo systemctl restart php8.1-fpm
sudo systemctl restart nginx
```

---

### BƯỚC 5: Kiểm Tra Cấu Hình Nginx

```bash
# Xem cấu hình nginx cho site admin
sudo cat /etc/nginx/sites-enabled/lukistar.space

# Test cấu hình nginx
sudo nginx -t

# Nếu có thay đổi, reload nginx
sudo systemctl reload nginx
```

**Kiểm tra các điểm sau trong config:**

1. **Upstream configuration:**
```nginx
upstream backend {
    server 127.0.0.1:9000;  # hoặc unix:/run/php/php8.1-fpm.sock
}
```

2. **Proxy/FastCGI settings:**
```nginx
location ~ \.php$ {
    fastcgi_pass unix:/run/php/php8.1-fpm.sock;
    fastcgi_index index.php;
    include fastcgi_params;
}
```

3. **Timeout settings (tăng nếu cần):**
```nginx
proxy_connect_timeout 600;
proxy_send_timeout 600;
proxy_read_timeout 600;
send_timeout 600;

# Hoặc cho FastCGI
fastcgi_connect_timeout 600;
fastcgi_send_timeout 600;
fastcgi_read_timeout 600;
```

---

### BƯỚC 6: Kiểm Tra Socket/Port Connection

```bash
# Kiểm tra PHP-FPM socket
ls -la /run/php/php8.1-fpm.sock

# Kiểm tra port đang lắng nghe
sudo netstat -tulpn | grep LISTEN
# hoặc
sudo ss -tulpn | grep LISTEN

# Test connection đến backend
curl -I http://127.0.0.1:9000  # nếu dùng port
```

---

### BƯỚC 7: Fix Permission Issues

```bash
# Đảm bảo nginx có quyền truy cập socket
sudo chmod 777 /run/php/php8.1-fpm.sock

# Hoặc cấu hình đúng user/group trong PHP-FPM pool config
sudo nano /etc/php/8.1/fpm/pool.d/www.conf

# Tìm và đảm bảo:
listen.owner = www-data
listen.group = www-data
listen.mode = 0660

# Sau đó restart
sudo systemctl restart php8.1-fpm
```

---

## 🚀 Giải Pháp Tối Ưu Lâu Dài

### 1. **Tăng Timeout Values**
Trong `/etc/nginx/sites-enabled/lukistar.space`:
```nginx
location /admin {
    proxy_connect_timeout 300;
    proxy_send_timeout 300;
    proxy_read_timeout 300;
    
    # hoặc cho PHP
    fastcgi_read_timeout 300;
}
```

### 2. **Tăng Worker Processes và Connections**
Trong `/etc/nginx/nginx.conf`:
```nginx
worker_processes auto;
events {
    worker_connections 2048;
}
```

### 3. **Tối Ưu PHP-FPM Pool**
Trong `/etc/php/8.1/fpm/pool.d/www.conf`:
```ini
pm = dynamic
pm.max_children = 50
pm.start_servers = 5
pm.min_spare_servers = 5
pm.max_spare_servers = 35
pm.max_requests = 500
```

### 4. **Setup Monitoring và Auto-Restart**
```bash
# Cài đặt monitoring
sudo apt install monit

# Cấu hình auto-restart khi service down
sudo nano /etc/monit/conf.d/php-fpm
```

Thêm:
```
check process php-fpm with pidfile /var/run/php/php8.1-fpm.pid
    start program = "/bin/systemctl start php8.1-fpm"
    stop program = "/bin/systemctl stop php8.1-fpm"
    if failed unixsocket /var/run/php/php8.1-fpm.sock then restart
    if 3 restarts within 5 cycles then timeout
```

### 5. **Log Rotation**
Đảm bảo logs không làm đầy disk:
```bash
sudo nano /etc/logrotate.d/nginx
```

### 6. **Database Optimization**
Nếu admin panel chậm do database:
```bash
# Optimize MySQL/MariaDB
mysql -u root -p
> OPTIMIZE TABLE your_table;
> ANALYZE TABLE your_table;

# Tăng connection pool, query cache
```

### 7. **Caching Layer**
- Setup Redis/Memcached cho application
- Enable Nginx FastCGI cache
- Optimize application code

---

## 📋 Checklist Khắc Phục Nhanh

Khi gặp lỗi 502, làm theo thứ tự:

- [ ] 1. Kiểm tra application server có chạy không (`systemctl status`)
- [ ] 2. Xem nginx error log (`tail -f /var/log/nginx/error.log`)
- [ ] 3. Xem application error log
- [ ] 4. Kiểm tra RAM/CPU (`free -h`, `top`)
- [ ] 5. Restart application server
- [ ] 6. Restart nginx
- [ ] 7. Kiểm tra cấu hình nginx (`nginx -t`)
- [ ] 8. Tăng timeout nếu cần
- [ ] 9. Fix permissions nếu cần
- [ ] 10. Monitor logs để xác định vấn đề gốc

---

## 🆘 Lệnh Khắc Phục Nhanh (Quick Fix)

```bash
# Restart tất cả services liên quan
sudo systemctl restart php8.1-fpm
sudo systemctl restart nginx

# Hoặc nếu dùng Node.js
pm2 restart all
sudo systemctl restart nginx

# Kiểm tra status
sudo systemctl status php8.1-fpm
sudo systemctl status nginx

# Xem logs real-time
sudo tail -f /var/log/nginx/error.log
```

---

## 📞 Debug Script

Tạo file `debug-502.sh`:
```bash
#!/bin/bash
echo "=== Checking Nginx Status ==="
sudo systemctl status nginx | head -5

echo -e "\n=== Checking PHP-FPM Status ==="
sudo systemctl status php8.1-fpm | head -5

echo -e "\n=== Recent Nginx Errors ==="
sudo tail -20 /var/log/nginx/error.log

echo -e "\n=== System Resources ==="
free -h
df -h | grep -v loop

echo -e "\n=== Listening Ports ==="
sudo netstat -tulpn | grep LISTEN | grep -E '(nginx|php)'

echo -e "\n=== Recent PHP-FPM Errors ==="
sudo tail -20 /var/log/php8.1-fpm.log 2>/dev/null || echo "No PHP-FPM log found"
```

Chạy:
```bash
chmod +x debug-502.sh
./debug-502.sh
```

---

## 💡 Lời Khuyên

1. **Luôn xem logs trước** - Logs sẽ cho bạn biết chính xác vấn đề
2. **Monitor tài nguyên** - Nhiều lỗi 502 do hết RAM
3. **Backup cấu hình** trước khi thay đổi
4. **Test từng bước** - Không thay đổi nhiều thứ cùng lúc
5. **Setup alerts** - Biết ngay khi có vấn đề

---

Chúc bạn khắc phục thành công! 🎉

