#!/usr/bin/env python3
"""
测试LayoutLMv3服务使用gemini模型的文本和边界框数据
"""

import requests
import json
import os

# 测试图片路径
image_path = os.path.join(os.getcwd(), "downloaded_images", "ft_uk_2026-03-10.jpg")

# 模拟来自gemini模型的文本和边界框数据
words = [
    "Global markets rally on inflation data",
    "Central banks signal rate cuts",
    "Tech stocks lead gains",
    "Economic outlook improves",
    "Oil prices stabilize"
]

# 模拟边界框数据（像素坐标）
boxes = [
    [100, 50, 500, 100],   # 标题1
    [100, 120, 400, 150],  # 标题2
    [100, 170, 350, 200],  # 标题3
    [100, 220, 450, 250],  # 标题4
    [100, 270, 300, 300]   # 标题5
]

# 构建请求数据
data = {
    "image_path": image_path,
    "words": words,
    "boxes": boxes
}

# 发送请求
try:
    response = requests.post(
        "http://127.0.0.1:5000/analyze",
        json=data,
        timeout=30
    )
    
    if response.status_code == 200:
        result = response.json()
        print("测试结果:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
        if result.get("success"):
            print(f"\n成功检测到 {result.get('regions_count', 0)} 个新闻区域")
            for i, region in enumerate(result.get('regions', [])):
                print(f"区域 {i+1}: 坐标={region['coordinates']}, 标签={region['label']}")
        else:
            print(f"\n服务返回错误: {result.get('error')}")
    else:
        print(f"服务响应异常: {response.status_code}")
        print(response.text)
        
except Exception as e:
    print(f"请求失败: {e}")
