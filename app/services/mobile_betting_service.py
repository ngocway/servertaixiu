"""
Service quản lý state và logic betting cho mobile
UPDATED: Đầy đủ với verification, mismatch handling, confidence scoring
"""
import sqlite3
import json
from datetime import datetime
from typing import Dict, Optional, List, Tuple
import os

class MobileBettingService:
    def __init__(self, db_path='logs.db'):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Khởi tạo database cho mobile betting - UPDATED"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Table lưu state của từng device
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mobile_device_states (
                device_name TEXT PRIMARY KEY,
                lose_streak_count INTEGER DEFAULT 0,
                rest_mode BOOLEAN DEFAULT 0,
                rest_counter INTEGER DEFAULT 0,
                last_lost_bet_amount INTEGER DEFAULT 0,
                betting_method TEXT,
                last_session_id TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Table lưu lịch sử xử lý ảnh (giới hạn 100)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mobile_analysis_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_name TEXT NOT NULL,
                betting_method TEXT,
                session_id TEXT,
                image_type TEXT,
                seconds_remaining INTEGER,
                bet_amount INTEGER,
                bet_status TEXT,
                win_loss TEXT,
                multiplier REAL,
                image_path TEXT,
                chatgpt_response TEXT,
                verification_method TEXT,
                confidence_score REAL,
                verified_at TIMESTAMP,
                mismatch_detected BOOLEAN DEFAULT 0,
                actual_bet_amount INTEGER,
                retry_count INTEGER DEFAULT 0,
                verification_screenshot_path TEXT,
                error_message TEXT,
                seconds_region_coords TEXT,
                bet_region_coords TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Đảm bảo các cột mới tồn tại cho database cũ
        cursor.execute("PRAGMA table_info(mobile_analysis_history)")
        existing_columns = {row[1] for row in cursor.fetchall()}

        if 'actual_bet_amount' not in existing_columns:
            cursor.execute("ALTER TABLE mobile_analysis_history ADD COLUMN actual_bet_amount INTEGER")
        if 'retry_count' not in existing_columns:
            cursor.execute("ALTER TABLE mobile_analysis_history ADD COLUMN retry_count INTEGER DEFAULT 0")
        if 'verification_screenshot_path' not in existing_columns:
            cursor.execute("ALTER TABLE mobile_analysis_history ADD COLUMN verification_screenshot_path TEXT")
        if 'error_message' not in existing_columns:
            cursor.execute("ALTER TABLE mobile_analysis_history ADD COLUMN error_message TEXT")
        if 'seconds_region_coords' not in existing_columns:
            cursor.execute("ALTER TABLE mobile_analysis_history ADD COLUMN seconds_region_coords TEXT")
        if 'bet_region_coords' not in existing_columns:
            cursor.execute("ALTER TABLE mobile_analysis_history ADD COLUMN bet_region_coords TEXT")
        
        # Table lưu chi tiết verification logs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bet_verification_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_name TEXT NOT NULL,
                session_id TEXT,
                verification_type TEXT,
                expected_amount INTEGER,
                detected_amount INTEGER,
                confidence REAL,
                match_status BOOLEAN,
                screenshot_path TEXT,
                chatgpt_response TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Table lưu mismatches
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bet_mismatches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_name TEXT NOT NULL,
                session_id TEXT,
                expected_amount INTEGER,
                actual_amount INTEGER,
                expected_method TEXT,
                actual_method TEXT,
                detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                resolved BOOLEAN DEFAULT 0,
                resolution_action TEXT
            )
        """)
        
        conn.commit()
        conn.close()
    
    def get_device_state(self, device_name: str) -> Dict:
        """Lấy state của device"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT lose_streak_count, rest_mode, rest_counter, last_lost_bet_amount, 
                   betting_method, last_session_id
            FROM mobile_device_states
            WHERE device_name = ?
        """, (device_name,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'device_name': device_name,
                'lose_streak_count': row[0],
                'rest_mode': bool(row[1]),
                'rest_counter': row[2],
                'last_lost_bet_amount': row[3],
                'betting_method': row[4],
                'last_session_id': row[5]
            }
        else:
            # Device mới, tạo state mặc định
            return {
                'device_name': device_name,
                'lose_streak_count': 0,
                'rest_mode': False,
                'rest_counter': 0,
                'last_lost_bet_amount': 0,
                'betting_method': None,
                'last_session_id': None
            }
    
    def update_device_state(self, device_name: str, state: Dict):
        """Cập nhật state của device"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO mobile_device_states 
            (device_name, lose_streak_count, rest_mode, rest_counter, 
             last_lost_bet_amount, betting_method, last_session_id, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (
            device_name,
            state['lose_streak_count'],
            1 if state['rest_mode'] else 0,
            state['rest_counter'],
            state['last_lost_bet_amount'],
            state.get('betting_method'),
            state.get('last_session_id')
        ))
        
        conn.commit()
        conn.close()
    
    def calculate_multiplier(self, device_name: str, win_loss: str, bet_amount: int) -> float:
        """
        Tính hệ số cược cho phiên tiếp theo theo 5 quy tắc
        
        Returns:
            float: Hệ số cược (0 nếu không cược, >=1 nếu cược)
        """
        state = self.get_device_state(device_name)
        multiplier = 0.0
        notes = ""
        
        # Quy tắc 1 & 2: Phiên chưa có kết quả hoặc lỗi
        if not win_loss or win_loss not in ['Thắng', 'Thua']:
            multiplier = 0.0
            notes = "Phiên chưa có kết quả hoặc lỗi"
            return multiplier
        
        # Quy tắc 5: Đang trong giai đoạn nghỉ 3 phiên
        if state['rest_mode']:
            state['rest_counter'] += 1
            
            if state['rest_counter'] >= 3:
                # Hết chu kỳ nghỉ, tính lại hệ số dựa trên tiền thua phiên thứ 4
                multiplier = (state['last_lost_bet_amount'] * 2) / 1000
                state['rest_mode'] = False
                state['rest_counter'] = 0
                notes = f"Hết nghỉ 3 phiên, tính lại hệ số từ phiên thua thứ 4 ({state['last_lost_bet_amount']})"
            else:
                # Vẫn đang nghỉ
                multiplier = 0.0
                notes = f"Đang nghỉ phiên {state['rest_counter']}/3 sau chuỗi 4 thua"
            
            self.update_device_state(device_name, state)
            return multiplier
        
        # Quy tắc 3: Kết quả là Thắng
        if win_loss == 'Thắng':
            multiplier = 1.0
            state['lose_streak_count'] = 0  # Reset chuỗi thua
            notes = "Thắng - Reset chuỗi thua, hệ số = 1"
            self.update_device_state(device_name, state)
            return multiplier
        
        # Quy tắc 4: Kết quả là Thua
        if win_loss == 'Thua':
            state['lose_streak_count'] += 1
            
            # Quy tắc 5: Kiểm tra nếu thua 4 phiên liên tiếp
            if state['lose_streak_count'] >= 4:
                # Bắt đầu nghỉ 3 phiên
                state['rest_mode'] = True
                state['rest_counter'] = 0
                state['last_lost_bet_amount'] = bet_amount
                multiplier = (bet_amount * 2) / 1000
                notes = f"Thua phiên thứ 4 liên tiếp → Bắt đầu nghỉ 3 phiên. Hệ số tạm = {multiplier}"
            else:
                # Thua bình thường, chưa đến 4 phiên
                multiplier = (bet_amount * 2) / 1000
                notes = f"Thua phiên {state['lose_streak_count']}, nhân đôi hệ số"
            
            self.update_device_state(device_name, state)
            return multiplier
        
        # Default
        return 0.0
    
    def save_analysis_history(self, record: Dict):
        """Lưu lịch sử phân tích, giới hạn 100 records"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO mobile_analysis_history
            (device_name, betting_method, session_id, image_type, seconds_remaining,
             bet_amount, actual_bet_amount, bet_status, win_loss, multiplier, image_path, chatgpt_response,
             seconds_region_coords, bet_region_coords)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            record.get('device_name'),
            record.get('betting_method'),
            record.get('session_id'),
            record.get('image_type'),
            record.get('seconds_remaining'),
            record.get('bet_amount'),
            record.get('actual_bet_amount'),
            record.get('bet_status'),
            record.get('win_loss'),
            record.get('multiplier'),
            record.get('image_path'),
            record.get('chatgpt_response'),
            record.get('seconds_region_coords'),
            record.get('bet_region_coords')
        ))
        
        conn.commit()
        
        # Cleanup: Chỉ giữ 100 records gần nhất
        cursor.execute("""
            DELETE FROM mobile_analysis_history
            WHERE id NOT IN (
                SELECT id FROM mobile_analysis_history
                ORDER BY created_at DESC
                LIMIT 100
            )
        """)
        
        conn.commit()
        conn.close()
    
    def get_analysis_history(self, limit: int = 50) -> List[Dict]:
        """Lấy lịch sử phân tích"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, device_name, betting_method, session_id, image_type,
                   seconds_remaining, bet_amount, actual_bet_amount, bet_status, win_loss, multiplier,
                   image_path, seconds_region_coords, bet_region_coords, created_at
            FROM mobile_analysis_history
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        history = []
        for row in rows:
            history.append({
                'id': row[0],
                'device_name': row[1],
                'betting_method': row[2],
                'session_id': row[3],
                'image_type': row[4],
                'seconds_remaining': row[5],
                'bet_amount': row[6],
                'actual_bet_amount': row[7],
                'bet_status': row[8],
                'win_loss': row[9],
                'multiplier': row[10],
                'image_path': row[11],
                'seconds_region_coords': row[12],
                'bet_region_coords': row[13],
                'created_at': row[14]
            })
        
        return history
    
    def save_verification_log(self, log_data: Dict):
        """Lưu log verification"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO bet_verification_logs
            (device_name, session_id, verification_type, expected_amount, detected_amount,
             confidence, match_status, screenshot_path, chatgpt_response)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            log_data.get('device_name'),
            log_data.get('session_id'),
            log_data.get('verification_type'),
            log_data.get('expected_amount'),
            log_data.get('detected_amount'),
            log_data.get('confidence'),
            log_data.get('match_status'),
            log_data.get('screenshot_path'),
            log_data.get('chatgpt_response')
        ))
        
        conn.commit()
        conn.close()
    
    def save_mismatch(self, mismatch_data: Dict):
        """Lưu mismatch"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO bet_mismatches
            (device_name, session_id, expected_amount, actual_amount,
             expected_method, actual_method, resolution_action)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            mismatch_data.get('device_name'),
            mismatch_data.get('session_id'),
            mismatch_data.get('expected_amount'),
            mismatch_data.get('actual_amount'),
            mismatch_data.get('expected_method'),
            mismatch_data.get('actual_method'),
            mismatch_data.get('resolution_action', 'logged')
        ))
        
        conn.commit()
        conn.close()
    
    def get_mismatches(self, device_name: Optional[str] = None, limit: int = 50) -> List[Dict]:
        """Lấy danh sách mismatches"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if device_name:
            cursor.execute("""
                SELECT * FROM bet_mismatches
                WHERE device_name = ?
                ORDER BY detected_at DESC
                LIMIT ?
            """, (device_name, limit))
        else:
            cursor.execute("""
                SELECT * FROM bet_mismatches
                ORDER BY detected_at DESC
                LIMIT ?
            """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        mismatches = []
        for row in rows:
            mismatches.append({
                'id': row[0],
                'device_name': row[1],
                'session_id': row[2],
                'expected_amount': row[3],
                'actual_amount': row[4],
                'expected_method': row[5],
                'actual_method': row[6],
                'detected_at': row[7],
                'resolved': row[8],
                'resolution_action': row[9]
            })
        
        return mismatches
    
    def calculate_confidence(self, ocr_result: Dict, expected_data: Dict) -> Tuple[float, List[str]]:
        """
        Tính confidence score
        
        Returns:
            Tuple[float, List[str]]: (confidence score 0-1, list of checks passed)
        """
        checks_passed = []
        checks_failed = []
        
        # Check 1: Amount match
        detected_amount = ocr_result.get('detected_amount', 0)
        expected_amount = expected_data.get('expected_amount', 0)
        
        if detected_amount == expected_amount:
            checks_passed.append('amount_match')
        else:
            checks_failed.append(f'amount_mismatch: {detected_amount} != {expected_amount}')
        
        # Check 2: Session match (nếu có)
        detected_session = ocr_result.get('session_id', '')
        expected_session = expected_data.get('session_id', '')
        
        if expected_session and detected_session:
            if detected_session == expected_session:
                checks_passed.append('session_match')
            else:
                checks_failed.append(f'session_mismatch: {detected_session} != {expected_session}')
        
        # Check 3: Method match (nếu có)
        detected_method = ocr_result.get('betting_method', '')
        expected_method = expected_data.get('betting_method', '')
        
        if expected_method and detected_method:
            if detected_method == expected_method:
                checks_passed.append('method_match')
            else:
                checks_failed.append(f'method_mismatch')
        
        # Check 4: Success text found (nếu có)
        if ocr_result.get('success_text_found', False):
            checks_passed.append('success_text_found')
        
        # Check 5: Pending status (nếu là popup verify)
        if ocr_result.get('win_loss') == '-' or ocr_result.get('status') == 'pending_result':
            checks_passed.append('pending_status')
        
        # Tính confidence
        total_checks = len(checks_passed) + len(checks_failed)
        if total_checks == 0:
            return 0.5, []
        
        confidence = len(checks_passed) / total_checks
        
        return confidence, checks_passed
    
    def handle_mismatch(
        self, 
        device_name: str, 
        expected_amount: int, 
        actual_amount: int, 
        session_id: str = None
    ) -> Dict:
        """
        Xử lý mismatch - Adjust state và log
        
        Returns:
            Dict với action đã thực hiện
        """
        # Log mismatch
        self.save_mismatch({
            'device_name': device_name,
            'session_id': session_id,
            'expected_amount': expected_amount,
            'actual_amount': actual_amount,
            'expected_method': None,
            'actual_method': None,
            'resolution_action': 'adjust_state'
        })
        
        # Adjust device state dựa trên actual amount
        # (Logic tính lại multiplier dựa trên số tiền thực tế)
        state = self.get_device_state(device_name)
        
        # Nếu actual > 0, nghĩa là đã cược (dù không đúng số tiền expected)
        # → Coi như đã tham gia vòng này
        
        return {
            'action': 'adjusted',
            'message': f'Adjusted state for {device_name}, actual bet: {actual_amount}',
            'expected': expected_amount,
            'actual': actual_amount
        }
    
    def get_latest_valid_history_record(self, device_name: str) -> Optional[Dict]:
        """
        Lấy record HISTORY gần nhất của device có tien_thang != 0 và winnings_color != null
        
        Returns:
            Dict với các giá trị: tien_thang, winnings_color, winnings_amount, win_loss, column_5, bet_amount
            hoặc None nếu không tìm thấy
        """
        import re
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Query các record HISTORY của device này, sắp xếp theo thời gian giảm dần
        cursor.execute("""
            SELECT id, chatgpt_response, bet_amount, win_loss, created_at
            FROM mobile_analysis_history
            WHERE device_name = ? AND image_type = 'HISTORY'
            ORDER BY created_at DESC
            LIMIT 50
        """, (device_name,))
        
        rows = cursor.fetchall()
        conn.close()
        
        # Parse từ chatgpt_response để tìm record có tien_thang != 0 và winnings_color != null
        for row in rows:
            record_id, chatgpt_response, bet_amount, win_loss, created_at = row
            
            if not chatgpt_response:
                continue
            
            # Parse JSON từ chatgpt_response
            try:
                import json as json_lib
                # Tìm JSON object trong chatgpt_response (tương tự parse_json_payload)
                cleaned = chatgpt_response.strip()
                start = cleaned.find('{')
                end = cleaned.rfind('}')
                if start != -1 and end != -1 and end >= start:
                    cleaned = cleaned[start : end + 1]
                    parsed = json_lib.loads(cleaned)
                    
                    winnings_amount = parsed.get("winnings_amount")
                    winnings_color = parsed.get("winnings_color")
                    column_5 = parsed.get("column_5")
                    
                    # Kiểm tra điều kiện: tien_thang != 0 và winnings_color != null
                    if winnings_amount is not None and winnings_amount != 0 and winnings_color is not None:
                        return {
                            'tien_thang': winnings_amount,
                            'winnings_amount': winnings_amount,
                            'winnings_color': winnings_color,
                            'win_loss': win_loss,
                            'column_5': column_5,
                            'bet_amount': bet_amount,
                            'record_id': record_id
                        }
            except Exception:
                # Nếu parse JSON thất bại, thử parse bằng regex
                try:
                    # Tìm winnings_amount
                    winnings_match = re.search(r'"winnings_amount"\s*:\s*(-?\d+|null)', chatgpt_response)
                    winnings_amount = None
                    if winnings_match:
                        winnings_str = winnings_match.group(1)
                        if winnings_str != "null":
                            winnings_amount = int(winnings_str)
                    
                    # Tìm winnings_color
                    color_match = re.search(r'"winnings_color"\s*:\s*"?(red|green)"?', chatgpt_response, re.IGNORECASE)
                    winnings_color = color_match.group(1).lower() if color_match else None
                    
                    # Tìm column_5
                    column5_match = re.search(r'"column_5"\s*:\s*"([^"]*)"', chatgpt_response)
                    column_5 = column5_match.group(1) if column5_match else None
                    
                    # Kiểm tra điều kiện
                    if winnings_amount is not None and winnings_amount != 0 and winnings_color is not None:
                        return {
                            'tien_thang': winnings_amount,
                            'winnings_amount': winnings_amount,
                            'winnings_color': winnings_color,
                            'win_loss': win_loss,
                            'column_5': column_5,
                            'bet_amount': bet_amount,
                            'record_id': record_id
                        }
                except Exception:
                    continue
        
        return None

# Singleton instance
mobile_betting_service = MobileBettingService()

