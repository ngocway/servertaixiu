"""
Template Service - Quản lý ảnh mẫu và so sánh với screenshots
"""
import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import shutil


class TemplateService:
    def __init__(self, db_path: str = "logs.db", templates_dir: str = "templates"):
        self.db_path = db_path
        self.templates_dir = templates_dir
        
        # Tạo thư mục templates nếu chưa có
        os.makedirs(templates_dir, exist_ok=True)
        
        # Khởi tạo database
        self._init_db()
    
    def _init_db(self):
        """Tạo bảng template_images và cập nhật analysis_logs"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tạo bảng template_images
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS template_images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                filename TEXT NOT NULL,
                green_dots_positions TEXT NOT NULL,
                image_width INTEGER,
                image_height INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active INTEGER DEFAULT 0,
                description TEXT
            )
        """)
        
        # Kiểm tra và thêm cột mới vào analysis_logs nếu chưa có
        cursor.execute("PRAGMA table_info(analysis_logs)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'template_id' not in columns:
            cursor.execute("ALTER TABLE analysis_logs ADD COLUMN template_id INTEGER")
        
        if 'match_score' not in columns:
            cursor.execute("ALTER TABLE analysis_logs ADD COLUMN match_score REAL")
        
        conn.commit()
        conn.close()
    
    def save_template(self, image_data: bytes, name: str, green_dots: List[Dict], 
                     width: int, height: int, description: str = "", 
                     extension: str = "png") -> int:
        """
        Lưu template image và metadata
        CHỈ CHO PHÉP 1 TEMPLATE DUY NHẤT - Xóa template cũ trước khi tạo mới
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Xóa tất cả templates cũ (files + database)
        cursor.execute("SELECT id, filename FROM template_images")
        old_templates = cursor.fetchall()
        
        for old_id, old_filename in old_templates:
            # Xóa file ảnh cũ
            old_filepath = os.path.join(self.templates_dir, old_filename)
            if os.path.exists(old_filepath):
                try:
                    os.remove(old_filepath)
                except Exception as e:
                    print(f"Warning: Could not delete old template file: {e}")
        
        # Xóa tất cả records cũ
        cursor.execute("DELETE FROM template_images")
        conn.commit()
        
        # Tạo template mới
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        filename = f"template_{timestamp}.{extension}"
        filepath = os.path.join(self.templates_dir, filename)
        
        # Lưu file ảnh
        with open(filepath, "wb") as f:
            f.write(image_data)
        
        # Lưu metadata vào DB (luôn active vì chỉ có 1)
        cursor.execute("""
            INSERT INTO template_images 
            (name, filename, green_dots_positions, image_width, image_height, description, is_active)
            VALUES (?, ?, ?, ?, ?, ?, 1)
        """, (name, filename, json.dumps(green_dots), width, height, description))
        
        template_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return template_id
    
    def get_template(self, template_id: int) -> Optional[Dict]:
        """Lấy thông tin template theo ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, name, filename, green_dots_positions, image_width, image_height,
                   created_at, is_active, description
            FROM template_images
            WHERE id = ?
        """, (template_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return {
            "id": row[0],
            "name": row[1],
            "filename": row[2],
            "green_dots_positions": json.loads(row[3]),
            "image_width": row[4],
            "image_height": row[5],
            "created_at": row[6],
            "is_active": bool(row[7]),
            "description": row[8],
            "filepath": os.path.join(self.templates_dir, row[2])
        }
    
    def list_templates(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """Lấy danh sách templates"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, name, filename, green_dots_positions, image_width, image_height,
                   created_at, is_active, description
            FROM template_images
            ORDER BY is_active DESC, created_at DESC
            LIMIT ? OFFSET ?
        """, (limit, offset))
        
        rows = cursor.fetchall()
        conn.close()
        
        templates = []
        for row in rows:
            templates.append({
                "id": row[0],
                "name": row[1],
                "filename": row[2],
                "dots_count": len(json.loads(row[3])),
                "image_width": row[4],
                "image_height": row[5],
                "created_at": row[6],
                "is_active": bool(row[7]),
                "description": row[8]
            })
        
        return templates
    
    def get_active_template(self) -> Optional[Dict]:
        """
        Lấy template (luôn chỉ có 1 template duy nhất)
        Kept for backward compatibility
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, name, filename, green_dots_positions, image_width, image_height,
                   created_at, is_active, description
            FROM template_images
            LIMIT 1
        """)
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return {
            "id": row[0],
            "name": row[1],
            "filename": row[2],
            "green_dots_positions": json.loads(row[3]),
            "image_width": row[4],
            "image_height": row[5],
            "created_at": row[6],
            "is_active": bool(row[7]),
            "description": row[8],
            "filepath": os.path.join(self.templates_dir, row[2])
        }
    
    def set_active_template(self, template_id: int) -> bool:
        """Set template làm active (deactivate các template khác)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Deactivate tất cả templates
        cursor.execute("UPDATE template_images SET is_active = 0")
        
        # Activate template được chọn
        cursor.execute("""
            UPDATE template_images 
            SET is_active = 1 
            WHERE id = ?
        """, (template_id,))
        
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        
        return affected > 0
    
    def delete_template(self, template_id: int) -> bool:
        """Xóa template (file và database)"""
        # Lấy thông tin template
        template = self.get_template(template_id)
        if not template:
            return False
        
        # Xóa file ảnh
        filepath = template["filepath"]
        if os.path.exists(filepath):
            os.remove(filepath)
        
        # Xóa từ database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM template_images WHERE id = ?", (template_id,))
        conn.commit()
        conn.close()
        
        return True
    
    def update_dots_positions(self, template_id: int, green_dots: List[Dict]) -> bool:
        """Cập nhật vị trí các nốt xanh"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE template_images 
            SET green_dots_positions = ?
            WHERE id = ?
        """, (json.dumps(green_dots), template_id))
        
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        
        return affected > 0
    
    def compare_with_template(self, screenshot_dots: List[Dict], 
                             template_dots: List[Dict], 
                             tolerance: int = 10) -> Tuple[float, Dict]:
        """
        So sánh screenshot dots với template dots
        
        Returns:
            match_score: Điểm khớp (0-100)
            details: Chi tiết matching
        """
        if not template_dots:
            return 0.0, {"matched": 0, "missing": [], "extra": []}
        
        matched_dots = []
        missing_dots = []
        
        # Check từng dot trong template
        for t_dot in template_dots:
            found = False
            for s_dot in screenshot_dots:
                # Tính khoảng cách Euclidean
                distance = ((t_dot["x"] - s_dot["x"]) ** 2 + 
                           (t_dot["y"] - s_dot["y"]) ** 2) ** 0.5
                
                if distance <= tolerance:
                    matched_dots.append(t_dot["number"])
                    found = True
                    break
            
            if not found:
                missing_dots.append(t_dot["number"])
        
        # Tìm extra dots (dots có trong screenshot nhưng không có trong template)
        extra_dots = []
        for s_dot in screenshot_dots:
            found = False
            for t_dot in template_dots:
                distance = ((t_dot["x"] - s_dot["x"]) ** 2 + 
                           (t_dot["y"] - s_dot["y"]) ** 2) ** 0.5
                if distance <= tolerance:
                    found = True
                    break
            if not found:
                extra_dots.append(s_dot.get("number", -1))
        
        # Tính match score
        match_score = (len(matched_dots) / len(template_dots)) * 100 if template_dots else 0
        
        return match_score, {
            "matched": len(matched_dots),
            "matched_dots": matched_dots,
            "missing": len(missing_dots),
            "missing_dots": missing_dots,
            "extra": len(extra_dots),
            "extra_dots": extra_dots,
            "total_template_dots": len(template_dots),
            "total_screenshot_dots": len(screenshot_dots)
        }
    
    def get_template_filepath(self, template_id: int) -> Optional[str]:
        """Lấy đường dẫn file của template"""
        template = self.get_template(template_id)
        if not template:
            return None
        return template["filepath"]
    
    def get_templates_count(self) -> int:
        """Đếm số lượng templates"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM template_images")
        count = cursor.fetchone()[0]
        conn.close()
        return count

