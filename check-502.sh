#!/bin/bash

# Script kiểm tra lỗi 502 Bad Gateway
# Tạo bởi AI Assistant

echo "======================================"
echo "  KIỂM TRA LỖI 502 BAD GATEWAY"
echo "======================================"
echo ""

# Màu sắc cho output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Kiểm tra Nginx
echo -e "${YELLOW}[1] Kiểm tra Nginx Status...${NC}"
if systemctl is-active --quiet nginx; then
    echo -e "${GREEN}✓ Nginx đang chạy${NC}"
else
    echo -e "${RED}✗ Nginx KHÔNG chạy!${NC}"
    echo "   → Chạy: sudo systemctl start nginx"
fi
echo ""

# 2. Kiểm tra PHP-FPM
echo -e "${YELLOW}[2] Kiểm tra PHP-FPM Status...${NC}"
PHP_FOUND=false
for version in 8.2 8.1 8.0 7.4 7.3; do
    if systemctl list-unit-files | grep -q "php${version}-fpm"; then
        if systemctl is-active --quiet php${version}-fpm; then
            echo -e "${GREEN}✓ PHP ${version}-FPM đang chạy${NC}"
            PHP_FOUND=true
        else
            echo -e "${RED}✗ PHP ${version}-FPM KHÔNG chạy!${NC}"
            echo "   → Chạy: sudo systemctl start php${version}-fpm"
            PHP_FOUND=true
        fi
        break
    fi
done

if [ "$PHP_FOUND" = false ]; then
    echo -e "${YELLOW}⚠ Không tìm thấy PHP-FPM${NC}"
    echo "   Kiểm tra service khác (Node.js, Python, etc.)"
fi
echo ""

# 3. Kiểm tra PM2 (Node.js)
echo -e "${YELLOW}[3] Kiểm tra PM2 (Node.js)...${NC}"
if command -v pm2 &> /dev/null; then
    PM2_STATUS=$(pm2 jlist 2>/dev/null | grep -o '"status":"online"' | wc -l)
    if [ "$PM2_STATUS" -gt 0 ]; then
        echo -e "${GREEN}✓ PM2 có $PM2_STATUS process đang chạy${NC}"
    else
        echo -e "${RED}✗ PM2 không có process nào chạy${NC}"
        echo "   → Chạy: pm2 restart all"
    fi
else
    echo "  PM2 không được cài đặt"
fi
echo ""

# 4. Kiểm tra RAM
echo -e "${YELLOW}[4] Kiểm tra RAM...${NC}"
MEMORY_USAGE=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100}')
if [ "$MEMORY_USAGE" -gt 90 ]; then
    echo -e "${RED}✗ RAM sử dụng: ${MEMORY_USAGE}% - QUÁ CAO!${NC}"
    echo "   → Cần restart services hoặc thêm SWAP"
elif [ "$MEMORY_USAGE" -gt 75 ]; then
    echo -e "${YELLOW}⚠ RAM sử dụng: ${MEMORY_USAGE}% - Cao${NC}"
else
    echo -e "${GREEN}✓ RAM sử dụng: ${MEMORY_USAGE}% - Tốt${NC}"
fi
free -h
echo ""

# 5. Kiểm tra Disk Space
echo -e "${YELLOW}[5] Kiểm tra Disk Space...${NC}"
DISK_USAGE=$(df -h / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 90 ]; then
    echo -e "${RED}✗ Disk sử dụng: ${DISK_USAGE}% - ĐẦY!${NC}"
elif [ "$DISK_USAGE" -gt 75 ]; then
    echo -e "${YELLOW}⚠ Disk sử dụng: ${DISK_USAGE}% - Cao${NC}"
else
    echo -e "${GREEN}✓ Disk sử dụng: ${DISK_USAGE}% - Tốt${NC}"
fi
df -h / | grep -v loop
echo ""

# 6. Kiểm tra Nginx Error Log (10 dòng cuối)
echo -e "${YELLOW}[6] Nginx Error Log (10 dòng gần nhất)...${NC}"
if [ -f /var/log/nginx/error.log ]; then
    sudo tail -10 /var/log/nginx/error.log
else
    echo "  Không tìm thấy error log"
fi
echo ""

# 7. Kiểm tra socket/port đang listen
echo -e "${YELLOW}[7] Kiểm tra Ports/Sockets đang Listen...${NC}"
echo "Nginx ports:"
sudo netstat -tulpn 2>/dev/null | grep nginx || sudo ss -tulpn | grep nginx
echo ""
echo "PHP-FPM sockets:"
sudo ls -lah /run/php/*.sock 2>/dev/null || echo "  Không tìm thấy socket"
echo ""

# 8. Test cấu hình Nginx
echo -e "${YELLOW}[8] Test cấu hình Nginx...${NC}"
if sudo nginx -t 2>&1 | grep -q "successful"; then
    echo -e "${GREEN}✓ Cấu hình Nginx OK${NC}"
else
    echo -e "${RED}✗ Cấu hình Nginx có LỖI:${NC}"
    sudo nginx -t
fi
echo ""

# 9. Tóm tắt và khuyến nghị
echo "======================================"
echo -e "${YELLOW}TÓM TẮT VÀ KHUYẾN NGHỊ:${NC}"
echo "======================================"

# Kiểm tra các vấn đề thường gặp
ISSUES=0

if ! systemctl is-active --quiet nginx; then
    echo -e "${RED}→ Nginx không chạy - KHỞI ĐỘNG NGAY!${NC}"
    echo "  sudo systemctl start nginx"
    ((ISSUES++))
fi

PHP_RUNNING=false
for version in 8.2 8.1 8.0 7.4; do
    if systemctl is-active --quiet php${version}-fpm 2>/dev/null; then
        PHP_RUNNING=true
        break
    fi
done

if [ "$PHP_RUNNING" = false ] && [ "$PHP_FOUND" = true ]; then
    echo -e "${RED}→ PHP-FPM không chạy - KHỞI ĐỘNG NGAY!${NC}"
    echo "  sudo systemctl start php8.1-fpm  # (hoặc version bạn dùng)"
    ((ISSUES++))
fi

if [ "$MEMORY_USAGE" -gt 90 ]; then
    echo -e "${RED}→ RAM quá cao - CẦN XỬ LÝ!${NC}"
    echo "  sudo systemctl restart php-fpm && sudo systemctl restart nginx"
    ((ISSUES++))
fi

if [ -f /var/log/nginx/error.log ]; then
    if sudo grep -q "Connection refused" /var/log/nginx/error.log | tail -20; then
        echo -e "${RED}→ Backend service không chạy hoặc không kết nối được${NC}"
        ((ISSUES++))
    fi
    if sudo grep -q "upstream timed out" /var/log/nginx/error.log | tail -20; then
        echo -e "${RED}→ Backend xử lý quá chậm - cần tăng timeout${NC}"
        ((ISSUES++))
    fi
fi

if [ $ISSUES -eq 0 ]; then
    echo -e "${GREEN}✓ Không phát hiện vấn đề rõ ràng${NC}"
    echo ""
    echo "Nếu vẫn gặp lỗi 502, hãy:"
    echo "  1. Kiểm tra application logs chi tiết"
    echo "  2. Xem file: 502_error_troubleshooting.md"
    echo "  3. Kiểm tra cấu hình upstream trong nginx"
fi

echo ""
echo "======================================"
echo "Để xem hướng dẫn chi tiết, đọc file:"
echo "  502_error_troubleshooting.md"
echo "======================================"

