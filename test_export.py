#!/usr/bin/env python3
"""
测试新闻图片导出功能
"""

import os
from news_image_exporter import NewsImageExporter

def test_export():
    """测试导出功能"""
    print("=" * 60)
    print("测试新闻图片导出功能")
    print("=" * 60)
    
    # 创建导出器
    exporter = NewsImageExporter()
    
    # 查找测试图片
    test_images = [
        "downloaded_images/ft_uk_2026-03-10.jpg",
        "downloaded_images/wsj_2026-03-10.jpg",
        "test_image.png",
        "test_newspaper.png"
    ]
    
    image_path = None
    for img in test_images:
        if os.path.exists(img):
            image_path = img
            break
    
    if not image_path:
        print("❌ 未找到测试图片")
        print("请确保有以下图片之一:")
        for img in test_images:
            print(f"  - {img}")
        return
    
    print(f"✅ 找到测试图片: {image_path}")
    
    # 模拟6条新闻数据
    news_data = [
        {"title": "新闻1：全球经济复苏势头强劲"},
        {"title": "新闻2：科技巨头发布新产品"},
        {"title": "新闻3：气候变化应对新政策"},
        {"title": "新闻4：金融市场波动分析"},
        {"title": "新闻5：国际贸易谈判进展"},
        {"title": "新闻6：新兴市场投资机会"}
    ]
    print(f"✅ 模拟 {len(news_data)} 条新闻数据")
    
    # 测试导出
    try:
        print("\n开始导出新闻图片...")
        exported_paths, export_dir = exporter.export_news_images(
            image_path=image_path,
            news_data=news_data,
            newspaper_name="测试报纸"
        )
        
        print("\n" + "=" * 60)
        print("导出结果")
        print("=" * 60)
        print(f"导出目录: {export_dir}")
        print(f"导出数量: {len(exported_paths)}")
        
        if exported_paths:
            print("\n导出的文件:")
            for path in exported_paths:
                print(f"  - {path}")
            print("\n✅ 导出成功！")
        else:
            print("\n⚠️ 未导出任何图片")
            
    except Exception as e:
        print(f"\n❌ 导出失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_export()
