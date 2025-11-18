$file = "app/main.py"
$content = Get-Content $file -Raw -Encoding UTF8

# Thay logic tính win_loss
$oldLogic = @'
            result_value = parsed_response.get("result") or parsed_response.get("Result")
            if not result_value:
                detail_match = re.search(r'Đặt\s+([A-Za-zÀ-ỹ]+).*?Kết\s+quả:\s*([A-Za-zÀ-ỹ]+)', chatgpt_text, re.IGNORECASE | re.DOTALL)
                if detail_match:
                    result_value = detail_match.group(2)

            bet_choice_norm = normalize_choice(betting_method)
            result_choice_norm = normalize_choice(result_value)

            if bet_choice_norm and result_choice_norm:
                win_loss_token = "win" if bet_choice_norm == result_choice_norm else "loss"
            else:
                win_loss_token = None
'@

$newLogic = @'
            # Lấy giá trị "Tiền thắng" từ dòng đầu tiên của bảng để tính win_loss
            winnings_amount = None
            
            # Thử lấy từ JSON response trước
            winnings_amount_raw = parsed_response.get("winnings_amount") or parsed_response.get("winnings")
            if winnings_amount_raw is not None:
                winnings_amount = parse_numeric_value(winnings_amount_raw)
            
            # Nếu không có trong JSON, parse từ text ChatGPT (tìm số trong cột "Tiền thắng")
            if winnings_amount is None:
                # Tìm số có thể có dấu + hoặc - trong text (ví dụ: +980, -1000, 0)
                winnings_match = re.search(r'Tiền\s+thắng[:\s]+([+\-]?\d[\d,\.]*)', chatgpt_text, re.IGNORECASE)
                if not winnings_match:
                    # Thử tìm số có dấu + hoặc - ở đầu dòng đầu tiên của bảng
                    winnings_match = re.search(r'([+\-]?\d[\d,\.]+)', chatgpt_text)
                if winnings_match:
                    winnings_amount = parse_numeric_value(winnings_match.group(1))

            # Tính win_loss dựa trên winnings_amount
            if winnings_amount is not None:
                if winnings_amount > 0:
                    win_loss_token = "win"
                elif winnings_amount < 0:
                    win_loss_token = "loss"
                else:  # winnings_amount == 0
                    win_loss_token = None
            else:
                win_loss_token = None
'@

$content = $content.Replace($oldLogic, $newLogic)
Set-Content $file -Value $content -Encoding UTF8 -NoNewline
Write-Host "Done!"
















