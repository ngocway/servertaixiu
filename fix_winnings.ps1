$file = "app/main.py"
$content = Get-Content $file -Raw -Encoding UTF8

# Thay prompt
$content = $content -replace '   - Doc phan "Chi tiet".*?bet_amount":<so tien>}\.', @'
   - Lay so trong cot "Tong cuoc" (Tổng cược) cua dong nay (bo dau phan cach nghin) va gan vao khoa "bet_amount" duoi dang so nguyen.
   - Lay so trong cot "Tien thang" (Tiền thắng) cua dong nay (bo dau phan cach nghin, bao gom dau + hoac -) va gan vao khoa "winnings_amount" duoi dang so nguyen (co the am hoac duong).
   - Lay so phien o cot "Phien" cua dong nay lam gia tri cho khoa "Id" (bo ky tu "#" neu co).
   - Tra ve dung JSON: {"image_type":"HISTORY","Id":"<ma phien>","bet_amount":<so tien>,"winnings_amount":<so tien thang/thua>}.
'@

Set-Content $file -Value $content -Encoding UTF8 -NoNewline
Write-Host "Done!"


















