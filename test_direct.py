#!/usr/bin/env python3
"""
直接测试分析函数
"""

from layoutlmv3_service import analyze_document_layout

# 直接调用分析函数
image_path = "downloaded_images/ft_uk_2026-03-10.jpg"
result = analyze_document_layout(image_path)

print("\n=== 分析结果 ===")
print(f"成功: {result['success']}")
if result['success']:
    print(f"图像尺寸: {result['image_size']['width']}x{result['image_size']['height']}")
    print(f"区域数量: {result['regions_count']}")
    print("区域列表:")
    for i, region in enumerate(result['regions']):
        print(f"  区域 {i+1}: {region['coordinates']}")
else:
    print(f"错误: {result['error']}")
