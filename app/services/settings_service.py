"""
Service để quản lý settings/cấu hình hệ thống
"""
import sqlite3
from typing import Optional


class SettingsService:
    def __init__(self, db_path: str = "logs.db"):
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """Khởi tạo bảng settings nếu chưa tồn tại"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        conn.commit()
        conn.close()

    def set_setting(self, key: str, value: str) -> bool:
        """Lưu hoặc cập nhật setting"""
        from datetime import datetime, timezone, timedelta
        
        vn_tz = timezone(timedelta(hours=7))
        updated_at = datetime.now(vn_tz).isoformat()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Upsert: Insert or update if exists
        cursor.execute("""
            INSERT INTO settings (key, value, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value,
                updated_at = excluded.updated_at
        """, (key, value, updated_at))
        
        conn.commit()
        conn.close()
        return True

    def get_setting(self, key: str) -> Optional[str]:
        """Lấy giá trị setting theo key"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return row[0]
        return None

    def set_betting_method(self, method: str) -> bool:
        """Lưu cách cược (Tài/Xỉu)"""
        if method not in ['tai', 'xiu']:
            return False
        return self.set_setting('betting_method', method)

    def get_betting_method(self) -> Optional[str]:
        """Lấy cách cược hiện tại"""
        return self.get_setting('betting_method')







