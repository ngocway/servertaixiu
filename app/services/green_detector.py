from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict
import numpy as np


# Match the frontend configuration (tuned for #1AFF0D)
GREEN_DETECTION_CONFIG = {
    "greenMin": (20, 200, 10),
    "greenMax": (30, 255, 20),
    "minArea": 20,
    "minDistance": 30,
}


@dataclass
class Dot:
    x: int
    y: int
    area: int


def is_green_color(r: int, g: int, b: int) -> bool:
    minR, minG, minB = GREEN_DETECTION_CONFIG["greenMin"]
    maxR, maxG, maxB = GREEN_DETECTION_CONFIG["greenMax"]
    return (minR <= r <= maxR) and (minG <= g <= maxG) and (minB <= b <= maxB)


def detect_green_dots(rgba_image: np.ndarray) -> List[Dict]:
    h, w = rgba_image.shape[0], rgba_image.shape[1]
    visited = np.zeros((h, w), dtype=bool)
    dots: List[Dot] = []

    # Iterate all pixels
    for y in range(h):
        for x in range(w):
            if visited[y, x]:
                continue
            r, g, b, a = rgba_image[y, x]
            if a < 128:
                continue
            if not is_green_color(int(r), int(g), int(b)):
                continue

            # Flood fill to find connected region
            area, cx_sum, cy_sum = 0, 0, 0
            stack = [(x, y)]
            while stack:
                sx, sy = stack.pop()
                if sx < 0 or sx >= w or sy < 0 or sy >= h:
                    continue
                if visited[sy, sx]:
                    continue
                rr, gg, bb, aa = rgba_image[sy, sx]
                if aa < 128 or not is_green_color(int(rr), int(gg), int(bb)):
                    continue
                visited[sy, sx] = True
                area += 1
                cx_sum += sx
                cy_sum += sy
                # 8-neighborhood
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        if dx == 0 and dy == 0:
                            continue
                        stack.append((sx + dx, sy + dy))

            if area >= GREEN_DETECTION_CONFIG["minArea"]:
                cx = int(round(cx_sum / area))
                cy = int(round(cy_sum / area))
                # Enforce min distance
                too_close = any(((d.x - cx) ** 2 + (d.y - cy) ** 2) ** 0.5 < GREEN_DETECTION_CONFIG["minDistance"] for d in dots)
                if not too_close:
                    dots.append(Dot(x=cx, y=cy, area=area))

    # Zigzag order (top->bottom rows; row0 right->left; row1 left->right; ...)
    ordered_dots = order_dots_zigzag(dots)
    
    # Convert Dot objects to dictionaries for JSON serialization
    return [{"x": d.x, "y": d.y} for d in ordered_dots]


def order_dots_zigzag(dots: List[Dot]) -> List[Dot]:
    """
    Sắp xếp các nốt theo pattern zigzag THEO CỘT (column-based)
    Bắt đầu từ cột PHẢI NHẤT, TRÊN CÙNG
    Cột 1 (phải nhất): top → bottom
    Cột 2: bottom → top
    Cột 3: top → bottom
    ...
    """
    if not dots:
        return []
    
    # Sort theo X trước để nhóm cột
    dots_sorted = sorted(dots, key=lambda d: (d.x, d.y))
    
    # Nhóm các dots thành cột (dựa vào khoảng cách X)
    col_threshold = 20
    columns: List[List[Dot]] = []
    current_col: List[Dot] = []
    current_x = dots_sorted[0].x
    
    for d in dots_sorted:
        if abs(d.x - current_x) <= col_threshold:
            current_col.append(d)
        else:
            columns.append(current_col)
            current_col = [d]
            current_x = d.x
    if current_col:
        columns.append(current_col)
    
    # Sắp xếp cột từ PHẢI sang TRÁI (giảm dần theo X)
    columns.sort(key=lambda col: col[0].x if col else 0, reverse=True)
    
    # Zigzag theo cột
    ordered: List[Dot] = []
    for i, col in enumerate(columns):
        # Sort theo Y
        col.sort(key=lambda d: d.y)
        
        if i % 2 == 0:
            # Cột chẵn (0, 2, 4...): top → bottom
            ordered.extend(col)
        else:
            # Cột lẻ (1, 3, 5...): bottom → top
            ordered.extend(reversed(col))
    
    return ordered


def luminance_brightness(r: int, g: int, b: int) -> int:
    return int(round(0.299 * r + 0.587 * g + 0.114 * b))


def classify_black_white(r: int, g: int, b: int, threshold: int = 128) -> Dict[str, int | str]:
    brightness = luminance_brightness(r, g, b)
    cls = "ĐEN" if brightness < threshold else "TRẮNG"
    distance = abs(brightness - threshold)
    confidence = int(round(max(0, 100 - (distance / 128) * 100)))
    return {"classification": cls, "brightness": brightness, "confidence": confidence}


def extract_colors_at_positions(rgba_image: np.ndarray, dots: List[Dict]) -> List[Dict[str, int | str]]:
    h, w = rgba_image.shape[0], rgba_image.shape[1]
    results: List[Dict[str, int | str]] = []
    for idx, d in enumerate(dots):
        # Support both dict and Dot object for backward compatibility
        x = max(0, min(w - 1, int(round(d["x"] if isinstance(d, dict) else d.x))))
        y = max(0, min(h - 1, int(round(d["y"] if isinstance(d, dict) else d.y))))
        r, g, b, a = [int(v) for v in rgba_image[y, x]]
        cls = classify_black_white(r, g, b)
        results.append({
            "number": idx + 1,
            "x": x,
            "y": y,
            "color_r": r,
            "color_g": g,
            "color_b": b,
            "color_rgb": f"rgb({r}, {g}, {b})",
            "classification": cls["classification"],
            "brightness": cls["brightness"],
            "confidence": cls["confidence"],
        })
    return results














