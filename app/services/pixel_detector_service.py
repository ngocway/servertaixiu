"""
Service để detect pixel màu #1AFF0D và OCR nội dung tại các vị trí đó
"""
import sqlite3
from PIL import Image
import numpy as np
from typing import List, Dict, Tuple, Optional
import io
from datetime import datetime
import pytesseract

class PixelDetectorService:
    def __init__(self, db_path: str = "logs.db"):
        self.db_path = db_path
        self.target_color = (0x1A, 0xFF, 0x0D)  # #1AFF0D in RGB
        self.color_tolerance = 10  # Tolerance cho màu sắc
        self._init_database()
    
    def _init_database(self):
        """Khởi tạo database tables cho pixel detector"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Table lưu template và các pixel đã detect
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pixel_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                image_width INTEGER NOT NULL,
                image_height INTEGER NOT NULL,
                pixel_count INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active INTEGER DEFAULT 1
            )
        """)
        
        # Table lưu vị trí các pixel
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pixel_positions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                template_id INTEGER NOT NULL,
                pixel_x INTEGER NOT NULL,
                pixel_y INTEGER NOT NULL,
                FOREIGN KEY (template_id) REFERENCES pixel_templates(id) ON DELETE CASCADE
            )
        """)
        
        # Table lưu kết quả phân tích
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pixel_analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                template_id INTEGER NOT NULL,
                analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                image_path TEXT,
                results TEXT,
                FOREIGN KEY (template_id) REFERENCES pixel_templates(id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def detect_color_pixels(self, image: Image.Image) -> List[Tuple[int, int]]:
        """
        Detect tất cả pixel có màu #1AFF0D trong ảnh
        Returns: List of (x, y) coordinates
        """
        # Convert image to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Convert to numpy array
        img_array = np.array(image)
        
        # Extract RGB channels
        r, g, b = img_array[:, :, 0], img_array[:, :, 1], img_array[:, :, 2]
        
        # Find pixels matching the target color (with tolerance)
        target_r, target_g, target_b = self.target_color
        
        matches = (
            (np.abs(r.astype(int) - target_r) <= self.color_tolerance) &
            (np.abs(g.astype(int) - target_g) <= self.color_tolerance) &
            (np.abs(b.astype(int) - target_b) <= self.color_tolerance)
        )
        
        # Get coordinates of matching pixels
        y_coords, x_coords = np.where(matches)
        
        # Return as list of (x, y) tuples
        pixel_positions = list(zip(x_coords.tolist(), y_coords.tolist()))
        
        return pixel_positions
    
    def save_template(self, name: str, image: Image.Image, pixel_positions: List[Tuple[int, int]]) -> int:
        """
        Lưu template và các vị trí pixel vào database
        Chỉ cho phép 1 template duy nhất - sẽ xóa template cũ khi upload mới
        Returns: template_id
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Xóa TẤT CẢ templates cũ (chỉ giữ 1 template duy nhất)
            cursor.execute("DELETE FROM pixel_positions WHERE template_id IN (SELECT id FROM pixel_templates)")
            cursor.execute("DELETE FROM pixel_templates")
            
            # Insert new template
            cursor.execute("""
                INSERT INTO pixel_templates (name, image_width, image_height, pixel_count, is_active)
                VALUES (?, ?, ?, ?, 1)
            """, (name, image.width, image.height, len(pixel_positions)))
            
            template_id = cursor.lastrowid
            
            # Insert pixel positions
            cursor.executemany("""
                INSERT INTO pixel_positions (template_id, pixel_x, pixel_y)
                VALUES (?, ?, ?)
            """, [(template_id, x, y) for x, y in pixel_positions])
            
            conn.commit()
            return template_id
        
        finally:
            conn.close()
    
    def get_active_template(self) -> Optional[Dict]:
        """Lấy template đang active"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT id, name, image_width, image_height, pixel_count, created_at
                FROM pixel_templates
                WHERE is_active = 1
                ORDER BY created_at DESC
                LIMIT 1
            """)
            
            row = cursor.fetchone()
            if row:
                return {
                    "id": row[0],
                    "name": row[1],
                    "image_width": row[2],
                    "image_height": row[3],
                    "pixel_count": row[4],
                    "created_at": row[5]
                }
            return None
        
        finally:
            conn.close()
    
    def get_template_pixels(self, template_id: int) -> List[Tuple[int, int]]:
        """Lấy danh sách vị trí pixel của template"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT pixel_x, pixel_y
                FROM pixel_positions
                WHERE template_id = ?
                ORDER BY id
            """, (template_id,))
            
            return [(row[0], row[1]) for row in cursor.fetchall()]
        
        finally:
            conn.close()
    
    def extract_region_around_pixel(self, image: Image.Image, x: int, y: int, 
                                    width: int = 100, height: int = 40) -> Image.Image:
        """
        Trích xuất vùng hình chữ nhật xung quanh pixel
        """
        # Calculate bounding box
        left = max(0, x - width // 2)
        top = max(0, y - height // 2)
        right = min(image.width, x + width // 2)
        bottom = min(image.height, y + height // 2)
        
        return image.crop((left, top, right, bottom))
    
    def ocr_text_from_region(self, region_image: Image.Image) -> str:
        """
        Sử dụng OCR để đọc text từ vùng ảnh
        """
        try:
            # Convert to grayscale for better OCR
            if region_image.mode != 'L':
                region_image = region_image.convert('L')
            
            # Enhance contrast
            region_array = np.array(region_image)
            region_array = np.clip(region_array * 1.5, 0, 255).astype(np.uint8)
            region_image = Image.fromarray(region_array)
            
            # OCR
            text = pytesseract.image_to_string(region_image, config='--psm 6')
            return text.strip()
        except Exception as e:
            return f"Error: {str(e)}"
    
    def count_light_dark_pixels(self, region_image: Image.Image) -> Tuple[int, int]:
        """
        Đếm số lượng pixel sáng và tối trong vùng ảnh
        Ngưỡng: 128 (0-127 là tối, 128-255 là sáng)
        Returns: (light_count, dark_count)
        """
        # Convert to grayscale
        if region_image.mode != 'L':
            gray_image = region_image.convert('L')
        else:
            gray_image = region_image
        
        # Convert to numpy array
        pixels = np.array(gray_image)
        
        # Đếm pixel sáng (>= 128) và tối (< 128)
        threshold = 128
        light_count = np.sum(pixels >= threshold)
        dark_count = np.sum(pixels < threshold)
        
        return int(light_count), int(dark_count)
    
    def analyze_image_with_template(self, image: Image.Image, template_id: int,
                                   region_width: int = 100, region_height: int = 40) -> List[Dict]:
        """
        Phân tích ảnh dựa trên template
        Kiểm tra từng pixel tại các vị trí đã đánh dấu (Sáng hoặc Tối)
        """
        pixel_positions = self.get_template_pixels(template_id)
        
        # Convert to grayscale for easier brightness check
        if image.mode != 'L':
            gray_image = image.convert('L')
        else:
            gray_image = image
        
        # Get pixel array
        pixels = np.array(gray_image)
        
        results = []
        threshold = 128  # Ngưỡng sáng/tối
        
        for idx, (x, y) in enumerate(pixel_positions, 1):
            # Check if coordinates are within image bounds
            if 0 <= x < image.width and 0 <= y < image.height:
                # Get pixel brightness value
                pixel_value = pixels[y, x]
                
                # Determine if pixel is light or dark
                is_light = pixel_value >= threshold
                result_text = "Sáng" if is_light else "Tối"
                
                results.append({
                    "position_number": idx,
                    "x": x,
                    "y": y,
                    "brightness": int(pixel_value),
                    "result": result_text
                })
            else:
                # Pixel out of bounds
                results.append({
                    "position_number": idx,
                    "x": x,
                    "y": y,
                    "brightness": 0,
                    "result": "Ngoài biên"
                })
        
        return results
    
    def save_analysis_result(self, template_id: int, results: List[Dict], image_path: str = None):
        """Lưu kết quả phân tích vào database"""
        import json
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO pixel_analyses (template_id, image_path, results)
                VALUES (?, ?, ?)
            """, (template_id, image_path, json.dumps(results)))
            
            conn.commit()
            return cursor.lastrowid
        
        finally:
            conn.close()
    
    def get_all_templates(self) -> List[Dict]:
        """Lấy tất cả templates"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT id, name, image_width, image_height, pixel_count, created_at, is_active
                FROM pixel_templates
                ORDER BY created_at DESC
            """)
            
            templates = []
            for row in cursor.fetchall():
                templates.append({
                    "id": row[0],
                    "name": row[1],
                    "image_width": row[2],
                    "image_height": row[3],
                    "pixel_count": row[4],
                    "created_at": row[5],
                    "is_active": bool(row[6])
                })
            
            return templates
        
        finally:
            conn.close()
    
    def delete_template(self, template_id: int):
        """Xóa template"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("DELETE FROM pixel_positions WHERE template_id = ?", (template_id,))
            cursor.execute("DELETE FROM pixel_templates WHERE id = ?", (template_id,))
            conn.commit()
        
        finally:
            conn.close()
    
    def cleanup_old_analyses(self, keep_count: int = 10):
        """
        Xóa các analysis record cũ, chỉ giữ lại keep_count record mới nhất
        Và xóa luôn file ảnh tương ứng trên disk
        """
        import os
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Lấy ID của các record cần giữ lại (10 mới nhất)
            cursor.execute("""
                SELECT id, image_path
                FROM pixel_analyses
                ORDER BY analyzed_at DESC
                LIMIT ?
            """, (keep_count,))
            
            keep_records = cursor.fetchall()
            keep_ids = [row[0] for row in keep_records]
            
            if not keep_ids:
                # Không có record nào, không cần xóa
                return
            
            # Lấy các record cũ cần xóa (không nằm trong danh sách keep)
            cursor.execute("""
                SELECT id, image_path
                FROM pixel_analyses
                WHERE id NOT IN ({})
            """.format(','.join('?' * len(keep_ids))), keep_ids)
            
            records_to_delete = cursor.fetchall()
            
            # Xóa file ảnh trên disk trước
            for record_id, image_path in records_to_delete:
                if image_path and os.path.exists(image_path):
                    try:
                        os.remove(image_path)
                        print(f"Deleted image file: {image_path}")
                    except Exception as e:
                        print(f"Error deleting image file {image_path}: {str(e)}")
            
            # Xóa records khỏi database
            if records_to_delete:
                delete_ids = [record[0] for record in records_to_delete]
                cursor.execute("""
                    DELETE FROM pixel_analyses
                    WHERE id NOT IN ({})
                """.format(','.join('?' * len(keep_ids))), keep_ids)
                
                conn.commit()
                print(f"Deleted {len(delete_ids)} old analysis records, kept {len(keep_ids)} newest")
            
        finally:
            conn.close()
    
    def get_analysis_history(self, limit: int = 10) -> List[Dict]:
        """Lấy lịch sử phân tích"""
        import json
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT 
                    pa.id,
                    pa.template_id,
                    pt.name as template_name,
                    pa.analyzed_at,
                    pa.image_path,
                    pa.results
                FROM pixel_analyses pa
                JOIN pixel_templates pt ON pa.template_id = pt.id
                ORDER BY pa.analyzed_at DESC
                LIMIT ?
            """, (limit,))
            
            history = []
            for row in cursor.fetchall():
                history.append({
                    "id": row[0],
                    "template_id": row[1],
                    "template_name": row[2],
                    "analyzed_at": row[3],
                    "image_path": row[4],
                    "results": json.loads(row[5]) if row[5] else []
                })
            
            return history
        
        finally:
            conn.close()

