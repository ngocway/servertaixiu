"""
Service quản lý dữ liệu phiên cược (session history)
"""
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional
import re


class SessionService:
    def __init__(self, db_path: str = "logs.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Khởi tạo database và tạo bảng session_history nếu chưa có"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS session_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                session_time TEXT NOT NULL,
                bet_placed TEXT NOT NULL,
                result TEXT,
                total_bet TEXT NOT NULL,
                winnings TEXT,
                win_loss TEXT NOT NULL,
                image_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tạo index cho session_id để tìm kiếm nhanh
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_session_id 
            ON session_history(session_id)
        """)
        
        # Tạo index cho created_at để sắp xếp nhanh
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_created_at 
            ON session_history(created_at DESC)
        """)
        
        conn.commit()
        conn.close()
    
    def parse_ocr_text(self, ocr_text: str) -> List[Dict]:
        """
        Parse text từ OCR thành danh sách các session
        
        Format mong đợi:
        Phiên|Thời gian|Đặt cược|Kết quả|Tổng cược|Tiền thắng|Thắng/Thua
        524124|03-11-2025 17:41:46|Tài|Tài|2,000|+1,960|Thắng
        """
        sessions = []
        lines = ocr_text.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('Phiên|') or line.startswith('...'):
                continue
            
            # Tách các cột bằng dấu |
            parts = line.split('|')
            
            # Cần ít nhất 7 cột
            if len(parts) >= 7:
                session = {
                    'session_id': parts[0].strip(),
                    'session_time': parts[1].strip(),
                    'bet_placed': parts[2].strip(),
                    'result': parts[3].strip() if parts[3].strip() else None,
                    'total_bet': parts[4].strip(),
                    'winnings': parts[5].strip() if parts[5].strip() else None,
                    'win_loss': parts[6].strip()
                }
                
                # Validate session_id (phải là số)
                if session['session_id'] and session['session_id'].replace(',', '').replace('.', '').isdigit():
                    sessions.append(session)
        
        return sessions
    
    def session_exists(self, session_id: str) -> bool:
        """Kiểm tra xem session đã tồn tại trong database chưa"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COUNT(*) FROM session_history 
            WHERE session_id = ?
        """, (session_id,))
        
        count = cursor.fetchone()[0]
        conn.close()
        
        return count > 0
    
    def add_session(self, session: Dict, image_path: Optional[str] = None) -> bool:
        """
        Thêm session mới vào database (nếu chưa tồn tại)
        Returns: True nếu thêm thành công, False nếu session đã tồn tại
        """
        # Kiểm tra trùng lặp
        if self.session_exists(session['session_id']):
            return False
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO session_history 
                (session_id, session_time, bet_placed, result, total_bet, winnings, win_loss, image_path)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session['session_id'],
                session['session_time'],
                session['bet_placed'],
                session.get('result'),
                session['total_bet'],
                session.get('winnings'),
                session['win_loss'],
                image_path
            ))
            
            conn.commit()
            
            # Cleanup: Chỉ giữ 100 sessions mới nhất
            cursor.execute("""
                DELETE FROM session_history 
                WHERE id NOT IN (
                    SELECT id FROM session_history 
                    ORDER BY created_at DESC 
                    LIMIT 100
                )
            """)
            
            conn.commit()
            return True
            
        except sqlite3.IntegrityError:
            # Session đã tồn tại (UNIQUE constraint)
            return False
        finally:
            conn.close()
    
    def get_recent_sessions(self, limit: int = 100) -> List[Dict]:
        """Lấy danh sách các session gần nhất (tối đa 100)"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                id,
                session_id,
                session_time,
                bet_placed,
                result,
                total_bet,
                winnings,
                win_loss,
                image_path,
                created_at
            FROM session_history
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        sessions = []
        for row in rows:
            sessions.append({
                'id': row['id'],
                'session_id': row['session_id'],
                'session_time': row['session_time'],
                'bet_placed': row['bet_placed'],
                'result': row['result'],
                'total_bet': row['total_bet'],
                'winnings': row['winnings'],
                'win_loss': row['win_loss'],
                'image_path': row['image_path'],
                'created_at': row['created_at']
            })
        
        return sessions
    
    def get_session_count(self) -> int:
        """Đếm tổng số session trong database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM session_history")
        count = cursor.fetchone()[0]
        
        conn.close()
        return count
    
    def delete_session(self, session_id: str) -> bool:
        """Xóa session theo session_id"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            DELETE FROM session_history WHERE session_id = ?
        """, (session_id,))
        
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return deleted
    
    def clear_all_sessions(self):
        """Xóa tất cả sessions (cẩn thận!)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM session_history")
        
        conn.commit()
        conn.close()


