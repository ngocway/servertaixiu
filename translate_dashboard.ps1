$file = "app/main.py"
$content = Get-Content $file -Raw -Encoding UTF8

# Replace Vietnamese text in HTML/JavaScript
$content = $content -replace 'Theo dÃµi áº£nh tá»« thiáº¿t bá»‹ mobile vÃ tráº¡ng thÃ¡i phÃ¢n tÃ­ch tá»± Ä''á»™ng', 'Monitor mobile device images and automatic analysis status'
$content = $content -replace 'Gá»­i form-data gá»"m', 'Send form-data including'
$content = $content -replace 'Thiáº¿t bá»‹', 'Devices'
$content = $content -replace 'Báº£n ghi', 'Records'
$content = $content -replace 'LÃ m má»›i', 'Refresh'
$content = $content -replace 'Hiá»ƒn thá»‹', 'Display'
$content = $content -replace 'báº£n ghi má»›i nháº¥t', 'latest records'
$content = $content -replace 'Loáº¡i áº£nh', 'Image Type'
$content = $content -replace 'PhiÃªn', 'Session'
$content = $content -replace 'GiÃ¢y', 'Seconds'
$content = $content -replace 'Tiá» n dá»± kiáº¿n', 'Planned Amount'
$content = $content -replace 'Tiá» n thá»±c', 'Actual Amount'
$content = $content -replace 'Káº¿t quáº£', 'Result'
$content = $content -replace 'Há»‡ sá»''', 'Multiplier'
$content = $content -replace 'HÃ nh Ä''á»™ng', 'Actions'
$content = $content -replace 'Thá» i gian', 'Time'
$content = $content -replace 'Ä''ang táº£i dá»¯ liá»‡u', 'Loading data...'
$content = $content -replace 'áº¢nh Run Mobile', 'Run Mobile Image'
$content = $content -replace 'Táº£i áº¢nh', 'Download Image'
$content = $content -replace 'Ä''Ã£ copy endpoint!', 'Endpoint copied!'
$content = $content -replace 'Ä''Ã£ copy JSON!', 'JSON copied!'
$content = $content -replace 'ChÆ°a cÃ³ dá»¯ liá»‡u', 'No data available'
$content = $content -replace 'Lá»—i táº£i dá»¯ liá»‡u', 'Error loading data'
$content = $content -replace 'áº¢nh', 'Image'
$content = $content -replace '"Tháº¯ng"', '"Win"'
$content = $content -replace '"Thua"', '"Loss"'
$content = $content -replace 'toLocaleString\(''vi-VN''\)', 'toLocaleString(''en-US'')'

Set-Content $file -Value $content -Encoding UTF8 -NoNewline
Write-Host "Translation completed!"






















