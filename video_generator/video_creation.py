# Video creation module
# 视频生成模块

import os
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import datetime
import tkinter as tk
from tkinter import filedialog
class VideoCreator:
    def __init__(self, config, progress_label_widget=None, progress_bar_widget=None, root=None):
        pass
    
    def generate_video(self):
        """生成视频"""
        try:
            if not self.video_data:
                self.show_warning("警告", "没有视频数据")
                return False
            
            if not self.current_image_file or not os.path.exists(self.current_image_file):
                self.show_warning("警告", "没有选择报纸图片")
                return False
            
            # 选择保存位置
            save_path = filedialog.asksaveasfilename(
                defaultextension=".mp4",
                filetypes=[("MP4文件", "*.mp4"), ("所有文件", "*")],
                initialfile=f"news_video_{datetime.datetime.now().strftime('%Y%m%d')}.mp4"
            )
            
            if not save_path:
                return False
            
            # 视频参数
            width, height = 1080, 1920
            fps = 24
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(save_path, fourcc, fps, (width, height))
            
            # 计算视频总时长
            news_count = len(self.video_data)
            video_duration = max(15, news_count * 3)  # 至少15秒
            total_frames = int(video_duration * fps)
            
            # 加载报纸图片
            newspaper_image = Image.open(self.current_image_file)
            
            # 字体设置
            font_path = "C:\\Windows\\Fonts\\msyh.ttc"  # 微软雅黑
            if not os.path.exists(font_path):
                font_path = "C:\\Windows\\Fonts\\simhei.ttf"  # 黑体备用
            
            # 报纸名称（从文件名识别）
            filename = os.path.basename(self.current_image_file).lower()
            if "wall" in filename or "wsj" in filename:
                newspaper_name = "华尔街日报"
            elif "financial" in filename or "ft" in filename:
                newspaper_name = "金融时报"
            else:
                newspaper_name = "报纸"
            
            # 日期显示
            today = datetime.datetime.now()
            date_str = today.strftime("%Y年%m月%d日")
            weekday_map = {0: "周日", 1: "周一", 2: "周二", 3: "周三", 4: "周四", 5: "周五", 6: "周六"}
            weekday_str = weekday_map[today.weekday()]
            date_display = f"{date_str} {weekday_str}"
            
            self.update_progress("正在生成视频...")
            self.progress_bar['value'] = 0
            
            # 生成每帧
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
                
                # 计算当前时间和新闻索引
                current_time = frame_idx / fps
                news_index = min(int(current_time / 3), news_count - 1)
                news_time = current_time % 3
                
                # 绘制报纸名称
                pil_image = Image.fromarray(frame)
                draw = ImageDraw.Draw(pil_image)
                
                try:
                    font = ImageFont.truetype(font_path, 60)
                    bbox = draw.textbbox((0, 0), newspaper_name, font=font)
                    text_width = bbox[2] - bbox[0]
                    text_height = bbox[3] - bbox[1]
                    x = (width - text_width) // 2
                    y = 50
                    draw.text((x, y), newspaper_name, font=font, fill=(255, 255, 255))
                    
                    # 绘制日期
                    font = ImageFont.truetype(font_path, 36)
                    bbox = draw.textbbox((0, 0), date_display, font=font)
                    text_width = bbox[2] - bbox[0]
                    text_height = bbox[3] - bbox[1]
                    x = (width - text_width) // 2
                    y = 130
                    draw.text((x, y), date_display, font=font, fill=(255, 215, 0))  # 金色
                    
                    # 计算图片位置
                    image_height = height - 200 - 400  # 总高度 - 标题200px - 字幕400px
                    image_width = int(newspaper_image.width * (image_height / newspaper_image.height))
                    if image_width > width:
                        image_width = width
                        image_height = int(newspaper_image.height * (image_width / newspaper_image.width))
                    
                    # 调整图片大小
                    resized_image = newspaper_image.resize((image_width, image_height), Image.Resampling.LANCZOS)
                    
                    # 计算图片位置（居中）
                    image_x = (width - image_width) // 2
                    image_y = 200  # 顶部留出200px给标题
                    
                    # 粘贴图片到帧
                    pil_image.paste(resized_image, (image_x, image_y))
                    
                    # 绘制字幕
                    if news_index < len(self.video_data):
                        news = self.video_data[news_index]
                        content = news.get('content', '')
                        
                        # 字幕动画
                        if news_time < 0.5:
                            # 淡入效果
                            alpha = news_time / 0.5
                        elif news_time > 2.5:
                            # 淡出效果
                            alpha = 1.0 - (news_time - 2.5) / 0.5
                        else:
                            # 正常显示
                            alpha = 1.0
                        
                        # 绘制字幕框
                        subtitle_y = image_y + image_height + 50
                        subtitle_height = 120
                        subtitle_width = width - 100
                        subtitle_x = 50
                        
                        # 半透明背景
                        overlay = Image.new('RGBA', pil_image.size, (0, 0, 0, 128))
                        overlay_draw = ImageDraw.Draw(overlay)
                        overlay_draw.rectangle([subtitle_x, subtitle_y, subtitle_x + subtitle_width, subtitle_y + subtitle_height], fill=(0, 0, 0, 128))
                        
                        # 合成半透明背景
                        pil_image = Image.alpha_composite(pil_image.convert('RGBA'), overlay)
                        draw = ImageDraw.Draw(pil_image)
                        
                        # 绘制字幕文本
                        font = ImageFont.truetype(font_path, 40)
                        # 文本换行
                        words = content.split()
                        lines = []
                        current_line = []
                        current_width = 0
                        
                        for word in words:
                            bbox = draw.textbbox((0, 0), word + ' ', font=font)
                            word_width = bbox[2] - bbox[0]
                            if current_width + word_width <= subtitle_width:
                                current_line.append(word)
                                current_width += word_width
                            else:
                                lines.append(' '.join(current_line))
                                current_line = [word]
                                current_width = word_width
                        
                        if current_line:
                            lines.append(' '.join(current_line))
                        
                        # 绘制多行文本
                        line_height = 50
                        for i, line in enumerate(lines[:2]):  # 最多显示2行
                            bbox = draw.textbbox((0, 0), line, font=font)
                            text_width = bbox[2] - bbox[0]
                            text_x = subtitle_x + (subtitle_width - text_width) // 2
                            text_y = subtitle_y + 10 + i * line_height
                            draw.text((text_x, text_y), line, font=font, fill=(255, 255, 255, int(alpha * 255)))
                    
                except Exception as e:
                    print(f"绘制文本失败: {e}")
                
                # 转换回OpenCV格式
                frame = np.array(pil_image.convert('RGB'))
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                
                # 写入帧
                out.write(frame)
                
                # 更新进度
                progress = int((frame_idx + 1) / total_frames * 100)
                self.progress_bar['value'] = progress
                self.update_progress(f"生成中... {progress}%")
                if self.root:
                    self.root.update()
            
            # 释放资源
            out.release()
            
            self.update_progress("视频生成成功", 100, "#27AE60")
            self.show_info("成功", f"视频生成成功!\n\n已保存到: {save_path}")
            
            return True
            
        except Exception as e:
            self.update_progress(f"生成失败: {str(e)}", 0, "#E74C3C")
            self.show_error("错误", f"生成视频失败:\n{str(e)}")
            return False