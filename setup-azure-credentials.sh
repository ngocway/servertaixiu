#!/bin/bash
# Script setup Azure Computer Vision credentials

echo "=================================================="
echo "  SETUP AZURE COMPUTER VISION CREDENTIALS"
echo "=================================================="
echo ""

ENV_FILE="/home/myadmin/screenshot-analyzer/.env"

# Azure credentials from user's image
AZURE_KEY="EEaWyBtz0U7Aw1d30xm8uNdlQahX4IFUMOZPMPSkH6uJeWJYvFwmJQQJ99BKACqBBLyXJ3W3AAAFACOGxAsr"
AZURE_ENDPOINT="https://taixiu.cognitiveservices.azure.com/"

echo "📝 Thêm Azure credentials vào .env file..."

# Check if .env exists
if [ ! -f "$ENV_FILE" ]; then
    echo "⚠️  File .env chưa tồn tại, tạo mới..."
    touch "$ENV_FILE"
fi

# Check if Azure credentials already exist
if grep -q "AZURE_COMPUTER_VISION_KEY" "$ENV_FILE"; then
    echo "⚠️  Azure credentials đã tồn tại trong .env"
    echo "   Cập nhật giá trị mới..."
    
    # Remove old values
    sed -i '/AZURE_COMPUTER_VISION_KEY/d' "$ENV_FILE"
    sed -i '/AZURE_COMPUTER_VISION_ENDPOINT/d' "$ENV_FILE"
fi

# Add new credentials
echo "" >> "$ENV_FILE"
echo "# Azure Computer Vision Credentials" >> "$ENV_FILE"
echo "AZURE_COMPUTER_VISION_KEY=$AZURE_KEY" >> "$ENV_FILE"
echo "AZURE_COMPUTER_VISION_ENDPOINT=$AZURE_ENDPOINT" >> "$ENV_FILE"

echo "✅ Đã thêm Azure credentials vào .env"
echo ""
echo "=================================================="
echo "  KIỂM TRA"
echo "=================================================="
echo ""
echo "Azure Key: ${AZURE_KEY:0:30}...${AZURE_KEY: -10}"
echo "Azure Endpoint: $AZURE_ENDPOINT"
echo ""
echo "=================================================="
echo "✅ HOÀN TẤT!"
echo "   Restart server để áp dụng credentials mới:"
echo "   sudo systemctl restart screenshot-analyzer"
echo "=================================================="

