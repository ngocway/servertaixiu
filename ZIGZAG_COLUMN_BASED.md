# 🔄 Zigzag Logic - Column-Based Ordering

## 📋 Overview

Thay đổi logic sắp xếp nốt xanh từ **row-based** (theo hàng) sang **column-based** (theo cột) để khớp với pattern game.

---

## 🔄 Logic Comparison

### **OLD (Row-Based) ❌**

```
Sắp xếp theo HÀNG:
Hàng 1: phải → trái
Hàng 2: trái → phải
Hàng 3: phải → trái

Example:
  1 ← 2 ← 3      (Row 1: right to left)
  4 → 5 → 6      (Row 2: left to right)
  7 ← 8 ← 9      (Row 3: right to left)

Sequence: 3, 2, 1, 4, 5, 6, 9, 8, 7
```

**Problem:** Không khớp với game zigzag pattern!

---

### **NEW (Column-Based) ✅**

```
Sắp xếp theo CỘT:
Cột 1 (phải nhất): trên → dưới
Cột 2:             dưới → trên
Cột 3:             trên → dưới
Cột 4:             dưới → trên

Example (3 cols x 4 rows):
      Col 3   Col 2   Col 1
      (left)          (right)
        
Row 1:  13      9   →   1   ← START HERE
        ↓       ↑       ↓
Row 2:  14     10       2
        ↓       ↑       ↓
Row 3:  15     11       3
        ↓       ↑       ↓
Row 4:  16     12       4
        ↓       ↑       

Sequence: 1→2→3→4 (col 1, down) → 12→11→10→9 (col 2, up) → 13→14→15→16 (col 3, down)
```

**Result:** Khớp với game pattern! ✅

---

## 🎯 Algorithm

### **Step-by-step:**

```python
1. Sort dots theo X coordinate (để nhóm cột)
   sorted(dots, key=lambda d: (d.x, d.y))

2. Nhóm dots thành columns (threshold: 20px)
   - Nếu abs(x1 - x2) <= 20 → Cùng cột
   - Nếu abs(x1 - x2) > 20 → Cột khác

3. Sort columns từ PHẢI sang TRÁI
   columns.sort(key=lambda col: col[0].x, reverse=True)

4. Zigzag trong mỗi cột:
   for i, col in enumerate(columns):
       col.sort(key=lambda d: d.y)  # Sort by Y
       
       if i % 2 == 0:
           # Cột chẵn (0, 2, 4...): top → bottom
           ordered.extend(col)
       else:
           # Cột lẻ (1, 3, 5...): bottom → top
           ordered.extend(reversed(col))
```

---

## 📊 Visual Example

### **Game Grid (từ screenshot):**

```
       X: 1555   1492   (right to left)
          ↓       ↓
Y: 219    ⚪      ⚪      Row 1
          1       
          
Y: 276    ⚫      ⚫      Row 2
          2       
          
Y: 332    ⚪      ⚪      Row 3
          3       
          
Y: 388    ⚫      ⚫      Row 4
          4       

Pattern: ⚪ → ⚫ → ⚪ → ⚫ → ...
```

### **Sequence Result:**

**OLD (Row-based):**
```
⚪ → ⚪ → ⚫ → ⚫ → ⚪ → ⚪ → ⚫ → ⚫
❌ WRONG - không khớp game
```

**NEW (Column-based):**
```
⚪ → ⚫ → ⚪ → ⚫ → ⚪ → ⚫ → ⚪ → ⚫
✅ CORRECT - khớp với game pattern
```

---

## 🔧 Configuration

### **Thresholds:**

```python
col_threshold = 20  # pixels
```

**Meaning:**
- Nếu 2 nốt có `abs(x1 - x2) <= 20px` → Cùng cột
- Điều chỉnh nếu game có khoảng cách cột khác

---

## 🎮 Game Pattern Explained

### **Từ ảnh game:**

1. **Nốt 1:** Cột phải nhất, hàng trên cùng → **TRẮNG** ⚪
2. **Nốt 2:** Cột phải nhất, hàng thứ 2 → **ĐEN** ⚫
3. **Nốt 3:** Cột phải nhất, hàng thứ 3 → **TRẮNG** ⚪
4. **Nốt 4:** Cột phải nhất, hàng thứ 4 → **ĐEN** ⚫
5. **Nốt 5:** Cột thứ 2, hàng thứ 4 (bottom) → **TRẮNG** ⚪
6. **Nốt 6:** Cột thứ 2, hàng thứ 3 (going up) → **ĐEN** ⚫
7. ...

**Pattern:** Column 1 down → Column 2 up → Column 3 down → ...

---

## 🧪 Testing

### **Test Case 1: Simple 2x2 Grid**

```python
Input dots:
  (1555, 219) → Col 1, Row 1
  (1555, 332) → Col 1, Row 2
  (1492, 219) → Col 2, Row 1
  (1492, 332) → Col 2, Row 2

Expected output order:
  1. (1555, 219) - Col 1, top
  2. (1555, 332) - Col 1, bottom
  3. (1492, 332) - Col 2, bottom (reverse)
  4. (1492, 219) - Col 2, top (reverse)
```

### **Test Case 2: From Game Screenshot**

```python
Input: 10 dots in 2 columns x 5 rows
Expected sequence:
  ["TRẮNG", "ĐEN", "TRẮNG", "ĐEN", "TRẮNG", 
   "ĐEN", "TRẮNG", "ĐEN", "TRẮNG", "ĐEN"]
```

---

## 📝 Code Changes

### **File:** `app/services/green_detector.py`

**Function:** `order_dots_zigzag(dots: List[Dot]) -> List[Dot]`

**Changed:**
- Logic từ row grouping → column grouping
- Sort từ left-right zigzag → right-left zigzag
- Pattern từ row alternating → column alternating

---

## 🎯 Impact

### **Affected Components:**

1. ✅ **Template upload:** Auto-detect green dots
2. ✅ **Screenshot analysis:** Khi không dùng template coordinates
3. ✅ **All endpoints:** Sử dụng `detect_green_dots()`

### **NOT Affected:**

❌ **Direct coordinates mode:** Không dùng zigzag ordering (dùng template coords trực tiếp)

---

## ⚠️ Important Notes

1. **Threshold:** 20px là giá trị mặc định, có thể cần điều chỉnh
2. **Starting point:** Luôn bắt đầu từ **cột phải nhất, hàng trên cùng**
3. **Column detection:** Dựa vào X coordinate proximity
4. **Row order in column:** Dựa vào Y coordinate

---

## 🔄 Migration

### **Existing Data:**

- ✅ Template cũ: Vẫn hoạt động (dùng coordinates cố định)
- ✅ Logs cũ: Không thay đổi (đã lưu với sequence cũ)
- ✅ New uploads: Sử dụng logic mới

### **No Breaking Changes:**

- Response format không thay đổi
- API endpoints không thay đổi
- Database schema không thay đổi
- Chỉ thứ tự sequence thay đổi

---

## 📚 References

- **File:** `app/services/green_detector.py`
- **Function:** `order_dots_zigzag()`
- **Line:** ~84-131
- **Commit:** Zigzag logic changed from row-based to column-based
- **Date:** 2025-11-01

---

## 🎓 Summary

**Before:** Row-based zigzag (không khớp game)  
**After:** Column-based zigzag (khớp game pattern)  
**Result:** Sequence đúng với game! ✅

**Key Points:**
- Bắt đầu: Cột phải, hàng trên
- Pattern: Col 1 down → Col 2 up → Col 3 down
- Threshold: 20px cho column grouping
- Impact: Tất cả green dot detection







