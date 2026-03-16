#!/usr/bin/env python3
"""
测试分析接口
"""

import requests
import json

# 测试分析接口
url = "http://127.0.0.1:5000/analyze"
data = {
    "image_path": "downloaded_images/ft_uk_2026-03-10.jpg"
}

response = requests.post(url, json=data, timeout=30)

print(f"状态码: {response.status_code}")
print("响应内容:")
print(json.dumps(response.json(), indent=2, ensure_ascii=False))
