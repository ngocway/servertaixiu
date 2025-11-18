from fastapi import FastAPI, File, UploadFile, HTTPException, Query, Form
from fastapi.responses import HTMLResponse, FileResponse, Response, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, Dict, Any, Union
from pathlib import Path
from datetime import datetime
import asyncio
import base64
import io
import json
import os
import re
import sqlite3
import unicodedata

import httpx
from PIL import Image, ImageOps, ImageEnhance
import pytesseract
from pytesseract import TesseractNotFoundError
import numpy as np
import cv2

from .services.mobile_betting_service import mobile_betting_service


app = FastAPI(title="Run Mobile Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def normalize_choice(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    text = unicodedata.normalize("NFD", str(value))
    text = ''.join(ch for ch in text if unicodedata.category(ch) != 'Mn')
    text = text.lower().strip()
    if text.startswith("tai"):
        return "tai"
    if text.startswith("xiu"):
        return "xiu"
    return None


def win_label_from_token(token: Optional[str]) -> Optional[str]:
    if token == "win":
        return "Win"
    if token == "loss":
        return "Loss"
    if token == "unknown":
        return "Unknown"
    return None


def win_token_from_label(label: Optional[str]) -> Optional[str]:
    if label is None:
        return None
    text = unicodedata.normalize("NFD", str(label))
    text = ''.join(ch for ch in text if unicodedata.category(ch) != 'Mn')
    text = text.lower().strip()
    if text.startswith("thang") or text.startswith("win"):
        return "win"
    if text.startswith("thua") or text.startswith("loss"):
        return "loss"
    if text.startswith("unknown") or text.startswith("chua xac dinh"):
        return "unknown"
    return None


def get_openai_api_key() -> str:
    key = os.getenv("OPENAI_API_KEY")
    if key:
        return key

    env_path = Path(__file__).resolve().parent.parent / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            if line.startswith("OPENAI_API_KEY="):
                value = line.split("=", 1)[1].strip()
                if value:
                    return value
    raise HTTPException(status_code=500, detail="OPENAI_API_KEY chÆ°a Ä'Æ°á»£c cáº¥u hÃ¬nh")



@app.get("/", include_in_schema=False)
async def root_redirect():
    return RedirectResponse(url="/admin", status_code=307)


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard():
    html_path = Path(__file__).with_name("run_mobile_dashboard.html")
    html_content = html_path.read_text(encoding="utf-8") if html_path.exists() else _build_dashboard_html()
    html_bytes = html_content.encode('utf-8')
    return Response(
        content=html_bytes,
        media_type="text/html; charset=utf-8",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )


def _build_dashboard_html() -> str:
    return """<!DOCTYPE html>
<html lang=\"vi\">
<head>
    <meta charset=\"UTF-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
    <title>Run Mobile Dashboard</title>
    <style>
        :root { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #1f2933; }
        body { margin: 0; background: linear-gradient(135deg, #5EE7DF 0%, #B490CA 100%); min-height: 100vh; }
        .shell { max-width: 1200px; margin: 0 auto; padding: 40px 20px 80px; }
        header { color: white; text-align: center; margin-bottom: 40px; }
        header h1 { font-size: 2.5rem; margin: 0 0 12px; }
        header p { margin: 0; opacity: 0.9; }
        .card { background: white; border-radius: 16px; box-shadow: 0 18px 40px rgba(31, 41, 51, 0.2); padding: 32px; }
        .api-card { border-left: 5px solid #ff6b6b; margin-bottom: 32px; }
        .api-row { display: flex; gap: 12px; align-items: center; margin-bottom: 8px; flex-wrap: wrap; }
        code { background: #f1f5f9; padding: 10px 14px; border-radius: 8px; font-size: 0.95rem; }
        button { cursor: pointer; border: none; border-radius: 8px; padding: 10px 18px; font-weight: 600; transition: transform 0.15s ease, box-shadow 0.15s ease; }
        button.primary { background: linear-gradient(135deg, #ff6b6b, #f06595); color: white; box-shadow: 0 10px 18px rgba(240, 101, 149, 0.35); }
        button.secondary { background: #4c51bf; color: white; box-shadow: 0 10px 18px rgba(76, 81, 191, 0.35); }
        button.small { padding: 6px 12px; font-size: 0.85rem; }
        button:hover { transform: translateY(-2px); }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; margin-bottom: 28px; }
        .stat { background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 18px; border-radius: 14px; text-align: center; }
        .stat h2 { margin: 0; font-size: 2rem; }
        .stat p { margin: 6px 0 0; opacity: 0.85; }
        .toolbar { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px; margin-bottom: 16px; }
        select { padding: 8px 12px; border-radius: 8px; border: 2px solid #e2e8f0; }
        table { width: 100%; border-collapse: collapse; }
        thead { background: linear-gradient(135deg, #ff6b6b, #f06595); color: white; }
        th, td { padding: 14px 16px; text-align: left; font-size: 0.95rem; }
        tbody tr { background: white; }
        tbody tr:nth-child(even) { background: #f7fafc; }
        tbody tr:hover { background: #ffeef3; }
        .center { text-align: center; }
        .right { text-align: right; }
        .tag { display: inline-flex; align-items: center; padding: 4px 10px; border-radius: 999px; font-size: 0.8rem; font-weight: 600; }
        .tag.history { background: #E0E7FF; color: #4338CA; }
        .tag.betting { background: #DCFCE7; color: #166534; }
        .tag.unknown { background: #FED7AA; color: #9A3412; }
        .actions { display: flex; gap: 8px; flex-wrap: wrap; }
        .muted { color: #94a3b8; font-size: 0.85rem; }
        .empty { text-align: center; padding: 40px 0; color: #475569; font-style: italic; }
        .pagination { display: flex; justify-content: center; align-items: center; gap: 8px; margin-top: 20px; flex-wrap: wrap; }
        .pagination button { padding: 8px 12px; border: 1px solid #e2e8f0; background: white; border-radius: 6px; cursor: pointer; font-size: 0.9rem; }
        .pagination button:hover:not(:disabled) { background: #f1f5f9; }
        .pagination button:disabled { opacity: 0.5; cursor: not-allowed; }
        .pagination button.active { background: linear-gradient(135deg, #ff6b6b, #f06595); color: white; border-color: transparent; }
        .pagination-info { color: #64748b; font-size: 0.9rem; margin: 0 10px; }
        .modal { position: fixed; inset: 0; background: rgba(15, 23, 42, 0.55); display: none; align-items: center; justify-content: center; padding: 40px 20px; }
        .modal-content { background: white; border-radius: 12px; max-width: 960px; width: 100%; max-height: 90vh; display: flex; flex-direction: column; overflow: hidden; }
        .modal-header { display: flex; justify-content: space-between; align-items: center; padding: 18px 24px; border-bottom: 1px solid #e2e8f0; }
        .modal-body { padding: 20px 24px; overflow-y: auto; overflow-x: hidden; display: flex; justify-content: center; align-items: center; min-height: 0; }
        .close-btn { background: none; color: #64748b; font-size: 1.5rem; padding: 0; }
        .image-wrapper { position: relative; display: flex; justify-content: center; align-items: center; max-width: 100%; width: 100%; min-width: 0; }
        #modal-image { max-width: 100%; max-height: calc(90vh - 200px); width: auto; height: auto; object-fit: contain; border-radius: 10px; display: block; }
        #mobile-image-preview { max-width: 100%; border-radius: 10px; }
        #mobile-image-overlay { position: absolute; inset: 0; pointer-events: none; }
        .mobile-overlay-box { position: absolute; border: 2px solid rgba(255, 99, 132, 0.85); border-radius: 6px; }
        .mobile-overlay-label { position: absolute; top: -26px; left: 0; background: rgba(255, 99, 132, 0.9); color: white; padding: 4px 10px; border-radius: 6px; font-size: 0.75rem; }
        pre { background: #0f172a; color: #e2e8f0; border-radius: 10px; padding: 20px; overflow: auto; }
        .sample-images-container {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 16px;
            margin-bottom: 32px;
        }
        .sample-image-card {
            background: white;
            border-radius: 16px;
            box-shadow: 0 18px 40px rgba(31, 41, 51, 0.2);
            padding: 32px;
        }
        .drop-zones-container {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
            margin-top: 20px;
        }
        .drop-zone {
            border: 2px dashed #cbd5e1;
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            background: #f8fafc;
            transition: all 0.3s ease;
            cursor: pointer;
            min-height: 200px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
        }
        .drop-zone:hover {
            border-color: #667eea;
            background: #f0f4ff;
        }
        .drop-zone.dragover {
            border-color: #667eea;
            background: #e0e7ff;
            border-style: solid;
        }
        .drop-zone-label {
            font-weight: 600;
            color: #475569;
            margin-bottom: 8px;
            font-size: 0.95rem;
        }
        .drop-zone-preview {
            max-width: 100%;
            max-height: 150px;
            border-radius: 8px;
            margin-top: 8px;
            display: none;
        }
        .drop-zone-preview.show {
            display: block;
        }
        .drop-zone-placeholder {
            color: #94a3b8;
            font-size: 0.85rem;
            margin-top: 8px;
        }
        .drop-zone-status {
            margin-top: 8px;
            font-size: 0.8rem;
        }
        @media (max-width: 768px) {
            .shell { padding: 24px 16px 60px; }
            button { width: 100%; }
            .toolbar { flex-direction: column; align-items: stretch; }
            .actions { flex-direction: column; }
            .drop-zones-container {
                grid-template-columns: repeat(2, 1fr);
            }
            /* Ẩn các phần chỉ hiển thị trên desktop */
            .api-card {
                display: none;
            }
            .sample-images-container {
                display: none;
            }
            .desktop-only {
                display: none;
            }
            /* Ẩn các nút trên mobile, chỉ giữ nút Image */
            .mobile-hide {
                display: none;
            }
        }
    </style>
</head>
<body>
    <div class=\"shell\">
        <header class=\"desktop-only\">
            <h1>ðŸ“± Run Mobile Dashboard</h1>
            <p>Theo dÃµi áº£nh tá»« thiáº¿t bá»‹ mobile vÃ  tráº¡ng thÃ¡i phÃ¢n tÃ­ch tá»± Ä‘á»™ng.</p>
        </header>
        <div class=\"card api-card\">
            <div class=\"api-row\">
                <strong>POST API:</strong>
                <code id=\"api-endpoint\">/api/mobile/analyze</code>
                <button class=\"secondary small\" onclick=\"copyEndpoint()\">ðŸ“‹ Copy</button>
            </div>
            <p class="muted" style="margin-bottom: 8px;">Gá»­i form-data gá»"m:</p>
            <div style="margin-left: 16px; margin-bottom: 8px;">
                <p class="muted" style="margin: 4px 0;"><strong>Bắt buộc:</strong> <code>file</code>, <code>device_name</code>, <code>betting_method</code></p>
                <p class="muted" style="margin: 4px 0;"><strong>Tùy chọn:</strong> <code>seconds_region_coords</code>, <code>bet_amount_region_coords</code>, <code>screenshot_width</code>, <code>screenshot_height</code>, <code>simulator_width</code>, <code>simulator_height</code></p>
                <p class="muted" style="margin: 4px 0; color: #10b981;"><strong>Để tính tọa độ nút 1K:</strong> <code>device_real_width</code> (chiều rộng màn hình mobile thật), <code>device_real_height</code> (chiều cao màn hình mobile thật)</p>
            </div>
        </div>
        <div class=\"sample-images-container\">
            <div class=\"sample-image-card\" style=\"border-left: 5px solid #10b981;\">
                <h3 style=\"margin-top: 0;\">📸 BETTING Sample Image</h3>
                <p class=\"muted\">Upload a sample BETTING image with the seconds timer marked (red box). This image will be used to help ChatGPT identify the correct seconds location.</p>
                <div style=\"display: flex; gap: 16px; align-items: center; flex-wrap: wrap;\">
                    <input type=\"file\" id=\"betting-sample-input\" accept=\"image/*\" style=\"display: none;\" onchange=\"uploadBettingSample()\">
                    <button class=\"primary\" onclick=\"document.getElementById('betting-sample-input').click()\">📤 Upload/Replace Sample</button>
                    <div id=\"betting-sample-status\" style=\"flex: 1; min-width: 200px;\"></div>
                </div>
                <div id=\"betting-sample-preview\" style=\"margin-top: 16px; text-align: center;\"></div>
            </div>
            <div class=\"sample-image-card\" style=\"border-left: 5px solid #3b82f6;\">
                <h3 style=\"margin-top: 0;\">📸 HISTORY Sample Image</h3>
                <p class=\"muted\">Upload a sample HISTORY image with the crop region marked in green (#1AFF0D). This image will be used to auto-crop HISTORY screenshots.</p>
                <div style=\"display: flex; gap: 16px; align-items: center; flex-wrap: wrap;\">
                    <input type=\"file\" id=\"history-sample-input\" accept=\"image/*\" style=\"display: none;\" onchange=\"uploadHistorySample()\">
                    <button class=\"primary\" onclick=\"document.getElementById('history-sample-input').click()\">📤 Upload/Replace Sample</button>
                    <div id=\"history-sample-status\" style=\"flex: 1; min-width: 200px;\"></div>
                </div>
                <div id=\"history-sample-preview\" style=\"margin-top: 16px; text-align: center;\"></div>
            </div>
        </div>
        <div class=\"card desktop-only\" style=\"border-left: 5px solid #f59e0b;\">
            <h3 style=\"margin-top: 0;\">🖼️ Ảnh Mẫu (Drag & Drop)</h3>
            <p class=\"muted\">Kéo thả ảnh vào các vùng bên dưới để upload ảnh mẫu. Ảnh sẽ tự động lưu khi drop.</p>
            <div class=\"drop-zones-container\">
                <div class=\"drop-zone\" id=\"drop-zone-1k\" 
                     ondragover=\"event.preventDefault(); this.classList.add('dragover');\" 
                     ondragleave=\"this.classList.remove('dragover');\" 
                     ondrop=\"handleDrop(event, '1k')\"
                     onclick=\"document.getElementById('file-input-1k').click()\">
                    <div class=\"drop-zone-label\">💰 Ảnh 1K</div>
                    <img class=\"drop-zone-preview\" id=\"preview-1k\" alt=\"Preview\" />
                    <div class=\"drop-zone-placeholder\" id=\"placeholder-1k\">Kéo thả ảnh vào đây<br/>hoặc click để chọn</div>
                    <div class=\"drop-zone-status\" id=\"status-1k\"></div>
                    <input type=\"file\" id=\"file-input-1k\" accept=\"image/*\" style=\"display: none;\" onchange=\"handleFileSelect(event, '1k')\" />
                </div>
                <div class=\"drop-zone\" id=\"drop-zone-10k\" 
                     ondragover=\"event.preventDefault(); this.classList.add('dragover');\" 
                     ondragleave=\"this.classList.remove('dragover');\" 
                     ondrop=\"handleDrop(event, '10k')\"
                     onclick=\"document.getElementById('file-input-10k').click()\">
                    <div class=\"drop-zone-label\">💵 Ảnh 10K</div>
                    <img class=\"drop-zone-preview\" id=\"preview-10k\" alt=\"Preview\" />
                    <div class=\"drop-zone-placeholder\" id=\"placeholder-10k\">Kéo thả ảnh vào đây<br/>hoặc click để chọn</div>
                    <div class=\"drop-zone-status\" id=\"status-10k\"></div>
                    <input type=\"file\" id=\"file-input-10k\" accept=\"image/*\" style=\"display: none;\" onchange=\"handleFileSelect(event, '10k')\" />
                </div>
                <div class=\"drop-zone\" id=\"drop-zone-50k\" 
                     ondragover=\"event.preventDefault(); this.classList.add('dragover');\" 
                     ondragleave=\"this.classList.remove('dragover');\" 
                     ondrop=\"handleDrop(event, '50k')\"
                     onclick=\"document.getElementById('file-input-50k').click()\">
                    <div class=\"drop-zone-label\">💴 Ảnh 50K</div>
                    <img class=\"drop-zone-preview\" id=\"preview-50k\" alt=\"Preview\" />
                    <div class=\"drop-zone-placeholder\" id=\"placeholder-50k\">Kéo thả ảnh vào đây<br/>hoặc click để chọn</div>
                    <div class=\"drop-zone-status\" id=\"status-50k\"></div>
                    <input type=\"file\" id=\"file-input-50k\" accept=\"image/*\" style=\"display: none;\" onchange=\"handleFileSelect(event, '50k')\" />
                </div>
                <div class=\"drop-zone\" id=\"drop-zone-bet-button\" 
                     ondragover=\"event.preventDefault(); this.classList.add('dragover');\" 
                     ondragleave=\"this.classList.remove('dragover');\" 
                     ondrop=\"handleDrop(event, 'bet-button')\"
                     onclick=\"document.getElementById('file-input-bet-button').click()\">
                    <div class=\"drop-zone-label\">🎯 Nút Cược</div>
                    <img class=\"drop-zone-preview\" id=\"preview-bet-button\" alt=\"Preview\" />
                    <div class=\"drop-zone-placeholder\" id=\"placeholder-bet-button\">Kéo thả ảnh vào đây<br/>hoặc click để chọn</div>
                    <div class=\"drop-zone-status\" id=\"status-bet-button\"></div>
                    <input type=\"file\" id=\"file-input-bet-button\" accept=\"image/*\" style=\"display: none;\" onchange=\"handleFileSelect(event, 'bet-button')\" />
                </div>
                <div class=\"drop-zone\" id=\"drop-zone-place-bet-button\" 
                     ondragover=\"event.preventDefault(); this.classList.add('dragover');\" 
                     ondragleave=\"this.classList.remove('dragover');\" 
                     ondrop=\"handleDrop(event, 'place-bet-button')\"
                     onclick=\"document.getElementById('file-input-place-bet-button').click()\">
                    <div class=\"drop-zone-label\">🚀 Nút Đặt Cược</div>
                    <img class=\"drop-zone-preview\" id=\"preview-place-bet-button\" alt=\"Preview\" />
                    <div class=\"drop-zone-placeholder\" id=\"placeholder-place-bet-button\">Kéo thả ảnh vào đây<br/>hoặc click để chọn</div>
                    <div class=\"drop-zone-status\" id=\"status-place-bet-button\"></div>
                    <input type=\"file\" id=\"file-input-place-bet-button\" accept=\"image/*\" style=\"display: none;\" onchange=\"handleFileSelect(event, 'place-bet-button')\" />
                </div>
            </div>
        </div>
        <div class=\"card\">
            <div class=\"stats desktop-only\">
                <div class=\"stat\">
                    <h2 id=\"stat-devices\">0</h2>
                    <p>Devices</p>
                </div>
                <div class=\"stat\">
                    <h2 id=\"stat-entries\">0</h2>
                    <p>Records</p>
                </div>
            </div>
            <div class=\"toolbar\">
                <button class=\"primary\" onclick=\"loadHistory(1)\">🔄 Refresh</button>
                <label>
                    Image Type
                    <select id=\"filter-image-type\" onchange=\"loadHistory(1)\">
                        <option value=\"\">All</option>
                        <option value=\"HISTORY\">HISTORY</option>
                        <option value=\"BETTING\">BETTING</option>
                    </select>
                </label>
                <label>
                    Device
                    <select id=\"filter-device\" onchange=\"loadHistory(1)\">
                        <option value=\"\">All</option>
                    </select>
                </label>
                <label>
                    Result
                    <select id=\"filter-result\" onchange=\"loadHistory(1)\">
                        <option value=\"\">All</option>
                        <option value=\"Win\">Win</option>
                        <option value=\"Loss\">Loss</option>
                        <option value=\"Unknown\">Unknown</option>
                    </select>
                </label>
                <label>
                    Display
                    <select id=\"history-limit\" onchange=\"loadHistory(1)\">
                        <option value=\"10\">10</option>
                        <option value=\"25\">25</option>
                        <option value=\"50\" selected>50</option>
                        <option value=\"100\">100</option>
                    </select>
                    latest records
                </label>
            </div>
            <div class=\"table-wrapper\">
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Device</th>
                            <th>Image Type</th>
                            <th class=\"center\">Seconds</th>
                            <th class=\"right\">Bet amount</th>
                            <th class=\"center\">Result</th>
                            <th>Action</th>
                        </tr>
                    </thead>
                    <tbody id=\"history-body\">
                        <tr><td colspan="7" class=\"empty\">Äang táº£i dá»¯ liá»‡u...</td></tr>
                    </tbody>
                </table>
            </div>
            <div id=\"pagination\" style=\"margin-top: 20px; display: flex; justify-content: center; align-items: center; gap: 10px; flex-wrap: wrap;\"></div>
        </div>
    </div>

    <div class=\"modal\" id=\"image-modal\">
        <div class=\"modal-content\">
            <div class=\"modal-header\">
                <div>
                    <h3>áº¢nh Run Mobile #<span id=\"modal-image-id\"></span></h3>
                    <div id=\"modal-image-info\" style=\"font-size: 12px; color: #64748b; margin-top: 4px;\"></div>
                </div>
                <div class=\"actions\">
                    <a id=\"download-link\" class=\"secondary small\" href=\"#\" download>â¬‡ï¸ Táº£i áº¢nh</a>
                    <button class=\"close-btn\" onclick=\"closeImageModal()\">&times;</button>
                </div>
            </div>
            <div class=\"modal-body\">
                <div class=\"image-wrapper\">
                    <img id=\"modal-image\" src=\"\" alt=\"Screenshot\" />
                    <div id=\"modal-overlay\"></div>
                </div>
            </div>
        </div>
    </div>

    <div class=\"modal\" id=\"json-modal\">
        <div class=\"modal-content\" style=\"max-width: 720px;\">
            <div class=\"modal-header\">
                <h3>JSON #<span id=\"modal-json-id\"></span></h3>
                <div class=\"actions\">
                    <button class=\"secondary small\" onclick=\"copyJson()\">ðŸ“‹ Copy</button>
                    <button class=\"close-btn\" onclick=\"closeJsonModal()\">&times;</button>
                </div>
            </div>
            <div class=\"modal-body\">
                <pre id=\"modal-json-content\"></pre>
            </div>
        </div>
    </div>

    <script>
        async function uploadBettingSample() {
            const input = document.getElementById('betting-sample-input');
            const file = input.files[0];
            if (!file) return;

            const statusDiv = document.getElementById('betting-sample-status');
            statusDiv.innerHTML = '<span style="color: #64748b;">Uploading...</span>';

            const formData = new FormData();
            formData.append('file', file);

            try {
                const resp = await fetch('/api/mobile/betting-sample/upload', {
                    method: 'POST',
                    body: formData
                });
                const data = await resp.json();
                
                if (resp.ok && data.success) {
                    statusDiv.innerHTML = '<span style="color: #10b981; font-weight: 600;">✓ Uploaded successfully!</span>';
                    loadBettingSamplePreview();
                } else {
                    statusDiv.innerHTML = `<span style="color: #ef4444;">Error: ${data.detail || 'Upload failed'}</span>`;
                }
            } catch (error) {
                statusDiv.innerHTML = `<span style="color: #ef4444;">Error: ${error.message}</span>`;
            }
        }

        async function loadBettingSamplePreview() {
            const previewDiv = document.getElementById('betting-sample-preview');
            try {
                const resp = await fetch('/api/mobile/betting-sample');
                if (resp.ok) {
                    const blob = await resp.blob();
                    const url = URL.createObjectURL(blob);
                    previewDiv.innerHTML = `<img src="${url}" alt="Betting Sample" style="max-width: 100%; max-height: 400px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);" />`;
                } else {
                    previewDiv.innerHTML = '<p class="muted">No sample image uploaded yet.</p>';
                }
            } catch (error) {
                previewDiv.innerHTML = '<p class="muted">No sample image uploaded yet.</p>';
            }
        }

        async function uploadHistorySample() {
            const input = document.getElementById('history-sample-input');
            const file = input.files[0];
            if (!file) return;

            const statusDiv = document.getElementById('history-sample-status');
            statusDiv.innerHTML = '<span style="color: #64748b;">Uploading...</span>';

            const formData = new FormData();
            formData.append('file', file);

            try {
                const resp = await fetch('/api/mobile/history-sample/upload', {
                    method: 'POST',
                    body: formData
                });
                const data = await resp.json();
                
                if (resp.ok && data.success) {
                    statusDiv.innerHTML = '<span style="color: #10b981; font-weight: 600;">✓ Uploaded successfully!</span>';
                    loadHistorySamplePreview();
                } else {
                    statusDiv.innerHTML = `<span style="color: #ef4444;">Error: ${data.detail || 'Upload failed'}</span>`;
                }
            } catch (error) {
                statusDiv.innerHTML = `<span style="color: #ef4444;">Error: ${error.message}</span>`;
            }
        }

        async function loadHistorySamplePreview() {
            const previewDiv = document.getElementById('history-sample-preview');
            try {
                const resp = await fetch('/api/mobile/history-sample');
                if (resp.ok) {
                    const blob = await resp.blob();
                    const url = URL.createObjectURL(blob);
                    previewDiv.innerHTML = `<img src="${url}" alt="History Sample" style="max-width: 100%; max-height: 400px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);" />`;
                } else {
                    previewDiv.innerHTML = '<p class="muted">No sample image uploaded yet.</p>';
                }
            } catch (error) {
                previewDiv.innerHTML = '<p class="muted">No sample image uploaded yet.</p>';
            }
        }

        // Drag & Drop handlers for sample images
        function handleDrop(event, type) {
            event.preventDefault();
            event.stopPropagation();
            const dropZone = event.currentTarget;
            dropZone.classList.remove('dragover');
            
            const files = event.dataTransfer.files;
            if (files.length > 0) {
                uploadSampleImage(files[0], type);
            }
        }
        
        function handleFileSelect(event, type) {
            const file = event.target.files[0];
            if (file) {
                uploadSampleImage(file, type);
            }
        }
        
        async function uploadSampleImage(file, type) {
            if (!file.type.startsWith('image/')) {
                showStatus(type, 'Chỉ chấp nhận file ảnh!', 'error');
                return;
            }
            
            const statusEl = document.getElementById(`status-${type}`);
            const previewEl = document.getElementById(`preview-${type}`);
            const placeholderEl = document.getElementById(`placeholder-${type}`);
            
            showStatus(type, 'Đang upload...', 'uploading');
            
            // Show preview immediately
            const reader = new FileReader();
            reader.onload = (e) => {
                previewEl.src = e.target.result;
                previewEl.classList.add('show');
                placeholderEl.style.display = 'none';
            };
            reader.readAsDataURL(file);
            
            const formData = new FormData();
            formData.append('file', file);
            
            const endpointMap = {
                '1k': '/api/mobile/sample-1k/upload',
                '10k': '/api/mobile/sample-10k/upload',
                '50k': '/api/mobile/sample-50k/upload',
                'bet-button': '/api/mobile/sample-bet-button/upload',
                'place-bet-button': '/api/mobile/sample-place-bet-button/upload'
            };
            
            try {
                const resp = await fetch(endpointMap[type], {
                    method: 'POST',
                    body: formData
                });
                
                const data = await resp.json();
                
                if (resp.ok && data.success) {
                    showStatus(type, '✓ Đã lưu thành công!', 'success');
                    // Load preview from server
                    loadSamplePreview(type);
                } else {
                    showStatus(type, `Lỗi: ${data.detail || 'Upload thất bại'}`, 'error');
                    previewEl.classList.remove('show');
                    placeholderEl.style.display = 'block';
                }
            } catch (error) {
                showStatus(type, `Lỗi: ${error.message}`, 'error');
                previewEl.classList.remove('show');
                placeholderEl.style.display = 'block';
            }
        }
        
        function showStatus(type, message, status) {
            const statusEl = document.getElementById(`status-${type}`);
            const colors = {
                'uploading': '#64748b',
                'success': '#10b981',
                'error': '#ef4444'
            };
            statusEl.innerHTML = `<span style="color: ${colors[status] || '#64748b'}; font-weight: ${status === 'success' ? '600' : 'normal'};">${message}</span>`;
        }
        
        async function loadSamplePreview(type) {
            const previewEl = document.getElementById(`preview-${type}`);
            const placeholderEl = document.getElementById(`placeholder-${type}`);
            
            const endpointMap = {
                '1k': '/api/mobile/sample-1k',
                '10k': '/api/mobile/sample-10k',
                '50k': '/api/mobile/sample-50k',
                'bet-button': '/api/mobile/sample-bet-button',
                'place-bet-button': '/api/mobile/sample-place-bet-button'
            };
            
            try {
                // Thêm timestamp để tránh cache
                const url = endpointMap[type] + '?t=' + Date.now();
                const resp = await fetch(url);
                if (resp.ok) {
                    const blob = await resp.blob();
                    // Revoke URL cũ nếu có để tránh memory leak
                    if (previewEl.src && previewEl.src.startsWith('blob:')) {
                        URL.revokeObjectURL(previewEl.src);
                    }
                    const newUrl = URL.createObjectURL(blob);
                    previewEl.src = newUrl;
                    previewEl.classList.add('show');
                    placeholderEl.style.display = 'none';
                } else {
                    previewEl.classList.remove('show');
                    placeholderEl.style.display = 'block';
                }
            } catch (error) {
                previewEl.classList.remove('show');
                placeholderEl.style.display = 'block';
            }
        }
        
        document.addEventListener('DOMContentLoaded', () => {
            loadHistory();
            loadBettingSamplePreview();
            loadHistorySamplePreview();
            // Load sample previews
            loadSamplePreview('1k');
            loadSamplePreview('10k');
            loadSamplePreview('50k');
            loadSamplePreview('bet-button');
            loadSamplePreview('place-bet-button');
        });

        async function copyEndpoint() {
            const endpoint = document.getElementById('api-endpoint').textContent;
            await navigator.clipboard.writeText(window.location.origin + endpoint);
            alert('ÄÃ£ copy endpoint!');
        }

        let currentPage = 1;
        let allHistoryData = [];
        let filteredHistoryData = [];

        async function loadHistory(page = 1) {
            currentPage = page;
            const limit = parseInt(document.getElementById('history-limit').value);
            const filterImageType = document.getElementById('filter-image-type').value;
            const filterDevice = document.getElementById('filter-device').value;
            const filterResult = document.getElementById('filter-result').value;
            const tbody = document.getElementById('history-body');
            tbody.innerHTML = '<tr><td colspan="7" class="empty">Äang táº£i dá»¯ liá»‡u...</td></tr>';
            try {
                // Lấy tất cả data từ server (không paginate ở server vì cần filter ở client)
                const resp = await fetch(`/api/mobile/history?limit=10000&page=1`);
                const data = await resp.json();
                if (!resp.ok || !data.success) {
                    throw new Error(data.detail || 'Failed to load data');
                }

                // Lưu tất cả data
                allHistoryData = data.history;

                // Populate Device dropdown với danh sách devices từ data
                const uniqueDevices = Array.from(new Set(allHistoryData.map(item => item.device_name))).filter(Boolean);
                const deviceSelect = document.getElementById('filter-device');
                const currentDeviceValue = deviceSelect.value;
                
                // Lưu giá trị hiện tại và clear dropdown
                deviceSelect.innerHTML = '<option value="">All</option>';
                
                // Thêm các device vào dropdown
                uniqueDevices.forEach(device => {
                    const option = document.createElement('option');
                    option.value = device;
                    option.textContent = device;
                    deviceSelect.appendChild(option);
                });
                
                // Khôi phục giá trị đã chọn nếu vẫn còn trong danh sách
                if (currentDeviceValue && uniqueDevices.includes(currentDeviceValue)) {
                    deviceSelect.value = currentDeviceValue;
                }

                // Filter data theo các giá trị đã chọn
                filteredHistoryData = allHistoryData;
                
                if (filterImageType) {
                    filteredHistoryData = filteredHistoryData.filter(record => record.image_type === filterImageType);
                }
                
                if (filterDevice) {
                    filteredHistoryData = filteredHistoryData.filter(record => record.device_name === filterDevice);
                }
                
                if (filterResult) {
                    // Normalize result value để so sánh
                    filteredHistoryData = filteredHistoryData.filter(record => {
                        const recordResult = record.win_loss || 'Unknown';
                        if (filterResult === 'Unknown') {
                            return !recordResult || recordResult === '-' || recordResult === 'Unknown';
                        }
                        return recordResult === filterResult;
                    });
                }

                // Paginate filtered data
                const totalFiltered = filteredHistoryData.length;
                const totalPages = Math.ceil(totalFiltered / limit);
                const startIndex = (currentPage - 1) * limit;
                const endIndex = startIndex + limit;
                const paginatedHistory = filteredHistoryData.slice(startIndex, endIndex);

                document.getElementById('stat-entries').textContent = totalFiltered;
                document.getElementById('stat-devices').textContent = uniqueDevices.length;

                if (paginatedHistory.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="7" class="empty">No data available</td></tr>';
                    renderPagination(1, 0);
                    return;
                }

                tbody.innerHTML = '';
                paginatedHistory.forEach(record => {
                    const tr = document.createElement('tr');

                    const tagClass = record.image_type === 'HISTORY' ? 'history' : (record.image_type === 'BETTING' ? 'betting' : 'unknown');
                    const tagLabel = record.image_type || 'UNKNOWN';

                    const planned = record.bet_amount ?? '-';
                    const winLoss = record.win_loss || '-';
                    const seconds = record.seconds_remaining ?? '-';

                    tr.innerHTML = `
                        <td>#${record.id}</td>
                        <td>${record.device_name || '-'}</td>
                        <td><span class="tag ${tagClass}">${tagLabel}</span></td>
                        <td class="center">${seconds}</td>
                        <td class="right">${formatNumber(planned)}</td>
                        <td class="center">${winLoss}</td>
                        <td class="actions">
                            ${record.image_path ? `<button class="secondary small" data-id="${record.id}" data-seconds="${record.seconds_region_coords || ''}" data-bet="${record.bet_region_coords || ''}" onclick="openImageModal(this)">🖼️ Image</button>` : ''}
                            ${record.image_type === 'HISTORY' && record.image_path ? `<button class="secondary small mobile-hide" data-id="${record.id}" onclick="openCroppedImageModal(this)">✂️ View Cropped</button>` : ''}
                            ${record.image_type === 'BETTING' && record.image_path ? `<button class="secondary small mobile-hide" data-id="${record.id}" onclick="openBettingCroppedImageModal(this)">✂️ View Cropped</button>` : ''}
                            <button class="primary small mobile-hide" onclick="openJsonModal(${record.id})">JSON</button>
                            <button class="secondary small mobile-hide" onclick="downloadJson(${record.id})">💾 Download JSON</button>
                        </td>
                    `;
                    tbody.appendChild(tr);
                });
                
                // Render pagination
                renderPagination(currentPage, totalPages);
            } catch (error) {
                console.error(error);
                tbody.innerHTML = `<tr><td colspan="7" class="empty">${error.message}</td></tr>`;
                renderPagination(1, 0);
            }
        }

        function renderPagination(currentPage, totalPages) {
            const paginationDiv = document.getElementById('pagination');
            if (!paginationDiv) return;
            
            paginationDiv.innerHTML = '';
            
            if (totalPages <= 1) {
                return;
            }
            
            // Previous button
            const prevBtn = document.createElement('button');
            prevBtn.textContent = '« Previous';
            prevBtn.disabled = currentPage === 1;
            prevBtn.onclick = () => loadHistory(currentPage - 1);
            paginationDiv.appendChild(prevBtn);
            
            // Page numbers
            const maxVisiblePages = 5;
            let startPage = Math.max(1, currentPage - Math.floor(maxVisiblePages / 2));
            let endPage = Math.min(totalPages, startPage + maxVisiblePages - 1);
            
            if (endPage - startPage < maxVisiblePages - 1) {
                startPage = Math.max(1, endPage - maxVisiblePages + 1);
            }
            
            if (startPage > 1) {
                const firstBtn = document.createElement('button');
                firstBtn.textContent = '1';
                firstBtn.onclick = () => loadHistory(1);
                paginationDiv.appendChild(firstBtn);
                
                if (startPage > 2) {
                    const ellipsis = document.createElement('span');
                    ellipsis.textContent = '...';
                    ellipsis.className = 'pagination-info';
                    paginationDiv.appendChild(ellipsis);
                }
            }
            
            for (let i = startPage; i <= endPage; i++) {
                const pageBtn = document.createElement('button');
                pageBtn.textContent = i;
                pageBtn.className = i === currentPage ? 'active' : '';
                pageBtn.onclick = () => loadHistory(i);
                paginationDiv.appendChild(pageBtn);
            }
            
            if (endPage < totalPages) {
                if (endPage < totalPages - 1) {
                    const ellipsis = document.createElement('span');
                    ellipsis.textContent = '...';
                    ellipsis.className = 'pagination-info';
                    paginationDiv.appendChild(ellipsis);
                }
                
                const lastBtn = document.createElement('button');
                lastBtn.textContent = totalPages;
                lastBtn.onclick = () => loadHistory(totalPages);
                paginationDiv.appendChild(lastBtn);
            }
            
            // Next button
            const nextBtn = document.createElement('button');
            nextBtn.textContent = 'Next »';
            nextBtn.disabled = currentPage === totalPages;
            nextBtn.onclick = () => loadHistory(currentPage + 1);
            paginationDiv.appendChild(nextBtn);
            
            // Page info
            const info = document.createElement('span');
            info.className = 'pagination-info';
            info.textContent = `Page ${currentPage} of ${totalPages}`;
            paginationDiv.appendChild(info);
        }

        function formatNumber(value) {
            if (value === null || value === undefined || value === '-') return '-';
            const number = Number(value);
            if (Number.isNaN(number)) return '-';
            return number.toLocaleString('vi-VN');
        }

        function openImageModal(button) {
            const recordId = button.dataset.id;
            const seconds = button.dataset.seconds || '';
            const bet = button.dataset.bet || '';
            const timestamp = Date.now();

            const image = document.getElementById('modal-image');
            const overlay = document.getElementById('modal-overlay');
            const download = document.getElementById('download-link');

            image.src = `/api/mobile/history/image/${recordId}?_=${timestamp}`;
            download.href = `/api/mobile/history/image/${recordId}?download=1&_=${timestamp}`;
            download.setAttribute('download', `mobile-${recordId}.jpg`);
            document.getElementById('modal-image-id').textContent = recordId;
            overlay.innerHTML = '';
            overlay.dataset.seconds = seconds;
            overlay.dataset.bet = bet;

            // Lấy thông tin kích thước
            fetch(`/api/mobile/history/image-info/${recordId}`)
                .then(res => res.json())
                .then(data => {
                    const infoEl = document.getElementById('modal-image-info');
                    if (data.actual_image_width && data.actual_image_height) {
                        let infoText = `Screenshot: ${data.actual_image_width} x ${data.actual_image_height}`;
                        if (data.device_real_width && data.device_real_height) {
                            infoText += ` | Device: ${data.device_real_width} x ${data.device_real_height}`;
                        }
                        infoEl.textContent = infoText;
                    } else {
                        infoEl.textContent = '';
                    }
                })
                .catch(err => {
                    console.error('Error fetching image info:', err);
                    document.getElementById('modal-image-info').textContent = '';
                });

            image.onload = () => renderOverlay();
            document.getElementById('image-modal').style.display = 'flex';
        }

        function openCroppedImageModal(button) {
            const recordId = button.dataset.id;
            const timestamp = Date.now();

            const image = document.getElementById('modal-image');
            const overlay = document.getElementById('modal-overlay');
            const download = document.getElementById('download-link');

            image.src = `/api/mobile/history/cropped-image/${recordId}?_=${timestamp}`;
            download.href = `/api/mobile/history/cropped-image/${recordId}?download=1&_=${timestamp}`;
            download.setAttribute('download', `cropped-mobile-${recordId}.jpg`);
            document.getElementById('modal-image-id').textContent = `${recordId} (Cropped)`;
            overlay.innerHTML = '';
            overlay.dataset.seconds = '';
            overlay.dataset.bet = '';

            image.onload = () => {
                overlay.innerHTML = '';
            };
            document.getElementById('image-modal').style.display = 'flex';
        }

        function openBettingCroppedImageModal(button) {
            const recordId = button.dataset.id;
            const timestamp = Date.now();

            const image = document.getElementById('modal-image');
            const overlay = document.getElementById('modal-overlay');
            const download = document.getElementById('download-link');

            image.src = `/api/mobile/history/betting-cropped/${recordId}?_=${timestamp}`;
            download.href = `/api/mobile/history/betting-cropped/${recordId}?download=1&_=${timestamp}`;
            download.setAttribute('download', `betting-cropped-${recordId}.jpg`);
            document.getElementById('modal-image-id').textContent = `${recordId} (Betting Cropped)`;
            overlay.innerHTML = '';
            overlay.dataset.seconds = '';
            overlay.dataset.bet = '';

            image.onload = () => {
                overlay.innerHTML = '';
            };
            document.getElementById('image-modal').style.display = 'flex';
        }

        function closeImageModal() {
            const modal = document.getElementById('image-modal');
            const image = document.getElementById('modal-image');
            const overlay = document.getElementById('modal-overlay');
            modal.style.display = 'none';
            image.src = '';
            overlay.innerHTML = '';
        }

        function parseRegions(raw) {
            if (!raw) return [];
            return raw.split('|').map(part => {
                const trimmed = part.trim();
                if (!trimmed) return null;
                const [start, end] = trimmed.split(';');
                if (!start || !end) return null;
                const [x1, y1] = start.split(':').map(Number);
                const [x2, y2] = end.split(':').map(Number);
                if ([x1, y1, x2, y2].some(v => Number.isNaN(v))) return null;
                const left = Math.min(x1, x2);
                const right = Math.max(x1, x2);
                const top = Math.min(y1, y2);
                const bottom = Math.max(y1, y2);
                if (right - left < 2 || bottom - top < 2) return null;
                return { left, right, top, bottom };
            }).filter(Boolean);
        }

        function renderOverlay() {
            const overlay = document.getElementById('modal-overlay');
            const image = document.getElementById('modal-image');
            overlay.innerHTML = '';
            const secondsRegions = parseRegions(overlay.dataset.seconds || '');
            const betRegions = parseRegions(overlay.dataset.bet || '');

            const naturalWidth = image.naturalWidth || 1;
            const naturalHeight = image.naturalHeight || 1;
            const scaleX = (image.clientWidth || naturalWidth) / naturalWidth;
            const scaleY = (image.clientHeight || naturalHeight) / naturalHeight;

            const addBox = (region, label) => {
                const box = document.createElement('div');
                box.className = 'mobile-overlay-box';
                box.style.left = `${region.left * scaleX}px`;
                box.style.top = `${region.top * scaleY}px`;
                box.style.width = `${(region.right - region.left) * scaleX}px`;
                box.style.height = `${(region.bottom - region.top) * scaleY}px`;
                if (label) {
                    const badge = document.createElement('div');
                    badge.className = 'mobile-overlay-label';
                    badge.textContent = label;
                    box.appendChild(badge);
                }
                overlay.appendChild(box);
            };

            if (secondsRegions.length > 0) addBox(secondsRegions[0], 'GiÃ¢y');
            if (betRegions.length > 0) {
                addBox(betRegions[0], 'Sáº½ cÆ°á»£c');
                if (betRegions.length > 1) addBox(betRegions[1], 'ÄÃ£ cÆ°á»£c');
            }
        }

        async function openJsonModal(id) {
            const modal = document.getElementById('json-modal');
            const content = document.getElementById('modal-json-content');
            content.textContent = 'Äang táº£i...';
            modal.style.display = 'flex';
            document.getElementById('modal-json-id').textContent = id;

            try {
                const resp = await fetch(`/api/mobile/history/json/${id}`);
                if (!resp.ok) {
                    const err = await resp.json().catch(() => ({}));
                    throw new Error(err.detail || 'KhÃ´ng thá»ƒ táº£i JSON');
                }
                const data = await resp.json();
                content.textContent = JSON.stringify(data, null, 2);
            } catch (error) {
                content.textContent = error.message;
            }
        }

        function copyJson() {
            const content = document.getElementById('modal-json-content').textContent;
            navigator.clipboard.writeText(content).then(() => alert('ÄÃ£ copy JSON!'));
        }

        async function downloadJson(id) {
            try {
                const resp = await fetch(`/api/mobile/history/json/${id}`);
                if (!resp.ok) {
                    const err = await resp.json().catch(() => ({}));
                    throw new Error(err.detail || 'Không thể tải JSON');
                }
                const data = await resp.json();
                const jsonStr = JSON.stringify(data, null, 2);
                const blob = new Blob([jsonStr], { type: 'application/json' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `json_${id}.json`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
            } catch (error) {
                alert('Lỗi tải JSON: ' + error.message);
            }
        }

        function closeJsonModal() {
            document.getElementById('json-modal').style.display = 'none';
        }

        window.addEventListener('keydown', (event) => {
            if (event.key === 'Escape') {
                closeImageModal();
                closeJsonModal();
            }
        });
    </script>
</body>
</html>
"""


@app.post("/api/mobile/analyze")
async def mobile_analyze(
    file: UploadFile = File(...),
    device_name: str = Form(...),
    betting_method: str = Form(...),
    seconds_region_coords: Optional[str] = Form(None),
    bet_amount_region_coords: Optional[str] = Form(None),
    screenshot_width: Optional[int] = Form(None),
    screenshot_height: Optional[int] = Form(None),
    simulator_width: Optional[int] = Form(None),
    simulator_height: Optional[int] = Form(None),
    device_real_width: Optional[int] = Form(None),
    device_real_height: Optional[int] = Form(None),
):
    """Nháº­n áº£nh tá»« mobile vÃ  phÃ¢n tÃ­ch."""
    try:
        image_data = await file.read()
        image = Image.open(io.BytesIO(image_data))
        actual_image_width = image.width
        actual_image_height = image.height

        scale_x = 1.0
        scale_y = 1.0
        needs_scaling = False

        if simulator_width and simulator_height and screenshot_width and screenshot_height:
            scale_x = actual_image_width / simulator_width if simulator_width > 0 else 1.0
            scale_y = actual_image_height / simulator_height if simulator_height > 0 else 1.0
            needs_scaling = True
        elif screenshot_width and screenshot_height:
            scale_x = actual_image_width / screenshot_width if screenshot_width > 0 else 1.0
            scale_y = actual_image_height / screenshot_height if screenshot_height > 0 else 1.0
            needs_scaling = True

        mobile_dir = "mobile_images/run_mobile"
        os.makedirs(mobile_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        file_extension = image.format.lower() if image.format else "jpg"
        if file_extension not in {"jpg", "jpeg", "png"}:
            file_extension = "jpg"
        saved_filename = f"mobile_{device_name}_{timestamp}.{file_extension}"
        saved_path = os.path.join(mobile_dir, saved_filename)
        image.save(saved_path, quality=95)

        def parse_region_coords(coord_str: Optional[str]):
            if not coord_str or not coord_str.strip():
                return None
            try:
                parts = coord_str.strip().split(';')
                if len(parts) != 2:
                    return None
                x1_str, y1_str = parts[0].split(':')
                x2_str, y2_str = parts[1].split(':')
                x1_raw, y1_raw = float(x1_str), float(y1_str)
                x2_raw, y2_raw = float(x2_str), float(y2_str)

                if needs_scaling:
                    x1 = int(x1_raw * scale_x)
                    y1 = int(y1_raw * scale_y)
                    x2 = int(x2_raw * scale_x)
                    y2 = int(y2_raw * scale_y)
                else:
                    x1, y1 = int(x1_raw), int(y1_raw)
                    x2, y2 = int(x2_raw), int(y2_raw)

                left, right = sorted([x1, x2])
                top, bottom = sorted([y1, y2])
                left = max(0, min(left, image.width))
                right = max(0, min(right, image.width))
                top = max(0, min(top, image.height))
                bottom = max(0, min(bottom, image.height))
                if right - left < 2 or bottom - top < 2:
                    return None
                return (left, top, right, bottom)
            except Exception:
                return None

        def parse_numeric_value(value: Optional[Union[str, int, float]]) -> Optional[int]:
            if value is None:
                return None
            if isinstance(value, (int, float)):
                return int(value)
            text = str(value).strip()
            if not text:
                return None
            digits = ''.join(ch for ch in text if ch.isdigit())
            if not digits:
                return None
            try:
                return int(digits)
            except ValueError:
                return None

        def parse_signed_numeric_value(value: Optional[Union[str, int, float]]) -> Optional[int]:
            """Parse số nguyên có giữ dấu âm/dương"""
            if value is None:
                return None
            if isinstance(value, (int, float)):
                return int(value)
            text = str(value).strip()
            if not text or text == "-":
                return None
            # Giữ dấu âm nếu có
            is_negative = text.startswith("-")
            # Loại bỏ dấu +, - và dấu phân cách nghìn
            cleaned = text.replace("+", "").replace("-", "").replace(",", "").replace(".", "")
            if not cleaned or not cleaned.isdigit():
                return None
            try:
                result = int(cleaned)
                return -result if is_negative else result
            except ValueError:
                return None

        def parse_json_payload(raw_text: str) -> Dict[str, Any]:
            if not raw_text:
                return {}
            cleaned = raw_text.strip()
            start = cleaned.find('{')
            end = cleaned.rfind('}')
            if start != -1 and end != -1 and end >= start:
                cleaned = cleaned[start : end + 1]
            try:
                return json.loads(cleaned)
            except json.JSONDecodeError:
                return {}
            except Exception:
                return {}

        

        def extract_number_from_region(base_image: Image.Image, coords: Optional[tuple]) -> int:
            if not coords:
                return 0
            region = base_image.crop(coords)
            region = region.resize(
                (
                    max(1, region.width * 2),
                    max(1, region.height * 2),
                ),
                Image.LANCZOS,
            )
            gray = ImageOps.grayscale(region)
            gray = ImageOps.autocontrast(gray)
            gray = ImageEnhance.Contrast(gray).enhance(2.0)
            try:
                text = pytesseract.image_to_string(
                    gray, config='--psm 7 -c tessedit_char_whitelist=0123456789'
                )
            except TesseractNotFoundError:
                return 0
            except Exception:
                return 0

            digits = re.sub(r'[^0-9]', '', text or '')
            if not digits:
                return 0
            try:
                return int(digits)
            except ValueError:
                return 0

        # Chuẩn bị prompts và crop regions trước (song song với API call phân loại)
        history_detail_prompt = """Phan tich anh BANG LICH SU da duoc crop va tra ve dung mot JSON:

- Chi doc DONG DAU TIEN cua bang (phien moi nhat nam tren cung, dong dau tien trong bang).
- Doc gia tri o cot "Tổng cược" (cot thu 3) cua DONG DAU TIEN va gan vao khoa "bet_amount" duoi dang so nguyen (bo dau phan cach nghin, vi du: "1,000" -> 1000, "4,000" -> 4000).
- Doc gia tri o cot "Tiền thắng" (cot thu 4) cua DONG DAU TIEN:
    * Neu cot "Tiền thắng" hien thi dau gach ngang "-" (khong co so) -> gan "winnings_amount" = null.
    * Neu cot "Tiền thắng" hien thi so duong (co dau + hoac khong, vi du: "+980", "+3,920", "980") -> lay so nguyen (bo dau + va dau phan cach nghin) va gan vao "winnings_amount" NHUNG GIU NGUYEN DAU DUONG (vi du: 980, 3920).
    * Neu cot "Tiền thắng" hien thi so am (co dau -, vi du: "-1,000", "-500") -> lay so nguyen (bo dau phan cach nghin) va gan vao "winnings_amount" NHUNG GIU NGUYEN DAU AM (vi du: -1000, -500).
    * Neu cot "Tiền thắng" hien thi "0" -> gan "winnings_amount" = 0.
- PHAN TICH MAU SAC cua TEXT trong cot "Tiền thắng":
    * Neu mau text gan voi mau DO (red, #FF0000, rgb(255,0,0), hoac mau tuong tu) -> gan "winnings_color" = "red".
    * Neu mau text gan voi mau XANH LA CAY (green, #00FF00, rgb(0,255,0), hoac mau tuong tu) -> gan "winnings_color" = "green".
    * Neu khong phai mau do hoac xanh la cay -> gan "winnings_color" = null.
- Doc NOI DUNG o COT THU 5 (cot ben phai cot "Tiền thắng") cua DONG DAU TIEN va gan vao khoa "column_5". 
    * Cot thu 5 thường chứa thông tin về "Đặt" và "Kết quả", ví dụ: "Đặt Tài, Kết quả Tài" hoặc "Đặt Xỉu, Kết quả Xỉu".
    * Neu co thong tin "Đặt" va "Kết quả", hay doc day du va gan vao "column_5" theo format: "Đặt <gia_tri>, Kết quả <gia_tri>" (vi du: "Đặt Tài, Kết quả Tài" hoac "Đặt Xỉu, Kết quả Xỉu").
    * Neu khong co thong tin "Đặt" va "Kết quả", hay doc toan bo noi dung cua cot thu 5 va gan vao "column_5".
- Lay so phien o cot "Phiên" (cot thu 1) cua DONG DAU TIEN lam gia tri cho khoa "Id" (bo ky tu "#" neu co).

Tra ve dung JSON: {"Id":"<ma phien>","bet_amount":<so tien>,"winnings_amount":<so tien thang/thua hoac null>,"winnings_color":<"red"|"green"|null>,"column_5":"<noi dung cot thu 5>"}.

CHI tra ve JSON thuan (khong giai thich, khong dung code block)."""

        betting_detail_prompt = """Phan tich anh man hinh BETTING da duoc crop va doc SO GIAY tu bo dem thoi gian:

- Ban la mo hinh doc hieu hinh anh (OCR) chuyen xac dinh bo dem thoi gian.
- Tim VONG TRON LON co VIEN VANG/CAM o CHINH GIUA man hinh (khong phai o tren, khong phai o duoi, khong phai o ben canh).
- Chi doc SO NAM TRONG VONG TRON nay thoi.
- So giay la SO NHO co 1-2 chu so (tu 1 den 60, vi du: 26, 39, 40, 38, 25, 10, 5).
- BO QUA TAT CA cac so lon hon 2 chu so (vi du: 31,608,201, 32,971,000, 33,232,000 - day la so tien, KHONG PHAI so giay).
- BO QUA cac so o banner tren cung, o banner duoi cung, o ben trai, o ben phai.
- BO QUA moi chu, bieu tuong, so phiên (#535825), so tien, so nguoi choi.
- CHI DOC SO TRONG VONG TRON O GIUA MAN HINH, khong doc so o vi tri khac.

Tra ve JSON: {"seconds":<so giay>}.

CHI tra ve JSON thuan (khong giai thich, khong dung code block)."""

        # Chuẩn bị crop regions trước
        history_crop_region = load_history_crop_region()
        betting_crop_region = load_betting_crop_region()
        actual_width, actual_height = image.size

        # Bước 1: Gửi nửa trên của ảnh cho ChatGPT CHỈ để phân loại
        # Crop nửa trên của ảnh để giảm kích thước và tăng tốc độ
        top_half_image = image.crop((0, 0, actual_width, actual_height // 2))
        
        img_byte_arr_original = io.BytesIO()
        top_half_image.save(img_byte_arr_original, format='JPEG', quality=95)
        img_byte_arr_original.seek(0)
        image_data_original = img_byte_arr_original.read()
        base64_image_original = base64.b64encode(image_data_original).decode('utf-8')
        openai_api_key = get_openai_api_key()

        # Prompt chỉ để phân loại (không đọc nội dung chi tiết)
        classification_prompt = """Phan tich anh giao dien game va xac dinh loai anh:

1. Neu co tieu de "LICH SU" hoac "LỊCH SỬ" -> tra ve {"image_type":"HISTORY"}

2. Neu co lua chon cuoc "TÀI" va "XỈU" hoac co dong ho dem nguoc -> tra ve {"image_type":"BETTING"}

3. Neu khong phai HISTORY, khong phai BETTING -> tra ve {"image_type":"UNKNOWN"}

CHI tra ve JSON thuan voi khoa "image_type" (khong giai thich, khong dung code block)."""

        # Helper function để gửi API call đọc chi tiết
        async def send_detail_analysis(prompt: str, cropped_img: Image.Image) -> tuple[str, dict]:
            """Gửi ảnh đã crop cho ChatGPT để đọc nội dung chi tiết"""
            img_byte_arr = io.BytesIO()
            cropped_img.save(img_byte_arr, format='JPEG', quality=85)  # Giảm quality để nhanh hơn
            img_byte_arr.seek(0)
            image_data = img_byte_arr.read()
            base64_image = base64.b64encode(image_data).decode('utf-8')
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {openai_api_key}",
                    },
                    json={
                        "model": "gpt-4o-mini",
                        "messages": [
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": prompt},
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:image/jpeg;base64,{base64_image}",
                                            "detail": "low",
                                        },
                                    },
                                ],
                            }
                        ],
                        "temperature": 0,
                        "max_tokens": 300 if "HISTORY" in prompt else 100,
                    },
                )

                if response.status_code != 200:
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"Lỗi ChatGPT: {response.text}",
                    )

                result = response.json()
                text = result["choices"][0]["message"]["content"]
                parsed = parse_json_payload(text)
                return text, parsed

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {openai_api_key}",
                },
                json={
                    "model": "gpt-4o-mini",
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": classification_prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{base64_image_original}",
                                        "detail": "low",
                                    },
                                },
                            ],
                        }
                    ],
                    "temperature": 0,
                    "max_tokens": 100,
                },
            )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Lá»—i ChatGPT: {response.text}",
                )

            result = response.json()
            classification_text = result["choices"][0]["message"]["content"]

        parsed_classification = parse_json_payload(classification_text)
        image_type_hint = str(parsed_classification.get("image_type") or "").upper()
        if not image_type_hint:
            if "TYPE: HISTORY" in classification_text.upper() or '"image_type":"HISTORY"' in classification_text.upper():
                image_type_hint = "HISTORY"
            elif "TYPE: GAME" in classification_text.upper() or "TYPE: BETTING" in classification_text.upper() or '"image_type":"GAME"' in classification_text.upper() or '"image_type":"BETTING"' in classification_text.upper():
                image_type_hint = "BETTING"
        # Normalize: "GAME" -> "BETTING" for consistency
        if image_type_hint == "GAME":
            image_type_hint = "BETTING"
        is_history = image_type_hint == "HISTORY"
        is_betting = image_type_hint == "BETTING"
        

        # Bước 2: Sau khi biết loại screenshot, crop theo template tương ứng và gửi API call ngay
        cropped_region_info = None
        cropped_image = image.copy()  # Ảnh đã crop để gửi cho ChatGPT đọc nội dung
        image_for_save = image.copy()  # Ảnh để lưu sau khi crop
        chatgpt_text = ""
        parsed_response = {}
        
        if is_history:
            # Crop theo HISTORY template nếu có
            if history_crop_region:
                sample_path = Path("samples/history_sample.jpg")
                if sample_path.exists():
                    sample_image = Image.open(sample_path)
                    sample_width, sample_height = sample_image.size
                    
                    scale_x = actual_width / sample_width
                    scale_y = actual_height / sample_height
                    
                    crop_x = int(history_crop_region["x"] * scale_x)
                    crop_y = int(history_crop_region["y"] * scale_y)
                    crop_width = int(history_crop_region["width"] * scale_x)
                    crop_height = int(history_crop_region["height"] * scale_y)
                    
                    crop_x = max(0, min(crop_x, actual_width - 1))
                    crop_y = max(0, min(crop_y, actual_height - 1))
                    crop_width = min(crop_width, actual_width - crop_x)
                    crop_height = min(crop_height, actual_height - crop_y)
                    
                    if crop_width > 0 and crop_height > 0:
                        cropped_image = cropped_image.crop((
                            crop_x, crop_y, 
                            crop_x + crop_width, crop_y + crop_height
                        ))
                        image_for_save = cropped_image.copy()
                        cropped_region_info = {
                            "x": crop_x, "y": crop_y,
                            "width": crop_width, "height": crop_height
                        }
            
            # Gửi ảnh đã crop cho ChatGPT để đọc nội dung chi tiết
            chatgpt_text, parsed_response = await send_detail_analysis(history_detail_prompt, cropped_image)
        
        elif is_betting:
            # Crop theo BETTING template nếu có
            if betting_crop_region:
                sample_path = Path("samples/betting_sample.jpg")
                if sample_path.exists():
                    sample_image = Image.open(sample_path)
                    sample_width, sample_height = sample_image.size
                    
                    scale_x = actual_width / sample_width
                    scale_y = actual_height / sample_height
                    
                    crop_x = int(betting_crop_region["x"] * scale_x)
                    crop_y = int(betting_crop_region["y"] * scale_y)
                    crop_width = int(betting_crop_region["width"] * scale_x)
                    crop_height = int(betting_crop_region["height"] * scale_y)
                    
                    crop_x = max(0, min(crop_x, actual_width - 1))
                    crop_y = max(0, min(crop_y, actual_height - 1))
                    crop_width = min(crop_width, actual_width - crop_x)
                    crop_height = min(crop_height, actual_height - crop_y)
                    
                    if crop_width > 0 and crop_height > 0:
                        cropped_image = cropped_image.crop((
                            crop_x, crop_y, 
                            crop_x + crop_width, crop_y + crop_height
                        ))
                        image_for_save = cropped_image.copy()
                        cropped_region_info = {
                            "x": crop_x, "y": crop_y,
                            "width": crop_width, "height": crop_height
                        }
            
            # Gửi ảnh đã crop cho ChatGPT để đọc nội dung chi tiết
            chatgpt_text, parsed_response = await send_detail_analysis(betting_detail_prompt, cropped_image)

        base_response_data = {
            "device_name": device_name,
            "betting_method": betting_method,
            "planned_bet_amount": None,
            "placed_bet_amount": None,
            "regions": {
                "seconds": seconds_region_coords,
                "bet_amount": bet_amount_region_coords,
            },
            "image_dimensions": {
                "actual_width": actual_image_width,
                "actual_height": actual_image_height,
                "screenshot_width": screenshot_width,
                "screenshot_height": screenshot_height,
                "simulator_width": simulator_width,
                "simulator_height": simulator_height,
            },
            "scaling": {
                "applied": needs_scaling,
                "scale_x": scale_x,
                "scale_y": scale_y,
            },
        }
        response_data: Optional[Dict[str, Any]] = None

        if is_history:
            session_id_raw = (
                parsed_response.get("Id")
                or parsed_response.get("id")
                or parsed_response.get("session_id")
            )
            session_id_clean = None
            if session_id_raw is not None:
                session_id_clean = str(session_id_raw).strip().lstrip("#") or None

            if not session_id_clean:
                session_match = re.search(r'"(?:Id|id)"\s*:\s*"?(#?\d+)"?', chatgpt_text)
                if session_match:
                    session_id_clean = session_match.group(1).lstrip("#")

            bet_amount_raw = parsed_response.get("bet_amount")
            bet_amount_value = parse_numeric_value(bet_amount_raw)
            if bet_amount_value is None:
                amount_match = re.search(r'"bet_amount"\s*:\s*"?([0-9.,]+)"?', chatgpt_text)
                if amount_match:
                    bet_amount_value = parse_numeric_value(amount_match.group(1))

            winnings_amount_raw = parsed_response.get("winnings_amount")
            win_loss_from_ai = parsed_response.get("win_loss")
            
            # Parse winnings_amount với hàm giữ dấu âm
            winnings_amount_value = parse_signed_numeric_value(winnings_amount_raw)
            
            # Fallback: nếu không parse được từ JSON, thử parse từ text response
            if winnings_amount_value is None and chatgpt_text:
                try:
                    # Tìm winnings_amount trong text response
                    winnings_match = re.search(r'"winnings_amount"\s*:\s*(-?\d+|null)', chatgpt_text)
                    if winnings_match:
                        winnings_str = winnings_match.group(1)
                        if winnings_str != "null":
                            winnings_amount_value = int(winnings_str)
                    # Nếu vẫn không có, thử tìm pattern khác
                    if winnings_amount_value is None:
                        # Tìm số âm/dương trong cột "Tiền thắng"
                        tien_thang_match = re.search(r'Tiền thắng.*?([+-]?\d{1,3}(?:,\d{3})*)', chatgpt_text, re.IGNORECASE)
                        if tien_thang_match:
                            winnings_str = tien_thang_match.group(1).replace(",", "")
                            winnings_amount_value = int(winnings_str)
                except Exception:
                    pass
            
            # Parse winnings_color từ ChatGPT response (cần parse trước để dùng cho logic win_loss)
            winnings_color = parsed_response.get("winnings_color")
            if winnings_color:
                winnings_color = str(winnings_color).lower()
                if winnings_color not in ["red", "green"]:
                    winnings_color = None
            else:
                # Fallback: tìm trong text response
                if '"winnings_color"\s*:\s*"red"' in chatgpt_text.lower():
                    winnings_color = "red"
                elif '"winnings_color"\s*:\s*"green"' in chatgpt_text.lower():
                    winnings_color = "green"
                else:
                    winnings_color = None

            # Parse column_5 từ ChatGPT response (cần parse trước để dùng cho logic win_loss)
            column_5 = parsed_response.get("column_5")
            if not column_5 and chatgpt_text:
                # Fallback: tìm trong text response
                column_5_match = re.search(r'"column_5"\s*:\s*"([^"]*)"', chatgpt_text)
                if column_5_match:
                    column_5 = column_5_match.group(1)
                else:
                    column_5 = None
            
            # Nếu column_5 là placeholder text "<noi dung cot thu 5>" thì set thành "unknown"
            if column_5 and isinstance(column_5, str):
                column_5_normalized = column_5.strip().lower()
                if column_5_normalized == "<noi dung cot thu 5>" or column_5_normalized == "<nội dung cột thứ 5>":
                    column_5 = "unknown"

            # Hàm helper để parse "Đặt" và "Kết quả" từ column_5
            def parse_dat_ket_qua(column_5_text: str) -> tuple:
                """Parse 'Đặt' và 'Kết quả' từ column_5. Trả về (dat_value, ket_qua_value) hoặc (None, None)"""
                if not column_5_text:
                    return None, None
                
                column_5_text = str(column_5_text).strip()
                # Tìm pattern: "Đặt <value>, Kết quả <value>" hoặc "Đặt Tài. Kết quả: Tài." hoặc tương tự
                # Có thể có nhiều format: "Đặt Tài, Kết quả Tài", "Đặt: Tài, Kết quả: Tài", "Đặt Tài. Kết quả: Tài.", etc.
                
                # Lấy giá trị sau "Đặt" cho đến khi gặp dấu phẩy, dấu chấm, hoặc "Kết quả"
                # Sử dụng non-greedy match để lấy giá trị ngắn nhất
                dat_match = re.search(r'Đặt\s*:?\s*([^,\.]+?)(?=[,\.]|\s*Kết quả|$)', column_5_text, re.IGNORECASE)
                
                # Lấy giá trị sau "Kết quả" cho đến khi gặp dấu phẩy, dấu chấm, hoặc hết chuỗi
                ket_qua_match = re.search(r'Kết quả\s*:?\s*([^,\.]+)', column_5_text, re.IGNORECASE)
                
                dat_value = dat_match.group(1).strip() if dat_match else None
                ket_qua_value = ket_qua_match.group(1).strip() if ket_qua_match else None
                
                # Loại bỏ dấu chấm và dấu phẩy ở cuối (nếu có)
                if dat_value:
                    dat_value = dat_value.rstrip('.,').strip()
                if ket_qua_value:
                    ket_qua_value = ket_qua_value.rstrip('.,').strip()
                
                return dat_value, ket_qua_value

            # Tính win_loss
            win_loss_token = None
            
            # Kiểm tra điều kiện đặc biệt: winnings_color = null, tien_thang = 0, bet_amount != 0 → unknown
            if (winnings_color is None and 
                (winnings_amount_value == 0 or winnings_amount_value is None) and 
                bet_amount_value is not None and bet_amount_value != 0):
                win_loss_token = "unknown"
            # Kiểm tra nếu "Tiền thắng" là "-" → unknown
            elif winnings_amount_raw is None or (isinstance(winnings_amount_raw, str) and winnings_amount_raw.strip() == "-"):
                if '"win_loss"\s*:\s*"unknown"' in chatgpt_text or re.search(r'Tiền thắng.*?[-]', chatgpt_text, re.IGNORECASE):
                    win_loss_token = "unknown"
            else:
                # Parse column_5 để kiểm tra điều kiện
                dat_value, ket_qua_value = parse_dat_ket_qua(column_5)
                has_column_5_format = dat_value is not None and ket_qua_value is not None
                
                # Kiểm tra điều kiện: bet_amount != 0, tien_thang != 0, winnings_color là red/green, column_5 có format đúng
                if (bet_amount_value is not None and bet_amount_value != 0 and
                    winnings_amount_value is not None and winnings_amount_value != 0 and
                    winnings_color in ["red", "green"] and
                    has_column_5_format):
                    # Ưu tiên: Set win_loss từ column_5
                    dat_normalized = dat_value.strip().lower()
                    ket_qua_normalized = ket_qua_value.strip().lower()
                    if dat_normalized == ket_qua_normalized:
                        win_loss_token = "win"
                    else:
                        win_loss_token = "loss"
                else:
                    # Không thỏa điều kiện, tính theo 4 cách như cũ
                    win_loss_methods = []
                    
                    # Cách 1: Dựa vào tien_thang
                    method1 = None
                    if winnings_amount_value is not None:
                        if winnings_amount_value > 0:
                            method1 = "win"
                        elif winnings_amount_value < 0:
                            method1 = "loss"
                    win_loss_methods.append(method1)
                    
                    # Cách 2: Dựa vào winnings_color
                    method2 = None
                    if winnings_color == "green":
                        method2 = "win"
                    elif winnings_color == "red":
                        method2 = "loss"
                    win_loss_methods.append(method2)
                    
                    # Cách 3: Dựa vào column_5 (so sánh "Đặt" và "Kết quả")
                    method3 = None
                    if has_column_5_format:
                        dat_normalized = dat_value.strip().lower()
                        ket_qua_normalized = ket_qua_value.strip().lower()
                        if dat_normalized == ket_qua_normalized:
                            method3 = "win"
                        else:
                            method3 = "loss"
                    win_loss_methods.append(method3)
                    
                    # Cách 4: Dựa vào giá trị tuyệt đối của winnings_amount và bet_amount
                    method4 = None
                    if winnings_amount_value is not None and bet_amount_value is not None:
                        abs_winnings = abs(winnings_amount_value)
                        abs_bet = abs(bet_amount_value)
                        if abs_winnings == abs_bet:
                            method4 = "loss"
                        else:
                            method4 = "win"
                    win_loss_methods.append(method4)
                    
                    # Tổng hợp kết quả: Nếu cả 4 cách đều ra cùng 1 kết quả → dùng kết quả đó
                    # Nếu ít nhất 1 cách ra kết quả khác → "unknown"
                    valid_methods = [m for m in win_loss_methods if m is not None]
                    if len(valid_methods) == 4:
                        # Có đủ 4 methods, kiểm tra xem có giống nhau không
                        if len(set(valid_methods)) == 1:
                            # Tất cả đều giống nhau → dùng kết quả đó
                            win_loss_token = valid_methods[0]
                        else:
                            # Có ít nhất 1 method khác → unknown
                            win_loss_token = "unknown"
                    else:
                        # Không có đủ 4 methods → không thể xác nhận → unknown
                        win_loss_token = "unknown"

            win_loss_label = win_label_from_token(win_loss_token)

            session_id_for_db = None
            if session_id_clean:
                session_id_for_db = session_id_clean
                if not session_id_for_db.startswith("#"):
                    session_id_for_db = f"#{session_id_for_db}"

            bet_amount_for_calc = bet_amount_value if bet_amount_value is not None else 0

            multiplier = mobile_betting_service.calculate_multiplier(
                device_name,
                win_loss_label,
                bet_amount_for_calc,
            )

            # Lưu ảnh crop nếu có và là HISTORY
            cropped_image_path = None
            if cropped_region_info and is_history and image_for_save:
                try:
                    # Lưu ảnh crop vào cùng thư mục với ảnh gốc
                    original_dir = Path(saved_path).parent
                    original_name = Path(saved_path).stem
                    cropped_image_path = original_dir / f"cropped_{original_name}.jpg"
                    image_for_save.save(cropped_image_path, format='JPEG', quality=95)
                    cropped_image_path = str(cropped_image_path)
                except Exception as exc:
                    print(f"Error saving cropped HISTORY image: {exc}")

            # win_loss đã được tính từ dữ liệu của record hiện tại ở trên (dòng 1654-1734)
            # Không copy bất kỳ dữ liệu nào từ record trước

            mobile_betting_service.save_analysis_history(
                {
                    "device_name": device_name,
                    "betting_method": betting_method,
                    "session_id": session_id_for_db,
                    "image_type": "HISTORY",
                    "seconds_remaining": None,
                    "bet_amount": bet_amount_value,
                    "actual_bet_amount": bet_amount_value,
                    "bet_status": None,
                    "win_loss": win_loss_label,
                    "multiplier": multiplier,
                    "image_path": saved_path,
                    "chatgpt_response": chatgpt_text,
                    "seconds_region_coords": seconds_region_coords,
                    "bet_region_coords": bet_amount_region_coords,
                }
            )

            response_data = {
                "Id": session_id_clean,
                "device_name": device_name,
                "betting_method": betting_method,
                "image_type": "HISTORY",
                "bet_amount": bet_amount_value,
                "tien_thang": winnings_amount_value,
                "winnings_amount": winnings_amount_value,  # Alias cho tương thích
                "winnings_color": winnings_color,  # "red" hoặc "green" hoặc null
                "win_loss": win_loss_token,
                "column_5": column_5,  # Nội dung cột thứ 5 (bên phải cột Tiền thắng)
            }
            

        elif is_betting:
            # Ưu tiên lấy seconds từ ChatGPT response
            seconds_from_ai = parse_numeric_value(parsed_response.get("seconds"))
            seconds_from_region = None
            seconds_coords = parse_region_coords(seconds_region_coords)
            if seconds_coords:
                seconds_from_region = extract_number_from_region(image, seconds_coords)

            # Ưu tiên giá trị từ ChatGPT, fallback sang OCR region, cuối cùng là 0
            seconds_value = (
                seconds_from_ai
                if seconds_from_ai is not None
                else (seconds_from_region if seconds_from_region is not None else 0)
            )

            # Lưu ảnh crop nếu có và là BETTING
            cropped_image_path = None
            if cropped_region_info and is_betting and image_for_save:
                try:
                    # Lưu ảnh crop vào cùng thư mục với ảnh gốc
                    original_dir = Path(saved_path).parent
                    original_name = Path(saved_path).stem
                    cropped_image_path = original_dir / f"cropped_{original_name}.jpg"
                    image_for_save.save(cropped_image_path, format='JPEG', quality=95)
                    cropped_image_path = str(cropped_image_path)
                except Exception as exc:
                    print(f"Error saving cropped BETTING image: {exc}")

            # Kiểm tra xem đã có tọa độ button đã lưu cho device này chưa
            saved_coords = mobile_betting_service.get_device_button_coords(device_name)
            should_match, match_counter = mobile_betting_service.should_match_buttons(device_name)
            
            # Hàm helper để tìm và tính tọa độ cho một loại button
            def find_button_coords(sample_path: Path, button_name: str):
                coords = None
                error = None
                
                if not sample_path.exists():
                    error = f"Thiếu ảnh mẫu {button_name}. Vui lòng upload ảnh {button_name} vào vùng drop trên dashboard."
                elif not device_real_width or not device_real_height:
                    missing_params = []
                    if not device_real_width:
                        missing_params.append("device_real_width")
                    if not device_real_height:
                        missing_params.append("device_real_height")
                    error = f"Thiếu tham số: {', '.join(missing_params)}. Client cần gửi kích thước màn hình mobile thật trong request."
                else:
                    try:
                        template_match_result = find_template_in_image(str(sample_path), image, threshold=0.5)
                        if template_match_result:
                            # Template matching trả về tọa độ điểm chính giữa trong không gian của image (actual_image_width x actual_image_height)
                            image_center_x = template_match_result["center_x"]
                            image_center_y = template_match_result["center_y"]
                            
                            # Scale trực tiếp từ image coordinates sang device coordinates
                            # Dùng actual_image_width/height (kích thước screenshot thực tế) và device_real_width/height (kích thước màn hình thật)
                            scale_to_device_x = device_real_width / actual_image_width if actual_image_width > 0 else 1.0
                            scale_to_device_y = device_real_height / actual_image_height if actual_image_height > 0 else 1.0
                            
                            device_x = int(image_center_x * scale_to_device_x)
                            device_y = int(image_center_y * scale_to_device_y)
                            
                            coords = {
                                "x": device_x,
                                "y": device_y,
                                "confidence": template_match_result.get("confidence", 0.0),
                                "template_match_x": image_center_x,  # Tọa độ template match gốc (image coordinates)
                                "template_match_y": image_center_y
                            }
                            print(f"Found {button_name} button at device coordinates: ({device_x}, {device_y}), template match: ({image_center_x}, {image_center_y}), confidence: {template_match_result.get('confidence', 0.0):.2f}")
                        else:
                            error = f"Không tìm thấy ảnh {button_name} trong screenshot BETTING. Template matching không khớp (confidence < 0.5). Kiểm tra lại ảnh mẫu {button_name} hoặc screenshot."
                    except Exception as exc:
                        error = f"Lỗi khi xử lý template matching cho {button_name}: {str(exc)}"
                        print(f"Error finding {button_name} template in BETTING image: {exc}")
                
                return coords, error
            
            # Nút Cược và 1K: LUÔN match mỗi lần
            print(f"[BETTING] Matching Nút Cược and 1K for device {device_name} (always match)")
            button_bet_coords, button_bet_error = find_button_coords(Path("samples/sample_bet_button.jpg"), "Nút Cược")
            button_1k_coords, button_1k_error = find_button_coords(Path("samples/sample_1k.jpg"), "1K")
            
            # 10K, 50K, Nút Đặt Cược: chỉ match khi đến lượt (mỗi 10 lần 1 lần)
            if saved_coords and not should_match:
                print(f"[BETTING] Using saved button coordinates for 10K/50K/PlaceBet (counter: {match_counter}, skip matching)")
                button_10k_coords = saved_coords.get('button_10k_coords')
                button_50k_coords = saved_coords.get('button_50k_coords')
                button_place_bet_coords = saved_coords.get('button_place_bet_coords')
                button_10k_error = None
                button_50k_error = None
                button_place_bet_error = None
                print(f"[BETTING] Loaded saved coordinates - 10K: {button_10k_coords}, 50K: {button_50k_coords}, PlaceBet: {button_place_bet_coords}")
            else:
                # Cần match 10K, 50K, Nút Đặt Cược: chưa có tọa độ hoặc đến lượt match (mỗi 10 lần 1 lần)
                print(f"[BETTING] Matching 10K/50K/PlaceBet button coordinates for device {device_name} (counter: {match_counter}, should_match: {should_match})")
                button_10k_coords, button_10k_error = find_button_coords(Path("samples/sample_10k.jpg"), "10K")
                button_50k_coords, button_50k_error = find_button_coords(Path("samples/sample_50k.jpg"), "50K")
                button_place_bet_coords, button_place_bet_error = find_button_coords(Path("samples/sample_place_bet_button.jpg"), "Nút Đặt Cược")
            
            # Lưu tọa độ vào database
            # Nếu đã match 10K/50K/PlaceBet lần này, lưu tất cả (bao gồm cả Nút Cược và 1K mới match)
            # Nếu skip match 10K/50K/PlaceBet, chỉ cần cập nhật Nút Cược và 1K mới match, giữ nguyên các button khác
            if saved_coords and not should_match:
                # Skip match: chỉ cập nhật Nút Cược và 1K, giữ nguyên các button khác từ saved_coords
                coords_to_save = {
                    'button_1k_coords': button_1k_coords,  # Luôn cập nhật 1K
                    'button_10k_coords': saved_coords.get('button_10k_coords'),
                    'button_50k_coords': saved_coords.get('button_50k_coords'),
                    'button_bet_coords': button_bet_coords,  # Luôn cập nhật Nút Cược
                    'button_place_bet_coords': saved_coords.get('button_place_bet_coords')
                }
            else:
                # Đã match: lưu tất cả các button đã match
                coords_to_save = {
                    'button_1k_coords': button_1k_coords,  # Luôn cập nhật 1K
                    'button_10k_coords': button_10k_coords,
                    'button_50k_coords': button_50k_coords,
                    'button_bet_coords': button_bet_coords,  # Luôn cập nhật Nút Cược
                    'button_place_bet_coords': button_place_bet_coords
                }
            
            # Chỉ lưu nếu có ít nhất 1 tọa độ
            if any(coords_to_save.values()):
                mobile_betting_service.save_device_button_coords(device_name, coords_to_save)
                print(f"[BETTING] Saved button coordinates for device {device_name} - 1K: {coords_to_save['button_1k_coords']}, 10K: {coords_to_save['button_10k_coords']}, 50K: {coords_to_save['button_50k_coords']}, Bet: {coords_to_save['button_bet_coords']}, PlaceBet: {coords_to_save['button_place_bet_coords']}")

            mobile_betting_service.save_analysis_history(
                {
                    "device_name": device_name,
                    "betting_method": betting_method,
                    "session_id": None,
                    "image_type": "BETTING",
                    "seconds_remaining": seconds_value,
                    "bet_amount": 0,
                    "actual_bet_amount": 0,
                    "bet_status": None,
                    "win_loss": None,
                    "multiplier": None,
                    "image_path": saved_path,
                    "chatgpt_response": chatgpt_text,
                    "seconds_region_coords": seconds_region_coords,
                    "bet_region_coords": bet_amount_region_coords,
                    "button_1k_coords": button_1k_coords,
                    "button_1k_error": button_1k_error,
                    "button_10k_coords": button_10k_coords,
                    "button_10k_error": button_10k_error,
                    "button_50k_coords": button_50k_coords,
                    "button_50k_error": button_50k_error,
                    "button_bet_coords": button_bet_coords,
                    "button_bet_error": button_bet_error,
                    "button_place_bet_coords": button_place_bet_coords,
                    "button_place_bet_error": button_place_bet_error,
                    "device_real_width": device_real_width,
                    "device_real_height": device_real_height,
                    "screenshot_width": screenshot_width,
                    "screenshot_height": screenshot_height,
                    "actual_image_width": actual_image_width,
                    "actual_image_height": actual_image_height,
                }
            )

            # Đảm bảo seconds luôn có trong JSON response cho client
            response_data = {
                "id": "",
                "Device name": device_name,
                "betting_method": betting_method,
                "image_type": "BETTING",
                "seconds": seconds_value,  # Giá trị giây đọc được từ ChatGPT hoặc OCR
            }
            
            
            # Thêm tọa độ các button nếu tìm được, hoặc thông báo lỗi nếu không tìm được
            if button_1k_coords:
                response_data["button_1k_coords"] = {
                    "x": button_1k_coords["x"],
                    "y": button_1k_coords["y"]
                }
            elif button_1k_error:
                response_data["button_1k_error"] = button_1k_error
            
            if button_10k_coords:
                response_data["button_10k_coords"] = {
                    "x": button_10k_coords["x"],
                    "y": button_10k_coords["y"]
                }
            elif button_10k_error:
                response_data["button_10k_error"] = button_10k_error
            
            if button_50k_coords:
                response_data["button_50k_coords"] = {
                    "x": button_50k_coords["x"],
                    "y": button_50k_coords["y"]
                }
            elif button_50k_error:
                response_data["button_50k_error"] = button_50k_error
            
            if button_bet_coords:
                response_data["button_bet_coords"] = {
                    "x": button_bet_coords["x"],
                    "y": button_bet_coords["y"]
                }
            elif button_bet_error:
                response_data["button_bet_error"] = button_bet_error
            
            if button_place_bet_coords:
                response_data["button_place_bet_coords"] = {
                    "x": button_place_bet_coords["x"],
                    "y": button_place_bet_coords["y"]
                }
            elif button_place_bet_error:
                response_data["button_place_bet_error"] = button_place_bet_error

        else:
            response_data = base_response_data.copy()
            mobile_betting_service.save_analysis_history(
                {
                    "device_name": device_name,
                    "betting_method": betting_method,
                    "session_id": None,
                    "image_type": "UNKNOWN",
                    "seconds_remaining": None,
                    "bet_amount": 0,
                    "actual_bet_amount": None,
                    "bet_status": None,
                    "win_loss": None,
                    "multiplier": None,
                    "image_path": saved_path,
                    "chatgpt_response": chatgpt_text,
                    "seconds_region_coords": seconds_region_coords,
                    "bet_region_coords": bet_amount_region_coords,
                }
            )

            response_data.update(
                {
                    "image_type": "UNKNOWN",
                    "multiplier": 0,
                    "note": "áº¢nh khÃ´ng pháº£i lÃ  popup lá»‹ch sá»­ cÆ°á»£c hoáº·c mÃ n hÃ¬nh Ä‘ang cÆ°á»£c",
                }
            )

        return response_data

    except HTTPException:
        raise
    except Exception as exc:
        import traceback

        print("[Mobile Analyze Error]", traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Lá»—i phÃ¢n tÃ­ch mobile: {exc}")


@app.get("/api/mobile/history")
async def get_mobile_history(limit: int = 50, page: int = 1):
    try:
        history, total_count = mobile_betting_service.get_analysis_history(limit=limit, page=page)
        total_pages = (total_count + limit - 1) // limit if limit > 0 else 1
        return {
            "success": True,
            "total": total_count,
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
            "history": history
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Lá»—i láº¥y lá»‹ch sá»­: {exc}")


@app.get("/api/mobile/history/image/{record_id}")
async def get_mobile_history_image(record_id: int, download: bool = Query(False)):
    try:
        conn = sqlite3.connect("logs.db")
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT image_path, button_1k_coords, button_10k_coords, button_50k_coords, 
                   button_bet_coords, button_place_bet_coords, image_type, 
                   device_real_width, device_real_height, screenshot_width, screenshot_height, 
                   actual_image_width, actual_image_height
            FROM mobile_analysis_history
            WHERE id = ?
            """,
            (record_id,),
        )
        row = cursor.fetchone()
        conn.close()

        if not row or not row[0]:
            raise HTTPException(status_code=404, detail="Không tìm thấy ảnh")

        image_path = row[0]
        button_1k_coords_json = row[1]
        button_10k_coords_json = row[2]
        button_50k_coords_json = row[3]
        button_bet_coords_json = row[4]
        button_place_bet_coords_json = row[5]
        image_type = row[6] if len(row) > 6 else None
        device_real_width = row[7] if len(row) > 7 else None
        device_real_height = row[8] if len(row) > 8 else None
        screenshot_width = row[9] if len(row) > 9 else None
        screenshot_height = row[10] if len(row) > 10 else None
        saved_actual_image_width = row[11] if len(row) > 11 else None
        saved_actual_image_height = row[12] if len(row) > 12 else None
        
        if not os.path.exists(image_path):
            raise HTTPException(status_code=404, detail=f"File ảnh không tồn tại: {image_path}")

        # Vẽ khung viền cho BETTING images khi có button coordinates
        if image_type == "BETTING":
            try:
                import json
                from PIL import ImageDraw
                
                # Load ảnh
                image = Image.open(image_path)
                current_image_width = image.width
                current_image_height = image.height
                
                # Dùng kích thước đã lưu hoặc kích thước hiện tại
                actual_image_width = saved_actual_image_width if saved_actual_image_width else current_image_width
                actual_image_height = saved_actual_image_height if saved_actual_image_height else current_image_height
                
                # Convert image sang RGBA để hỗ trợ alpha composite
                image_rgba = image.convert("RGBA")
                draw = ImageDraw.Draw(image_rgba)
                box_size = 100  # Kích thước khung viền
                
                # Tạo overlay để vẽ background transparent
                overlay = Image.new("RGBA", image_rgba.size, (0, 0, 0, 0))
                overlay_draw = ImageDraw.Draw(overlay)
                
                # Hàm helper để vẽ khung viền cho một button
                def draw_button_box(coords_json, color, label, is_template_match=False):
                    if not coords_json:
                        return
                    try:
                        coords = json.loads(coords_json) if isinstance(coords_json, str) else coords_json
                        if coords and isinstance(coords, dict):
                            if is_template_match:
                                # Vẽ khung tại vị trí template match (image coordinates gốc)
                                if "template_match_x" in coords and "template_match_y" in coords:
                                    image_x = coords.get("template_match_x", 0)
                                    image_y = coords.get("template_match_y", 0)
                                else:
                                    return  # Không có template match coordinates
                            else:
                                # Vẽ khung tại vị trí device coordinates (sau khi scale)
                                if "x" not in coords or "y" not in coords:
                                    return
                                device_x = coords.get("x", 0)
                                device_y = coords.get("y", 0)
                                
                                # Scale từ device coordinates về image coordinates
                                if device_real_width and device_real_height and actual_image_width and actual_image_height:
                                    image_x = int(device_x * (actual_image_width / device_real_width)) if device_real_width > 0 else device_x
                                    image_y = int(device_y * (actual_image_height / device_real_height)) if device_real_height > 0 else device_y
                                else:
                                    image_x = device_x
                                    image_y = device_y
                            
                            # Vẽ khung viền
                            box_x1 = max(0, image_x - box_size // 2)
                            box_y1 = max(0, image_y - box_size // 2)
                            box_x2 = min(actual_image_width, image_x + box_size // 2)
                            box_y2 = min(actual_image_height, image_y + box_size // 2)
                            
                            if is_template_match:
                                # Vẽ khung template match với background transparent (màu nhạt hơn)
                                from PIL import ImageColor
                                try:
                                    rgb_color = ImageColor.getcolor(color, "RGB")
                                    # Tạo màu nhạt hơn với alpha (transparent background 75%)
                                    fill_color = (*rgb_color, 64)  # Alpha = 64 (transparent 75%, opacity 25%)
                                    outline_color = color
                                except:
                                    fill_color = None
                                    outline_color = color
                                
                                # Vẽ background transparent trên overlay
                                if fill_color:
                                    overlay_draw.rectangle([box_x1, box_y1, box_x2, box_y2], fill=fill_color)
                                
                                # Vẽ viền khung template match (nét đứt để phân biệt)
                                dash_length = 5
                                gap_length = 3
                                # Vẽ đường trên
                                x = box_x1
                                while x < box_x2:
                                    overlay_draw.line([(x, box_y1), (min(x + dash_length, box_x2), box_y1)], fill=outline_color, width=2)
                                    x += dash_length + gap_length
                                # Vẽ đường dưới
                                x = box_x1
                                while x < box_x2:
                                    overlay_draw.line([(x, box_y2), (min(x + dash_length, box_x2), box_y2)], fill=outline_color, width=2)
                                    x += dash_length + gap_length
                                # Vẽ đường trái
                                y = box_y1
                                while y < box_y2:
                                    overlay_draw.line([(box_x1, y), (box_x1, min(y + dash_length, box_y2))], fill=outline_color, width=2)
                                    y += dash_length + gap_length
                                # Vẽ đường phải
                                y = box_y1
                                while y < box_y2:
                                    overlay_draw.line([(box_x2, y), (box_x2, min(y + dash_length, box_y2))], fill=outline_color, width=2)
                                    y += dash_length + gap_length
                                
                                # Vẽ label với prefix "TM:" trên overlay
                                overlay_draw.text((box_x1, box_y1 - 15), f"TM:{label}", fill=outline_color)
                            else:
                                # Vẽ khung device coordinates (nét liền) trên image chính
                                for i in range(3):
                                    draw.rectangle([box_x1 - i, box_y1 - i, box_x2 + i, box_y2 + i], outline=color, width=1)
                                
                                # Vẽ label trên image chính
                                draw.text((box_x1, box_y1 - 15), label, fill=color)
                    except Exception as e:
                        print(f"Error drawing {label} button box: {e}")
                
                # Vẽ khung template match trước (nét đứt, background transparent)
                draw_button_box(button_1k_coords_json, "red", "1K", is_template_match=True)
                draw_button_box(button_10k_coords_json, "blue", "10K", is_template_match=True)
                draw_button_box(button_50k_coords_json, "green", "50K", is_template_match=True)
                draw_button_box(button_bet_coords_json, "orange", "Bet", is_template_match=True)
                draw_button_box(button_place_bet_coords_json, "purple", "PlaceBet", is_template_match=True)
                
                # Composite overlay lên image
                image_rgba = Image.alpha_composite(image_rgba, overlay)
                
                # Vẽ khung viền cho các button với màu khác nhau (device coordinates - nét liền)
                draw = ImageDraw.Draw(image_rgba)  # Cập nhật draw sau khi composite
                draw_button_box(button_1k_coords_json, "red", "1K", is_template_match=False)
                draw_button_box(button_10k_coords_json, "blue", "10K", is_template_match=False)
                draw_button_box(button_50k_coords_json, "green", "50K", is_template_match=False)
                draw_button_box(button_bet_coords_json, "orange", "Bet", is_template_match=False)
                draw_button_box(button_place_bet_coords_json, "purple", "PlaceBet", is_template_match=False)
                
                # Convert về RGB để lưu JPEG
                image = image_rgba.convert("RGB")
                
                # Lưu ảnh tạm vào BytesIO
                import io
                output = io.BytesIO()
                image.save(output, format='JPEG', quality=95)
                output.seek(0)
                
                extension = os.path.splitext(image_path)[1].lower()
                media_type = {
                    ".jpg": "image/jpeg",
                    ".jpeg": "image/jpeg",
                    ".png": "image/png",
                    ".gif": "image/gif",
                    ".webp": "image/webp",
                }.get(extension, "image/jpeg")
                
                filename = os.path.basename(image_path) if download else None
                return Response(content=output.read(), media_type=media_type, headers={"Content-Disposition": f'attachment; filename="{filename}"'} if filename else {})
            except Exception as e:
                print(f"Error drawing button boxes: {e}")
                # Fallback: trả về ảnh gốc nếu có lỗi

        extension = os.path.splitext(image_path)[1].lower()
        media_type = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp",
        }.get(extension, "image/jpeg")

        filename = os.path.basename(image_path) if download else None
        return FileResponse(image_path, media_type=media_type, filename=filename)

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Lỗi lấy ảnh: {exc}")


@app.get("/api/mobile/history/image-info/{record_id}")
async def get_mobile_history_image_info(record_id: int):
    """Lấy thông tin kích thước screenshot và device"""
    try:
        conn = sqlite3.connect("logs.db")
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT actual_image_width, actual_image_height, device_real_width, device_real_height
            FROM mobile_analysis_history
            WHERE id = ?
            """,
            (record_id,),
        )
        row = cursor.fetchone()
        conn.close()

        if not row:
            raise HTTPException(status_code=404, detail="Không tìm thấy record")

        return {
            "actual_image_width": row[0],
            "actual_image_height": row[1],
            "device_real_width": row[2],
            "device_real_height": row[3],
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Lỗi lấy thông tin ảnh: {exc}")


@app.get("/api/mobile/history/cropped-image/{record_id}")
async def get_mobile_history_cropped_image(record_id: int, download: bool = Query(False)):
    try:
        conn = sqlite3.connect("logs.db")
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT image_path, image_type
            FROM mobile_analysis_history
            WHERE id = ?
            """,
            (record_id,),
        )
        row = cursor.fetchone()
        conn.close()

        if not row or not row[0]:
            raise HTTPException(status_code=404, detail="Không tìm thấy ảnh")

        image_path = row[0]
        image_type = row[1] if len(row) > 1 else None
        
        if not os.path.exists(image_path):
            raise HTTPException(status_code=404, detail=f"File ảnh không tồn tại: {image_path}")

        # Kiểm tra xem có file cropped đã lưu không
        original_dir = Path(image_path).parent
        original_name = Path(image_path).stem
        cropped_image_path = original_dir / f"cropped_{original_name}.jpg"
        
        if cropped_image_path.exists():
            # Trả về ảnh crop đã lưu
            extension = os.path.splitext(str(cropped_image_path))[1].lower()
            media_type = {
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".png": "image/png",
                ".gif": "image/gif",
                ".webp": "image/webp",
            }.get(extension, "image/jpeg")
            
            filename = f"cropped_{os.path.basename(image_path)}" if download else None
            return FileResponse(str(cropped_image_path), media_type=media_type, filename=filename)
        
        # Nếu không có file crop đã lưu, trả về ảnh gốc
        extension = os.path.splitext(image_path)[1].lower()
        media_type = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp",
        }.get(extension, "image/jpeg")
        
        filename = os.path.basename(image_path) if download else None
        return FileResponse(image_path, media_type=media_type, filename=filename)

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Lỗi lấy ảnh crop: {exc}")


def find_template_in_image(template_path: str, target_image: Image.Image, threshold: float = 0.4) -> Optional[Dict[str, int]]:
    """
    Tìm vùng ảnh template trong target image sử dụng template matching với multi-scale và nhiều phương pháp.
    Trả về dict với keys: x, y, width, height, center_x, center_y, confidence
    """
    try:
        if not Path(template_path).exists():
            return None
        
        # Load template image
        template = cv2.imread(template_path)
        if template is None:
            return None
        
        # Convert PIL Image to OpenCV format
        target_array = np.array(target_image)
        if len(target_array.shape) == 2:  # Grayscale
            target_cv = cv2.cvtColor(target_array, cv2.COLOR_GRAY2BGR)
        elif target_array.shape[2] == 4:  # RGBA
            target_cv = cv2.cvtColor(target_array, cv2.COLOR_RGBA2BGR)
        else:  # RGB
            target_cv = cv2.cvtColor(target_array, cv2.COLOR_RGB2BGR)
        
        # Preprocessing để tăng độ chính xác
        # 1. Convert sang grayscale để giảm nhiễu màu
        template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
        target_gray = cv2.cvtColor(target_cv, cv2.COLOR_BGR2GRAY)
        
        # 2. Tăng contrast để làm nổi bật đặc điểm
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        template_gray = clahe.apply(template_gray)
        target_gray = clahe.apply(target_gray)
        
        # 3. Gaussian blur nhẹ để giảm noise
        template_gray = cv2.GaussianBlur(template_gray, (3, 3), 0)
        target_gray = cv2.GaussianBlur(target_gray, (3, 3), 0)
        
        template_height, template_width = template_gray.shape[:2]
        target_height, target_width = target_gray.shape[:2]
        
        # Nếu template lớn hơn target, không thể match
        if template_width > target_width or template_height > target_height:
            return None
        
        best_match = None
        best_confidence = 0.0
        best_method = None
        
        # Thử nhiều phương pháp template matching
        methods = [
            ('TM_CCOEFF_NORMED', cv2.TM_CCOEFF_NORMED),
            ('TM_CCORR_NORMED', cv2.TM_CCORR_NORMED),
            ('TM_SQDIFF_NORMED', cv2.TM_SQDIFF_NORMED),
        ]
        
        # Thử multi-scale: scale template từ 0.5x đến 1.5x với bước nhỏ hơn để chính xác hơn
        scales = [0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 1.0, 1.05, 1.1, 1.15, 1.2, 1.25, 1.3, 1.35, 1.4, 1.45, 1.5]
        
        for scale in scales:
            # Resize template
            scaled_width = int(template_width * scale)
            scaled_height = int(template_height * scale)
            
            if scaled_width > target_width or scaled_height > target_height:
                continue
            
            scaled_template = cv2.resize(template_gray, (scaled_width, scaled_height), interpolation=cv2.INTER_AREA)
            
            # Thử từng phương pháp matching (sử dụng grayscale đã preprocessing)
            for method_name, method in methods:
                try:
                    result = cv2.matchTemplate(target_gray, scaled_template, method)
                    
                    if method == cv2.TM_SQDIFF_NORMED:
                        # Với SQDIFF, giá trị nhỏ hơn = tốt hơn
                        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                        confidence = 1.0 - min_val
                        match_loc = min_loc
                    else:
                        # Với các method khác, giá trị lớn hơn = tốt hơn
                        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                        confidence = max_val
                        match_loc = max_loc
                    
                    # Lưu match tốt nhất
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_match = {
                            "x": match_loc[0],
                            "y": match_loc[1],
                            "width": scaled_width,
                            "height": scaled_height,
                            "center_x": match_loc[0] + scaled_width // 2,
                            "center_y": match_loc[1] + scaled_height // 2,
                            "confidence": float(confidence),
                            "scale": scale,
                            "method": method_name
                        }
                except Exception as e:
                    continue
        
        # Kiểm tra threshold và validation
        if best_match and best_confidence >= threshold:
            # Validation: Kiểm tra kích thước hợp lý (không quá nhỏ hoặc quá lớn)
            scale_ratio = best_match.get('scale', 1.0)
            if scale_ratio < 0.5 or scale_ratio > 1.5:
                print(f"Template matching rejected: scale ratio {scale_ratio:.2f} out of valid range")
                return None
            
            # Validation: Kiểm tra vị trí hợp lý (không nằm ngoài ảnh)
            if (best_match["x"] < 0 or best_match["y"] < 0 or 
                best_match["x"] + best_match["width"] > target_width or
                best_match["y"] + best_match["height"] > target_height):
                print(f"Template matching rejected: coordinates out of bounds")
                return None
            
            print(f"Template matching success: confidence={best_confidence:.3f}, scale={best_match.get('scale', 1.0)}, method={best_match.get('method', 'unknown')}")
            return best_match
        else:
            if best_match:
                print(f"Template matching failed: best confidence={best_confidence:.3f} < threshold={threshold}")
            return None
            
    except Exception as exc:
        print(f"Error in template matching: {exc}")
        import traceback
        traceback.print_exc()
        return None


def load_betting_crop_region() -> Optional[Dict[str, int]]:
    """Load betting crop region from config file"""
    try:
        crop_config_path = Path("samples/betting_crop_region.json")
        if crop_config_path.exists():
            with open(crop_config_path, "r") as f:
                return json.load(f)
        return None
    except Exception as exc:
        print(f"Error loading crop region: {exc}")
        return None


def load_history_crop_region() -> Optional[Dict[str, int]]:
    """Load history crop region from config file"""
    try:
        crop_config_path = Path("samples/history_crop_region.json")
        if crop_config_path.exists():
            with open(crop_config_path, "r") as f:
                return json.load(f)
        return None
    except Exception as exc:
        print(f"Error loading history crop region: {exc}")
        return None


def detect_green_crop_region(image_path: str) -> Optional[Dict[str, int]]:
    """Detect green region (#1AFF0D) in image and return bounding box"""
    try:
        image = Image.open(image_path)
        img_array = np.array(image)
        
        # Convert to RGB if needed
        if len(img_array.shape) == 2:
            return None
        if img_array.shape[2] == 4:  # RGBA
            img_array = img_array[:, :, :3]
        
        # Color #1AFF0D = RGB(26, 255, 13)
        # Allow some tolerance for color matching
        green_color = np.array([26, 255, 13])
        tolerance = 10
        
        # Find pixels matching green color
        lower_bound = green_color - tolerance
        upper_bound = green_color + tolerance
        lower_bound = np.clip(lower_bound, 0, 255)
        upper_bound = np.clip(upper_bound, 0, 255)
        
        mask = np.all((img_array >= lower_bound) & (img_array <= upper_bound), axis=2)
        
        if not np.any(mask):
            return None
        
        # Find bounding box
        rows = np.any(mask, axis=1)
        cols = np.any(mask, axis=0)
        
        if not np.any(rows) or not np.any(cols):
            return None
        
        y_min, y_max = np.where(rows)[0][[0, -1]]
        x_min, x_max = np.where(cols)[0][[0, -1]]
        
        return {
            "x": int(x_min),
            "y": int(y_min),
            "width": int(x_max - x_min + 1),
            "height": int(y_max - y_min + 1)
        }
    except Exception as exc:
        print(f"Error detecting green region: {exc}")
        return None


@app.post("/api/mobile/betting-sample/upload")
async def upload_betting_sample(file: UploadFile = File(...)):
    """Upload or replace BETTING sample image and detect crop region"""
    try:
        # Create samples directory if not exists
        samples_dir = Path("samples")
        samples_dir.mkdir(exist_ok=True)
        
        # Save as betting_sample.jpg (replace if exists)
        sample_path = samples_dir / "betting_sample.jpg"
        
        # Read and save image
        image_data = await file.read()
        with open(sample_path, "wb") as f:
            f.write(image_data)
        
        # Detect green crop region (#1AFF0D)
        crop_region = detect_green_crop_region(str(sample_path))
        
        # Save crop region to JSON file
        crop_config_path = samples_dir / "betting_crop_region.json"
        if crop_region:
            with open(crop_config_path, "w") as f:
                json.dump(crop_region, f)
        else:
            # Remove config if no region detected
            if crop_config_path.exists():
                crop_config_path.unlink()
        
        return {
            "success": True,
            "message": "Betting sample image uploaded successfully",
            "path": str(sample_path),
            "crop_region": crop_region
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error uploading sample: {exc}")


@app.post("/api/mobile/history-sample/upload")
async def upload_history_sample(file: UploadFile = File(...)):
    """Upload or replace HISTORY sample image and detect crop region"""
    try:
        # Create samples directory if not exists
        samples_dir = Path("samples")
        samples_dir.mkdir(exist_ok=True)
        
        # Save as history_sample.jpg (replace if exists)
        sample_path = samples_dir / "history_sample.jpg"
        
        # Read and save image
        image_data = await file.read()
        with open(sample_path, "wb") as f:
            f.write(image_data)
        
        # Detect green crop region (#1AFF0D)
        crop_region = detect_green_crop_region(str(sample_path))
        
        # Save crop region to JSON file
        crop_config_path = samples_dir / "history_crop_region.json"
        if crop_region:
            with open(crop_config_path, "w") as f:
                json.dump(crop_region, f)
        else:
            # Remove config if no region detected
            if crop_config_path.exists():
                crop_config_path.unlink()
        
        return {
            "success": True,
            "message": "History sample image uploaded successfully",
            "path": str(sample_path),
            "crop_region": crop_region
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error uploading sample: {exc}")


@app.get("/api/mobile/history-sample")
async def get_history_sample():
    """Get HISTORY sample image"""
    try:
        sample_path = Path("samples/history_sample.jpg")
        if not sample_path.exists():
            raise HTTPException(status_code=404, detail="History sample image not found")
        
        return FileResponse(sample_path, media_type="image/jpeg")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error getting sample: {exc}")


@app.get("/api/mobile/history/betting-cropped/{record_id}")
async def get_betting_cropped_image(record_id: int, download: bool = Query(False)):
    """Get cropped BETTING image from screenshot"""
    try:
        conn = sqlite3.connect("logs.db")
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT image_path, image_type
            FROM mobile_analysis_history
            WHERE id = ?
            """,
            (record_id,),
        )
        row = cursor.fetchone()
        conn.close()

        if not row or not row[0]:
            raise HTTPException(status_code=404, detail="Không tìm thấy ảnh")

        image_path = row[0]
        image_type = row[1] if len(row) > 1 else None
        
        if image_type != "BETTING":
            raise HTTPException(status_code=400, detail="Chỉ hỗ trợ BETTING image type")

        if not os.path.exists(image_path):
            raise HTTPException(status_code=404, detail=f"File ảnh không tồn tại: {image_path}")

        # Tìm ảnh crop (cropped_{original_name}.jpg)
        original_dir = Path(image_path).parent
        original_name = Path(image_path).stem
        cropped_image_path = original_dir / f"cropped_{original_name}.jpg"
        
        if not cropped_image_path.exists():
            raise HTTPException(status_code=404, detail="Ảnh crop không tồn tại")

        extension = os.path.splitext(str(cropped_image_path))[1].lower()
        media_type = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp",
        }.get(extension, "image/jpeg")
        
        filename = f"betting_cropped_{record_id}.jpg" if download else None
        return FileResponse(str(cropped_image_path), media_type=media_type, filename=filename)

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Lỗi lấy ảnh crop: {exc}")


@app.get("/api/mobile/betting-sample")
async def get_betting_sample():
    """Get BETTING sample image"""
    try:
        sample_path = Path("samples/betting_sample.jpg")
        if not sample_path.exists():
            raise HTTPException(status_code=404, detail="Betting sample image not found")
        
        return FileResponse(sample_path, media_type="image/jpeg")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error getting sample: {exc}")


@app.post("/api/mobile/sample-1k/upload")
async def upload_sample_1k(file: UploadFile = File(...)):
    """Upload or replace 1K sample image"""
    try:
        samples_dir = Path("samples")
        samples_dir.mkdir(exist_ok=True)
        
        sample_path = samples_dir / "sample_1k.jpg"
        
        # Xóa file cũ nếu tồn tại để đảm bảo replace
        if sample_path.exists():
            sample_path.unlink()
        
        image_data = await file.read()
        with open(sample_path, "wb") as f:
            f.write(image_data)
            f.flush()
        
        return {
            "success": True,
            "message": "1K sample image uploaded successfully",
            "path": str(sample_path)
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error uploading sample: {exc}")


@app.post("/api/mobile/sample-10k/upload")
async def upload_sample_10k(file: UploadFile = File(...)):
    """Upload or replace 10K sample image"""
    try:
        samples_dir = Path("samples")
        samples_dir.mkdir(exist_ok=True)
        
        sample_path = samples_dir / "sample_10k.jpg"
        
        # Xóa file cũ nếu tồn tại để đảm bảo replace
        if sample_path.exists():
            sample_path.unlink()
        
        image_data = await file.read()
        with open(sample_path, "wb") as f:
            f.write(image_data)
            f.flush()
        
        return {
            "success": True,
            "message": "10K sample image uploaded successfully",
            "path": str(sample_path)
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error uploading sample: {exc}")


@app.post("/api/mobile/sample-bet-button/upload")
async def upload_sample_bet_button(file: UploadFile = File(...)):
    """Upload or replace Nút Cược sample image"""
    try:
        samples_dir = Path("samples")
        samples_dir.mkdir(exist_ok=True)
        
        sample_path = samples_dir / "sample_bet_button.jpg"
        
        # Xóa file cũ nếu tồn tại để đảm bảo replace
        if sample_path.exists():
            sample_path.unlink()
        
        image_data = await file.read()
        with open(sample_path, "wb") as f:
            f.write(image_data)
            f.flush()
        
        return {
            "success": True,
            "message": "Nút Cược sample image uploaded successfully",
            "path": str(sample_path)
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error uploading sample: {exc}")


@app.post("/api/mobile/sample-place-bet-button/upload")
async def upload_sample_place_bet_button(file: UploadFile = File(...)):
    """Upload or replace Nút Đặt Cược sample image"""
    try:
        samples_dir = Path("samples")
        samples_dir.mkdir(exist_ok=True)
        
        sample_path = samples_dir / "sample_place_bet_button.jpg"
        
        # Xóa file cũ nếu tồn tại để đảm bảo replace
        if sample_path.exists():
            sample_path.unlink()
        
        image_data = await file.read()
        with open(sample_path, "wb") as f:
            f.write(image_data)
            f.flush()
        
        return {
            "success": True,
            "message": "Nút Đặt Cược sample image uploaded successfully",
            "path": str(sample_path)
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error uploading sample: {exc}")


@app.post("/api/mobile/sample-50k/upload")
async def upload_sample_50k(file: UploadFile = File(...)):
    """Upload or replace 50K sample image"""
    try:
        samples_dir = Path("samples")
        samples_dir.mkdir(exist_ok=True)
        
        sample_path = samples_dir / "sample_50k.jpg"
        
        # Xóa file cũ nếu tồn tại để đảm bảo replace
        if sample_path.exists():
            sample_path.unlink()
        
        image_data = await file.read()
        with open(sample_path, "wb") as f:
            f.write(image_data)
            f.flush()
        
        return {
            "success": True,
            "message": "50K sample image uploaded successfully",
            "path": str(sample_path)
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error uploading sample: {exc}")


@app.get("/api/mobile/sample-1k")
async def get_sample_1k():
    """Get 1K sample image"""
    try:
        sample_path = Path("samples/sample_1k.jpg")
        if not sample_path.exists():
            raise HTTPException(status_code=404, detail="1K sample image not found")
        
        return FileResponse(sample_path, media_type="image/jpeg")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error getting sample: {exc}")


@app.get("/api/mobile/sample-10k")
async def get_sample_10k():
    """Get 10K sample image"""
    try:
        sample_path = Path("samples/sample_10k.jpg")
        if not sample_path.exists():
            raise HTTPException(status_code=404, detail="10K sample image not found")
        
        return FileResponse(sample_path, media_type="image/jpeg")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error getting sample: {exc}")


@app.get("/api/mobile/sample-50k")
async def get_sample_50k():
    """Get 50K sample image"""
    try:
        sample_path = Path("samples/sample_50k.jpg")
        if not sample_path.exists():
            raise HTTPException(status_code=404, detail="50K sample image not found")
        
        return FileResponse(sample_path, media_type="image/jpeg")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error getting sample: {exc}")


@app.get("/api/mobile/sample-bet-button")
async def get_sample_bet_button():
    """Get Nút Cược sample image"""
    try:
        sample_path = Path("samples/sample_bet_button.jpg")
        if not sample_path.exists():
            raise HTTPException(status_code=404, detail="Nút Cược sample image not found")
        
        return FileResponse(sample_path, media_type="image/jpeg")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error getting sample: {exc}")


@app.get("/api/mobile/sample-place-bet-button")
async def get_sample_place_bet_button():
    """Get Nút Đặt Cược sample image"""
    try:
        sample_path = Path("samples/sample_place_bet_button.jpg")
        if not sample_path.exists():
            raise HTTPException(status_code=404, detail="Nút Đặt Cược sample image not found")
        
        return FileResponse(sample_path, media_type="image/jpeg")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error getting sample: {exc}")


@app.get("/api/mobile/history/json/{record_id}")
async def download_mobile_history_json(record_id: int):
    try:
        conn = sqlite3.connect("logs.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM mobile_analysis_history WHERE id = ?",
            (record_id,),
        )
        row = cursor.fetchone()
        conn.close()

        if not row:
            raise HTTPException(status_code=404, detail="KhÃ´ng tÃ¬m tháº¥y dá»¯ liá»‡u")

        record = dict(row)
        base_payload: Dict[str, Any] = {
            "id": record.get("id"),
            "device_name": record.get("device_name"),
            "betting_method": record.get("betting_method"),
            "image_type": record.get("image_type"),
        }

        image_type = record.get("image_type")

        if image_type == "BETTING":
            # Helper function để parse coords từ JSON string
            def parse_coords(coords_str):
                if coords_str:
                    try:
                        return json.loads(coords_str)
                    except Exception:
                        pass
                return None
            
            payload: Dict[str, Any] = {
                **base_payload,
                "seconds": record.get("seconds_remaining"),
            }
            
            # Parse và thêm tọa độ các button nếu có
            button_1k_coords = parse_coords(record.get("button_1k_coords"))
            if button_1k_coords:
                payload["button_1k_coords"] = button_1k_coords
            elif record.get("button_1k_error"):
                payload["button_1k_error"] = record.get("button_1k_error")
            
            button_10k_coords = parse_coords(record.get("button_10k_coords"))
            if button_10k_coords:
                payload["button_10k_coords"] = button_10k_coords
            elif record.get("button_10k_error"):
                payload["button_10k_error"] = record.get("button_10k_error")
            
            button_50k_coords = parse_coords(record.get("button_50k_coords"))
            if button_50k_coords:
                payload["button_50k_coords"] = button_50k_coords
            elif record.get("button_50k_error"):
                payload["button_50k_error"] = record.get("button_50k_error")
            
            button_bet_coords = parse_coords(record.get("button_bet_coords"))
            if button_bet_coords:
                payload["button_bet_coords"] = button_bet_coords
            elif record.get("button_bet_error"):
                payload["button_bet_error"] = record.get("button_bet_error")
            
            button_place_bet_coords = parse_coords(record.get("button_place_bet_coords"))
            if button_place_bet_coords:
                payload["button_place_bet_coords"] = button_place_bet_coords
            elif record.get("button_place_bet_error"):
                payload["button_place_bet_error"] = record.get("button_place_bet_error")
        elif image_type == "HISTORY":
            # Parse các giá trị từ chatgpt_response nếu có
            tien_thang_value = None
            winnings_color_value = None
            column_5_value = None
            return_value = None
            win_loss_value = None
            chatgpt_response = record.get("chatgpt_response")
            
            if chatgpt_response:
                try:
                    # Parse JSON từ chatgpt_response nếu có
                    def parse_json_payload(raw_text: str) -> Dict[str, Any]:
                        if not raw_text:
                            return {}
                        cleaned = raw_text.strip()
                        start = cleaned.find('{')
                        end = cleaned.rfind('}')
                        if start != -1 and end != -1 and end >= start:
                            cleaned = cleaned[start : end + 1]
                        try:
                            return json.loads(cleaned)
                        except json.JSONDecodeError:
                            return {}
                        except Exception:
                            return {}
                    
                    parsed = parse_json_payload(chatgpt_response)
                    
                    # Pattern 1: Tìm winnings_amount trong JSON response (nhiều format)
                    patterns = [
                        r'"winnings_amount"\s*:\s*(-?\d+|null)',
                        r'"winnings_amount"\s*:\s*"?(-?\d+(?:,\d{3})*)"?',
                        r'winnings_amount["\s]*:[\s]*(-?\d+)',
                        r'"Tiền thắng"\s*:\s*(-?\d+|null)',
                    ]
                    for pattern in patterns:
                        winnings_match = re.search(pattern, chatgpt_response, re.IGNORECASE)
                        if winnings_match:
                            winnings_str = winnings_match.group(1)
                            if winnings_str and winnings_str.lower() != "null":
                                winnings_str = winnings_str.replace(",", "").replace("+", "")
                                if winnings_str.startswith("-"):
                                    tien_thang_value = -int(winnings_str[1:])
                                else:
                                    tien_thang_value = int(winnings_str)
                                break
                    
                    # Pattern 2: Tìm số trong cột "Tiền thắng" từ text mô tả
                    if tien_thang_value is None:
                        tien_thang_patterns = [
                            r'Tiền thắng.*?([+-]?\d{1,3}(?:,\d{3})*)',
                            r'Tiền thắng.*?(-?\d+)',
                            r'winnings.*?([+-]?\d{1,3}(?:,\d{3})*)',
                        ]
                        for pattern in tien_thang_patterns:
                            tien_thang_match = re.search(pattern, chatgpt_response, re.IGNORECASE)
                            if tien_thang_match:
                                winnings_str = tien_thang_match.group(1).replace(",", "").replace("+", "")
                                if winnings_str and winnings_str != "-":
                                    if winnings_str.startswith("-"):
                                        tien_thang_value = -int(winnings_str[1:])
                                    else:
                                        tien_thang_value = int(winnings_str)
                                    break
                    
                    # Parse return (hoàn trả) từ chatgpt_response
                    # Ưu tiên lấy từ parsed JSON
                    hoan_tra_str = parsed.get("hoan_tra") or parsed.get("Hoàn trả") or parsed.get("return")
                    if hoan_tra_str:
                        try:
                            hoan_tra_clean = str(hoan_tra_str).replace(",", "").replace(" ", "").strip()
                            if hoan_tra_clean.isdigit():
                                return_value = int(hoan_tra_clean)
                        except (ValueError, AttributeError):
                            pass
                    
                    # Nếu chưa có, tìm trong text
                    if return_value is None:
                        hoan_tra_patterns = [
                            r'"hoan_tra"\s*:\s*"?(\d+(?:,\d{3})*)"?',
                            r'"Hoàn trả"\s*:\s*"?(\d+(?:,\d{3})*)"?',
                            r'"return"\s*:\s*"?(\d+(?:,\d{3})*)"?',
                            r'Hoàn trả.*?(\d{1,3}(?:,\d{3})*)',
                            r'hoàn trả.*?(\d{1,3}(?:,\d{3})*)',
                        ]
                        for pattern in hoan_tra_patterns:
                            hoan_tra_match = re.search(pattern, chatgpt_response, re.IGNORECASE)
                            if hoan_tra_match:
                                hoan_tra_str = hoan_tra_match.group(1).replace(",", "").strip()
                                if hoan_tra_str.isdigit():
                                    return_value = int(hoan_tra_str)
                                    break
                    
                    # Parse winnings_color từ chatgpt_response
                    winnings_color_match = re.search(r'"winnings_color"\s*:\s*"(red|green)"', chatgpt_response, re.IGNORECASE)
                    if winnings_color_match:
                        winnings_color_value = winnings_color_match.group(1).lower()
                    
                    # Parse column_5 - ưu tiên lấy toàn bộ nội dung từ parsed JSON hoặc raw text
                    # Nếu có trong parsed JSON, lấy từ đó
                    column_5_value = parsed.get("column_5")
                    
                    # Nếu không có, tìm trong text với nhiều pattern
                    if not column_5_value:
                        column_5_match = re.search(r'"column_5"\s*:\s*"([^"]*)"', chatgpt_response)
                        if column_5_match:
                            column_5_value = column_5_match.group(1)
                    
                    # Nếu vẫn không có, thử lấy toàn bộ nội dung đọc được từ ảnh
                    # Tìm phần mô tả nội dung trong chatgpt_response
                    if not column_5_value or column_5_value in ["unknown", "<noi dung cot thu 5>", "<nội dung cột thứ 5>"]:
                        # Tìm phần mô tả chi tiết trong response
                        # Ví dụ: "Đặt Xiu. Kết quả: Tài. Tổng đặt 64,000. Hoàn trả 0."
                        detail_patterns = [
                            r'Đặt\s+[^\.]+\.\s*Kết quả[^\.]+\.\s*Tổng đặt[^\.]+\.\s*Hoàn trả[^\.]+\.',
                            r'Đặt\s+[^\.]+\.\s*Kết quả[^\.]+\.',
                            r'Đặt[^\.]+Kết quả[^\.]+',
                            r'column_5[^"]*"([^"]+)"',
                        ]
                        for pattern in detail_patterns:
                            detail_match = re.search(pattern, chatgpt_response, re.IGNORECASE | re.DOTALL)
                            if detail_match:
                                column_5_value = detail_match.group(0) if detail_match.groups() == () else detail_match.group(1)
                                break
                        
                        # Nếu vẫn không tìm thấy pattern cụ thể, thử lấy toàn bộ text mô tả từ ChatGPT
                        # (phần text không nằm trong JSON)
                        if not column_5_value or column_5_value in ["unknown", "<noi dung cot thu 5>", "<nội dung cột thứ 5>"]:
                            # Tách phần JSON và phần text mô tả
                            json_start = chatgpt_response.find('{')
                            json_end = chatgpt_response.rfind('}')
                            if json_start != -1 and json_end != -1:
                                # Lấy phần text trước và sau JSON
                                text_before = chatgpt_response[:json_start].strip()
                                text_after = chatgpt_response[json_end+1:].strip()
                                # Kết hợp lại để lấy toàn bộ mô tả
                                full_description = (text_before + " " + text_after).strip()
                                if full_description and len(full_description) > 10:  # Chỉ lấy nếu có nội dung đáng kể
                                    column_5_value = full_description
                    
                    # Parse win_loss từ column_5 nếu có
                    if column_5_value:
                        def parse_dat_ket_qua(column_5_text: str) -> tuple:
                            """Parse 'Đặt' và 'Kết quả' từ column_5. Trả về (dat_value, ket_qua_value) hoặc (None, None)"""
                            if not column_5_text:
                                return (None, None)
                            column_5_text = str(column_5_text).strip()
                            dat_value = None
                            ket_qua_value = None
                            
                            # Tìm "Đặt"
                            dat_match = re.search(r'Đặt\s*:?\s*([^,\.]+?)(?=[,\.]|\s*Kết quả|$)', column_5_text, re.IGNORECASE)
                            if dat_match:
                                dat_value = dat_match.group(1).strip()
                            
                            # Tìm "Kết quả"
                            ket_qua_match = re.search(r'Kết quả\s*:?\s*([^,\.]+)', column_5_text, re.IGNORECASE)
                            if ket_qua_match:
                                ket_qua_value = ket_qua_match.group(1).strip()
                            
                            return (dat_value, ket_qua_value)
                        
                        dat_value, ket_qua_value = parse_dat_ket_qua(column_5_value)
                        if dat_value and ket_qua_value:
                            dat_normalized = normalize_choice(dat_value)
                            ket_qua_normalized = normalize_choice(ket_qua_value)
                            if dat_normalized and ket_qua_normalized:
                                if dat_normalized == ket_qua_normalized:
                                    win_loss_value = "win"
                                else:
                                    win_loss_value = "loss"
                    
                    # Nếu win_loss vẫn chưa có, dùng giá trị từ database
                    if win_loss_value is None:
                        win_loss_value = win_token_from_label(record.get("win_loss"))
                except Exception as e:
                    # Log error nhưng không crash
                    import traceback
                    print(f"[Parse HISTORY JSON Error]: {traceback.format_exc()}")
                    # Fallback về giá trị từ database
                    win_loss_value = win_token_from_label(record.get("win_loss"))
            
            # Nếu không có chatgpt_response, dùng giá trị từ database
            if win_loss_value is None:
                win_loss_value = win_token_from_label(record.get("win_loss"))
            
            payload = {
                **base_payload,
                "bet_amount": record.get("bet_amount"),
                "tien_thang": tien_thang_value,
                "winnings_amount": tien_thang_value,  # Alias cho tương thích
                "winnings_color": winnings_color_value,  # "red" hoặc "green" hoặc null
                "win_loss": win_loss_value,
                "return": return_value,  # Giá trị hoàn trả
                "column_5": column_5_value,  # Nội dung cột thứ 5 (toàn bộ nội dung đọc được)
            }
        else:
            payload = base_payload

        # Giữ tien_thang, winnings_amount, winnings_color, column_5 và return ngay cả khi None, nhưng loại bỏ các field None khác
        tien_thang_val = payload.pop("tien_thang", None)
        winnings_amount_val = payload.pop("winnings_amount", None)
        winnings_color_val = payload.pop("winnings_color", None)
        column_5_val = payload.pop("column_5", None)
        return_val = payload.pop("return", None)
        filtered_payload = {k: v for k, v in payload.items() if v is not None}
        # Thêm lại các field quan trọng vào cuối (LUÔN thêm, kể cả khi None)
        if image_type == "HISTORY":
            # Đảm bảo luôn có các field này trong JSON, ngay cả khi None (sẽ hiển thị null)
            filtered_payload["tien_thang"] = tien_thang_val
            filtered_payload["winnings_amount"] = winnings_amount_val
            filtered_payload["winnings_color"] = winnings_color_val
            filtered_payload["column_5"] = column_5_val
            filtered_payload["return"] = return_val
            

        return filtered_payload

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Lá»—i táº£i JSON: {exc}")


@app.get("/api/mobile/device-state/{device_name}")
async def get_device_state(device_name: str):
    try:
        state = mobile_betting_service.get_device_state(device_name)
        return {"success": True, "state": state}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Lá»—i láº¥y state: {exc}")


@app.get("/api/mobile/result/{device_name}")
async def get_mobile_result(device_name: str):
    try:
        conn = sqlite3.connect("logs.db")
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT device_name, betting_method, session_id, image_type,
                   seconds_remaining, bet_amount, bet_status, win_loss, multiplier,
                   created_at
            FROM mobile_analysis_history
            WHERE device_name = ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (device_name,),
        )
        row = cursor.fetchone()
        conn.close()

        if not row:
            return {"success": False, "message": f"KhÃ´ng tÃ¬m tháº¥y káº¿t quáº£ cho device {device_name}"}

        response_data: Dict[str, Any] = {
            "success": True,
            "device_name": row[0],
            "betting_method": row[1],
            "image_type": row[3],
        }

        if row[3] == "HISTORY":
            response_data.update(
                {
                    "session_id": row[2],
                    "session_time": row[9],
                    "bet_amount": row[5],
                    "win_loss": row[7],
                    "multiplier": row[8],
                }
            )
        elif row[3] == "BETTING":
            response_data.update(
                {
                    "session_id": row[2],
                    "seconds": row[4],
                    "bet_amount": row[5],
                    "bet_status": row[6],
                }
            )

        return response_data

    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Lá»—i láº¥y káº¿t quáº£: {exc}")


@app.post("/api/mobile/verify-quick")
async def verify_quick(
    file: UploadFile = File(...),
    device_name: str = Form(...),
    expected_amount: int = Form(...),
):
    try:
        image_data = await file.read()
        mobile_dir = "mobile_images/verify_quick"
        os.makedirs(mobile_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        saved_path = os.path.join(mobile_dir, f"verify_{device_name}_{timestamp}.jpg")
        with open(saved_path, "wb") as f:
            f.write(image_data)

        base64_image = base64.b64encode(image_data).decode('utf-8')
        openai_api_key = get_openai_api_key()

        prompt = """ÄÃ¢y lÃ  giao diá»‡n game. Äá»c sá»‘ lÆ°á»£ng hiá»ƒn thá»‹:\n\nTÃ¬m sá»‘ mÃ u TRáº®NG náº±m DÆ¯á»šI chá»¯ TÃ€I hoáº·c Xá»ˆU (khÃ´ng pháº£i sá»‘ trong khung).\n\nTráº£ vá» CHá»ˆ 1 dÃ²ng:\nSá»‘ lÆ°á»£ng: [sá»‘]\n\nVÃ­ dá»¥: \nSá»‘ lÆ°á»£ng: 2000\nhoáº·c\nSá»‘ lÆ°á»£ng: 0"""

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {openai_api_key}",
                },
                json={
                    "model": "gpt-4o-mini",
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{base64_image}",
                                        "detail": "low",
                                    },
                                },
                            ],
                        }
                    ],
                    "temperature": 0,
                    "max_tokens": 100,
                },
            )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Lá»—i ChatGPT: {response.text}",
                )

            result = response.json()
            chatgpt_text = result["choices"][0]["message"]["content"]

        money_match = re.search(r'(?:Tiá»n cÆ°á»£c|Sá»‘ lÆ°á»£ng):\s*([\d,]+)', chatgpt_text)
        detected_amount = int(money_match.group(1).replace(',', '')) if money_match else 0

        amount_match = detected_amount == expected_amount
        confidence = 1.0 if amount_match else 0.3
        needs_popup = confidence < 0.85

        mobile_betting_service.save_verification_log(
            {
                "device_name": device_name,
                "session_id": None,
                "verification_type": "quick",
                "expected_amount": expected_amount,
                "detected_amount": detected_amount,
                "confidence": confidence,
                "match_status": amount_match,
                "screenshot_path": saved_path,
                "chatgpt_response": chatgpt_text,
            }
        )

        return {
            "verified": amount_match,
            "confidence": confidence,
            "detected_amount": detected_amount,
            "expected_amount": expected_amount,
            "needs_popup_verify": needs_popup,
            "screenshot_path": saved_path,
        }

    except HTTPException:
        raise
    except Exception as exc:
        import traceback

        print("[Verify Quick Error]", traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Lá»—i verify quick: {exc}")


@app.post("/api/mobile/verify-popup")
async def verify_popup(
    file: UploadFile = File(...),
    device_name: str = Form(...),
    expected_amount: int = Form(...),
    expected_method: str = Form(...),
    current_session: str = Form(default=""),
):
    try:
        image_data = await file.read()
        mobile_dir = "mobile_images/verify_popup"
        os.makedirs(mobile_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        saved_path = os.path.join(mobile_dir, f"popup_{device_name}_{timestamp}.jpg")
        with open(saved_path, "wb") as f:
            f.write(image_data)

        base64_image = base64.b64encode(image_data).decode('utf-8')
        openai_api_key = get_openai_api_key()

        prompt = """ÄÃ¢y lÃ  popup lá»‹ch sá»­ trong game. Äá»c CHá»ˆ dÃ²ng Äáº¦U TIÃŠN (má»›i nháº¥t):\n\nFormat tráº£ vá»:\nPhiÃªn: #[sá»‘]\nSá»‘ lÆ°á»£ng: [sá»‘]\nKáº¿t quáº£: [+sá»‘ / -sá»‘ / -]\nChi tiáº¿t: [text]\n\nLÆ°u Ã½: Náº¿u \"Káº¿t quáº£\" chá»‰ lÃ  dáº¥u gáº¡ch \"-\" nghÄ©a lÃ  Ä‘ang chá»."""

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {openai_api_key}",
                },
                json={
                    "model": "gpt-4o-mini",
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{base64_image}",
                                        "detail": "low",
                                    },
                                },
                            ],
                        }
                    ],
                    "temperature": 0,
                    "max_tokens": 200,
                },
            )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Lá»—i ChatGPT: {response.text}",
                )

            result = response.json()
            chatgpt_text = result["choices"][0]["message"]["content"]

        session_match = re.search(r'PhiÃªn:\s*#?(\d+)', chatgpt_text)
        amount_match = re.search(r'(?:Tá»•ng cÆ°á»£c|Sá»‘ lÆ°á»£ng):\s*([\d,]+)', chatgpt_text)
        win_loss_match = re.search(r'(?:Tiá»n tháº¯ng|Káº¿t quáº£):\s*([+\-]?\d+|[\-])', chatgpt_text)
        detail_match = re.search(r'Chi tiáº¿t:\s*(.+)', chatgpt_text)

        detected_session = f"#{session_match.group(1)}" if session_match else None
        detected_amount = int(amount_match.group(1).replace(',', '')) if amount_match else 0
        detected_win_loss = win_loss_match.group(1) if win_loss_match else None
        detected_detail = detail_match.group(1) if detail_match else ""

        detected_method = None
        if "TÃ i" in detected_detail:
            detected_method = "TÃ i"
        elif "Xá»‰u" in detected_detail:
            detected_method = "Xá»‰u"

        checks = []
        amount_ok = detected_amount == expected_amount
        checks.append(("amount_match", amount_ok))

        method_ok = (detected_method == expected_method) if detected_method else None
        if method_ok is not None:
            checks.append(("method_match", method_ok))

        pending_ok = detected_win_loss == "-"
        checks.append(("pending_status", pending_ok))

        passed = sum(1 for _, ok in checks if ok)
        total = len(checks)
        confidence = passed / total if total > 0 else 0.0
        verified = confidence >= 0.8

        mobile_betting_service.save_verification_log(
            {
                "device_name": device_name,
                "session_id": detected_session,
                "verification_type": "popup",
                "expected_amount": expected_amount,
                "detected_amount": detected_amount,
                "confidence": confidence,
                "match_status": verified,
                "screenshot_path": saved_path,
                "chatgpt_response": chatgpt_text,
            }
        )

        if not amount_ok and detected_amount > 0:
            mobile_betting_service.handle_mismatch(
                device_name,
                expected_amount,
                detected_amount,
                detected_session,
            )

        return {
            "verified": verified,
            "confidence": confidence,
            "session_match": True,
            "amount_match": amount_ok,
            "method_match": method_ok if method_ok is not None else True,
            "status": "pending_result" if pending_ok else "unknown",
            "detected_session": detected_session,
            "detected_amount": detected_amount,
            "detected_method": detected_method,
            "mismatch_details": None if amount_ok else f"Expected {expected_amount}, got {detected_amount}",
            "screenshot_path": saved_path,
        }

    except HTTPException:
        raise
    except Exception as exc:
        import traceback

        print("[Verify Popup Error]", traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Lá»—i verify popup: {exc}")


@app.post("/api/mobile/history/analyze-cropped")
async def analyze_history_cropped(
    record_id: Optional[int] = Form(None),
    image: Optional[UploadFile] = File(None),
):
    """
    Phân tích ảnh HISTORY đã crop để trích xuất:
    - win_loss: win/loss/unknown dựa trên so sánh "Đặt" vs "Kết quả"
    - bet_amount: giá trị "Tổng đặt"
    - return: giá trị "Hoàn trả"
    """
    try:
        # Lấy ảnh từ record_id hoặc upload
        cropped_image = None
        
        if record_id:
            # Lấy ảnh từ database
            conn = sqlite3.connect("logs.db")
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT image_path, image_type
                FROM mobile_analysis_history
                WHERE id = ?
                """,
                (record_id,),
            )
            row = cursor.fetchone()
            conn.close()
            
            if not row or not row[0]:
                raise HTTPException(status_code=404, detail="Không tìm thấy record")
            
            image_path = row[0]
            image_type = row[1] if len(row) > 1 else None
            
            if image_type != "HISTORY":
                raise HTTPException(status_code=400, detail="Chỉ hỗ trợ HISTORY image type")
            
            if not os.path.exists(image_path):
                raise HTTPException(status_code=404, detail=f"File ảnh không tồn tại: {image_path}")
            
            # Tìm ảnh crop
            original_dir = Path(image_path).parent
            original_name = Path(image_path).stem
            cropped_image_path = original_dir / f"cropped_{original_name}.jpg"
            
            if cropped_image_path.exists():
                cropped_image = Image.open(cropped_image_path)
            else:
                # Nếu không có crop, dùng ảnh gốc
                cropped_image = Image.open(image_path)
        
        elif image:
            # Lấy ảnh từ upload
            image_data = await image.read()
            cropped_image = Image.open(io.BytesIO(image_data))
        else:
            raise HTTPException(status_code=400, detail="Cần cung cấp record_id hoặc image file")
        
        # Gửi ảnh cho ChatGPT Vision để đọc text
        openai_api_key = get_openai_api_key()
        
        # Convert image to base64
        img_byte_arr = io.BytesIO()
        cropped_image.save(img_byte_arr, format='JPEG', quality=85)
        img_byte_arr.seek(0)
        image_data = img_byte_arr.read()
        base64_image = base64.b64encode(image_data).decode('utf-8')
        
        # Prompt cho ChatGPT
        prompt = """Đọc toàn bộ nội dung trong ảnh này. Ảnh này là màn hình HISTORY đã được crop.

Hãy đọc và trả về JSON với format:
{
  "dat": "Xiu" hoặc "Tài" hoặc null nếu không đọc được,
  "ket_qua": "Xiu" hoặc "Tài" hoặc null nếu không đọc được,
  "tong_dat": "64,000" hoặc số tiền tổng đặt (có thể có dấu phẩy) hoặc null,
  "hoan_tra": "0" hoặc số tiền hoàn trả (có thể có dấu phẩy) hoặc null
}

Chú ý:
- "Đặt" hoặc "Đặt Xiu"/"Đặt Tài" -> dat
- "Kết quả" hoặc "Kết quả: Xiu"/"Kết quả: Tài" -> ket_qua
- "Tổng đặt" -> tong_dat
- "Hoàn trả" -> hoan_tra

Trả về CHỈ JSON, không có text thêm."""
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {openai_api_key}",
                },
                json={
                    "model": "gpt-4o-mini",
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{base64_image}",
                                        "detail": "high",  # Dùng high để đọc text tốt hơn
                                    },
                                },
                            ],
                        }
                    ],
                    "temperature": 0,
                    "max_tokens": 500,
                },
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Lỗi ChatGPT: {response.text}",
                )
            
            result = response.json()
            chatgpt_text = result["choices"][0]["message"]["content"]
        
        # Parse JSON từ ChatGPT response
        def parse_json_payload(raw_text: str) -> Dict[str, Any]:
            if not raw_text:
                return {}
            cleaned = raw_text.strip()
            start = cleaned.find('{')
            end = cleaned.rfind('}')
            if start != -1 and end != -1 and end >= start:
                cleaned = cleaned[start : end + 1]
            try:
                return json.loads(cleaned)
            except json.JSONDecodeError:
                return {}
            except Exception:
                return {}
        
        parsed = parse_json_payload(chatgpt_text)
        
        # Trích xuất các giá trị
        dat_value = parsed.get("dat") or parsed.get("Đặt")
        ket_qua_value = parsed.get("ket_qua") or parsed.get("Kết quả") or parsed.get("ket_qua")
        tong_dat_str = parsed.get("tong_dat") or parsed.get("Tổng đặt") or parsed.get("tong_dat")
        hoan_tra_str = parsed.get("hoan_tra") or parsed.get("Hoàn trả") or parsed.get("hoan_tra")
        
        # Normalize dat và ket_qua (sử dụng hàm normalize_choice đã có sẵn)
        dat_normalized = normalize_choice(dat_value)
        ket_qua_normalized = normalize_choice(ket_qua_value)
        
        # Tính win_loss
        win_loss = "unknown"
        if dat_normalized and ket_qua_normalized:
            if dat_normalized == ket_qua_normalized:
                win_loss = "win"
            else:
                win_loss = "loss"
        
        # Parse bet_amount từ tong_dat
        bet_amount = "unknown"
        if tong_dat_str:
            try:
                # Loại bỏ dấu phẩy và khoảng trắng
                tong_dat_clean = str(tong_dat_str).replace(",", "").replace(" ", "").strip()
                if tong_dat_clean.isdigit():
                    bet_amount = int(tong_dat_clean)
            except (ValueError, AttributeError):
                pass
        
        # Parse return từ hoan_tra
        return_value = "unknown"
        if hoan_tra_str:
            try:
                # Loại bỏ dấu phẩy và khoảng trắng
                hoan_tra_clean = str(hoan_tra_str).replace(",", "").replace(" ", "").strip()
                if hoan_tra_clean.isdigit():
                    return_value = int(hoan_tra_clean)
            except (ValueError, AttributeError):
                pass
        
        return {
            "win_loss": win_loss,
            "bet_amount": bet_amount,
            "return": return_value,
            "raw_data": {
                "dat": dat_value,
                "ket_qua": ket_qua_value,
                "tong_dat": tong_dat_str,
                "hoan_tra": hoan_tra_str,
            },
            "chatgpt_response": chatgpt_text,
        }
    
    except HTTPException:
        raise
    except Exception as exc:
        import traceback
        print("[Analyze History Cropped Error]", traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Lỗi phân tích ảnh HISTORY: {exc}")
