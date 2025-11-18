#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re

with open('app/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace Vietnamese text
replacements = [
    ('Thiáº¿t bá»‹', 'Devices'),
    ('Báº£n ghi', 'Records'),
    ('LÃ m má»›i', 'Refresh'),
    ('Hiá»ƒn thá»‹', 'Display'),
    ('báº£n ghi má»›i nháº¥t', 'latest records'),
    ('Loáº¡i áº£nh', 'Image Type'),
    ('PhiÃªn', 'Session'),
    ('GiÃ¢y', 'Seconds'),
    ('Tiá» n dá»± kiáº¿n', 'Planned Amount'),
    ('Tiá» n thá»±c', 'Actual Amount'),
    ('Káº¿t quáº£', 'Result'),
    ('Há»‡ sá»\'', 'Multiplier'),
    ('HÃ nh Ä\'á»™ng', 'Actions'),
    ('Thá» i gian', 'Time'),
    ('Ä\'ang táº£i dá»¯ liá»‡u', 'Loading data...'),
    ('áº¢nh Run Mobile', 'Run Mobile Image'),
    ('Táº£i áº¢nh', 'Download Image'),
    ('Ä\'Ã£ copy endpoint!', 'Endpoint copied!'),
    ('Ä\'Ã£ copy JSON!', 'JSON copied!'),
    ('ChÆ°a cÃ³ dá»¯ liá»‡u', 'No data available'),
    ('Lá»—i táº£i dá»¯ liá»‡u', 'Error loading data'),
    ('"Tháº¯ng"', '"Win"'),
    ('"Thua"', '"Loss"'),
    ("toLocaleString('vi-VN')", "toLocaleString('en-US')"),
]

for old, new in replacements:
    content = content.replace(old, new)

with open('app/main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Translation completed!")


















