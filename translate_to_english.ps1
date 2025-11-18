$file = "app/main.py"
$content = Get-Content $file -Raw -Encoding UTF8

# Mapping Vietnamese to English
$replacements = @{
    'Theo dÃµi áº£nh tá»« thiáº¿t bá»‹ mobile vÃ tráº¡ng thÃ¡i phÃ¢n tÃ­ch tá»± Ä''á»™ng' = 'Monitor mobile device images and automatic analysis status'
    'Gá»­i form-data gá»"m' = 'Send form-data including'
    'Thiáº¿t bá»‹' = 'Devices'
    'Báº£n ghi' = 'Records'
    'LÃ m má»›i' = 'Refresh'
    'Hiá»ƒn thá»‹' = 'Display'
    'báº£n ghi má»›i nháº¥t' = 'latest records'
    'Loáº¡i áº£nh' = 'Image Type'
    'PhiÃªn' = 'Session'
    'GiÃ¢y' = 'Seconds'
    'Tiá» n dá»± kiáº¿n' = 'Planned Amount'
    'Tiá» n thá»±c' = 'Actual Amount'
    'Káº¿t quáº£' = 'Result'
    'Há»‡ sá»'' = 'Multiplier'
    'HÃ nh Ä''á»™ng' = 'Actions'
    'Thá» i gian' = 'Time'
    'Ä'ang táº£i dá»¯ liá»‡u' = 'Loading data...'
    'áº¢nh Run Mobile' = 'Run Mobile Image'
    'Táº£i áº¢nh' = 'Download Image'
    'Ä'Ã£ copy endpoint!' = 'Endpoint copied!'
    'ChÆ°a cÃ³ dá»¯ liá»‡u' = 'No data available'
    'Lá»—i táº£i dá»¯ liá»‡u' = 'Error loading data'
    'áº¢nh' = 'Image'
    'Tháº¯ng' = 'Win'
    'Thua' = 'Loss'
    'Chá»' = 'Pending'
}

foreach ($key in $replacements.Keys) {
    $content = $content -replace [regex]::Escape($key), $replacements[$key]
}

Set-Content $file -Value $content -Encoding UTF8 -NoNewline
Write-Host "Translation completed!"


















