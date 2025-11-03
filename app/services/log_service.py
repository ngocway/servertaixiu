"""
Service để quản lý log screenshots và kết quả phân tích
"""
import sqlite3
import os
import json
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional
from pathlib import Path


class LogService:
    def __init__(self, db_path: str = "logs.db", screenshots_dir: str = "screenshots"):
        self.db_path = db_path
        self.screenshots_dir = screenshots_dir
        os.makedirs(screenshots_dir, exist_ok=True)
        self._init_database()

    def _init_database(self):
        """Khởi tạo database nếu chưa tồn tại"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analysis_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                screenshot_filename TEXT NOT NULL,
                screenshot_path TEXT NOT NULL,
                total_dots INTEGER,
                white_count INTEGER,
                black_count INTEGER,
                analysis_result TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        conn.commit()
        conn.close()

    def save_analysis(
        self,
        screenshot_data: bytes,
        analysis_result: Dict,
        screenshot_extension: str = "png",
        template_id: Optional[int] = None,
        match_score: Optional[float] = None
    ) -> int:
        """
        Lưu screenshot và kết quả phân tích
        
        Trả về ID của log entry
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        screenshot_filename = f"screenshot_{timestamp}.{screenshot_extension}"
        screenshot_path = os.path.join(self.screenshots_dir, screenshot_filename)

        # Lưu screenshot
        with open(screenshot_path, "wb") as f:
            f.write(screenshot_data)

        # Lưu vào database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Đảm bảo các cột template_id và match_score tồn tại
        cursor.execute("PRAGMA table_info(analysis_logs)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'template_id' not in columns:
            cursor.execute("ALTER TABLE analysis_logs ADD COLUMN template_id INTEGER")
        
        if 'match_score' not in columns:
            cursor.execute("ALTER TABLE analysis_logs ADD COLUMN match_score REAL")
        
        # Sử dụng giờ Việt Nam (UTC+7)
        vn_tz = timezone(timedelta(hours=7))
        created_at = datetime.now(vn_tz).isoformat()
        
        cursor.execute("""
            INSERT INTO analysis_logs 
            (timestamp, screenshot_filename, screenshot_path, total_dots, white_count, black_count, 
             analysis_result, created_at, template_id, match_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            timestamp,
            screenshot_filename,
            screenshot_path,
            analysis_result.get("total", 0),
            analysis_result.get("white", 0),
            analysis_result.get("black", 0),
            json.dumps(analysis_result, ensure_ascii=False),
            created_at,
            template_id,
            match_score
        ))
        
        log_id = cursor.lastrowid
        conn.commit()
        
        # ==================== AUTO-CLEANUP: Chỉ giữ 20 screenshots mới nhất ====================
        MAX_SCREENSHOTS = 20
        
        # Đếm tổng số logs
        cursor.execute("SELECT COUNT(*) FROM analysis_logs")
        total_logs = cursor.fetchone()[0]
        
        if total_logs > MAX_SCREENSHOTS:
            # Tính số logs cần xóa
            to_delete = total_logs - MAX_SCREENSHOTS
            
            # Lấy danh sách logs cũ nhất (ORDER BY created_at ASC)
            cursor.execute("""
                SELECT id, screenshot_path 
                FROM analysis_logs 
                ORDER BY created_at ASC 
                LIMIT ?
            """, (to_delete,))
            
            old_logs = cursor.fetchall()
            
            for old_log_id, old_screenshot_path in old_logs:
                # Xóa file ảnh
                if old_screenshot_path and os.path.exists(old_screenshot_path):
                    try:
                        os.remove(old_screenshot_path)
                        print(f"Deleted old screenshot: {old_screenshot_path}")
                    except Exception as e:
                        print(f"Warning: Could not delete screenshot file: {e}")
                
                # Xóa từ database
                cursor.execute("DELETE FROM analysis_logs WHERE id = ?", (old_log_id,))
            
            conn.commit()
            print(f"Auto-cleanup: Deleted {to_delete} old screenshot(s). Kept {MAX_SCREENSHOTS} newest.")
        
        conn.close()
        
        return log_id

    def get_log(self, log_id: int) -> Optional[Dict]:
        """Lấy log theo ID"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM analysis_logs WHERE id = ?
        """, (log_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        result = dict(row)
        result["analysis_result"] = json.loads(result["analysis_result"])
        return result

    def list_logs(
        self,
        limit: int = 100,
        offset: int = 0,
        order_by: str = "created_at",
        order_direction: str = "DESC"
    ) -> List[Dict]:
        """Lấy danh sách logs"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        valid_order_by = ["id", "timestamp", "created_at", "total_dots"]
        if order_by not in valid_order_by:
            order_by = "created_at"
        
        order_direction = "DESC" if order_direction.upper() == "DESC" else "ASC"
        
        cursor.execute(f"""
            SELECT id, timestamp, screenshot_filename, total_dots, white_count, black_count, created_at, analysis_result
            FROM analysis_logs
            ORDER BY {order_by} {order_direction}
            LIMIT ? OFFSET ?
        """, (limit, offset))
        
        rows = cursor.fetchall()
        conn.close()
        
        # Parse analysis_result JSON
        result = []
        for row in rows:
            row_dict = dict(row)
            if row_dict.get("analysis_result"):
                try:
                    row_dict["analysis_result"] = json.loads(row_dict["analysis_result"])
                except:
                    row_dict["analysis_result"] = None
            result.append(row_dict)
        
        return result

    def get_logs_count(self) -> int:
        """Đếm tổng số logs"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM analysis_logs")
        count = cursor.fetchone()[0]
        conn.close()
        return count

    def get_screenshot_path(self, log_id: int) -> Optional[str]:
        """Lấy đường dẫn screenshot của log"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT screenshot_path FROM analysis_logs WHERE id = ?", (log_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row and os.path.exists(row[0]):
            return row[0]
        return None

