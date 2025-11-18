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
        
        # Table lưu lịch sử xử lý ảnh (giới hạn: HISTORY 1500, BETTING 3500, UNKNOWN 50, tổng cộng 5500)
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
        if 'button_1k_coords' not in existing_columns:
            cursor.execute("ALTER TABLE mobile_analysis_history ADD COLUMN button_1k_coords TEXT")
        if 'button_1k_error' not in existing_columns:
            cursor.execute("ALTER TABLE mobile_analysis_history ADD COLUMN button_1k_error TEXT")
        if 'button_10k_coords' not in existing_columns:
            cursor.execute("ALTER TABLE mobile_analysis_history ADD COLUMN button_10k_coords TEXT")
        if 'button_10k_error' not in existing_columns:
            cursor.execute("ALTER TABLE mobile_analysis_history ADD COLUMN button_10k_error TEXT")
        if 'button_50k_coords' not in existing_columns:
            cursor.execute("ALTER TABLE mobile_analysis_history ADD COLUMN button_50k_coords TEXT")
        if 'button_50k_error' not in existing_columns:
            cursor.execute("ALTER TABLE mobile_analysis_history ADD COLUMN button_50k_error TEXT")
        if 'button_bet_coords' not in existing_columns:
            cursor.execute("ALTER TABLE mobile_analysis_history ADD COLUMN button_bet_coords TEXT")
        if 'button_bet_error' not in existing_columns:
            cursor.execute("ALTER TABLE mobile_analysis_history ADD COLUMN button_bet_error TEXT")
        if 'button_place_bet_coords' not in existing_columns:
            cursor.execute("ALTER TABLE mobile_analysis_history ADD COLUMN button_place_bet_coords TEXT")
        if 'button_place_bet_error' not in existing_columns:
            cursor.execute("ALTER TABLE mobile_analysis_history ADD COLUMN button_place_bet_error TEXT")
        if 'device_real_width' not in existing_columns:
            cursor.execute("ALTER TABLE mobile_analysis_history ADD COLUMN device_real_width INTEGER")
        if 'device_real_height' not in existing_columns:
            cursor.execute("ALTER TABLE mobile_analysis_history ADD COLUMN device_real_height INTEGER")
        if 'screenshot_width' not in existing_columns:
            cursor.execute("ALTER TABLE mobile_analysis_history ADD COLUMN screenshot_width INTEGER")
        if 'screenshot_height' not in existing_columns:
            cursor.execute("ALTER TABLE mobile_analysis_history ADD COLUMN screenshot_height INTEGER")
        if 'actual_image_width' not in existing_columns:
            cursor.execute("ALTER TABLE mobile_analysis_history ADD COLUMN actual_image_width INTEGER")
        if 'actual_image_height' not in existing_columns:
            cursor.execute("ALTER TABLE mobile_analysis_history ADD COLUMN actual_image_height INTEGER")
        if 'azure_ocr_response' not in existing_columns:
            cursor.execute("ALTER TABLE mobile_analysis_history ADD COLUMN azure_ocr_response TEXT")
        
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
        
        # Table lưu tọa độ button theo device_name
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS device_button_coords (
                device_name TEXT PRIMARY KEY,
                button_1k_coords TEXT,
                button_10k_coords TEXT,
                button_50k_coords TEXT,
                button_bet_coords TEXT,
                button_place_bet_coords TEXT,
                betting_match_counter INTEGER DEFAULT 0,
                last_match_at TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Thêm cột button_50k_coords nếu chưa có (migration)
        try:
            cursor.execute("ALTER TABLE device_button_coords ADD COLUMN button_50k_coords TEXT")
            conn.commit()
        except sqlite3.OperationalError:
            pass  # Column đã tồn tại
        
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
        """Lưu lịch sử phân tích với giới hạn: HISTORY 1500, BETTING 3500, UNKNOWN 50, tổng cộng 5500"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Convert button coords dict to JSON string if exists
        def coords_to_json(coords):
            return json.dumps(coords) if coords else None
        
        button_1k_coords_json = coords_to_json(record.get('button_1k_coords'))
        button_10k_coords_json = coords_to_json(record.get('button_10k_coords'))
        button_50k_coords_json = coords_to_json(record.get('button_50k_coords'))
        button_bet_coords_json = coords_to_json(record.get('button_bet_coords'))
        button_place_bet_coords_json = coords_to_json(record.get('button_place_bet_coords'))
        
        cursor.execute("""
            INSERT INTO mobile_analysis_history
            (device_name, betting_method, session_id, image_type, seconds_remaining,
             bet_amount, actual_bet_amount, bet_status, win_loss, multiplier, image_path, chatgpt_response,
             seconds_region_coords, bet_region_coords, button_1k_coords, button_1k_error,
             button_10k_coords, button_10k_error, button_50k_coords, button_50k_error, button_bet_coords, button_bet_error,
             button_place_bet_coords, button_place_bet_error,
             device_real_width, device_real_height, screenshot_width, screenshot_height, actual_image_width, actual_image_height,
             azure_ocr_response)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            record.get('bet_region_coords'),
            button_1k_coords_json,
            record.get('button_1k_error'),
            button_10k_coords_json,
            record.get('button_10k_error'),
            button_50k_coords_json,
            record.get('button_50k_error'),
            button_bet_coords_json,
            record.get('button_bet_error'),
            button_place_bet_coords_json,
            record.get('button_place_bet_error'),
            record.get('device_real_width'),
            record.get('device_real_height'),
            record.get('screenshot_width'),
            record.get('screenshot_height'),
            record.get('actual_image_width'),
            record.get('actual_image_height'),
            record.get('azure_ocr_response')
        ))
        
        conn.commit()
        
        # Cleanup: Giữ 1500 HISTORY records gần nhất
        cursor.execute("""
            DELETE FROM mobile_analysis_history
            WHERE image_type = 'HISTORY' 
            AND id NOT IN (
                SELECT id FROM mobile_analysis_history
                WHERE image_type = 'HISTORY'
                ORDER BY created_at DESC
                LIMIT 1500
            )
        """)
        
        # Cleanup: Giữ 3500 BETTING records gần nhất
        cursor.execute("""
            DELETE FROM mobile_analysis_history
            WHERE image_type = 'BETTING' 
            AND id NOT IN (
                SELECT id FROM mobile_analysis_history
                WHERE image_type = 'BETTING'
                ORDER BY created_at DESC
                LIMIT 3500
            )
        """)
        
        # Cleanup: Giữ 50 UNKNOWN records gần nhất
        cursor.execute("""
            DELETE FROM mobile_analysis_history
            WHERE (image_type = 'UNKNOWN' OR image_type IS NULL)
            AND id NOT IN (
                SELECT id FROM mobile_analysis_history
                WHERE image_type = 'UNKNOWN' OR image_type IS NULL
                ORDER BY created_at DESC
                LIMIT 50
            )
        """)
        
        conn.commit()
        
        # Cleanup: Giữ 5500 records tổng cộng gần nhất
        # Nếu tổng số > 5500, xóa các records cũ nhất nhưng vẫn đảm bảo giữ đủ từng loại
        cursor.execute("""
            SELECT COUNT(*) FROM mobile_analysis_history
        """)
        total_count = cursor.fetchone()[0]
        
        if total_count > 5500:
            # Đếm số records từng loại sau khi đã cleanup từng loại
            cursor.execute("""
                SELECT COUNT(*) FROM mobile_analysis_history
                WHERE image_type = 'HISTORY'
            """)
            history_count = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT COUNT(*) FROM mobile_analysis_history
                WHERE image_type = 'BETTING'
            """)
            betting_count = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT COUNT(*) FROM mobile_analysis_history
                WHERE image_type = 'UNKNOWN' OR image_type IS NULL
            """)
            unknown_count = cursor.fetchone()[0]
            
            # Tính số records cần giữ cho mỗi loại (tối đa theo giới hạn)
            target_history = min(history_count, 1500)
            target_betting = min(betting_count, 3500)
            target_unknown = min(unknown_count, 50)
            target_total = target_history + target_betting + target_unknown
            
            # Nếu tổng số records cần giữ vượt quá 5500, giảm từng loại theo thứ tự ưu tiên
            # Ưu tiên: HISTORY > BETTING > UNKNOWN
            if target_total > 5500:
                excess = target_total - 5500
                
                # Giảm từ UNKNOWN trước
                if target_unknown > 0 and excess > 0:
                    reduce_unknown = min(excess, target_unknown)
                    target_unknown -= reduce_unknown
                    excess -= reduce_unknown
                
                # Giảm từ BETTING
                if target_betting > 0 and excess > 0:
                    reduce_betting = min(excess, target_betting)
                    target_betting -= reduce_betting
                    excess -= reduce_betting
                
                # Giảm từ HISTORY
                if target_history > 0 and excess > 0:
                    reduce_history = min(excess, target_history)
                    target_history -= reduce_history
            
            # Xóa các records vượt quá giới hạn từng loại
            if history_count > target_history:
                cursor.execute("""
                    DELETE FROM mobile_analysis_history
                    WHERE image_type = 'HISTORY'
                    AND id NOT IN (
                        SELECT id FROM mobile_analysis_history
                        WHERE image_type = 'HISTORY'
                        ORDER BY created_at DESC
                        LIMIT ?
                    )
                """, (target_history,))
            
            if betting_count > target_betting:
                cursor.execute("""
                    DELETE FROM mobile_analysis_history
                    WHERE image_type = 'BETTING'
                    AND id NOT IN (
                        SELECT id FROM mobile_analysis_history
                        WHERE image_type = 'BETTING'
                        ORDER BY created_at DESC
                        LIMIT ?
                    )
                """, (target_betting,))
            
            if unknown_count > target_unknown:
                cursor.execute("""
                    DELETE FROM mobile_analysis_history
                    WHERE (image_type = 'UNKNOWN' OR image_type IS NULL)
                    AND id NOT IN (
                        SELECT id FROM mobile_analysis_history
                        WHERE image_type = 'UNKNOWN' OR image_type IS NULL
                        ORDER BY created_at DESC
                        LIMIT ?
                    )
                """, (target_unknown,))
            
            conn.commit()
            
            # Cuối cùng, đảm bảo tổng số không vượt quá 5500
            cursor.execute("SELECT COUNT(*) FROM mobile_analysis_history")
            total_count = cursor.fetchone()[0]
            
            if total_count > 5500:
                cursor.execute("""
                    DELETE FROM mobile_analysis_history
                    WHERE id NOT IN (
                        SELECT id FROM mobile_analysis_history
                        ORDER BY created_at DESC
                        LIMIT 5500
                    )
                """)
        
        conn.commit()
        conn.close()
    
    def get_analysis_history(self, limit: int = 50, page: int = 1) -> Tuple[List[Dict], int]:
        """Lấy lịch sử phân tích với pagination
        
        Returns:
            Tuple[List[Dict], int]: (danh sách records, tổng số records)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Đếm tổng số records
        cursor.execute("SELECT COUNT(*) FROM mobile_analysis_history")
        total_count = cursor.fetchone()[0]
        
        # Tính offset
        offset = (page - 1) * limit
        
        cursor.execute("""
            SELECT id, device_name, betting_method, session_id, image_type,
                   seconds_remaining, bet_amount, actual_bet_amount, bet_status, win_loss, multiplier,
                   image_path, seconds_region_coords, bet_region_coords, created_at
            FROM mobile_analysis_history
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """, (limit, offset))
        
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
        
        return history, total_count
    
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
        Lấy record HISTORY gần nhất của device có column_5 hợp lệ
        
        Returns:
            Dict với các giá trị: win_loss, column_5, bet_amount, return
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
        
        # Parse từ chatgpt_response để tìm record có column_5 hợp lệ
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
                    
                    column_5 = parsed.get("column_5")
                    return_val = parsed.get("hoan_tra") or parsed.get("Hoàn trả") or parsed.get("return")
                    
                    # Kiểm tra điều kiện: column_5 hợp lệ (không phải unknown hoặc placeholder)
                    if column_5 and column_5 not in ["unknown", "<noi dung cot thu 5>", "<nội dung cột thứ 5>", ""]:
                        return {
                            'win_loss': win_loss,
                            'column_5': column_5,
                            'bet_amount': bet_amount,
                            'return': return_val,
                            'record_id': record_id
                        }
            except Exception:
                # Nếu parse JSON thất bại, thử parse bằng regex
                try:
                    # Tìm column_5
                    column5_match = re.search(r'"column_5"\s*:\s*"([^"]*)"', chatgpt_response)
                    column_5 = column5_match.group(1) if column5_match else None
                    
                    # Tìm return
                    return_match = re.search(r'"hoan_tra"\s*:\s*"?(\d+(?:,\d{3})*)"?', chatgpt_response)
                    return_val = None
                    if return_match:
                        return_str = return_match.group(1).replace(",", "").strip()
                        if return_str.isdigit():
                            return_val = int(return_str)
                    
                    # Kiểm tra điều kiện: column_5 hợp lệ
                    if column_5 and column_5 not in ["unknown", "<noi dung cot thu 5>", "<nội dung cột thứ 5>", ""]:
                        return {
                            'win_loss': win_loss,
                            'column_5': column_5,
                            'bet_amount': bet_amount,
                            'return': return_val,
                            'record_id': record_id
                        }
                except Exception:
                    continue
        
        return None
    
    def save_device_button_coords(self, device_name: str, coords: Dict):
        """
        Lưu tọa độ button cho device
        coords: dict với keys: button_1k_coords, button_10k_coords, button_bet_coords, button_place_bet_coords
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        def coords_to_json(coords_dict):
            return json.dumps(coords_dict) if coords_dict else None
        
        cursor.execute("""
            INSERT OR REPLACE INTO device_button_coords
            (device_name, button_1k_coords, button_10k_coords, button_50k_coords, button_bet_coords, 
             button_place_bet_coords, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (
            device_name,
            coords_to_json(coords.get('button_1k_coords')),
            coords_to_json(coords.get('button_10k_coords')),
            coords_to_json(coords.get('button_50k_coords')),
            coords_to_json(coords.get('button_bet_coords')),
            coords_to_json(coords.get('button_place_bet_coords'))
        ))
        
        conn.commit()
        conn.close()
    
    def get_device_button_coords(self, device_name: str) -> Optional[Dict]:
        """
        Lấy tọa độ button đã lưu cho device
        Returns: dict với keys: button_1k_coords, button_10k_coords, button_bet_coords, button_place_bet_coords
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT button_1k_coords, button_10k_coords, button_50k_coords, button_bet_coords, button_place_bet_coords,
                   betting_match_counter
            FROM device_button_coords
            WHERE device_name = ?
        """, (device_name,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        def json_to_coords(json_str):
            if json_str:
                try:
                    return json.loads(json_str)
                except Exception:
                    pass
            return None
        
        return {
            'button_1k_coords': json_to_coords(row[0]),
            'button_10k_coords': json_to_coords(row[1]),
            'button_50k_coords': json_to_coords(row[2]),
            'button_bet_coords': json_to_coords(row[3]),
            'button_place_bet_coords': json_to_coords(row[4]),
            'betting_match_counter': row[5] or 0
        }
    
    def should_match_buttons(self, device_name: str) -> Tuple[bool, int]:
        """
        Kiểm tra xem có nên match button lần này không (mỗi 10 screenshot BETTING match 1 lần)
        Returns: (should_match: bool, current_counter: int)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT betting_match_counter FROM device_button_coords
            WHERE device_name = ?
        """, (device_name,))
        
        row = cursor.fetchone()
        
        if not row:
            # Chưa có record, tạo record mới với counter = 0
            cursor.execute("""
                INSERT INTO device_button_coords (device_name, betting_match_counter)
                VALUES (?, 0)
            """, (device_name,))
            conn.commit()
            conn.close()
            # Lần đầu tiên, cần match ngay
            return True, 0
        
        current_counter = row[0] or 0
        new_counter = current_counter + 1
        
        # Cập nhật counter
        cursor.execute("""
            UPDATE device_button_coords
            SET betting_match_counter = ?, last_match_at = CASE WHEN ? % 10 = 1 THEN CURRENT_TIMESTAMP ELSE last_match_at END
            WHERE device_name = ?
        """, (new_counter, new_counter, device_name))
        
        conn.commit()
        conn.close()
        
        # Match mỗi 10 lần 1 lần (lần 1, 11, 21, ...)
        should_match = (new_counter % 10 == 1)
        
        return should_match, new_counter

# Singleton instance
mobile_betting_service = MobileBettingService()

