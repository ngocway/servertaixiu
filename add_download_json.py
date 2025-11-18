#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re

with open('app/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Thêm hàm downloadJson sau hàm copyJson
download_function = '''
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
'''

# Tìm vị trí sau hàm copyJson và trước hàm closeJsonModal
pattern = r'(function copyJson\(\) \{[^}]+\})\s+(function closeJsonModal\(\))'
replacement = r'\1\n' + download_function + r'\n        \2'

content = re.sub(pattern, replacement, content, flags=re.DOTALL)

with open('app/main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Added downloadJson function successfully!")

















