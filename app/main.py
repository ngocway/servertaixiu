from fastapi import FastAPI, File, UploadFile, HTTPException, Query, Request, Form
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional, Dict
import io
from PIL import Image
import numpy as np
import os
import json
import sqlite3
from datetime import datetime

from fastapi.middleware.cors import CORSMiddleware

# Load environment variables from .env file if exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from .services.green_detector import (
    detect_green_dots,
    extract_colors_at_positions,
    classify_black_white,
)
from .services.log_service import LogService
from .services.template_service import TemplateService
from .services.settings_service import SettingsService
from .services.pixel_detector_service import PixelDetectorService

# Import config (optional)
try:
    from config import VPS_IP, DOMAIN, API_BASE_URL
except ImportError:
    VPS_IP = None
    DOMAIN = None
    API_BASE_URL = None


class AnalyzedPosition(BaseModel):
    number: int
    x: int
    y: int
    classification: str


class AnalyzeResponse(BaseModel):
    total: int
    white: int
    black: int
    positions: List[AnalyzedPosition]
    sequence: List[str]  # Thứ tự các nốt TRẮNG/ĐEN


app = FastAPI(title="Screenshot Analyzer Server", version="2.0.0")

# ==================== CORS CONFIGURATION - ĐẶT Ở ĐẦU, TRƯỚC MỌI XỬ LÝ ====================
# ⚠️ QUAN TRỌNG: CORS middleware PHẢI được đặt TRƯỚC mọi endpoint/exception handler
# Middleware này sẽ TỰ ĐỘNG thêm CORS headers cho TẤT CẢ responses:
#   - OPTIONS requests (preflight)
#   - POST requests (actual request)
#   - GET requests
#   - Error responses (4xx, 5xx)
#   - Success responses (2xx)
#
# KHÔNG CẦN thêm CORS headers thủ công vào từng endpoint nữa.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cho phép mọi origin (chrome-extension://, http://, https://)
    allow_credentials=False,  # Không cần credentials với wildcard origin (*)
    allow_methods=["*"],  # Cho phép TẤT CẢ methods: GET, POST, OPTIONS, PUT, DELETE
    allow_headers=["*"],  # Cho phép TẤT CẢ headers từ client
    expose_headers=["*"],  # Expose TẤT CẢ headers cho client
)

# Khởi tạo Services
log_service = LogService()
template_service = TemplateService()
settings_service = SettingsService()
pixel_detector_service = PixelDetectorService()


# ==================== EXCEPTION HANDLERS - ĐẢM BẢO CORS HEADERS CHO TẤT CẢ ERRORS ====================
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    """
    Xử lý HTTPException - CORS headers sẽ được thêm TỰ ĐỘNG bởi CORSMiddleware
    KHÔNG CẦN thêm headers thủ công ở đây
    """
    response = JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )
    # CORSMiddleware sẽ tự động thêm CORS headers
    return response


@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    """
    Exception handler tổng quát - CORS headers sẽ được thêm TỰ ĐỘNG bởi CORSMiddleware
    Bắt tất cả exceptions không được xử lý bởi HTTPException handler
    """
    response = JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"}
    )
    # CORSMiddleware sẽ tự động thêm CORS headers
    return response


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/analyze/green-dots", response_model=AnalyzeResponse)
async def analyze_green_dots(image: UploadFile = File(...), save_log: bool = Query(default=True, description="Lưu log tự động")):
    """
    Nhận screenshot, phân tích nốt xanh và tự động lưu log
    """
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File tải lên không phải là ảnh")

    try:
        content = await image.read()
        pil_image = Image.open(io.BytesIO(content)).convert("RGBA")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Không đọc được ảnh: {str(e)}")

    # Convert PIL image to numpy array (RGBA)
    np_image = np.array(pil_image)
    height, width = np_image.shape[0], np_image.shape[1]

    # Detect green dots and order zigzag
    dots = detect_green_dots(np_image)

    # Extract and classify at dot centers
    results = extract_colors_at_positions(np_image, dots)

    white_count = sum(1 for r in results if r["classification"] == "TRẮNG")
    black_count = sum(1 for r in results if r["classification"] == "ĐEN")

    positions = [
        AnalyzedPosition(
            number=i + 1,
            x=int(r["x"]),
            y=int(r["y"]),
            classification=r["classification"],
        )
        for i, r in enumerate(results)
    ]

    # Tạo sequence từ positions
    sequence = [r["classification"] for r in results]
    
    response = AnalyzeResponse(
        total=len(positions),
        white=white_count,
        black=black_count,
        positions=positions,
        sequence=sequence,
    )

    # Lưu log tự động nếu được yêu cầu
    if save_log:
        try:
            # Xác định extension từ filename hoặc content_type
            extension = "png"
            if image.filename:
                ext = os.path.splitext(image.filename)[1].lstrip(".")
                if ext in ["png", "jpg", "jpeg"]:
                    extension = ext
            elif image.content_type:
                if "jpeg" in image.content_type or "jpg" in image.content_type:
                    extension = "jpg"
            
            # Convert PIL image back to bytes for saving
            img_bytes = io.BytesIO()
            pil_image.save(img_bytes, format=extension.upper() if extension == "jpg" else "PNG")
            img_bytes.seek(0)
            
            # Convert Pydantic model to dict
            response_dict = response.model_dump() if hasattr(response, 'model_dump') else response.dict()
            
            log_id = log_service.save_analysis(
                img_bytes.getvalue(),
                response_dict,
                extension
            )
            
            # Thêm log_id vào response
            response_dict["log_id"] = log_id
            return JSONResponse(content=response_dict)
        except Exception as e:
            # Nếu lưu log thất bại, vẫn trả về kết quả phân tích
            print(f"Lỗi khi lưu log: {str(e)}")

    return response


class BWItem(BaseModel):
    vị_trí: int
    phân_loại: str


@app.post("/results/black-white")
async def upload_black_white_results(items: List[BWItem]):
    # Persist JSON to disk under results/
    os.makedirs("results", exist_ok=True)
    # Compose filename
    from datetime import datetime

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join("results", f"black_white_{ts}.json")
    # Convert to plain dict list with ascii keys
    payload = [
        {"position": i.vị_trí, "classification": i.phân_loại}
        for i in items
    ]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return {"status": "saved", "file": path, "count": len(items)}


@app.get("/results/black-white")
async def list_black_white_results():
    root = "results"
    os.makedirs(root, exist_ok=True)
    files = []
    for name in sorted(os.listdir(root)):
        if not name.endswith(".json"):
            continue
        path = os.path.join(root, name)
        try:
            stat = os.stat(path)
            # Try read count quickly
            count = None
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        count = len(data)
            except Exception:
                pass
            files.append({
                "filename": name,
                "size": stat.st_size,
                "mtime": int(stat.st_mtime),
                "count": count
            })
        except Exception:
            continue
    return {"items": list(reversed(files))}


@app.get("/results/black-white/{filename}")
async def get_black_white_file(filename: str):
    path = os.path.join("results", filename)
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="Không tìm thấy file")
    return FileResponse(path, media_type="application/json", filename=filename)


# ==================== LOG MANAGEMENT APIs ====================

@app.get("/api/logs")
async def list_logs(
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    order_by: str = Query(default="created_at"),
    order_direction: str = Query(default="DESC")
):
    """
    Lấy danh sách logs với pagination
    """
    logs = log_service.list_logs(limit=limit, offset=offset, order_by=order_by, order_direction=order_direction)
    total = log_service.get_logs_count()
    
    return {
        "logs": logs,
        "total": total,
        "limit": limit,
        "offset": offset
    }


@app.get("/api/logs/{log_id}")
async def get_log_detail(log_id: int):
    """
    Lấy chi tiết log theo ID (bao gồm kết quả phân tích đầy đủ)
    """
    log = log_service.get_log(log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Không tìm thấy log")
    
    return log


@app.get("/api/logs/{log_id}/result")
async def get_log_result_json(log_id: int):
    """
    Trả về file JSON kết quả phân tích theo log ID
    """
    log = log_service.get_log(log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Không tìm thấy log")
    
    result = log["analysis_result"]
    
    return JSONResponse(
        content=result,
        headers={
            "Content-Disposition": f'attachment; filename="analysis_result_{log_id}.json"'
        }
    )


@app.get("/api/logs/{log_id}/screenshot")
async def get_log_screenshot(log_id: int):
    """
    Lấy screenshot của log
    """
    screenshot_path = log_service.get_screenshot_path(log_id)
    if not screenshot_path:
        raise HTTPException(status_code=404, detail="Không tìm thấy screenshot")
    
    return FileResponse(
        screenshot_path,
        media_type="image/png",
        filename=os.path.basename(screenshot_path)
    )


@app.get("/api/stats")
async def get_stats():
    """
    Lấy thống kê tổng quan
    """
    total_logs = log_service.get_logs_count()
    
    # Lấy 1000 logs gần nhất để tính toán
    recent_logs = log_service.list_logs(limit=1000, offset=0)
    
    total_dots = sum(log.get("total_dots", 0) for log in recent_logs)
    total_white = sum(log.get("white_count", 0) for log in recent_logs)
    total_black = sum(log.get("black_count", 0) for log in recent_logs)
    
    return {
        "total_logs": total_logs,
        "total_dots_analyzed": total_dots,
        "total_white": total_white,
        "total_black": total_black
    }


# ==================== ADMIN WEB INTERFACE ====================

# ==================== EXTENSION UPLOAD API ====================

@app.get("/upload")
async def upload_screenshot_get():
    """
    Endpoint GET cho extension upload (redirect to POST)
    CORSMiddleware sẽ tự động thêm CORS headers
    """
    response = JSONResponse(
        content={
            "message": "Please use POST method to upload screenshots",
            "endpoint": "/upload",
            "method": "POST",
            "field": "image"
        },
        status_code=405
    )
    # CORSMiddleware đã thêm CORS headers tự động
    return response


@app.options("/upload")
async def upload_screenshot_options():
    """
    Handle CORS preflight request (OPTIONS)
    CORSMiddleware sẽ tự động thêm CORS headers
    """
    # 204 No Content cho preflight - CORS headers được thêm tự động bởi middleware
    return Response(status_code=204)


@app.post("/upload/raw")
async def upload_screenshot_raw(
    request: Request,
    auto_analyze: bool = Query(default=True, description="Tự động phân tích nốt xanh")
):
    """
    Endpoint để Chrome Extension upload raw image bytes
    Content-Type: image/jpeg, image/png, image/webp
    Body: Raw image binary data
    Query params:
    - auto_analyze: Tự động phân tích (default: true)
    """
    from fastapi.responses import JSONResponse
    
    content_type = request.headers.get("content-type", "").lower()
    
    # Validate Content-Type
    if not content_type.startswith("image/"):
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": f"Content-Type phải là image/*, nhận được: {content_type}"}
        )
    
    # Xác định extension từ Content-Type
    extension = "png"
    if "jpeg" in content_type or "jpg" in content_type:
        extension = "jpg"
    elif "png" in content_type:
        extension = "png"
    elif "webp" in content_type:
        extension = "webp"
    
    try:
        screenshot_data = await request.body()
        
        if not screenshot_data:
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": "Body trống"}
            )
            
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": f"Không đọc được body: {str(e)}"}
        )
    
    try:
        content = screenshot_data
        
        # Lưu screenshot
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        screenshot_filename = f"screenshot_{timestamp}.{extension}"
        screenshot_path = os.path.join(log_service.screenshots_dir, screenshot_filename)
        
        with open(screenshot_path, "wb") as f:
            f.write(screenshot_data)
        
        log_id = None
        analysis_result = None
        template_comparison = None
        match_score = None
        template_id = None
        
        # Tự động phân tích nếu được yêu cầu
        if auto_analyze:
            try:
                # BƯỚC 1: Kiểm tra có template không
                active_template = template_service.get_active_template()
                if not active_template:
                    return JSONResponse(
                        status_code=400,
                        content={
                            "status": "error",
                            "message": "Chưa có template, vui lòng upload template trước khi phân tích"
                        }
                    )
                
                # BƯỚC 2: Lấy tọa độ từ template (NHANH - không cần detect)
                template_dots = active_template["green_dots_positions"]
                template_id = active_template["id"]
                
                if not template_dots or len(template_dots) == 0:
                    return JSONResponse(
                        status_code=400,
                        content={
                            "status": "error",
                            "message": "Template không có tọa độ nốt xanh"
                        }
                    )
                
                # BƯỚC 3: Load ảnh và extract colors trực tiếp tại tọa độ template
                pil_image = Image.open(io.BytesIO(content)).convert("RGBA")
                np_image = np.array(pil_image)
                
                # Extract colors tại các tọa độ CỐ ĐỊNH từ template
                results = extract_colors_at_positions(np_image, template_dots)
                
                white_count = sum(1 for r in results if r["classification"] == "TRẮNG")
                black_count = sum(1 for r in results if r["classification"] == "ĐEN")
                
                positions = [
                    {
                        "number": i + 1,
                        "x": int(r["x"]),
                        "y": int(r["y"]),
                        "classification": r["classification"],
                    }
                    for i, r in enumerate(results)
                ]
                
                analysis_result = {
                    "total": len(positions),
                    "white": white_count,
                    "black": black_count,
                    "positions": positions,
                }
                
                # Thêm sequence: thứ tự các nốt TRẮNG/ĐEN
                sequence = [pos["classification"] for pos in positions]
                analysis_result["sequence"] = sequence
                
                # Template comparison: Match score = 100% vì dùng tọa độ cố định
                match_score = 100.0
                comparison_details = {
                    "matched": len(template_dots),
                    "missing": 0,
                    "extra": 0,
                    "total_template_dots": len(template_dots),
                    "total_screenshot_dots": len(template_dots),
                    "missing_dots": [],
                    "method": "direct_coordinates"  # Đánh dấu là dùng tọa độ trực tiếp
                }
                
                template_comparison = {
                    "template_id": template_id,
                    "template_name": active_template["name"],
                    "match_score": 100.0,
                    "details": comparison_details
                }
                
                # Thêm template comparison vào analysis_result
                analysis_result["template_comparison"] = template_comparison
                
                # Lưu vào database
                log_id = log_service.save_analysis(
                    screenshot_data,
                    analysis_result,
                    extension,
                    template_id=template_id,
                    match_score=match_score
                )
            except Exception as e:
                print(f"Error during auto-analyze: {str(e)}")
                return JSONResponse(
                    status_code=500,
                    content={
                        "status": "error",
                        "message": f"Lỗi khi phân tích: {str(e)}"
                    }
                )
        
        response_data = {
            "status": "success",
            "message": "Screenshot uploaded successfully",
            "filename": screenshot_filename,
            "log_id": log_id,
            "analysis": analysis_result,
            "template_comparison": template_comparison,
            "auto_analyze": auto_analyze
        }
        return JSONResponse(content=response_data)
        
    except Exception as e:
        return JSONResponse(
            content={"status": "error", "message": f"Lỗi khi xử lý: {str(e)}"},
            status_code=500
        )


@app.post("/upload")
async def upload_screenshot(
    image: UploadFile = File(...),
    auto_analyze: bool = Query(default=True, description="Tự động phân tích nốt xanh")
):
    """
    Endpoint để upload screenshot qua multipart/form-data
    Trả về log_id nếu auto_analyze=True, hoặc chỉ lưu ảnh nếu False
    """
    from fastapi.responses import JSONResponse
    
    if not image.content_type or not image.content_type.startswith("image/"):
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": "File không phải là ảnh"}
        )

    try:
        screenshot_data = await image.read()
        
        # Xác định extension
        extension = "png"
        if image.filename:
            ext = os.path.splitext(image.filename)[1].lstrip(".")
            if ext in ["png", "jpg", "jpeg", "webp"]:
                extension = ext
        elif image.content_type:
            if "jpeg" in image.content_type or "jpg" in image.content_type:
                extension = "jpg"
            elif "webp" in image.content_type:
                extension = "webp"
                
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": f"Không đọc được file: {str(e)}"}
        )
    
    if not screenshot_data:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": "Dữ liệu ảnh trống"}
        )

    try:
        content = screenshot_data
        
        # Lưu screenshot
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        screenshot_filename = f"screenshot_{timestamp}.{extension}"
        screenshot_path = os.path.join(log_service.screenshots_dir, screenshot_filename)
        
        with open(screenshot_path, "wb") as f:
            f.write(screenshot_data)
        
        log_id = None
        analysis_result = None
        
        # Tự động phân tích nếu được yêu cầu
        if auto_analyze:
            try:
                pil_image = Image.open(io.BytesIO(content)).convert("RGBA")
                np_image = np.array(pil_image)
                
                dots = detect_green_dots(np_image)
                results = extract_colors_at_positions(np_image, dots)
                
                white_count = sum(1 for r in results if r["classification"] == "TRẮNG")
                black_count = sum(1 for r in results if r["classification"] == "ĐEN")
                
                positions = [
                    {
                        "number": i + 1,
                        "x": int(r["x"]),
                        "y": int(r["y"]),
                        "classification": r["classification"],
                    }
                    for i, r in enumerate(results)
                ]
                
                analysis_result = {
                    "total": len(positions),
                    "white": white_count,
                    "black": black_count,
                    "positions": positions,
                }
                
                # Thêm sequence: thứ tự các nốt TRẮNG/ĐEN theo thứ tự zigzag
                sequence = [pos["classification"] for pos in positions]
                analysis_result["sequence"] = sequence
                
                # Lưu vào database
                log_id = log_service.save_analysis(
                    screenshot_data,
                    analysis_result,
                    extension
                )
            except Exception as e:
                print(f"Error during auto-analyze: {str(e)}")
                # Vẫn trả về success nhưng không có analysis
        
        # POST response - CORSMiddleware sẽ tự động thêm CORS headers
        response_data = {
            "status": "success",
            "message": "Screenshot uploaded successfully",
            "filename": screenshot_filename,
            "log_id": log_id,
            "analysis": analysis_result,
            "auto_analyze": auto_analyze
        }
        response = JSONResponse(content=response_data)
        # CORSMiddleware đã thêm CORS headers tự động
        return response
        
    except Exception as e:
        # Error response - CORSMiddleware sẽ tự động thêm CORS headers
        error_response = JSONResponse(
            content={"status": "error", "message": f"Lỗi khi upload: {str(e)}"},
            status_code=500
        )
        # CORSMiddleware đã thêm CORS headers tự động
        return error_response


# ==================== SCREENSHOT MANAGEMENT ====================

@app.get("/api/screenshots")
async def list_screenshots(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0)
):
    """
    Lấy danh sách screenshots đã upload
    """
    logs = log_service.list_logs(limit=limit, offset=offset)
    total = log_service.get_logs_count()
    
    # Thêm thông tin screenshot
    result = []
    for log in logs:
        screenshot_path = log_service.get_screenshot_path(log["id"])
        file_exists = screenshot_path and os.path.exists(screenshot_path)
        
        result.append({
            **log,
            "screenshot_url": f"/api/screenshots/{log['id']}/image" if file_exists else None,
            "file_exists": file_exists,
            "file_size": os.path.getsize(screenshot_path) if file_exists else None
        })
    
    return {
        "screenshots": result,
        "total": total,
        "limit": limit,
        "offset": offset
    }


@app.get("/api/screenshots/{screenshot_id}/image")
async def get_screenshot_image(screenshot_id: int):
    """
    Lấy ảnh screenshot theo ID
    """
    screenshot_path = log_service.get_screenshot_path(screenshot_id)
    if not screenshot_path or not os.path.exists(screenshot_path):
        raise HTTPException(status_code=404, detail="Screenshot not found")
    
    return FileResponse(
        screenshot_path,
        media_type="image/png",
        filename=os.path.basename(screenshot_path)
    )


@app.delete("/api/screenshots/{screenshot_id}")
async def delete_screenshot(screenshot_id: int):
    """
    Xóa screenshot và log
    """
    log = log_service.get_log(screenshot_id)
    if not log:
        raise HTTPException(status_code=404, detail="Screenshot not found")
    
    # Xóa file ảnh
    screenshot_path = log.get("screenshot_path")
    if screenshot_path and os.path.exists(screenshot_path):
        try:
            os.remove(screenshot_path)
        except Exception as e:
            print(f"Error deleting screenshot file: {str(e)}")
    
    # Xóa từ database
    conn = sqlite3.connect(log_service.db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM analysis_logs WHERE id = ?", (screenshot_id,))
    conn.commit()
    conn.close()
    
    return {"status": "deleted", "id": screenshot_id}


# ==================== TEMPLATE MANAGEMENT APIs ====================

@app.post("/api/templates/upload")
async def upload_template(
    request: Request,
    name: str = Query(..., description="Tên template"),
    description: str = Query(default="", description="Mô tả template"),
    auto_detect: bool = Query(default=True, description="Tự động detect green dots")
):
    """
    Upload ảnh mẫu (template) và tự động detect green dots
    Hỗ trợ cả raw image bytes và multipart form-data
    """
    from fastapi.responses import JSONResponse
    
    screenshot_data = None
    extension = "png"
    content_type = request.headers.get("content-type", "").lower()
    
    # Case 1: Raw image bytes
    if content_type.startswith("image/"):
        try:
            screenshot_data = await request.body()
            
            if "jpeg" in content_type or "jpg" in content_type:
                extension = "jpg"
            elif "png" in content_type:
                extension = "png"
            elif "webp" in content_type:
                extension = "webp"
                
        except Exception as e:
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": f"Không đọc được raw image: {str(e)}"}
            )
    
    # Case 2: Multipart form-data
    elif "multipart/form-data" in content_type:
        try:
            form = await request.form()
            
            if "image" not in form:
                return JSONResponse(
                    status_code=400,
                    content={"status": "error", "message": "Không tìm thấy field 'image' trong form"}
                )
            
            image_file = form["image"]
            
            if hasattr(image_file, 'content_type'):
                if not image_file.content_type or not image_file.content_type.startswith("image/"):
                    return JSONResponse(
                        status_code=400,
                        content={"status": "error", "message": "File không phải là ảnh"}
                    )
                
                screenshot_data = await image_file.read()
                
                if image_file.filename:
                    ext = os.path.splitext(image_file.filename)[1].lstrip(".")
                    if ext in ["png", "jpg", "jpeg", "webp"]:
                        extension = ext
                elif image_file.content_type:
                    if "jpeg" in image_file.content_type or "jpg" in image_file.content_type:
                        extension = "jpg"
                    elif "webp" in image_file.content_type:
                        extension = "webp"
            else:
                return JSONResponse(
                    status_code=400,
                    content={"status": "error", "message": "Field 'image' không phải là file upload"}
                )
                    
        except Exception as e:
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": f"Không đọc được form data: {str(e)}"}
            )
    
    else:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": f"Content-Type không hợp lệ: '{content_type}'"}
        )
    
    if not screenshot_data:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": "Dữ liệu ảnh trống"}
        )

    try:
        # Convert to PIL Image
        pil_image = Image.open(io.BytesIO(screenshot_data)).convert("RGBA")
        np_image = np.array(pil_image)
        width, height = pil_image.size
        
        green_dots = []
        
        if auto_detect:
            # Auto-detect green dots
            dots = detect_green_dots(np_image)
            green_dots = [
                {
                    "number": i + 1,
                    "x": int(dot["x"]),
                    "y": int(dot["y"])
                }
                for i, dot in enumerate(dots)
            ]
        
        # Lưu template
        template_id = template_service.save_template(
            image_data=screenshot_data,
            name=name,
            green_dots=green_dots,
            width=width,
            height=height,
            description=description,
            extension=extension
        )
        
        return JSONResponse(content={
            "status": "success",
            "message": "Template uploaded successfully",
            "template_id": template_id,
            "name": name,
            "green_dots_count": len(green_dots),
            "green_dots": green_dots,
            "image_width": width,
            "image_height": height
        })
        
    except Exception as e:
        return JSONResponse(
            content={"status": "error", "message": f"Lỗi khi xử lý: {str(e)}"},
            status_code=500
        )


@app.get("/api/templates")
async def list_templates(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0)
):
    """Lấy danh sách templates"""
    templates = template_service.list_templates(limit=limit, offset=offset)
    total = template_service.get_templates_count()
    
    return {
        "templates": templates,
        "total": total,
        "limit": limit,
        "offset": offset
    }


@app.get("/api/templates/active")
async def get_active_template():
    """Lấy template đang active"""
    template = template_service.get_active_template()
    
    if not template:
        raise HTTPException(status_code=404, detail="Không có template active")
    
    return template


@app.get("/api/templates/{template_id}")
async def get_template(template_id: int):
    """Lấy chi tiết template theo ID"""
    template = template_service.get_template(template_id)
    
    if not template:
        raise HTTPException(status_code=404, detail="Không tìm thấy template")
    
    return template


@app.get("/api/templates/{template_id}/image")
async def get_template_image(template_id: int):
    """Lấy ảnh template"""
    filepath = template_service.get_template_filepath(template_id)
    
    if not filepath or not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Template image not found")
    
    return FileResponse(
        filepath,
        media_type="image/png",
        filename=os.path.basename(filepath)
    )


@app.put("/api/templates/{template_id}/activate")
async def activate_template(template_id: int):
    """Set template làm active"""
    success = template_service.set_active_template(template_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Không tìm thấy template")
    
    return {"status": "success", "message": "Template activated", "template_id": template_id}


@app.put("/api/templates/{template_id}/dots")
async def update_template_dots(template_id: int, dots: List[Dict]):
    """Cập nhật vị trí green dots của template"""
    success = template_service.update_dots_positions(template_id, dots)
    
    if not success:
        raise HTTPException(status_code=404, detail="Không tìm thấy template")
    
    return {
        "status": "success",
        "message": "Dots updated",
        "template_id": template_id,
        "dots_count": len(dots)
    }


@app.delete("/api/templates/{template_id}")
async def delete_template(template_id: int):
    """Xóa template"""
    success = template_service.delete_template(template_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Không tìm thấy template")
    
    return {"status": "success", "message": "Template deleted", "template_id": template_id}


@app.post("/api/templates/{template_id}/compare")
async def compare_with_template(
    template_id: int,
    screenshot_dots: List[Dict],
    tolerance: int = Query(default=10, ge=1, le=50)
):
    """So sánh screenshot dots với template"""
    template = template_service.get_template(template_id)
    
    if not template:
        raise HTTPException(status_code=404, detail="Không tìm thấy template")
    
    match_score, details = template_service.compare_with_template(
        screenshot_dots=screenshot_dots,
        template_dots=template["green_dots_positions"],
        tolerance=tolerance
    )
    
    return {
        "template_id": template_id,
        "template_name": template["name"],
        "match_score": round(match_score, 2),
        "details": details
    }


# ==================== SETTINGS MANAGEMENT APIs ====================

@app.post("/api/settings/betting-method")
async def set_betting_method(request: Request):
    """Lưu cách cược (Tài/Xỉu) vào database"""
    try:
        data = await request.json()
        method = data.get("method")
        
        if not method or method not in ['tai', 'xiu']:
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": "Method phải là 'tai' hoặc 'xiu'"}
            )
        
        success = settings_service.set_betting_method(method)
        
        if success:
            return JSONResponse(content={
                "status": "success",
                "message": "Đã lưu cách cược",
                "method": method
            })
        else:
            return JSONResponse(
                status_code=500,
                content={"status": "error", "message": "Không thể lưu"}
            )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )


@app.get("/api/settings/betting-method")
async def get_betting_method():
    """Lấy cách cược hiện tại từ database"""
    method = settings_service.get_betting_method()
    
    return {
        "method": method,
        "has_value": method is not None
    }


# ==================== PIXEL DETECTOR API ====================

@app.post("/api/pixel-detector/upload-template")
async def upload_pixel_template(
    file: UploadFile = File(...),
    name: str = Query(..., description="Tên template")
):
    """
    Upload ảnh mẫu, detect pixel màu #1AFF0D và lưu vào database
    """
    try:
        # Read image
        image_data = await file.read()
        image = Image.open(io.BytesIO(image_data))
        
        # Detect pixels with color #1AFF0D
        pixel_positions = pixel_detector_service.detect_color_pixels(image)
        
        if not pixel_positions:
            raise HTTPException(
                status_code=400,
                detail="Không tìm thấy pixel nào có màu #1AFF0D trong ảnh"
            )
        
        # Save template to database
        template_id = pixel_detector_service.save_template(name, image, pixel_positions)
        
        return {
            "success": True,
            "template_id": template_id,
            "template_name": name,
            "pixel_count": len(pixel_positions),
            "image_size": {
                "width": image.width,
                "height": image.height
            },
            "pixel_positions": [{"x": x, "y": y, "position_number": idx} for idx, (x, y) in enumerate(pixel_positions, 1)],
            "message": f"Đã phát hiện và lưu {len(pixel_positions)} pixel màu #1AFF0D"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi xử lý ảnh: {str(e)}")


@app.post("/api/pixel-detector/analyze")
async def analyze_with_pixel_template(
    file: UploadFile = File(...),
    region_width: int = Query(100, description="Chiều rộng vùng cần đọc"),
    region_height: int = Query(40, description="Chiều cao vùng cần đọc")
):
    """
    Upload ảnh cần phân tích và đọc nội dung tại các vị trí pixel đã lưu
    """
    try:
        # Get active template
        template = pixel_detector_service.get_active_template()
        if not template:
            raise HTTPException(
                status_code=404,
                detail="Chưa có template nào được tạo. Vui lòng upload template trước."
            )
        
        # Read image
        image_data = await file.read()
        image = Image.open(io.BytesIO(image_data))
        
        # Analyze image with template
        results = pixel_detector_service.analyze_image_with_template(
            image, 
            template["id"],
            region_width,
            region_height
        )
        
        # Save analysis result
        analysis_id = pixel_detector_service.save_analysis_result(
            template["id"],
            results,
            file.filename
        )
        
        return {
            "success": True,
            "analysis_id": analysis_id,
            "template_id": template["id"],
            "template_name": template["name"],
            "total_positions": len(results),
            "results": results,
            "message": f"Đã phân tích {len(results)} vị trí"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi phân tích ảnh: {str(e)}")


@app.post("/upload/mobile")
async def upload_from_mobile(request: Request):
    """
    API cho Mobile App - Upload ảnh và nhận kết quả thống kê pixel sáng/tối
    Hỗ trợ cả file binary và Base64 string (từ Geelerk)
    - Form-data field 'file': File binary (Encode as Base64 = No) hoặc Base64 string (Encode as Base64 = Yes)
    Lưu ảnh để có thể review lại sau
    """
    try:
        # Get active template
        template = pixel_detector_service.get_active_template()
        if not template:
            raise HTTPException(
                status_code=404,
                detail="Chưa có template. Vui lòng upload template trước."
            )
        
        # Xử lý ảnh - hỗ trợ cả file binary và Base64 string
        image = None
        image_data = None
        
        # Đọc form-data (Geelerk gửi qua form-data)
        try:
            form_data = await request.form()
            
            # Thử đọc field "file"
            if 'file' in form_data:
                file_value = form_data['file']
                
                # Trường hợp 1: Base64 string (khi Geelerk Encode as Base64 = Yes)
                if isinstance(file_value, str) and len(file_value) > 100:
                    try:
                        import base64
                        # Loại bỏ data URL prefix nếu có (data:image/png;base64,...)
                        base64_data = file_value
                        if ',' in base64_data:
                            base64_data = base64_data.split(',')[1]
                        else:
                            base64_data = base64_data.strip()
                        image_data = base64.b64decode(base64_data)
                        image = Image.open(io.BytesIO(image_data))
                    except Exception as e:
                        # Không phải Base64 hợp lệ
                        pass
                
                # Trường hợp 2: UploadFile object (khi Geelerk Encode as Base64 = No)
                elif hasattr(file_value, 'read'):
                    try:
                        image_data = await file_value.read()
                        if image_data and len(image_data) > 0:
                            image = Image.open(io.BytesIO(image_data))
                    except Exception as e:
                        raise HTTPException(status_code=400, detail=f"Không thể đọc file: {str(e)}")
        except Exception as e:
            # Nếu không phải form-data, thử đọc như raw body
            try:
                body = await request.body()
                if body and len(body) > 0:
                    # Thử parse như ảnh binary trực tiếp
                    image = Image.open(io.BytesIO(body))
            except:
                pass
        
        if not image:
            raise HTTPException(
                status_code=400,
                detail="Không nhận được ảnh hợp lệ. Vui lòng gửi file binary hoặc Base64 string trong field 'file' (form-data)"
            )
        
        # Tạo thư mục lưu ảnh mobile nếu chưa có
        mobile_images_dir = "mobile_images"
        os.makedirs(mobile_images_dir, exist_ok=True)
        
        # Tạo tên file với timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        # Lấy extension từ image format, mặc định là jpg
        file_extension = image.format.lower() if image.format else 'jpg'
        if file_extension not in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
            file_extension = 'jpg'
        saved_filename = f"mobile_{timestamp}.{file_extension}"
        saved_path = os.path.join(mobile_images_dir, saved_filename)
        
        # Lưu ảnh
        image.save(saved_path, quality=95)
        
        # Analyze image with template (sử dụng giá trị mặc định)
        results = pixel_detector_service.analyze_image_with_template(
            image, 
            template["id"],
            region_width=100,
            region_height=40
        )
        
        # Tính thống kê
        light_count = sum(1 for r in results if r.get('result') == 'Sáng')
        dark_count = sum(1 for r in results if r.get('result') == 'Tối')
        
        # Save analysis result với đường dẫn ảnh
        analysis_id = pixel_detector_service.save_analysis_result(
            template["id"],
            results,
            saved_path
        )
        
        # Cleanup: Xóa các record cũ, chỉ giữ lại 10 mới nhất
        pixel_detector_service.cleanup_old_analyses(keep_count=10)
        
        return {
            "success": True,
            "analysis_id": analysis_id,
            "template_id": template["id"],
            "template_name": template["name"],
            "total_positions": len(results),
            "statistics": {
                "light_pixels": light_count,
                "dark_pixels": dark_count
            },
            "image_path": saved_path,
            "image_url": f"/api/pixel-detector/image/{analysis_id}",
            "message": f"Phân tích thành công: {light_count} sáng, {dark_count} tối"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi phân tích: {str(e)}")


# Alias endpoint (giữ lại để tương thích)
@app.post("/api/pixel-detector/analyze-mobile")
async def analyze_for_mobile(file: UploadFile = File(...)):
    """API cho Mobile App - Alias của /upload/mobile"""
    return await upload_from_mobile(file)


@app.get("/api/pixel-detector/templates")
async def get_pixel_templates():
    """Lấy danh sách tất cả pixel templates"""
    try:
        templates = pixel_detector_service.get_all_templates()
        return {
            "success": True,
            "total": len(templates),
            "templates": templates
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi lấy danh sách templates: {str(e)}")


@app.get("/api/pixel-detector/template/{template_id}")
async def get_pixel_template_detail(template_id: int):
    """Lấy chi tiết template và các vị trí pixel"""
    try:
        templates = pixel_detector_service.get_all_templates()
        template = next((t for t in templates if t["id"] == template_id), None)
        
        if not template:
            raise HTTPException(status_code=404, detail="Template không tồn tại")
        
        # Get pixel positions
        positions = pixel_detector_service.get_template_pixels(template_id)
        
        return {
            "success": True,
            "template": template,
            "positions": [{"x": x, "y": y} for x, y in positions]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi lấy chi tiết template: {str(e)}")


@app.delete("/api/pixel-detector/template/{template_id}")
async def delete_pixel_template(template_id: int):
    """Xóa template"""
    try:
        pixel_detector_service.delete_template(template_id)
        return {
            "success": True,
            "message": "Đã xóa template thành công"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi xóa template: {str(e)}")


@app.get("/api/pixel-detector/analysis-history")
async def get_analysis_history(limit: int = Query(10, description="Số lượng kết quả (mặc định 10)")):
    """Lấy lịch sử phân tích"""
    try:
        history = pixel_detector_service.get_analysis_history(limit)
        return {
            "success": True,
            "total": len(history),
            "history": history
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi lấy lịch sử: {str(e)}")


@app.get("/api/pixel-detector/image/{analysis_id}")
async def get_analysis_image(analysis_id: int):
    """
    Xem lại ảnh đã upload từ mobile theo analysis_id
    """
    try:
        history = pixel_detector_service.get_analysis_history(limit=1000)
        analysis = next((h for h in history if h["id"] == analysis_id), None)
        
        if not analysis:
            raise HTTPException(status_code=404, detail="Không tìm thấy phân tích này")
        
        # Lấy image_path từ results hoặc từ database
        image_path = None
        if isinstance(analysis.get("results"), list) and len(analysis["results"]) > 0:
            # Nếu có lưu trong results (cũ)
            pass
        
        # Kiểm tra trong database
        conn = sqlite3.connect(pixel_detector_service.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT image_path FROM pixel_analyses WHERE id = ?", (analysis_id,))
            row = cursor.fetchone()
            if row and row[0]:
                image_path = row[0]
        finally:
            conn.close()
        
        if not image_path or not os.path.exists(image_path):
            raise HTTPException(status_code=404, detail="Ảnh không tồn tại hoặc đã bị xóa")
        
        return FileResponse(
            image_path,
            media_type="image/jpeg",
            filename=os.path.basename(image_path)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi lấy ảnh: {str(e)}")


# ==================== OCR (ChatGPT Vision) APIs ====================

@app.post("/api/ocr/analyze")
async def analyze_image_ocr(file: UploadFile = File(...)):
    """
    Đọc text từ ảnh sử dụng ChatGPT Vision API
    """
    try:
        import base64
        import httpx
        
        # Đọc ảnh
        image_data = await file.read()
        base64_image = base64.b64encode(image_data).decode('utf-8')
        
        # Lấy OpenAI API key từ environment variable hoặc .env file
        openai_api_key = os.getenv('OPENAI_API_KEY')
        
        # Nếu không có trong env, thử đọc từ file .env
        if not openai_api_key:
            env_file_path = os.path.join(os.path.dirname(__file__), '..', '.env')
            if os.path.exists(env_file_path):
                with open(env_file_path, 'r') as f:
                    for line in f:
                        if line.startswith('OPENAI_API_KEY='):
                            openai_api_key = line.split('=', 1)[1].strip()
                            break
        
        if not openai_api_key:
            raise HTTPException(
                status_code=500,
                detail="OPENAI_API_KEY chưa được cấu hình. Vui lòng tạo file .env hoặc set biến môi trường OPENAI_API_KEY"
            )
        
        # Gọi ChatGPT Vision API
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {openai_api_key}"
                },
                json={
                    "model": "gpt-4o",
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": """Extract text from this betting history table image and return in structured format.

IMPORTANT: This is a "LỊCH SỬ CƯỢC" (Betting History) table. Extract these columns in order:
1. Phiên (Session ID)
2. Thời gian (Time - format: DD-MM-YYYY HH:MM:SS)
3. Đặt cược (Bet: Tài or Xỉu)
4. Kết quả (Result: Tài or Xỉu)
5. Tổng cược (Total Bet)
6. Tiền thắng (Winnings)
7. Thắng/Thua (Win/Loss - calculate this: if Bet=Result → "Thắng", else → "Thua")

Return format (use pipe | as separator):
Phiên|Thời gian|Đặt cược|Kết quả|Tổng cược|Tiền thắng|Thắng/Thua
524124|03-11-2025 17:41:46|Tài|Tài|2,000|+1,960|Thắng
524123|03-11-2025 17:40:45|Tài|Xỉu|1,000|-1,000|Thua
524122|03-11-2025 17:39:50|Tài|Tài|1,000|+980|Thắng
524121|03-11-2025 17:38:43|Tài|Xỉu|1,000|-1,000|Thua

Rules:
- Each row on a new line
- Use | to separate columns
- Keep numbers with commas (e.g., 2,000)
- Keep + or - sign for winnings
- For "Thắng/Thua": if "Đặt cược" = "Kết quả" then "Thắng", else "Thua"
- If not a betting table, extract all text normally"""
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{base64_image}",
                                        "detail": "high"
                                    }
                                }
                            ]
                        }
                    ],
                    "max_tokens": 4096,
                    "temperature": 0.1
                }
            )
        
        if response.status_code != 200:
            error_detail = response.text
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Lỗi từ OpenAI API (HTTP {response.status_code}): {error_detail}"
            )
        
        result = response.json()
        extracted_text = result['choices'][0]['message']['content']
        
        # Kiểm tra nếu ChatGPT từ chối
        refusal_phrases = [
            "I'm sorry",
            "I can't assist",
            "I cannot help",
            "I'm unable to",
            "I apologize"
        ]
        
        if any(phrase.lower() in extracted_text.lower() for phrase in refusal_phrases):
            # Log để debug
            print(f"[OCR] ChatGPT refusal detected: {extracted_text}")
            print(f"[OCR] Full response: {json.dumps(result)}")
            
            # Kiểm tra xem có phải do content policy không
            refusal_detail = f"""OpenAI từ chối xử lý ảnh này.

Response từ ChatGPT: "{extracted_text}"

Nguyên nhân có thể:
1. ⚠️ Ảnh chứa nội dung liên quan đến cờ bạc/game/casino
2. ⚠️ Ảnh chứa nội dung nhạy cảm hoặc vi phạm policy
3. ⚠️ Ảnh không rõ ràng hoặc bị lỗi

Giải pháp:
- Thử ảnh khác không liên quan đến game/cờ bạc
- Đảm bảo ảnh rõ nét, không bị mờ
- Thử crop ảnh để chỉ lấy phần text cần đọc

Hoặc liên hệ admin để được hỗ trợ."""
            
            raise HTTPException(
                status_code=400,
                detail=refusal_detail
            )
        
        # Lưu vào database
        conn = sqlite3.connect('logs.db')
        cursor = conn.cursor()
        
        # Tạo table nếu chưa có
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ocr_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                extracted_text TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Insert result
        cursor.execute("""
            INSERT INTO ocr_results (extracted_text)
            VALUES (?)
        """, (extracted_text,))
        
        conn.commit()
        ocr_id = cursor.lastrowid
        conn.close()
        
        return {
            "success": True,
            "ocr_id": ocr_id,
            "text": extracted_text,
            "message": "Đọc text thành công"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi: {str(e)}")


@app.get("/api/ocr/history")
async def get_ocr_history(limit: int = Query(10, description="Số lượng kết quả")):
    """Lấy lịch sử đọc text"""
    try:
        conn = sqlite3.connect('logs.db')
        cursor = conn.cursor()
        
        # Tạo table nếu chưa có
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ocr_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                extracted_text TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        
        cursor.execute("""
            SELECT id, extracted_text, created_at
            FROM ocr_results
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,))
        
        history = []
        for row in cursor.fetchall():
            history.append({
                "id": row[0],
                "extracted_text": row[1],
                "created_at": row[2]
            })
        
        conn.close()
        
        return {
            "success": True,
            "total": len(history),
            "history": history
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi lấy lịch sử: {str(e)}")


# ==================== ADMIN WEB INTERFACE ====================

@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard():
    """
    Giao diện admin để xem logs
    """
    html_content = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Dashboard - Screenshot Analyzer</title>
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
    <meta http-equiv="Pragma" content="no-cache">
    <meta http-equiv="Expires" content="0">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f8f9fa;
        }
        
        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
        }
        
        .stat-card h3 {
            color: #667eea;
            font-size: 2em;
            margin-bottom: 10px;
        }
        
        .stat-card p {
            color: #666;
            font-size: 0.9em;
        }
        
        .controls {
            padding: 20px 30px;
            background: white;
            border-bottom: 1px solid #eee;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 15px;
        }
        
        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            transition: all 0.3s;
        }
        
        .btn-primary {
            background: #667eea;
            color: white;
        }
        
        .btn-primary:hover {
            background: #5568d3;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        }
        
        .btn-secondary {
            background: #6c757d;
            color: white;
        }
        
        .btn-secondary:hover {
            background: #5a6268;
        }
        
        .btn-success {
            background: #28a745;
            color: white;
        }
        
        .btn-info {
            background: #17a2b8;
            color: white;
        }
        
        .search-box {
            padding: 10px 15px;
            border: 2px solid #ddd;
            border-radius: 6px;
            font-size: 14px;
            width: 300px;
        }
        
        .table-container {
            overflow-x: auto;
            padding: 30px;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            background: white;
        }
        
        th {
            background: #667eea;
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: 600;
            position: sticky;
            top: 0;
        }
        
        td {
            padding: 15px;
            border-bottom: 1px solid #eee;
        }
        
        tr:hover {
            background: #f8f9fa;
        }
        
        .badge {
            display: inline-block;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 600;
        }
        
        .badge-success {
            background: #d4edda;
            color: #155724;
        }
        
        .badge-danger {
            background: #f8d7da;
            color: #721c24;
        }
        
        .badge-info {
            background: #d1ecf1;
            color: #0c5460;
        }
        
        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            overflow: auto;
        }
        
        .modal-content {
            background: white;
            margin: 5% auto;
            padding: 30px;
            border-radius: 12px;
            width: 90%;
            max-width: 800px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
        }
        
        .close {
            color: #aaa;
            float: right;
            font-size: 28px;
            font-weight: bold;
            cursor: pointer;
        }
        
        .close:hover {
            color: black;
        }
        
        .loading {
            text-align: center;
            padding: 40px;
            color: #667eea;
        }
        
        .pagination {
            padding: 20px 30px;
            display: flex;
            justify-content: center;
            gap: 10px;
        }
        
        .pagination button {
            padding: 8px 16px;
            border: 1px solid #ddd;
            background: white;
            cursor: pointer;
            border-radius: 4px;
        }
        
        .pagination button:hover {
            background: #667eea;
            color: white;
        }
        
        .pagination button.active {
            background: #667eea;
            color: white;
        }
        
        .screenshot-thumb {
            width: 100px;
            height: 60px;
            object-fit: cover;
            border-radius: 4px;
            cursor: pointer;
            border: 2px solid #ddd;
        }
        
        .screenshot-thumb:hover {
            border-color: #667eea;
        }
        
        .view-active {
            display: block !important;
        }
        
        .view-hidden {
            display: none !important;
        }
        
        .btn-danger {
            background: #dc3545;
            color: white;
        }
        
        .btn-danger:hover {
            background: #c82333;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Admin Dashboard</h1>
            <p>Quản lý và xem logs phân tích screenshots</p>
        </div>
        
        <div class="controls">
            <div style="display: flex; gap: 10px; align-items: center;">
                <button class="btn btn-primary" onclick="refreshCurrentView()">🔄 Làm mới</button>
                <button class="btn btn-success" onclick="switchView('screenshots')">🖼️ Screenshots</button>
                <button class="btn btn-success" onclick="switchView('templates')">📄 Templates</button>
                <button class="btn btn-info" onclick="switchView('pixel-detector')">🔍 Pixel Detector</button>
                <button class="btn btn-warning" onclick="switchView('ocr')">📝 Đọc text</button>
            </div>
            <input type="text" class="search-box" id="search" placeholder="Tìm kiếm..." onkeyup="filterTable()">
        </div>
        
        <!-- API URLs Section -->
        <div style="background: #f8f9fa; padding: 15px 30px; border-bottom: 1px solid #eee; display: flex; gap: 30px; align-items: center; flex-wrap: wrap;">
            <div style="display: flex; align-items: center; gap: 10px;">
                <span style="font-weight: 600; color: #667eea;">📤 POST URL (Extension):</span>
                <code style="background: white; padding: 8px 15px; border-radius: 6px; font-size: 13px; border: 1px solid #ddd; user-select: all;">https://lukistar.space/upload/raw</code>
                <button class="btn btn-secondary" onclick="copyToClipboard('https://lukistar.space/upload/raw')" style="padding: 6px 12px; font-size: 12px;">📋 Copy</button>
            </div>
            <div style="display: flex; align-items: center; gap: 10px;">
                <span style="font-weight: 600; color: #28a745;">📥 GET API:</span>
                <code style="background: white; padding: 8px 15px; border-radius: 6px; font-size: 13px; border: 1px solid #ddd; user-select: all;">https://lukistar.space/api/screenshots</code>
                <button class="btn btn-secondary" onclick="copyToClipboard('https://lukistar.space/api/screenshots')" style="padding: 6px 12px; font-size: 12px;">📋 Copy</button>
            </div>
        </div>
        
        <div class="table-container" id="screenshots-view">
            <div class="loading" id="screenshots-loading">Đang tải screenshots...</div>
            <table id="screenshots-table" style="display: none;">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Thời gian</th>
                        <th>Kết quả phân tích</th>
                        <th>Kết quả</th>
                        <th>Thắng/Thua</th>
                        <th>Hệ số</th>
                        <th>Hành động</th>
                    </tr>
                </thead>
                <tbody id="screenshots-tbody">
                </tbody>
            </table>
        </div>
        
        <div class="table-container" id="templates-view" style="display: none;">
            <div style="margin-bottom: 20px;">
                <button class="btn btn-primary" onclick="showUploadTemplateForm()">🔄 Upload/Replace Template</button>
                <span style="margin-left: 15px; color: #666; font-style: italic;">
                    Lưu ý: Chỉ cho phép 1 template duy nhất. Upload mới sẽ thay thế template cũ.
                </span>
            </div>
            
            <div class="loading" id="templates-loading">Đang tải templates...</div>
            <table id="templates-table" style="display: none;">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Tên</th>
                        <th>Số nốt xanh</th>
                        <th>Kích thước ảnh</th>
                        <th>Ngày tạo</th>
                        <th>Trạng thái</th>
                        <th>Hành động</th>
                    </tr>
                </thead>
                <tbody id="templates-tbody">
                </tbody>
            </table>
            
            <!-- Betting Coordinates Section -->
            <div id="betting-coords-section" style="margin-top: 40px; padding-top: 30px; border-top: 2px solid #eee;">
                <h2 style="color: #667eea; margin-bottom: 25px; text-align: center;">📍 Tọa độ điểm cược</h2>
                
                <!-- Dropdown Cách cược -->
                <div style="max-width: 400px; margin: 0 auto 30px auto; text-align: center;">
                    <label style="font-weight: 600; font-size: 1.1em; color: #667eea; display: block; margin-bottom: 10px;">
                        🎲 Cách cược:
                    </label>
                    <select id="cach-cuoc-select" style="width: 100%; padding: 12px 20px; font-size: 16px; border: 2px solid #667eea; border-radius: 8px; background: white; cursor: pointer; font-weight: 600; color: #333;" onchange="saveBettingMethod()">
                        <option value="">-- Chọn cách cược --</option>
                        <option value="tai">🔺 Tài</option>
                        <option value="xiu">🔻 Xỉu</option>
                    </select>
                    <div id="selected-betting-method" style="margin-top: 10px; font-size: 0.9em; color: #666; font-style: italic;"></div>
                </div>
                
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 30px; max-width: 1200px; margin: 0 auto;">
                    <!-- Điểm cược A -->
                    <div style="background: #f8f9fa; padding: 25px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                        <h3 style="color: #28a745; margin-bottom: 20px; text-align: center; font-size: 1.3em;">🎯 Điểm cược A</h3>
                        <div style="display: flex; flex-direction: column; gap: 15px;">
                            <div style="display: flex; align-items: center; gap: 10px;">
                                <label style="min-width: 30px; font-weight: 600;">X:</label>
                                <input type="number" id="diem-cuoc-a-x1" placeholder="X1" style="flex: 1; padding: 10px; border: 2px solid #ddd; border-radius: 6px; font-size: 14px;">
                                <label style="min-width: 30px; font-weight: 600;">Y:</label>
                                <input type="number" id="diem-cuoc-a-y1" placeholder="Y1" style="flex: 1; padding: 10px; border: 2px solid #ddd; border-radius: 6px; font-size: 14px;">
                            </div>
                            <div style="display: flex; align-items: center; gap: 10px;">
                                <label style="min-width: 30px; font-weight: 600;">X:</label>
                                <input type="number" id="diem-cuoc-a-x2" placeholder="X2" style="flex: 1; padding: 10px; border: 2px solid #ddd; border-radius: 6px; font-size: 14px;">
                                <label style="min-width: 30px; font-weight: 600;">Y:</label>
                                <input type="number" id="diem-cuoc-a-y2" placeholder="Y2" style="flex: 1; padding: 10px; border: 2px solid #ddd; border-radius: 6px; font-size: 14px;">
                            </div>
                            <div style="display: flex; align-items: center; gap: 10px;">
                                <label style="min-width: 30px; font-weight: 600;">X:</label>
                                <input type="number" id="diem-cuoc-a-x3" placeholder="X3" style="flex: 1; padding: 10px; border: 2px solid #ddd; border-radius: 6px; font-size: 14px;">
                                <label style="min-width: 30px; font-weight: 600;">Y:</label>
                                <input type="number" id="diem-cuoc-a-y3" placeholder="Y3" style="flex: 1; padding: 10px; border: 2px solid #ddd; border-radius: 6px; font-size: 14px;">
                            </div>
                        </div>
                    </div>
                    
                    <!-- Điểm cược B -->
                    <div style="background: #f8f9fa; padding: 25px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                        <h3 style="color: #dc3545; margin-bottom: 20px; text-align: center; font-size: 1.3em;">🎯 Điểm cược B</h3>
                        <div style="display: flex; flex-direction: column; gap: 15px;">
                            <div style="display: flex; align-items: center; gap: 10px;">
                                <label style="min-width: 30px; font-weight: 600;">X:</label>
                                <input type="number" id="diem-cuoc-b-x1" placeholder="X1" style="flex: 1; padding: 10px; border: 2px solid #ddd; border-radius: 6px; font-size: 14px;">
                                <label style="min-width: 30px; font-weight: 600;">Y:</label>
                                <input type="number" id="diem-cuoc-b-y1" placeholder="Y1" style="flex: 1; padding: 10px; border: 2px solid #ddd; border-radius: 6px; font-size: 14px;">
                            </div>
                            <div style="display: flex; align-items: center; gap: 10px;">
                                <label style="min-width: 30px; font-weight: 600;">X:</label>
                                <input type="number" id="diem-cuoc-b-x2" placeholder="X2" style="flex: 1; padding: 10px; border: 2px solid #ddd; border-radius: 6px; font-size: 14px;">
                                <label style="min-width: 30px; font-weight: 600;">Y:</label>
                                <input type="number" id="diem-cuoc-b-y2" placeholder="Y2" style="flex: 1; padding: 10px; border: 2px solid #ddd; border-radius: 6px; font-size: 14px;">
                            </div>
                            <div style="display: flex; align-items: center; gap: 10px;">
                                <label style="min-width: 30px; font-weight: 600;">X:</label>
                                <input type="number" id="diem-cuoc-b-x3" placeholder="X3" style="flex: 1; padding: 10px; border: 2px solid #ddd; border-radius: 6px; font-size: 14px;">
                                <label style="min-width: 30px; font-weight: 600;">Y:</label>
                                <input type="number" id="diem-cuoc-b-y3" placeholder="Y3" style="flex: 1; padding: 10px; border: 2px solid #ddd; border-radius: 6px; font-size: 14px;">
                            </div>
                        </div>
                    </div>
                    
                    <!-- Lượt cược A -->
                    <div style="background: #f8f9fa; padding: 25px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                        <h3 style="color: #17a2b8; margin-bottom: 20px; text-align: center; font-size: 1.3em;">🔄 Lượt cược A</h3>
                        <div style="display: flex; flex-direction: column; gap: 15px;">
                            <div style="display: flex; align-items: center; gap: 10px;">
                                <label style="min-width: 30px; font-weight: 600;">X:</label>
                                <input type="number" id="luot-cuoc-a-x1" placeholder="X1" style="flex: 1; padding: 10px; border: 2px solid #ddd; border-radius: 6px; font-size: 14px;">
                                <label style="min-width: 30px; font-weight: 600;">Y:</label>
                                <input type="number" id="luot-cuoc-a-y1" placeholder="Y1" style="flex: 1; padding: 10px; border: 2px solid #ddd; border-radius: 6px; font-size: 14px;">
                            </div>
                            <div style="display: flex; align-items: center; gap: 10px;">
                                <label style="min-width: 30px; font-weight: 600;">X:</label>
                                <input type="number" id="luot-cuoc-a-x2" placeholder="X2" style="flex: 1; padding: 10px; border: 2px solid #ddd; border-radius: 6px; font-size: 14px;">
                                <label style="min-width: 30px; font-weight: 600;">Y:</label>
                                <input type="number" id="luot-cuoc-a-y2" placeholder="Y2" style="flex: 1; padding: 10px; border: 2px solid #ddd; border-radius: 6px; font-size: 14px;">
                            </div>
                            <div style="display: flex; align-items: center; gap: 10px;">
                                <label style="min-width: 30px; font-weight: 600;">X:</label>
                                <input type="number" id="luot-cuoc-a-x3" placeholder="X3" style="flex: 1; padding: 10px; border: 2px solid #ddd; border-radius: 6px; font-size: 14px;">
                                <label style="min-width: 30px; font-weight: 600;">Y:</label>
                                <input type="number" id="luot-cuoc-a-y3" placeholder="Y3" style="flex: 1; padding: 10px; border: 2px solid #ddd; border-radius: 6px; font-size: 14px;">
                            </div>
                        </div>
                    </div>
                    
                    <!-- Lượt cược B -->
                    <div style="background: #f8f9fa; padding: 25px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                        <h3 style="color: #ffc107; margin-bottom: 20px; text-align: center; font-size: 1.3em;">🔄 Lượt cược B</h3>
                        <div style="display: flex; flex-direction: column; gap: 15px;">
                            <div style="display: flex; align-items: center; gap: 10px;">
                                <label style="min-width: 30px; font-weight: 600;">X:</label>
                                <input type="number" id="luot-cuoc-b-x1" placeholder="X1" style="flex: 1; padding: 10px; border: 2px solid #ddd; border-radius: 6px; font-size: 14px;">
                                <label style="min-width: 30px; font-weight: 600;">Y:</label>
                                <input type="number" id="luot-cuoc-b-y1" placeholder="Y1" style="flex: 1; padding: 10px; border: 2px solid #ddd; border-radius: 6px; font-size: 14px;">
                            </div>
                            <div style="display: flex; align-items: center; gap: 10px;">
                                <label style="min-width: 30px; font-weight: 600;">X:</label>
                                <input type="number" id="luot-cuoc-b-x2" placeholder="X2" style="flex: 1; padding: 10px; border: 2px solid #ddd; border-radius: 6px; font-size: 14px;">
                                <label style="min-width: 30px; font-weight: 600;">Y:</label>
                                <input type="number" id="luot-cuoc-b-y2" placeholder="Y2" style="flex: 1; padding: 10px; border: 2px solid #ddd; border-radius: 6px; font-size: 14px;">
                            </div>
                            <div style="display: flex; align-items: center; gap: 10px;">
                                <label style="min-width: 30px; font-weight: 600;">X:</label>
                                <input type="number" id="luot-cuoc-b-x3" placeholder="X3" style="flex: 1; padding: 10px; border: 2px solid #ddd; border-radius: 6px; font-size: 14px;">
                                <label style="min-width: 30px; font-weight: 600;">Y:</label>
                                <input type="number" id="luot-cuoc-b-y3" placeholder="Y3" style="flex: 1; padding: 10px; border: 2px solid #ddd; border-radius: 6px; font-size: 14px;">
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Save Button -->
                <div style="text-align: center; margin-top: 30px;">
                    <button class="btn btn-primary" onclick="saveBettingCoords()" style="padding: 12px 40px; font-size: 16px;">💾 Lưu tọa độ</button>
                </div>
            </div>
        </div>
        
        <!-- Pixel Detector View -->
        <div class="table-container" id="pixel-detector-view" style="display: none;">
            <h2 style="color: #667eea; margin-bottom: 25px;">🔍 Pixel Detector Tool</h2>
            <p style="margin-bottom: 30px; color: #666;">
                Tool này giúp bạn nhận diện vị trí các pixel có màu <strong style="color: #1AFF0D;">#1AFF0D</strong> 
                trong ảnh mẫu, sau đó <strong>kiểm tra từng pixel</strong> tại các vị trí tương ứng trong ảnh cần phân tích: <strong style="color: #f39c12;">Sáng</strong> hoặc <strong style="color: #555;">Tối</strong>.
            </p>
            
            <!-- Step 1: Upload Template -->
            <div style="background: #f8f9fa; padding: 25px; border-radius: 12px; margin-bottom: 30px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                <h3 style="color: #28a745; margin-bottom: 20px;">📤 Bước 1: Upload ảnh mẫu</h3>
                <p style="margin-bottom: 10px; color: #666;">
                    Upload ảnh có chứa các pixel màu <strong style="color: #1AFF0D;">#1AFF0D</strong> để đánh dấu vị trí cần đọc
                </p>
                <div style="background: #fff3cd; color: #856404; padding: 10px; border-radius: 6px; margin-bottom: 15px; border-left: 4px solid #ffc107;">
                    <strong>⚠️ Lưu ý:</strong> Chỉ cho phép <strong>1 ảnh mẫu duy nhất</strong>. Upload ảnh mới sẽ <strong>thay thế</strong> ảnh mẫu cũ!
                </div>
                <form id="pixel-template-form" onsubmit="uploadPixelTemplate(event); return false;" style="display: flex; flex-direction: column; gap: 15px;">
                    <div>
                        <label style="font-weight: 600; display: block; margin-bottom: 5px;">Chọn ảnh mẫu:</label>
                        <input type="file" id="pixel-template-file" accept="image/*" required style="width: 100%; padding: 10px; border: 2px solid #ddd; border-radius: 6px;">
                    </div>
                    <button type="submit" class="btn btn-success" style="align-self: flex-start;">🚀 Upload và Detect Pixels</button>
                </form>
                <div id="pixel-template-result" style="margin-top: 20px;">
                    <div style="background: #fffbea; border: 2px dashed #ddd; padding: 20px; border-radius: 8px; text-align: center; color: #999;">
                        <p style="margin: 0; font-style: italic;">📊 Kết quả detect pixel sẽ hiển thị ở đây sau khi upload...</p>
                    </div>
                </div>
            </div>
            
            <!-- Current Template Info -->
            <div id="current-pixel-template-info" style="background: #e8f5e9; padding: 20px; border-radius: 12px; margin-bottom: 30px; display: none;">
                <h3 style="color: #28a745; margin-bottom: 15px;">✅ Template hiện tại</h3>
                <div id="template-info-content"></div>
            </div>
            
            <!-- Step 2: Analyze Image -->
            <div style="background: #f8f9fa; padding: 25px; border-radius: 12px; margin-bottom: 30px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                <h3 style="color: #17a2b8; margin-bottom: 20px;">🔍 Bước 2: Phân tích ảnh</h3>
                <p style="margin-bottom: 15px; color: #666;">
                    Upload ảnh cần phân tích để <strong>kiểm tra từng pixel</strong> tại các vị trí đã đánh dấu: 
                    <strong style="color: #f39c12;">Sáng</strong> hoặc <strong style="color: #555;">Tối</strong>
                </p>
                
                <!-- API Info for Mobile -->
                <div style="background: #e3f2fd; border-left: 4px solid #2196F3; padding: 15px; margin-bottom: 20px; border-radius: 6px;">
                    <h4 style="color: #1976D2; margin: 0 0 10px 0;">📱 API cho Mobile App:</h4>
                    <div style="display: flex; align-items: center; gap: 10px; background: white; padding: 10px; border-radius: 4px;">
                        <code style="flex: 1; font-size: 13px; color: #1976D2; font-weight: 600; user-select: all;">https://lukistar.space/upload/mobile</code>
                        <button class="btn btn-secondary" onclick="copyToClipboard('https://lukistar.space/upload/mobile')" style="padding: 6px 12px; font-size: 12px;">📋 Copy</button>
                    </div>
                    <p style="margin: 10px 0 0 0; font-size: 12px; color: #666;">
                        <strong>Method:</strong> POST | <strong>Body:</strong> multipart/form-data với field <code>file</code>
                    </p>
                </div>
                
                <form id="pixel-analyze-form" onsubmit="analyzePixelImage(event); return false;" style="display: flex; flex-direction: column; gap: 15px;">
                    <div>
                        <label style="font-weight: 600; display: block; margin-bottom: 5px;">Chọn ảnh cần phân tích:</label>
                        <input type="file" id="pixel-analyze-file" accept="image/*" required style="width: 100%; padding: 10px; border: 2px solid #ddd; border-radius: 6px;">
                    </div>
                    <button type="submit" class="btn btn-primary" style="align-self: flex-start;">🔍 Phân tích</button>
                </form>
                <div id="pixel-analyze-result" style="margin-top: 20px;"></div>
            </div>
            
            <!-- Analysis Results -->
            <div id="pixel-analysis-results-container" style="display: none;">
                <h3 style="color: #667eea; margin-bottom: 20px;">📊 Kết quả phân tích</h3>
                <div id="pixel-analysis-results-content"></div>
            </div>
            
            <!-- Mobile Upload History -->
            <div style="margin-top: 40px; padding-top: 30px; border-top: 2px solid #eee;">
                <h3 style="color: #667eea; margin-bottom: 20px;">📱 Lịch sử upload từ Mobile</h3>
                <button class="btn btn-primary" onclick="loadMobileUploadHistory()" style="margin-bottom: 15px;">🔄 Làm mới</button>
                <div id="mobile-upload-history"></div>
            </div>
            
            <!-- Templates List -->
            <div style="margin-top: 40px; padding-top: 30px; border-top: 2px solid #eee;">
                <h3 style="color: #667eea; margin-bottom: 20px;">📋 Danh sách Templates</h3>
                <button class="btn btn-primary" onclick="loadPixelTemplates()" style="margin-bottom: 15px;">🔄 Làm mới</button>
                <div id="pixel-templates-list"></div>
            </div>
        </div>
        
        <!-- OCR View -->
        <div class="table-container" id="ocr-view" style="display: none;">
            <h2 style="color: #667eea; margin-bottom: 25px;">📝 Đọc text từ ảnh (ChatGPT Vision)</h2>
            <p style="margin-bottom: 30px; color: #666;">
                Sử dụng <strong>ChatGPT Vision API</strong> để đọc và trích xuất nội dung text từ ảnh.
            </p>
            
            <!-- Upload Section -->
            <div style="background: #f8f9fa; padding: 25px; border-radius: 12px; margin-bottom: 30px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                <h3 style="color: #28a745; margin-bottom: 20px;">📤 Upload ảnh cần đọc</h3>
                
                <form id="ocr-form" onsubmit="startOCR(event); return false;" style="display: flex; flex-direction: column; gap: 15px;">
                    <div>
                        <label style="font-weight: 600; display: block; margin-bottom: 5px;">Chọn ảnh:</label>
                        <input type="file" id="ocr-file" accept="image/*" required style="width: 100%; padding: 10px; border: 2px solid #ddd; border-radius: 6px;">
                    </div>
                    
                    <!-- Image Preview -->
                    <div id="ocr-preview" style="display: none; margin-top: 10px;">
                        <p style="font-weight: 600; margin-bottom: 5px;">Xem trước:</p>
                        <img id="ocr-preview-img" style="max-width: 100%; max-height: 400px; border: 2px solid #ddd; border-radius: 8px;" />
                    </div>
                    
                    <button type="submit" class="btn btn-success" style="align-self: flex-start; font-size: 16px; padding: 12px 24px;">🚀 Bắt đầu đọc</button>
                </form>
                
                <!-- Loading Indicator -->
                <div id="ocr-loading" style="display: none; margin-top: 20px; text-align: center;">
                    <div style="display: inline-block; padding: 20px; background: #fff3cd; border-radius: 8px; border: 2px solid #ffc107;">
                        <p style="margin: 0; color: #856404; font-weight: 600;">⏳ Đang xử lý với ChatGPT...</p>
                        <p style="margin: 5px 0 0 0; color: #856404; font-size: 14px;">Vui lòng đợi...</p>
                    </div>
                </div>
                
                <!-- Result -->
                <div id="ocr-result" style="margin-top: 20px; display: none;">
                    <h4 style="color: #28a745; margin-bottom: 15px;">✅ Kết quả đọc text:</h4>
                    
                    <!-- Column filter for table -->
                    <div id="ocr-column-filter" style="display: none; margin-bottom: 15px; padding: 15px; background: #f0f8ff; border-radius: 6px; border: 1px solid #2196F3;">
                        <strong style="display: block; margin-bottom: 10px;">🔧 Chọn cột hiển thị:</strong>
                        <div style="display: flex; gap: 15px; flex-wrap: wrap;">
                            <label style="display: flex; align-items: center; gap: 5px; cursor: pointer;">
                                <input type="checkbox" class="column-toggle" data-col="0" checked> Phiên
                            </label>
                            <label style="display: flex; align-items: center; gap: 5px; cursor: pointer;">
                                <input type="checkbox" class="column-toggle" data-col="1" checked> Thời gian
                            </label>
                            <label style="display: flex; align-items: center; gap: 5px; cursor: pointer;">
                                <input type="checkbox" class="column-toggle" data-col="2" checked> Đặt cược
                            </label>
                            <label style="display: flex; align-items: center; gap: 5px; cursor: pointer;">
                                <input type="checkbox" class="column-toggle" data-col="3" checked> Kết quả
                            </label>
                            <label style="display: flex; align-items: center; gap: 5px; cursor: pointer;">
                                <input type="checkbox" class="column-toggle" data-col="4" checked> Tổng cược
                            </label>
                            <label style="display: flex; align-items: center; gap: 5px; cursor: pointer;">
                                <input type="checkbox" class="column-toggle" data-col="5" checked> Tiền thắng
                            </label>
                            <label style="display: flex; align-items: center; gap: 5px; cursor: pointer;">
                                <input type="checkbox" class="column-toggle" data-col="6" checked> Thắng/Thua
                            </label>
                        </div>
                    </div>
                    
                    <div id="ocr-result-content" style="background: white; padding: 20px; border-radius: 8px; border: 2px solid #28a745; white-space: pre-wrap; font-family: monospace; max-height: 500px; overflow-y: auto;"></div>
                </div>
                
                <!-- Error -->
                <div id="ocr-error" style="margin-top: 20px; display: none;">
                    <div style="background: #f8d7da; color: #721c24; padding: 15px; border-radius: 6px; border: 2px solid #f5c6cb;">
                        <strong>❌ Lỗi:</strong> <span id="ocr-error-message"></span>
                    </div>
                </div>
            </div>
            
            <!-- History Section -->
            <div style="margin-top: 40px; padding-top: 30px; border-top: 2px solid #eee;">
                <h3 style="color: #667eea; margin-bottom: 20px;">📋 Lịch sử đọc text</h3>
                <button class="btn btn-primary" onclick="loadOCRHistory()" style="margin-bottom: 15px;">🔄 Làm mới</button>
                <div id="ocr-history"></div>
            </div>
        </div>
        
        <div class="pagination" id="pagination"></div>
    </div>
    
    <!-- Modal for template upload -->
    <div id="uploadTemplateModal" class="modal">
        <div class="modal-content">
            <span class="close" onclick="closeUploadTemplateModal()">&times;</span>
            <h2>Upload/Replace Template Image</h2>
            <p style="color: #e74c3c; margin-bottom: 15px;">⚠️ Upload template mới sẽ <strong>XÓA</strong> template cũ!</p>
            <form id="upload-template-form" onsubmit="uploadTemplate(event)">
                <div style="margin-bottom: 15px;">
                    <label>Tên template:</label>
                    <input type="text" id="template-name" required style="width: 100%; padding: 10px; margin-top: 5px;">
                </div>
                <div style="margin-bottom: 15px;">
                    <label>Mô tả:</label>
                    <textarea id="template-description" style="width: 100%; padding: 10px; margin-top: 5px;" rows="3"></textarea>
                </div>
                <div style="margin-bottom: 15px;">
                    <label>Chọn ảnh:</label>
                    <input type="file" id="template-file" accept="image/*" required style="margin-top: 5px;">
                </div>
                <div style="margin-bottom: 15px;">
                    <label>
                        <input type="checkbox" id="auto-detect" checked>
                        Tự động detect nốt xanh
                    </label>
                </div>
                <button type="submit" class="btn btn-primary">Upload</button>
            </form>
        </div>
    </div>
    
    <!-- Modal for log details -->
    <div id="detailModal" class="modal">
        <div class="modal-content">
            <span class="close" onclick="closeModal()">&times;</span>
            <h2>Chi tiết log #<span id="modal-log-id"></span></h2>
            <div id="modal-content"></div>
        </div>
    </div>
    
    <!-- Modal for viewing template dots -->
    <div id="templateDotsModal" class="modal">
        <div class="modal-content">
            <span class="close" onclick="closeTemplateDotsModal()">&times;</span>
            <h2>📍 Tọa độ các nốt xanh - <span id="template-dots-name"></span></h2>
            <p style="color: #666; margin-bottom: 20px;">Tổng số nốt: <strong id="template-dots-count">0</strong></p>
            <div id="template-dots-content" style="max-height: 500px; overflow-y: auto;"></div>
        </div>
    </div>
    
    <script>
        let currentPage = 0;
        const limit = 50;
        
        function refreshCurrentView() {
            if (currentView === 'screenshots') {
                loadScreenshots();
            } else if (currentView === 'templates') {
                loadTemplates();
            }
        }
        
        function closeModal() {
            document.getElementById('detailModal').style.display = 'none';
        }
        
        function formatDateTime(dt) {
            if (!dt) return '-';
            
            // Parse timestamp - có thể là UTC hoặc VN time từ Extension
            const d = new Date(dt);
            
            // Format: HH:mm:ss dd/MM/yyyy
            const hours = String(d.getHours()).padStart(2, '0');
            const minutes = String(d.getMinutes()).padStart(2, '0');
            const seconds = String(d.getSeconds()).padStart(2, '0');
            const day = String(d.getDate()).padStart(2, '0');
            const month = String(d.getMonth() + 1).padStart(2, '0');
            const year = d.getFullYear();
            
            return `${hours}:${minutes}:${seconds} ${day}/${month}/${year}`;
        }
        
        function filterTable() {
            const input = document.getElementById('search');
            const filter = input.value.toLowerCase();
            const table = document.getElementById('logs-table');
            const tr = table.getElementsByTagName('tr');
            
            for (let i = 1; i < tr.length; i++) {
                const td = tr[i].getElementsByTagName('td');
                let found = false;
                for (let j = 0; j < td.length; j++) {
                    if (td[j]) {
                        const txtValue = td[j].textContent || td[j].innerText;
                        if (txtValue.toLowerCase().indexOf(filter) > -1) {
                            found = true;
                            break;
                        }
                    }
                }
                tr[i].style.display = found ? '' : 'none';
            }
        }
        
        let currentView = 'screenshots';
        
        function switchView(view) {
            currentView = view;
            document.getElementById('screenshots-view').style.display = 'none';
            document.getElementById('templates-view').style.display = 'none';
            document.getElementById('pixel-detector-view').style.display = 'none';
            document.getElementById('ocr-view').style.display = 'none';
            
            if (view === 'screenshots') {
                document.getElementById('screenshots-view').style.display = 'block';
                loadScreenshots();
            } else if (view === 'templates') {
                document.getElementById('templates-view').style.display = 'block';
                loadTemplates();
            } else if (view === 'pixel-detector') {
                document.getElementById('pixel-detector-view').style.display = 'block';
                loadPixelTemplates();
                loadMobileUploadHistory();
            } else if (view === 'ocr') {
                document.getElementById('ocr-view').style.display = 'block';
                loadOCRHistory();
            }
        }
        
        async function loadScreenshots(page = 0) {
            try {
                document.getElementById('screenshots-loading').style.display = 'block';
                document.getElementById('screenshots-table').style.display = 'none';
                
                const response = await fetch(`/api/screenshots?limit=50&offset=${page * 50}`);
                const data = await response.json();
                
                const tbody = document.getElementById('screenshots-tbody');
                tbody.innerHTML = '';
                
                if (data.screenshots.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 40px;">Không có screenshot</td></tr>';
                } else {
                    let previousCoefficient = 1;  // Hệ số ban đầu = 1
                    
                    data.screenshots.forEach((screenshot, index) => {
                        const row = document.createElement('tr');
                        
                        // Hiển thị sequence chi tiết: T, Đ, T, Đ...
                        let analysisInfo = '';
                        if (screenshot.analysis_result && screenshot.analysis_result.sequence) {
                            const sequence = screenshot.analysis_result.sequence;
                            const shortSeq = sequence.map(s => s === 'TRẮNG' ? 'T' : 'Đ').join(', ');
                            
                            analysisInfo = `<div style="line-height: 1.8;">
                                <span class="badge badge-info">${screenshot.total_dots || sequence.length} nốt</span><br>
                                <span class="badge badge-success">${screenshot.white_count || 0} TRẮNG</span>
                                <span class="badge badge-danger">${screenshot.black_count || 0} ĐEN</span><br>
                                <div style="margin-top: 8px; font-family: monospace; font-size: 0.9em; color: #333;">
                                    ${shortSeq}
                                </div>
                            </div>`;
                        } else {
                            analysisInfo = '<span style="color: #999;">Chưa phân tích</span>';
                        }
                        
                        // Lấy sequence hiện tại và screenshot tiếp theo (cũ hơn)
                        let currentSequence = null;
                        let nextSequence = null;
                        
                        if (screenshot.analysis_result && 
                            screenshot.analysis_result.sequence && 
                            screenshot.analysis_result.sequence.length > 0) {
                            currentSequence = screenshot.analysis_result.sequence;
                        }
                        
                        // Lấy screenshot tiếp theo trong list (cũ hơn, ID nhỏ hơn)
                        const nextScreenshot = data.screenshots[index + 1];
                        if (nextScreenshot && 
                            nextScreenshot.analysis_result && 
                            nextScreenshot.analysis_result.sequence) {
                            nextSequence = nextScreenshot.analysis_result.sequence;
                        }
                        
                        // So sánh với screenshot cũ hơn (define ở đây để dùng chung)
                        const sequenceChanged = currentSequence && (!nextSequence || 
                                               JSON.stringify(currentSequence) !== JSON.stringify(nextSequence));
                        
                        // Cột "Kết quả"
                        let firstDotResult = '';
                        
                        if (currentSequence && sequenceChanged) {
                            const firstDotClass = currentSequence[0];  // Nốt đầu tiên
                            firstDotResult = firstDotClass === 'TRẮNG' 
                                ? '<span class="badge badge-success">TRẮNG</span>' 
                                : '<span class="badge badge-danger">ĐEN</span>';
                        } else if (!currentSequence) {
                            firstDotResult = '<span style="color: #ccc;">-</span>';
                        }
                        // Nếu có currentSequence nhưng không thay đổi → để trống ('')
                        
                        // Cột "Thắng/Thua" và "Hệ số"
                        let winLoss = '';
                        let coefficient = '';
                        let currentCoefficient = 1;  // Default
                        
                        if (currentSequence && sequenceChanged) {
                            // Chỉ tính khi cột "Kết quả" có hiển thị (có thay đổi)
                            const bettingMethodSelect = document.getElementById('cach-cuoc-select');
                            const bettingMethod = bettingMethodSelect ? bettingMethodSelect.value : null;
                            const resultClassification = currentSequence[0]; // TRẮNG hoặc ĐEN
                            
                            if (bettingMethod) {
                                let isWin = false;
                                
                                // Tài = TRẮNG, Xỉu = ĐEN
                                if (bettingMethod === 'tai' && resultClassification === 'TRẮNG') {
                                    isWin = true;  // Tài và TRẮNG → Thắng
                                } else if (bettingMethod === 'xiu' && resultClassification === 'ĐEN') {
                                    isWin = true;  // Xỉu và ĐEN → Thắng
                                }
                                
                                // Tính hệ số
                                if (isWin) {
                                    currentCoefficient = 1;  // Thắng → Reset về 1
                                    winLoss = '<span class="badge badge-success" style="font-size: 1em;">✅ Thắng</span>';
                                } else {
                                    currentCoefficient = previousCoefficient * 2;  // Thua → Nhân đôi
                                    winLoss = '<span class="badge badge-danger" style="font-size: 1em;">❌ Thua</span>';
                                }
                                
                                // Hiển thị hệ số
                                coefficient = `<span style="font-weight: 600; font-size: 1.1em; color: ${isWin ? '#28a745' : '#dc3545'};">${currentCoefficient}</span>`;
                                
                                // Update previousCoefficient cho lần tiếp theo
                                previousCoefficient = currentCoefficient;
                            }
                        }
                        // Nếu không có thay đổi hoặc không chọn cách cược → để trống
                        
                        row.innerHTML = `
                            <td>${screenshot.id}</td>
                            <td>${formatDateTime(screenshot.created_at)}</td>
                            <td>${analysisInfo}</td>
                            <td style="text-align: center;">${firstDotResult}</td>
                            <td style="text-align: center;">${winLoss}</td>
                            <td style="text-align: center;">${coefficient}</td>
                            <td>
                                <button class="btn btn-info" onclick="viewScreenshotDetail(${screenshot.id})">Xem</button>
                                <button class="btn btn-success" onclick="downloadJSON(${screenshot.id})">JSON</button>
                                <button class="btn btn-danger" onclick="deleteScreenshot(${screenshot.id})">Xóa</button>
                            </td>
                        `;
                        tbody.appendChild(row);
                    });
                }
                
                document.getElementById('screenshots-loading').style.display = 'none';
                document.getElementById('screenshots-table').style.display = 'table';
            } catch (error) {
                console.error('Error loading screenshots:', error);
                document.getElementById('screenshots-loading').innerHTML = 'Lỗi khi tải screenshots: ' + error.message;
            }
        }
        
        function viewScreenshot(screenshotId) {
            window.open(`/api/screenshots/${screenshotId}/image`, '_blank');
        }
        
        function downloadJSON(screenshotId) {
            window.open(`/api/logs/${screenshotId}/result`, '_blank');
        }
        
        async function viewScreenshotDetail(screenshotId) {
            try {
                const response = await fetch(`/api/logs/${screenshotId}`);
                const log = await response.json();
                
                document.getElementById('modal-log-id').textContent = screenshotId;
                
                // Hiển thị ảnh screenshot ngay đầu tiên
                let detailHtml = '<div style="text-align: center; margin-bottom: 20px;">';
                detailHtml += `<img src="/api/screenshots/${screenshotId}/image" style="max-width: 100%; max-height: 500px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);" />`;
                detailHtml += '</div>';
                
                // Thông tin cơ bản
                detailHtml += `<p><strong>📅 Thời gian:</strong> ${formatDateTime(log.created_at)}</p>`;
                
                if (log.analysis_result && log.analysis_result.positions) {
                    const positions = log.analysis_result.positions;
                    
                    // Template comparison (nếu có)
                    if (log.analysis_result.template_comparison) {
                        const tc = log.analysis_result.template_comparison;
                        const scoreColor = tc.match_score >= 90 ? '#28a745' : tc.match_score >= 70 ? '#ffc107' : '#dc3545';
                        
                        detailHtml += '<div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 15px 0;">';
                        detailHtml += '<h3 style="margin-top: 0;">📊 So sánh với Template</h3>';
                        detailHtml += `<p><strong>Template:</strong> ${tc.template_name}</p>`;
                        detailHtml += `<p><strong>Match Score:</strong> <span style="color: ${scoreColor}; font-size: 1.5em; font-weight: bold;">${tc.match_score}%</span></p>`;
                        detailHtml += `<p><strong>Khớp:</strong> ${tc.details.matched}/${tc.details.total_template_dots} nốt</p>`;
                        
                        if (tc.details.missing > 0) {
                            detailHtml += `<p><strong>Thiếu:</strong> ${tc.details.missing} nốt (${tc.details.missing_dots.join(', ')})</p>`;
                        }
                        if (tc.details.extra > 0) {
                            detailHtml += `<p><strong>Thừa:</strong> ${tc.details.extra} nốt</p>`;
                        }
                        detailHtml += '</div>';
                    }
                    
                    // Kết quả phân tích
                    detailHtml += '<h3>📈 Kết quả phân tích:</h3>';
                    detailHtml += `<p><strong>Tổng:</strong> ${log.analysis_result.total || 0} nốt</p>`;
                    detailHtml += `<p><strong>TRẮNG:</strong> <span class="badge badge-success">${log.analysis_result.white || 0}</span></p>`;
                    detailHtml += `<p><strong>ĐEN:</strong> <span class="badge badge-danger">${log.analysis_result.black || 0}</span></p>`;
                    
                    detailHtml += '<h4>Chi tiết các nốt:</h4>';
                    detailHtml += '<div style="max-height: 400px; overflow-y: auto;">';
                    detailHtml += '<table style="width: 100%; margin-top: 10px; border-collapse: collapse;">';
                    detailHtml += '<thead><tr style="background: #667eea; color: white; position: sticky; top: 0;">';
                    detailHtml += '<th style="padding: 10px; text-align: center;">STT</th>';
                    detailHtml += '<th style="padding: 10px; text-align: center;">X</th>';
                    detailHtml += '<th style="padding: 10px; text-align: center;">Y</th>';
                    detailHtml += '<th style="padding: 10px; text-align: center;">Mã màu</th>';
                    detailHtml += '<th style="padding: 10px; text-align: center;">Độ sáng</th>';
                    detailHtml += '<th style="padding: 10px; text-align: center;">Phân loại</th>';
                    detailHtml += '</tr></thead><tbody>';
                    
                    positions.forEach((pos, index) => {
                        const bgColor = index % 2 === 0 ? '#f8f9fa' : 'white';
                        const colorRgb = pos.color_rgb || 'N/A';
                        const brightness = pos.brightness !== undefined ? pos.brightness : 'N/A';
                        
                        // Color preview box
                        const colorPreview = pos.color_r !== undefined 
                            ? `<div style="display: inline-flex; align-items: center; gap: 8px;">
                                 <div style="width: 20px; height: 20px; background-color: rgb(${pos.color_r}, ${pos.color_g}, ${pos.color_b}); border: 1px solid #ccc; border-radius: 3px;"></div>
                                 <span style="font-family: monospace; font-size: 0.9em;">${colorRgb}</span>
                               </div>`
                            : colorRgb;
                        
                        detailHtml += `<tr style="background: ${bgColor};">
                            <td style="padding: 10px; text-align: center; border-bottom: 1px solid #ddd;"><strong>${pos.number}</strong></td>
                            <td style="padding: 10px; text-align: center; border-bottom: 1px solid #ddd;">${pos.x}</td>
                            <td style="padding: 10px; text-align: center; border-bottom: 1px solid #ddd;">${pos.y}</td>
                            <td style="padding: 10px; text-align: center; border-bottom: 1px solid #ddd;">${colorPreview}</td>
                            <td style="padding: 10px; text-align: center; border-bottom: 1px solid #ddd;">${brightness}</td>
                            <td style="padding: 10px; text-align: center; border-bottom: 1px solid #ddd;"><span class="badge ${pos.classification === 'TRẮNG' ? 'badge-success' : 'badge-danger'}">${pos.classification}</span></td>
                        </tr>`;
                    });
                    detailHtml += '</tbody></table>';
                    detailHtml += '</div>';
                } else {
                    detailHtml += '<p style="color: #999;">Screenshot chưa được phân tích</p>';
                }
                
                document.getElementById('modal-content').innerHTML = detailHtml;
                document.getElementById('detailModal').style.display = 'block';
            } catch (error) {
                console.error('Error loading detail:', error);
                alert('Lỗi khi tải chi tiết: ' + error.message);
            }
        }
        
        async function deleteScreenshot(screenshotId) {
            if (!confirm(`Xác nhận xóa screenshot #${screenshotId}?`)) {
                return;
            }
            
            try {
                const response = await fetch(`/api/screenshots/${screenshotId}`, {
                    method: 'DELETE'
                });
                
                if (response.ok) {
                    alert('Đã xóa screenshot!');
                    loadScreenshots();
                    loadLogs();
                } else {
                    alert('Lỗi khi xóa screenshot');
                }
            } catch (error) {
                console.error('Error deleting screenshot:', error);
                alert('Lỗi khi xóa: ' + error.message);
            }
        }
        
        // ==================== TEMPLATE FUNCTIONS ====================
        
        async function loadTemplates() {
            try {
                document.getElementById('templates-loading').style.display = 'block';
                document.getElementById('templates-table').style.display = 'none';
                
                const response = await fetch('/api/templates');
                const data = await response.json();
                
                const tbody = document.getElementById('templates-tbody');
                tbody.innerHTML = '';
                
                if (data.templates.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 40px;">Chưa có template. Click "Upload/Replace Template" để tạo.</td></tr>';
                } else {
                    // Chỉ hiển thị template đầu tiên (luôn chỉ có 1)
                    const template = data.templates[0];
                    const row = document.createElement('tr');
                    
                    row.innerHTML = `
                        <td>${template.id}</td>
                        <td><strong>${template.name}</strong></td>
                        <td><span class="badge badge-info">${template.dots_count} nốt</span></td>
                        <td>${template.image_width} x ${template.image_height}</td>
                        <td>${formatDateTime(template.created_at)}</td>
                        <td><span class="badge badge-success">Active</span></td>
                        <td>
                            <button class="btn btn-info" onclick="viewTemplateImage(${template.id})">Xem ảnh</button>
                            <button class="btn btn-success" onclick="viewTemplateDots(${template.id})">👁️ Xem nốt</button>
                            <button class="btn btn-danger" onclick="deleteTemplate(${template.id})">Xóa</button>
                        </td>
                    `;
                    tbody.appendChild(row);
                    
                    // Warning nếu có nhiều hơn 1 template (không nên xảy ra)
                    if (data.templates.length > 1) {
                        const warningRow = document.createElement('tr');
                        warningRow.innerHTML = '<td colspan="7" style="background: #fff3cd; color: #856404; text-align: center; padding: 10px;">⚠️ Phát hiện nhiều templates. Hệ thống chỉ dùng template đầu tiên.</td>';
                        tbody.appendChild(warningRow);
                    }
                }
                
                document.getElementById('templates-loading').style.display = 'none';
                document.getElementById('templates-table').style.display = 'table';
            } catch (error) {
                console.error('Error loading templates:', error);
                document.getElementById('templates-loading').innerHTML = 'Lỗi khi tải templates: ' + error.message;
            }
        }
        
        function showUploadTemplateForm() {
            document.getElementById('uploadTemplateModal').style.display = 'block';
        }
        
        function closeUploadTemplateModal() {
            document.getElementById('uploadTemplateModal').style.display = 'none';
            document.getElementById('upload-template-form').reset();
        }
        
        async function uploadTemplate(event) {
            event.preventDefault();
            
            const name = document.getElementById('template-name').value;
            const description = document.getElementById('template-description').value;
            const autoDetect = document.getElementById('auto-detect').checked;
            const file = document.getElementById('template-file').files[0];
            
            if (!file) {
                alert('Vui lòng chọn file ảnh!');
                return;
            }
            
            try {
                const formData = new FormData();
                formData.append('image', file);
                
                const response = await fetch(`/api/templates/upload?name=${encodeURIComponent(name)}&description=${encodeURIComponent(description)}&auto_detect=${autoDetect}`, {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                
                if (result.status === 'success') {
                    alert(`✅ Template đã được upload/replace thành công!\n\nDetected: ${result.green_dots_count} nốt xanh\nKích thước: ${result.image_width}x${result.image_height}`);
                    closeUploadTemplateModal();
                    loadTemplates();
                } else {
                    alert('❌ Lỗi: ' + result.message);
                }
            } catch (error) {
                console.error('Error uploading template:', error);
                alert('Lỗi khi upload: ' + error.message);
            }
        }
        
        async function deleteTemplate(templateId) {
            if (!confirm(`Xác nhận xóa template #${templateId}?`)) {
                return;
            }
            
            try {
                const response = await fetch(`/api/templates/${templateId}`, {
                    method: 'DELETE'
                });
                
                const result = await response.json();
                
                if (result.status === 'success') {
                    alert('Đã xóa template!');
                    loadTemplates();
                } else {
                    alert('Lỗi: ' + result.message);
                }
            } catch (error) {
                console.error('Error deleting template:', error);
                alert('Lỗi: ' + error.message);
            }
        }
        
        function viewTemplateImage(templateId) {
            window.open(`/api/templates/${templateId}/image`, '_blank');
        }
        
        // Helper function: Sort dots theo zigzag column-based
        function sortDotsZigzag(dots) {
            if (!dots || dots.length === 0) return [];
            
            // Clone array để không modify original
            const dotsCopy = [...dots];
            
            // 1. Group theo cột (dựa vào X)
            const colThreshold = 20;
            dotsCopy.sort((a, b) => a.x - b.x || a.y - b.y);
            
            const columns = [];
            let currentCol = [dotsCopy[0]];
            let currentX = dotsCopy[0].x;
            
            for (let i = 1; i < dotsCopy.length; i++) {
                const dot = dotsCopy[i];
                if (Math.abs(dot.x - currentX) <= colThreshold) {
                    currentCol.push(dot);
                } else {
                    columns.push(currentCol);
                    currentCol = [dot];
                    currentX = dot.x;
                }
            }
            if (currentCol.length > 0) {
                columns.push(currentCol);
            }
            
            // 2. Sort cột từ PHẢI sang TRÁI
            columns.sort((a, b) => b[0].x - a[0].x);
            
            // 3. Zigzag trong mỗi cột
            const ordered = [];
            columns.forEach((col, colIndex) => {
                // Sort theo Y
                col.sort((a, b) => a.y - b.y);
                
                if (colIndex % 2 === 0) {
                    // Cột chẵn: top → bottom
                    ordered.push(...col);
                } else {
                    // Cột lẻ: bottom → top
                    ordered.push(...col.reverse());
                }
            });
            
            return ordered;
        }
        
        async function viewTemplateDots(templateId) {
            try {
                const response = await fetch(`/api/templates/${templateId}`);
                const template = await response.json();
                
                if (!template) {
                    alert('❌ Không tìm thấy template');
                    return;
                }
                
                document.getElementById('template-dots-name').textContent = template.name;
                document.getElementById('template-dots-count').textContent = template.dots_count;
                
                const dotsContent = document.getElementById('template-dots-content');
                
                if (template.green_dots_positions && template.green_dots_positions.length > 0) {
                    // Sort theo zigzag column-based
                    const sortedDots = sortDotsZigzag(template.green_dots_positions);
                    
                    let html = '<table style="width: 100%; border-collapse: collapse;">';
                    html += '<thead><tr style="background: #667eea; color: white;">';
                    html += '<th style="padding: 10px; text-align: center;">STT</th>';
                    html += '<th style="padding: 10px; text-align: center;">Tọa độ X</th>';
                    html += '<th style="padding: 10px; text-align: center;">Tọa độ Y</th>';
                    html += '<th style="padding: 10px; text-align: center;">Action</th>';
                    html += '</tr></thead><tbody>';
                    
                    sortedDots.forEach((dot, index) => {
                        const bgColor = index % 2 === 0 ? '#f8f9fa' : 'white';
                        html += `<tr style="background: ${bgColor};">`;
                        html += `<td style="padding: 10px; text-align: center; border-bottom: 1px solid #ddd;"><strong>${index + 1}</strong></td>`;
                        html += `<td style="padding: 10px; text-align: center; border-bottom: 1px solid #ddd;">${dot.x}</td>`;
                        html += `<td style="padding: 10px; text-align: center; border-bottom: 1px solid #ddd;">${dot.y}</td>`;
                        html += `<td style="padding: 10px; text-align: center; border-bottom: 1px solid #ddd;">`;
                        html += `<button class="btn btn-secondary" onclick="copyToClipboard('(${dot.x}, ${dot.y})')" style="padding: 5px 10px; font-size: 12px;">📋 Copy</button>`;
                        html += `</td>`;
                        html += '</tr>';
                    });
                    
                    html += '</tbody></table>';
                    
                    // Add copy all button
                    const allCoords = sortedDots.map((dot, i) => `${i + 1}. (${dot.x}, ${dot.y})`).join('\\n');
                    html += `<div style="text-align: center; margin-top: 20px;">`;
                    html += `<button class="btn btn-primary" onclick="copyToClipboard('${allCoords.replace(/'/g, "\\'")}')">📋 Copy tất cả tọa độ</button>`;
                    html += `</div>`;
                    
                    dotsContent.innerHTML = html;
                } else {
                    dotsContent.innerHTML = '<p style="text-align: center; color: #999; padding: 40px;">Không có nốt xanh nào được detect.</p>';
                }
                
                document.getElementById('templateDotsModal').style.display = 'block';
                
            } catch (error) {
                console.error('Error loading template dots:', error);
                alert('❌ Lỗi khi tải tọa độ: ' + error.message);
            }
        }
        
        function closeTemplateDotsModal() {
            document.getElementById('templateDotsModal').style.display = 'none';
        }
        
        // ==================== END TEMPLATE FUNCTIONS ====================
        
        // ==================== UTILITY FUNCTIONS ====================
        
        function copyToClipboard(text) {
            navigator.clipboard.writeText(text).then(() => {
                alert('✅ Đã copy vào clipboard:\\n' + text);
            }).catch(err => {
                console.error('Copy failed:', err);
                alert('❌ Không thể copy. Vui lòng copy thủ công.');
            });
        }
        
        // ==================== BETTING COORDINATES FUNCTIONS ====================
        
        async function saveBettingMethod() {
            const select = document.getElementById('cach-cuoc-select');
            const value = select.value;
            const text = select.options[select.selectedIndex].text;
            
            if (value) {
                try {
                    // Lưu vào SQLite qua API
                    const response = await fetch('/api/settings/betting-method', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({method: value})
                    });
                    
                    const result = await response.json();
                    
                    if (result.status === 'success') {
                        document.getElementById('selected-betting-method').textContent = `Đã chọn: ${text} (đã lưu vào DB)`;
                        document.getElementById('selected-betting-method').style.color = value === 'tai' ? '#28a745' : '#dc3545';
                        
                        // Refresh bảng Screenshots để cập nhật cột Thắng/Thua
                        if (currentView === 'screenshots') {
                            loadScreenshots();
                        }
                    } else {
                        alert('❌ Lỗi khi lưu: ' + result.message);
                    }
                } catch (error) {
                    console.error('Error saving betting method:', error);
                    alert('❌ Lỗi khi lưu: ' + error.message);
                }
            }
        }
        
        async function loadBettingMethod() {
            try {
                // Load từ SQLite qua API
                const response = await fetch('/api/settings/betting-method');
                const data = await response.json();
                
                if (data.has_value && data.method) {
                    const select = document.getElementById('cach-cuoc-select');
                    select.value = data.method;
                    const text = select.options[select.selectedIndex].text;
                    document.getElementById('selected-betting-method').textContent = `Đã chọn: ${text}`;
                    document.getElementById('selected-betting-method').style.color = data.method === 'tai' ? '#28a745' : '#dc3545';
                }
            } catch (error) {
                console.error('Error loading betting method:', error);
            }
        }
        
        function saveBettingCoords() {
            const coords = {
                diem_cuoc_a: [
                    {
                        x: parseInt(document.getElementById('diem-cuoc-a-x1').value) || 0,
                        y: parseInt(document.getElementById('diem-cuoc-a-y1').value) || 0
                    },
                    {
                        x: parseInt(document.getElementById('diem-cuoc-a-x2').value) || 0,
                        y: parseInt(document.getElementById('diem-cuoc-a-y2').value) || 0
                    },
                    {
                        x: parseInt(document.getElementById('diem-cuoc-a-x3').value) || 0,
                        y: parseInt(document.getElementById('diem-cuoc-a-y3').value) || 0
                    }
                ],
                diem_cuoc_b: [
                    {
                        x: parseInt(document.getElementById('diem-cuoc-b-x1').value) || 0,
                        y: parseInt(document.getElementById('diem-cuoc-b-y1').value) || 0
                    },
                    {
                        x: parseInt(document.getElementById('diem-cuoc-b-x2').value) || 0,
                        y: parseInt(document.getElementById('diem-cuoc-b-y2').value) || 0
                    },
                    {
                        x: parseInt(document.getElementById('diem-cuoc-b-x3').value) || 0,
                        y: parseInt(document.getElementById('diem-cuoc-b-y3').value) || 0
                    }
                ],
                luot_cuoc_a: [
                    {
                        x: parseInt(document.getElementById('luot-cuoc-a-x1').value) || 0,
                        y: parseInt(document.getElementById('luot-cuoc-a-y1').value) || 0
                    },
                    {
                        x: parseInt(document.getElementById('luot-cuoc-a-x2').value) || 0,
                        y: parseInt(document.getElementById('luot-cuoc-a-y2').value) || 0
                    },
                    {
                        x: parseInt(document.getElementById('luot-cuoc-a-x3').value) || 0,
                        y: parseInt(document.getElementById('luot-cuoc-a-y3').value) || 0
                    }
                ],
                luot_cuoc_b: [
                    {
                        x: parseInt(document.getElementById('luot-cuoc-b-x1').value) || 0,
                        y: parseInt(document.getElementById('luot-cuoc-b-y1').value) || 0
                    },
                    {
                        x: parseInt(document.getElementById('luot-cuoc-b-x2').value) || 0,
                        y: parseInt(document.getElementById('luot-cuoc-b-y2').value) || 0
                    },
                    {
                        x: parseInt(document.getElementById('luot-cuoc-b-x3').value) || 0,
                        y: parseInt(document.getElementById('luot-cuoc-b-y3').value) || 0
                    }
                ]
            };
            
            // Lưu vào localStorage
            localStorage.setItem('betting_coords', JSON.stringify(coords));
            
            alert('✅ Đã lưu tọa độ thành công!\\n\\nĐiểm cược A: ' + coords.diem_cuoc_a.length + ' tọa độ\\nĐiểm cược B: ' + coords.diem_cuoc_b.length + ' tọa độ\\nLượt cược A: ' + coords.luot_cuoc_a.length + ' tọa độ\\nLượt cược B: ' + coords.luot_cuoc_b.length + ' tọa độ');
        }
        
        function loadBettingCoords() {
            const saved = localStorage.getItem('betting_coords');
            if (!saved) return;
            
            try {
                const coords = JSON.parse(saved);
                
                // Load Điểm cược A
                if (coords.diem_cuoc_a && coords.diem_cuoc_a.length >= 3) {
                    document.getElementById('diem-cuoc-a-x1').value = coords.diem_cuoc_a[0].x;
                    document.getElementById('diem-cuoc-a-y1').value = coords.diem_cuoc_a[0].y;
                    document.getElementById('diem-cuoc-a-x2').value = coords.diem_cuoc_a[1].x;
                    document.getElementById('diem-cuoc-a-y2').value = coords.diem_cuoc_a[1].y;
                    document.getElementById('diem-cuoc-a-x3').value = coords.diem_cuoc_a[2].x;
                    document.getElementById('diem-cuoc-a-y3').value = coords.diem_cuoc_a[2].y;
                }
                
                // Load Điểm cược B
                if (coords.diem_cuoc_b && coords.diem_cuoc_b.length >= 3) {
                    document.getElementById('diem-cuoc-b-x1').value = coords.diem_cuoc_b[0].x;
                    document.getElementById('diem-cuoc-b-y1').value = coords.diem_cuoc_b[0].y;
                    document.getElementById('diem-cuoc-b-x2').value = coords.diem_cuoc_b[1].x;
                    document.getElementById('diem-cuoc-b-y2').value = coords.diem_cuoc_b[1].y;
                    document.getElementById('diem-cuoc-b-x3').value = coords.diem_cuoc_b[2].x;
                    document.getElementById('diem-cuoc-b-y3').value = coords.diem_cuoc_b[2].y;
                }
                
                // Load Lượt cược A
                if (coords.luot_cuoc_a && coords.luot_cuoc_a.length >= 3) {
                    document.getElementById('luot-cuoc-a-x1').value = coords.luot_cuoc_a[0].x;
                    document.getElementById('luot-cuoc-a-y1').value = coords.luot_cuoc_a[0].y;
                    document.getElementById('luot-cuoc-a-x2').value = coords.luot_cuoc_a[1].x;
                    document.getElementById('luot-cuoc-a-y2').value = coords.luot_cuoc_a[1].y;
                    document.getElementById('luot-cuoc-a-x3').value = coords.luot_cuoc_a[2].x;
                    document.getElementById('luot-cuoc-a-y3').value = coords.luot_cuoc_a[2].y;
                }
                
                // Load Lượt cược B
                if (coords.luot_cuoc_b && coords.luot_cuoc_b.length >= 3) {
                    document.getElementById('luot-cuoc-b-x1').value = coords.luot_cuoc_b[0].x;
                    document.getElementById('luot-cuoc-b-y1').value = coords.luot_cuoc_b[0].y;
                    document.getElementById('luot-cuoc-b-x2').value = coords.luot_cuoc_b[1].x;
                    document.getElementById('luot-cuoc-b-y2').value = coords.luot_cuoc_b[1].y;
                    document.getElementById('luot-cuoc-b-x3').value = coords.luot_cuoc_b[2].x;
                    document.getElementById('luot-cuoc-b-y3').value = coords.luot_cuoc_b[2].y;
                }
            } catch (e) {
                console.error('Error loading betting coords:', e);
            }
        }
        
        // ==================== END BETTING COORDINATES FUNCTIONS ====================
        
        // ==================== PIXEL DETECTOR FUNCTIONS ====================
        
        async function uploadPixelTemplate(event) {
                console.log('uploadPixelTemplate called');
                event.preventDefault();
                event.stopPropagation();
                
                const resultDiv = document.getElementById('pixel-template-result');
                resultDiv.innerHTML = '<div class="loading">Đang xử lý ảnh mẫu...</div>';
                
                try {
                    // Tự động tạo tên template
                    const name = 'Template ' + new Date().toLocaleString('vi-VN');
                    
                    const fileInput = document.getElementById('pixel-template-file');
                    const file = fileInput.files[0];
                    
                    if (!file) {
                        throw new Error('Vui lòng chọn file ảnh');
                    }
                    
                    const formData = new FormData();
                    formData.append('file', file);
                    
                    const response = await fetch(`/api/pixel-detector/upload-template?name=${encodeURIComponent(name)}`, {
                        method: 'POST',
                        body: formData
                    });
                    
                    const data = await response.json();
                    console.log('Upload response:', data);
                    
                    if (response.ok && data.success) {
                        console.log('Upload successful, displaying results');
                        // Không hiển thị danh sách pixel positions nữa
                        
                        resultDiv.innerHTML = `
                            <div style="background: #d4edda; color: #155724; padding: 20px; border-radius: 8px; border: 2px solid #28a745;">
                                <h4 style="margin: 0 0 15px 0;">✅ ${data.message}</h4>
                                
                                <!-- Số lượng pixel nổi bật -->
                                <div style="background: #fff; padding: 15px; border-radius: 8px; text-align: center; margin-bottom: 15px; border: 2px solid #1AFF0D;">
                                    <div style="font-size: 14px; color: #666; margin-bottom: 5px;">Số lượng pixel màu #1AFF0D phát hiện được:</div>
                                    <div style="font-size: 42px; font-weight: bold; color: #28a745;">${data.pixel_count}</div>
                                    <div style="font-size: 12px; color: #999; margin-top: 5px;">vị trí đã lưu vào database</div>
                                </div>
                                
                                <div style="background: rgba(255,255,255,0.5); padding: 10px; border-radius: 6px;">
                                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; font-size: 14px;">
                                        <div><strong>Template ID:</strong> ${data.template_id}</div>
                                        <div><strong>Kích thước ảnh:</strong> ${data.image_size.width}x${data.image_size.height}</div>
                                    </div>
                                </div>
                            </div>
                        `;
                        
                        // Reset form
                        document.getElementById('pixel-template-form').reset();
                        
                        // Reload templates
                        loadPixelTemplates();
                    } else {
                        throw new Error(data.detail || 'Lỗi không xác định');
                    }
                } catch (error) {
                    console.error('Upload error:', error);
                    resultDiv.innerHTML = `
                        <div style="background: #f8d7da; color: #721c24; padding: 15px; border-radius: 6px;">
                            <strong>❌ Lỗi:</strong> ${error.message}
                        </div>
                    `;
                }
                
                return false; // Thêm return false để chắc chắn không submit
            }
            
            async function analyzePixelImage(event) {
                event.preventDefault();
                
                const resultDiv = document.getElementById('pixel-analyze-result');
                resultDiv.innerHTML = '<div class="loading">Đang phân tích ảnh...</div>';
                
                try {
                    const fileInput = document.getElementById('pixel-analyze-file');
                    const file = fileInput.files[0];
                    
                    if (!file) {
                        throw new Error('Vui lòng chọn file ảnh');
                    }
                    
                    // Sử dụng giá trị mặc định
                    const regionWidth = 100;
                    const regionHeight = 40;
                    
                    const formData = new FormData();
                    formData.append('file', file);
                    
                    const response = await fetch(`/api/pixel-detector/analyze?region_width=${regionWidth}&region_height=${regionHeight}`, {
                        method: 'POST',
                        body: formData
                    });
                    
                    const data = await response.json();
                    
                    if (response.ok && data.success) {
                        resultDiv.innerHTML = `
                            <div style="background: #d4edda; color: #155724; padding: 15px; border-radius: 6px;">
                                <h4>✅ ${data.message}</h4>
                                <p><strong>Template:</strong> ${data.template_name}</p>
                            </div>
                        `;
                        
                        // Display results
                        displayAnalysisResults(data.results);
                        
                        // Reload mobile upload history
                        loadMobileUploadHistory();
                        
                        // Reset form
                        document.getElementById('pixel-analyze-form').reset();
                    } else {
                        throw new Error(data.detail || 'Lỗi không xác định');
                    }
                } catch (error) {
                    resultDiv.innerHTML = `
                        <div style="background: #f8d7da; color: #721c24; padding: 15px; border-radius: 6px;">
                            <strong>❌ Lỗi:</strong> ${error.message}
                        </div>
                    `;
                }
            }
            
            function displayAnalysisResults(results) {
                const container = document.getElementById('pixel-analysis-results-container');
                const content = document.getElementById('pixel-analysis-results-content');
                
                if (!results || results.length === 0) {
                    content.innerHTML = '<p>Không có kết quả</p>';
                    container.style.display = 'block';
                    return;
                }
                
                // Tính thống kê
                let lightCount = 0;
                let darkCount = 0;
                results.forEach(result => {
                    if (result.result === 'Sáng') lightCount++;
                    else if (result.result === 'Tối') darkCount++;
                });
                
                // CHỈ hiển thị thống kê tổng
                let html = `
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                        <div style="background: #fff9e6; padding: 30px; border-radius: 12px; text-align: center; border: 3px solid #f39c12; box-shadow: 0 4px 12px rgba(243, 156, 18, 0.3);">
                            <div style="font-size: 18px; color: #666; margin-bottom: 15px; font-weight: 600;">🔆 Pixel Sáng</div>
                            <div style="font-size: 64px; font-weight: bold; color: #f39c12;">${lightCount}</div>
                            <div style="font-size: 16px; color: #999; margin-top: 10px;">vị trí</div>
                        </div>
                        <div style="background: #f0f0f0; padding: 30px; border-radius: 12px; text-align: center; border: 3px solid #555; box-shadow: 0 4px 12px rgba(85, 85, 85, 0.3);">
                            <div style="font-size: 18px; color: #666; margin-bottom: 15px; font-weight: 600;">🌑 Pixel Tối</div>
                            <div style="font-size: 64px; font-weight: bold; color: #555;">${darkCount}</div>
                            <div style="font-size: 16px; color: #999; margin-top: 10px;">vị trí</div>
                        </div>
                    </div>
                    <div style="text-align: center; margin-top: 30px; padding: 20px; background: #f8f9fa; border-radius: 8px;">
                        <p style="font-size: 18px; color: #667eea; font-weight: 600; margin: 0;">
                            Tổng cộng: <strong>${results.length}</strong> vị trí đã được phân tích
                        </p>
                    </div>
                `;
                
                content.innerHTML = html;
                container.style.display = 'block';
            }
            
            async function loadMobileUploadHistory() {
                const historyDiv = document.getElementById('mobile-upload-history');
                historyDiv.innerHTML = '<div class="loading">Đang tải lịch sử...</div>';
                
                try {
                    const response = await fetch('/api/pixel-detector/analysis-history?limit=10');
                    const data = await response.json();
                    
                    if (response.ok && data.success) {
                        if (data.history.length === 0) {
                            historyDiv.innerHTML = '<p style="color: #666; font-style: italic; padding: 20px; text-align: center;">Chưa có ảnh nào được upload từ mobile</p>';
                        } else {
                            let html = '<div style="overflow-x: auto;">';
                            html += '<table style="width: 100%; border-collapse: collapse; background: white;">';
                            html += '<thead><tr style="background: #667eea; color: white;">';
                            html += '<th style="padding: 12px; text-align: left;">ID</th>';
                            html += '<th style="padding: 12px; text-align: left;">Ảnh</th>';
                            html += '<th style="padding: 12px; text-align: left;">Thời gian nhận</th>';
                            html += '<th style="padding: 12px; text-align: center;">Pixel Sáng</th>';
                            html += '<th style="padding: 12px; text-align: center;">Pixel Tối</th>';
                            html += '<th style="padding: 12px; text-align: center;">Tổng</th>';
                            html += '<th style="padding: 12px; text-align: center;">Hành động</th>';
                            html += '</tr></thead><tbody>';
                            
                            data.history.forEach(item => {
                                // Tính thống kê
                                let lightCount = 0;
                                let darkCount = 0;
                                if (item.results && Array.isArray(item.results)) {
                                    item.results.forEach(r => {
                                        if (r.result === 'Sáng') lightCount++;
                                        else if (r.result === 'Tối') darkCount++;
                                    });
                                }
                                
                                // Format thời gian
                                const analyzedAt = new Date(item.analyzed_at).toLocaleString('vi-VN');
                                
                                // Image URL
                                const imageUrl = item.image_path 
                                    ? `/api/pixel-detector/image/${item.id}` 
                                    : null;
                                
                                html += '<tr style="border-bottom: 1px solid #eee;">';
                                html += `<td style="padding: 12px;">#${item.id}</td>`;
                                
                                // Thumbnail
                                html += '<td style="padding: 12px;">';
                                if (imageUrl) {
                                    html += `<img src="${imageUrl}" style="width: 80px; height: 60px; object-fit: cover; border-radius: 4px; cursor: pointer; border: 2px solid #ddd;" onclick="window.open('${imageUrl}', '_blank')" title="Click để xem ảnh gốc">`;
                                } else {
                                    html += '<span style="color: #999; font-style: italic;">Không có</span>';
                                }
                                html += '</td>';
                                
                                // Thời gian
                                html += `<td style="padding: 12px;">${analyzedAt}</td>`;
                                
                                // Pixel Sáng
                                html += `<td style="padding: 12px; text-align: center; background: #fff9e6;"><strong style="color: #f39c12;">${lightCount}</strong></td>`;
                                
                                // Pixel Tối
                                html += `<td style="padding: 12px; text-align: center; background: #f0f0f0;"><strong style="color: #555;">${darkCount}</strong></td>`;
                                
                                // Tổng
                                html += `<td style="padding: 12px; text-align: center;"><strong>${lightCount + darkCount}</strong></td>`;
                                
                                // Hành động
                                html += '<td style="padding: 12px; text-align: center;">';
                                if (imageUrl) {
                                    html += `<button class="btn btn-info" onclick="window.open('${imageUrl}', '_blank')" style="padding: 5px 10px; font-size: 12px;">👁️ Xem ảnh</button>`;
                                }
                                html += '</td>';
                                
                                html += '</tr>';
                            });
                            
                            html += '</tbody></table></div>';
                            historyDiv.innerHTML = html;
                        }
                    } else {
                        throw new Error(data.detail || 'Lỗi tải lịch sử');
                    }
                } catch (error) {
                    historyDiv.innerHTML = `
                        <div style="background: #f8d7da; color: #721c24; padding: 15px; border-radius: 6px;">
                            <strong>❌ Lỗi:</strong> ${error.message}
                        </div>
                    `;
                }
            }
            
            async function loadPixelTemplates() {
                const listDiv = document.getElementById('pixel-templates-list');
                listDiv.innerHTML = '<div class="loading">Đang tải templates...</div>';
                
                try {
                    const response = await fetch('/api/pixel-detector/templates');
                    const data = await response.json();
                    
                    if (response.ok && data.success) {
                        const uploadSection = document.querySelector('#pixel-detector-view > div:nth-child(3)'); // Upload form section
                        
                        if (data.templates.length === 0) {
                            listDiv.innerHTML = '<p style="color: #666; font-style: italic;">Chưa có template nào</p>';
                            // Chưa có template - HIỆN form upload
                            if (uploadSection) uploadSection.style.display = 'block';
                            document.getElementById('current-pixel-template-info').style.display = 'none';
                        } else {
                            let html = '<table style="width: 100%; border-collapse: collapse;">';
                            html += '<thead><tr style="background: #667eea; color: white;">';
                            html += '<th style="padding: 10px; text-align: left;">ID</th>';
                            html += '<th style="padding: 10px; text-align: left;">Tên</th>';
                            html += '<th style="padding: 10px; text-align: left;">Số pixel</th>';
                            html += '<th style="padding: 10px; text-align: left;">Kích thước</th>';
                            html += '<th style="padding: 10px; text-align: left;">Ngày tạo</th>';
                            html += '<th style="padding: 10px; text-align: left;">Trạng thái</th>';
                            html += '<th style="padding: 10px; text-align: left;">Hành động</th>';
                            html += '</tr></thead><tbody>';
                            
                            data.templates.forEach(template => {
                                html += '<tr style="border-bottom: 1px solid #eee;">';
                                html += `<td style="padding: 10px;">${template.id}</td>`;
                                html += `<td style="padding: 10px;">${template.name}</td>`;
                                html += `<td style="padding: 10px;">${template.pixel_count}</td>`;
                                html += `<td style="padding: 10px;">${template.image_width}x${template.image_height}</td>`;
                                html += `<td style="padding: 10px;">${new Date(template.created_at).toLocaleString('vi-VN')}</td>`;
                                html += `<td style="padding: 10px;">`;
                                if (template.is_active) {
                                    html += '<span class="badge badge-success">Đang dùng</span>';
                                } else {
                                    html += '<span class="badge badge-info">Không dùng</span>';
                                }
                                html += '</td>';
                                html += `<td style="padding: 10px;">`;
                                html += `<button class="btn btn-danger" onclick="deletePixelTemplate(${template.id})" style="padding: 5px 10px; font-size: 12px;">🗑️ Xóa</button>`;
                                html += '</td>';
                                html += '</tr>';
                            });
                            
                            html += '</tbody></table>';
                            listDiv.innerHTML = html;
                            
                            // Show current active template và ẩn/hiện upload form
                            const activeTemplate = data.templates.find(t => t.is_active);
                            const uploadSection = document.querySelector('#pixel-detector-view > div:nth-child(3)'); // Upload form section
                            
                            if (activeTemplate) {
                                // Đã có template - ẨN form upload, HIỆN thông tin template
                                if (uploadSection) uploadSection.style.display = 'none';
                                document.getElementById('current-pixel-template-info').style.display = 'block';
                                document.getElementById('template-info-content').innerHTML = `
                                    <p><strong>Tên:</strong> ${activeTemplate.name}</p>
                                    <p><strong>Số pixel:</strong> ${activeTemplate.pixel_count} vị trí</p>
                                    <p><strong>Kích thước:</strong> ${activeTemplate.image_width}x${activeTemplate.image_height}</p>
                                    <p><strong>Ngày tạo:</strong> ${new Date(activeTemplate.created_at).toLocaleString('vi-VN')}</p>
                                    <p style="margin-top: 15px;"><em>✅ Template đã sẵn sàng. Bạn có thể phân tích ảnh ngay!</em></p>
                                `;
                            } else {
                                // Chưa có template - HIỆN form upload, ẨN thông tin template
                                if (uploadSection) uploadSection.style.display = 'block';
                                document.getElementById('current-pixel-template-info').style.display = 'none';
                            }
                        }
                    } else {
                        throw new Error(data.detail || 'Lỗi tải templates');
                    }
                } catch (error) {
                    listDiv.innerHTML = `
                        <div style="background: #f8d7da; color: #721c24; padding: 15px; border-radius: 6px;">
                            <strong>❌ Lỗi:</strong> ${error.message}
                        </div>
                    `;
                }
            }
            
            async function deletePixelTemplate(templateId) {
                if (!confirm('Bạn có chắc muốn xóa template này?')) {
                    return;
                }
                
                try {
                    const response = await fetch(`/api/pixel-detector/template/${templateId}`, {
                        method: 'DELETE'
                    });
                    
                    const data = await response.json();
                    
                    if (response.ok && data.success) {
                        alert('✅ Đã xóa template thành công');
                        loadPixelTemplates();
                    } else {
                        throw new Error(data.detail || 'Lỗi không xác định');
                    }
                } catch (error) {
                    alert('❌ Lỗi: ' + error.message);
                }
            }
            
            // ==================== OCR FUNCTIONS ====================
            
            // Preview image when selected
            document.addEventListener('DOMContentLoaded', function() {
                const fileInput = document.getElementById('ocr-file');
                if (fileInput) {
                    fileInput.addEventListener('change', function(e) {
                        const file = e.target.files[0];
                        if (file) {
                            const reader = new FileReader();
                            reader.onload = function(e) {
                                document.getElementById('ocr-preview-img').src = e.target.result;
                                document.getElementById('ocr-preview').style.display = 'block';
                            };
                            reader.readAsDataURL(file);
                        }
                    });
                }
            });
            
            async function startOCR(event) {
                event.preventDefault();
                event.stopPropagation();
                
                const fileInput = document.getElementById('ocr-file');
                const file = fileInput.files[0];
                
                if (!file) {
                    alert('Vui lòng chọn ảnh');
                    return;
                }
                
                // Hide previous results/errors
                document.getElementById('ocr-result').style.display = 'none';
                document.getElementById('ocr-error').style.display = 'none';
                
                // Show loading
                document.getElementById('ocr-loading').style.display = 'block';
                
                const formData = new FormData();
                formData.append('file', file);
                
                try {
                    const response = await fetch('/api/ocr/analyze', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const data = await response.json();
                    
                    // Hide loading
                    document.getElementById('ocr-loading').style.display = 'none';
                    
                    if (response.ok && data.success) {
                        // Parse and display result
                        const resultDiv = document.getElementById('ocr-result-content');
                        const text = data.text;
                        
                        // Check if result is table format (contains pipe separator)
                        if (text.includes('|') && text.split('\\\\n').length > 1) {
                            // Parse as table
                            const lines = text.trim().split('\\\\n');
                            let html = '<div style="overflow-x: auto;">';
                            html += '<table id="ocr-table" style="width: 100%; border-collapse: collapse; background: white; margin-top: 10px;">';
                            
                            lines.forEach((line, index) => {
                                const cells = line.split('|').map(c => c.trim());
                                
                                if (index === 0) {
                                    // Header row
                                    html += '<thead><tr style="background: #28a745; color: white;">';
                                    cells.forEach((cell, cellIndex) => {
                                        html += `<th class="col-${cellIndex}" style="padding: 12px; text-align: left; border: 1px solid #ddd;">${cell}</th>`;
                                    });
                                    html += '</tr></thead><tbody>';
                                } else {
                                    // Data row
                                    html += '<tr style="border-bottom: 1px solid #eee;">';
                                    cells.forEach((cell, cellIndex) => {
                                        let style = 'padding: 12px; border: 1px solid #ddd;';
                                        
                                        // Highlight "Thắng/Thua" column (index 6)
                                        if (cellIndex === 6) {
                                            if (cell === 'Thắng') {
                                                style += 'background: #d4edda; color: #155724; font-weight: bold; font-size: 16px;';
                                            } else if (cell === 'Thua') {
                                                style += 'background: #f8d7da; color: #721c24; font-weight: bold; font-size: 16px;';
                                            }
                                        }
                                        
                                        // Highlight winnings column (index 5) - lighter
                                        if (cellIndex === 5) {
                                            if (cell.startsWith('+')) {
                                                style += 'color: #28a745; font-weight: 600;';
                                            } else if (cell.startsWith('-')) {
                                                style += 'color: #dc3545; font-weight: 600;';
                                            }
                                        }
                                        
                                        html += `<td class="col-${cellIndex}" style="${style}">${cell}</td>`;
                                    });
                                    html += '</tr>';
                                }
                            });
                            
                            html += '</tbody></table></div>';
                            
                            // Add summary
                            const dataRows = lines.slice(1);
                            html += `<div style="margin-top: 15px; padding: 10px; background: #e7f3ff; border-radius: 6px; border-left: 4px solid #2196F3;">
                                <strong>📊 Tổng kết:</strong> ${dataRows.length} dòng dữ liệu
                            </div>`;
                            
                            resultDiv.innerHTML = html;
                            
                            // Show column filter
                            document.getElementById('ocr-column-filter').style.display = 'block';
                            
                            // Add column toggle handlers
                            document.querySelectorAll('.column-toggle').forEach(checkbox => {
                                checkbox.addEventListener('change', function() {
                                    const colIndex = this.getAttribute('data-col');
                                    const cells = document.querySelectorAll(`.col-${colIndex}`);
                                    cells.forEach(cell => {
                                        cell.style.display = this.checked ? '' : 'none';
                                    });
                                });
                            });
                        } else {
                            // Display as plain text
                            resultDiv.textContent = text;
                            document.getElementById('ocr-column-filter').style.display = 'none';
                        }
                        
                        document.getElementById('ocr-result').style.display = 'block';
                        
                        // Reload history
                        loadOCRHistory();
                        
                        // Reset form
                        document.getElementById('ocr-form').reset();
                        document.getElementById('ocr-preview').style.display = 'none';
                    } else {
                        throw new Error(data.detail || 'Lỗi không xác định');
                    }
                } catch (error) {
                    // Hide loading
                    document.getElementById('ocr-loading').style.display = 'none';
                    
                    // Show error
                    document.getElementById('ocr-error-message').textContent = error.message;
                    document.getElementById('ocr-error').style.display = 'block';
                }
            }
            
            async function loadOCRHistory() {
                const historyDiv = document.getElementById('ocr-history');
                historyDiv.innerHTML = '<div class="loading">Đang tải lịch sử...</div>';
                
                try {
                    const response = await fetch('/api/ocr/history?limit=10');
                    const data = await response.json();
                    
                    if (response.ok && data.success) {
                        if (data.history.length === 0) {
                            historyDiv.innerHTML = '<p style="color: #666; font-style: italic; padding: 20px; text-align: center;">Chưa có lịch sử đọc text</p>';
                        } else {
                            let html = '<div style="overflow-x: auto;">';
                            html += '<table style="width: 100%; border-collapse: collapse; background: white;">';
                            html += '<thead><tr style="background: #667eea; color: white;">';
                            html += '<th style="padding: 12px; text-align: left;">ID</th>';
                            html += '<th style="padding: 12px; text-align: left;">Thời gian</th>';
                            html += '<th style="padding: 12px; text-align: left;">Nội dung</th>';
                            html += '</tr></thead><tbody>';
                            
                            data.history.forEach(item => {
                                const createdAt = new Date(item.created_at).toLocaleString('vi-VN');
                                const textPreview = item.extracted_text.length > 100 
                                    ? item.extracted_text.substring(0, 100) + '...' 
                                    : item.extracted_text;
                                
                                html += '<tr style="border-bottom: 1px solid #eee;">';
                                html += `<td style="padding: 12px;">#${item.id}</td>`;
                                html += `<td style="padding: 12px;">${createdAt}</td>`;
                                html += `<td style="padding: 12px; font-family: monospace; white-space: pre-wrap;">${textPreview}</td>`;
                                html += '</tr>';
                            });
                            
                            html += '</tbody></table></div>';
                            historyDiv.innerHTML = html;
                        }
                    } else {
                        throw new Error(data.detail || 'Lỗi tải lịch sử');
                    }
                } catch (error) {
                    historyDiv.innerHTML = `
                        <div style="background: #f8d7da; color: #721c24; padding: 15px; border-radius: 6px;">
                            <strong>❌ Lỗi:</strong> ${error.message}
                        </div>
                    `;
                }
            }
            
        // ==================== EVENT HANDLERS ====================
        
        // Close modal when clicking outside
        window.onclick = function(event) {
            const modal = document.getElementById('detailModal');
            const uploadModal = document.getElementById('uploadTemplateModal');
            const dotsModal = document.getElementById('templateDotsModal');
            if (event.target == modal) {
                closeModal();
            } else if (event.target == uploadModal) {
                closeUploadTemplateModal();
            } else if (event.target == dotsModal) {
                closeTemplateDotsModal();
            }
        }
        
        // Load data on page load
        window.onload = function() {
            // Load Screenshots view by default
            loadScreenshots();
            
            // Load saved betting coordinates
            loadBettingCoords();
            loadBettingMethod();
        }
    </script>
</body>
</html>
    """
    return html_content

