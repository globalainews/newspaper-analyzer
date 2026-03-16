from PIL import Image
import os
import json

def test_coordinates():
    """测试坐标裁剪是否正确"""
    try:
        # 加载测试数据
        with open('analysis_results/ft_uk_2026-03-10.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 假设我们有一个测试图片
        # 注意：这里需要替换为实际的图片路径
        test_image_path = 'path_to_test_image.png'
        
        if not os.path.exists(test_image_path):
            print(f"测试图片不存在: {test_image_path}")
            print("请替换为实际的报纸图片路径")
            return
        
        # 加载图片
        image = Image.open(test_image_path)
        print(f"图片尺寸: {image.size}")
        
        # 测试每条新闻的坐标
        for i, news in enumerate(data['news_blocks']):
            position = news['position']
            x1, y1, x2, y2 = position
            
            print(f"\n新闻 {i+1}: {news['title']}")
            print(f"原始坐标: {position}")
            print(f"坐标范围: x1={x1}, y1={y1}, x2={x2}, y2={y2}")
            print(f"区域大小: 宽={x2-x1}, 高={y2-y1}")
            
            # 检查坐标是否有效
            if x1 < 0 or y1 < 0 or x2 > image.width or y2 > image.height:
                print("⚠️  坐标超出图片范围")
            
            if x2 <= x1 or y2 <= y1:
                print("⚠️  无效坐标（宽度或高度为负）")
            
            # 尝试裁剪
            try:
                # 扩展区域
                extended_y2 = y2 + 200
                extended_y2 = min(image.height, extended_y2)
                
                # 裁剪
                cropped = image.crop((x1, y1, x2, extended_y2))
                print(f"裁剪后尺寸: {cropped.size}")
                
                # 保存测试图片
                test_output = f'test_crop_{i+1}.png'
                cropped.save(test_output)
                print(f"测试裁剪已保存: {test_output}")
                
            except Exception as e:
                print(f"裁剪失败: {e}")
                
    except Exception as e:
        print(f"测试失败: {e}")

if __name__ == "__main__":
    test_coordinates()
