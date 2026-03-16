import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import datetime
import os

# 测试视频生成的核心功能
def test_video_generation():
    print("测试视频生成功能...")
    
    # 视频参数
    width, height = 1080, 1920
    fps = 24
    duration = 5  # 5秒测试视频
    total_frames = int(duration * fps)
    
    # 临时输出文件
    output_file = "test_video.mp4"
    
    try:
        # 创建视频编写器
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_file, fourcc, fps, (width, height))
        
        # 字体设置
        font_path = "C:\\Windows\\Fonts\\msyh.ttc"  # 微软雅黑
        if not os.path.exists(font_path):
            font_path = "C:\\Windows\\Fonts\\simhei.ttf"  # 黑体备用
        
        # 测试数据
        newspaper_name = "测试报纸"
        today = datetime.datetime.now()
        date_str = today.strftime("%Y年%m月%d日")
        weekday_map = {0: "周日", 1: "周一", 2: "周二", 3: "周三", 4: "周四", 5: "周五", 6: "周六"}
        weekday_str = weekday_map[today.weekday()]
        date_display = f"{date_str} {weekday_str}"
        
        # 生成测试帧
        for frame_idx in range(total_frames):
            # 创建背景
            frame = np.zeros((height, width, 3), dtype=np.uint8)
            
            # 渐变背景
            for y in range(height):
                ratio = y / height
                blue = int(30 + (0 - 30) * ratio)
                green = int(0 + (0 - 0) * ratio)
                red = int(60 + (30 - 60) * ratio)
                frame[y, :, 0] = blue  # B
                frame[y, :, 1] = green  # G
                frame[y, :, 2] = red  # R
            
            # 绘制文本
            pil_image = Image.fromarray(frame)
            draw = ImageDraw.Draw(pil_image)
            
            try:
                # 绘制报纸名称
                font = ImageFont.truetype(font_path, 60)
                bbox = draw.textbbox((0, 0), newspaper_name, font=font)
                text_width = bbox[2] - bbox[0]
                x = (width - text_width) // 2
                y = 50
                draw.text((x, y), newspaper_name, font=font, fill=(255, 255, 255))
                
                # 绘制日期
                font = ImageFont.truetype(font_path, 36)
                bbox = draw.textbbox((0, 0), date_display, font=font)
                text_width = bbox[2] - bbox[0]
                x = (width - text_width) // 2
                y = 130
                draw.text((x, y), date_display, font=font, fill=(255, 215, 0))  # 金色
                
                # 绘制测试字幕
                font = ImageFont.truetype(font_path, 40)
                test_text = "测试视频生成功能..."
                bbox = draw.textbbox((0, 0), test_text, font=font)
                text_width = bbox[2] - bbox[0]
                x = (width - text_width) // 2
                y = height - 200
                draw.text((x, y), test_text, font=font, fill=(255, 255, 255))
                
            except Exception as e:
                print(f"绘制文本失败: {e}")
            
            # 转换回OpenCV格式
            frame = np.array(pil_image.convert('RGB'))
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            
            # 写入帧
            out.write(frame)
            
            # 显示进度
            if frame_idx % (total_frames // 10) == 0:
                print(f"进度: {int((frame_idx + 1) / total_frames * 100)}%")
        
        # 释放资源
        out.release()
        
        print(f"测试视频生成成功! 输出文件: {output_file}")
        print("视频生成功能正常工作")
        
        # 清理测试文件
        if os.path.exists(output_file):
            os.remove(output_file)
            print("测试文件已清理")
        
        return True
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_video_generation()