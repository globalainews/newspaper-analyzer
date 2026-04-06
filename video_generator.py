import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog
import os
import json
import time
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import datetime
from news_image_exporter import NewsImageExporter


class VideoGenerator:
    def __init__(self, config, progress_label_widget, progress_bar_widget, root=None):
        self.config = config
        self.progress_label = progress_label_widget
        self.progress_bar = progress_bar_widget
        self.root = root
        
        self.video_data = []
        self.current_news_index = -1
        self.news_listbox = None
        self.analysis_dir = self.config.get('analysis_settings', {}).get('analysis_directory', 'analysis_results')
        self.download_dir = self.config['download_settings']['save_directory']
        self.current_image_file = None
        # 剪映草稿文件夹配置
        self.jianying_drafts_dir = self.config.get('jianying_settings', {}).get('drafts_directory', 'F:\\剪映5.9\\JianyingPro Drafts')
    
    def set_news_listbox(self, news_listbox):
        self.news_listbox = news_listbox
    
    def silent_load_json(self, image_filename):
        """静默加载JSON文件（不显示提示框）"""
        try:
            if not image_filename:
                return
            
            base_name = os.path.splitext(image_filename)[0]
            json_filename = f"{base_name}.json"
            json_file_path = os.path.join(self.analysis_dir, json_filename)
            
            if os.path.exists(json_file_path):
                self.current_image_file = os.path.join(self.download_dir, image_filename)
                self.load_json_file(json_file_path)
                # 显示报纸图片
                self.show_newspaper_image()
        except Exception as e:
            print(f"静默加载JSON文件失败: {str(e)}")
    
    def load_json_files(self, image_filename=None):
        """加载分析目录中的JSON文件"""
        try:
            json_files = []
            if os.path.exists(self.analysis_dir):
                for file in os.listdir(self.analysis_dir):
                    if file.endswith('.json'):
                        json_files.append(file)
            
            if json_files:
                # 如果提供了图片文件名，尝试加载对应的JSON文件
                if image_filename:
                    base_name = os.path.splitext(image_filename)[0]
                    json_filename = f"{base_name}.json"
                    json_file_path = os.path.join(self.analysis_dir, json_filename)
                    
                    if os.path.exists(json_file_path):
                        self.current_image_file = os.path.join(self.download_dir, image_filename)
                        self.load_json_file(json_file_path)
                        # 显示报纸图片
                        self.show_newspaper_image()
                        return
                
                # 否则显示文件选择对话框
                selected_file = filedialog.askopenfilename(
                    initialdir=self.analysis_dir,
                    title="选择JSON文件",
                    filetypes=[("JSON文件", "*.json"), ("所有文件", "*")]
                )
                
                if selected_file:
                    # 尝试找到对应的图片文件
                    base_name = os.path.splitext(os.path.basename(selected_file))[0]
                    image_filename = f"{base_name}.jpg"
                    image_filepath = os.path.join(self.download_dir, image_filename)
                    if os.path.exists(image_filepath):
                        self.current_image_file = image_filepath
                    self.load_json_file(selected_file)
                    # 显示报纸图片
                    self.show_newspaper_image()
            else:
                messagebox.showinfo("提示", "没有找到JSON文件，请先分析图片")
        except Exception as e:
            messagebox.showerror("错误", f"加载JSON文件失败: {str(e)}")
    
    def load_json_file(self, json_file):
        """加载指定的JSON文件"""
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 提取新闻块数据
            self.video_data = []
            if 'news_blocks' in data:
                for i, news in enumerate(data['news_blocks']):
                    self.video_data.append({
                        "id": i + 1,
                        "title": news.get('title', f"新闻{i+1}"),
                        "content": news.get('content', ""),
                        "position": news.get('position', [0, 0, 0, 0])
                    })
            
            # 更新新闻列表
            self.update_news_list()
            
            self.progress_label.config(text="JSON文件加载成功", fg="#27AE60")
            
        except Exception as e:
            self.progress_label.config(text=f"加载失败: {str(e)}", fg="#E74C3C")
            messagebox.showerror("错误", f"加载JSON文件失败:\n{str(e)}")
    
    def on_news_select(self, event):
        if not self.news_listbox:
            return
            
        selection = self.news_listbox.curselection()
        if selection:
            index = selection[0]
            self.current_news_index = index
            self.show_news_preview(index)
    
    def show_news_preview(self, news_index):
        if 0 <= news_index < len(self.video_data):
            news_item = self.video_data[news_index]
            self.progress_label.config(text=f"显示新闻: {news_item.get('title', '未命名')}")
            # 在图片预览中高亮显示选中的新闻块
            self.highlight_news_block(news_index)
    
    def highlight_news_block(self, news_index):
        """在图片预览中高亮显示选中的新闻块"""
        try:
            if not hasattr(self, 'preview_canvas') or not self.current_image_file:
                return
            
            if not os.path.exists(self.current_image_file):
                return
            
            from PIL import Image, ImageTk
            
            canvas = self.preview_canvas
            image = Image.open(self.current_image_file)
            
            canvas.update_idletasks()
            canvas_width = canvas.winfo_width()
            canvas_height = canvas.winfo_height()
            
            if canvas_width <= 1 or canvas_height <= 1:
                canvas_width = 400
                canvas_height = 500
            
            orig_width, orig_height = image.size
            
            ratio = min(canvas_width / orig_width, canvas_height / orig_height, 1.0)
            new_size = (int(orig_width * ratio), int(orig_height * ratio))
            
            image = image.resize(new_size, Image.Resampling.LANCZOS)
            
            self.preview_photo = ImageTk.PhotoImage(image)
            
            canvas.delete("all")
            
            x_offset = (canvas_width - new_size[0]) // 2
            y_offset = (canvas_height - new_size[1]) // 2
            
            # 绘制图片
            canvas.create_image(x_offset, y_offset, anchor=tk.NW, image=self.preview_photo)
            
            # 直接从video_data中获取新闻块的位置信息
            print(f"从JSON数据中获取 {len(self.video_data)} 个新闻块的位置信息...")
            processed_regions = []
            for i, news in enumerate(self.video_data):
                position = news.get('position', [0, 0, 0, 0])
                if len(position) == 4:
                    x1, y1, x2, y2 = position
                    # 确保坐标在图片范围内
                    x1 = max(0, int(x1))
                    y1 = max(0, int(y1))
                    x2 = min(orig_width, int(x2))
                    y2 = min(orig_height, int(y2))
                    
                    if x2 > x1 and y2 > y1:
                        processed_regions.append((x1, y1, x2, y2))
                        print(f"新闻块 {i+1}: {x1},{y1}-{x2},{y2}")
                    else:
                        print(f"新闻块 {i+1}: 无效坐标，跳过")
                else:
                    print(f"新闻块 {i+1}: 无有效位置信息")
            
            # 颜色列表
            colors = ['#FF0000', '#00FF00', '#0000FF', '#FFFF00', '#FF00FF', '#00FFFF', 
                      '#FF8800', '#8800FF', '#0088FF', '#88FF00']
            
            # 为每个新闻绘制矩形框
            for i, news in enumerate(self.video_data):
                try:
                    if i < len(processed_regions):
                        # 使用处理后的区域
                        region = processed_regions[i]
                        x1, y1, x2, y2 = region
                    else:
                        # 如果区域不够，使用最后一个区域
                        if processed_regions:
                            region = processed_regions[-1]
                            x1, y1, x2, y2 = region
                        else:
                            # 没有区域，使用默认位置
                            x1, y1, x2, y2 = 0, 0, orig_width, orig_height
                    
                    # 缩放坐标到画布大小
                    x1_scaled = x_offset + int(x1 * ratio)
                    y1_scaled = y_offset + int(y1 * ratio)
                    x2_scaled = x_offset + int(x2 * ratio)
                    y2_scaled = y_offset + int(y2 * ratio)
                    
                    # 选中的新闻块用红色粗线显示，其他用细线显示
                    if i == news_index:
                        color = '#FF0000'
                        line_width = 4
                    else:
                        color = colors[i % len(colors)]
                        line_width = 2
                    
                    canvas.create_rectangle(
                        x1_scaled, y1_scaled, x2_scaled, y2_scaled,
                        outline=color, width=line_width, tags=f'news_block_{i}'
                    )
                    
                    # 显示新闻标题
                    label_text = f"{i+1}. {news['title'][:10]}..."
                    label_y = y1_scaled - 20 if y1_scaled - 20 > 0 else y1_scaled
                    canvas.create_text(
                        x1_scaled + 5, label_y,
                        text=label_text,
                        fill=color, font=("Microsoft YaHei", 9, "bold"),
                        anchor=tk.SW
                    )
                except Exception as e:
                    print(f"绘制新闻块 {i} 失败: {e}")
                    
        except Exception as e:
            print(f"高亮显示新闻块失败: {e}")
    
    def show_newspaper_image(self):
        """在视频生成页签显示报纸图片"""
        try:
            if self.current_image_file and os.path.exists(self.current_image_file):
                from PIL import Image, ImageTk
                
                if hasattr(self, 'preview_canvas'):
                    canvas = self.preview_canvas
                    image = Image.open(self.current_image_file)
                    
                    canvas.update_idletasks()
                    canvas_width = canvas.winfo_width()
                    canvas_height = canvas.winfo_height()
                    
                    if canvas_width <= 1 or canvas_height <= 1:
                        canvas_width = 400
                        canvas_height = 500
                    
                    orig_width, orig_height = image.size
                    
                    ratio = min(canvas_width / orig_width, canvas_height / orig_height, 1.0)
                    new_size = (int(orig_width * ratio), int(orig_height * ratio))
                    
                    image = image.resize(new_size, Image.Resampling.LANCZOS)
                    
                    self.preview_photo = ImageTk.PhotoImage(image)
                    
                    canvas.delete("all")
                    
                    x_offset = (canvas_width - new_size[0]) // 2
                    y_offset = (canvas_height - new_size[1]) // 2
                    
                    # 绘制图片
                    canvas.create_image(x_offset, y_offset, anchor=tk.NW, image=self.preview_photo)
                    
                    # 绘制所有新闻块的矩形框
                    colors = ['#FF0000', '#00FF00', '#0000FF', '#FFFF00', '#FF00FF', '#00FFFF', 
                              '#FF8800', '#8800FF', '#0088FF', '#88FF00']
                    
                    for i, news in enumerate(self.video_data):
                        try:
                            x1, y1, x2, y2 = news['position']
                            x1_scaled = x_offset + int(x1 * ratio)
                            y1_scaled = y_offset + int(y1 * ratio)
                            x2_scaled = x_offset + int(x2 * ratio)
                            y2_scaled = y_offset + int(y2 * ratio)
                            
                            color = colors[i % len(colors)]
                            line_width = 2
                            
                            canvas.create_rectangle(
                                x1_scaled, y1_scaled, x2_scaled, y2_scaled,
                                outline=color, width=line_width, tags=f'news_block_{i}'
                            )
                            
                            # 显示新闻标题
                            label_text = f"{i+1}. {news['title'][:10]}..."
                            label_y = y1_scaled - 20 if y1_scaled - 20 > 0 else y1_scaled
                            canvas.create_text(
                                x1_scaled + 5, label_y,
                                text=label_text,
                                fill=color, font=("Microsoft YaHei", 9, "bold"),
                                anchor=tk.SW
                            )
                        except Exception as e:
                            print(f"绘制新闻块 {i} 失败: {e}")
                            
        except Exception as e:
            print(f"显示报纸图片失败: {e}")
    
    def generate_video_data(self):
        """从分析结果中提取视频数据"""
        try:
            # 加载最新的JSON文件
            json_files = []
            if os.path.exists(self.analysis_dir):
                for file in os.listdir(self.analysis_dir):
                    if file.endswith('.json'):
                        file_path = os.path.join(self.analysis_dir, file)
                        json_files.append((file_path, os.path.getmtime(file_path)))
            
            if json_files:
                # 按修改时间排序，取最新的
                json_files.sort(key=lambda x: x[1], reverse=True)
                latest_file = json_files[0][0]
                
                with open(latest_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 提取新闻块数据
                self.video_data = []
                if 'news_blocks' in data:
                    for i, news in enumerate(data['news_blocks']):
                        self.video_data.append({
                            "id": i + 1,
                            "title": news.get('title', f"新闻{i+1}"),
                            "content": news.get('content', ""),
                            "position": news.get('position', [0, 0, 0, 0])
                        })
                
                # 更新新闻列表
                self.update_news_list()
                
                # 保存为视频数据JSON文件
                video_data_file = os.path.join(self.analysis_dir, "video_data.json")
                with open(video_data_file, 'w', encoding='utf-8') as f:
                    json.dump(self.video_data, f, ensure_ascii=False, indent=2)
                
                self.progress_label.config(text="视频数据生成成功", fg="#27AE60")
                messagebox.showinfo("成功", f"视频数据生成成功!\n\n已保存到: {video_data_file}")
                
                return True
            else:
                self.progress_label.config(text="没有找到JSON文件", fg="#E74C3C")
                messagebox.showinfo("提示", "没有找到JSON文件，请先分析图片")
                return False
                
        except Exception as e:
            self.progress_label.config(text=f"生成失败: {str(e)}", fg="#E74C3C")
            messagebox.showerror("错误", f"生成视频数据失败:\n{str(e)}")
            return False
    
    def save_video_data(self):
        """保存视频数据为JSON文件"""
        try:
            if not self.video_data:
                messagebox.showwarning("警告", "没有视频数据可保存")
                return False
            
            # 查找原始JSON文件
            if self.current_image_file:
                base_name = os.path.splitext(os.path.basename(self.current_image_file))[0]
                json_file = os.path.join(self.analysis_dir, f"{base_name}.json")
                
                # 读取原始JSON文件
                if os.path.exists(json_file):
                    with open(json_file, 'r', encoding='utf-8') as f:
                        original_data = json.load(f)
                    
                    # 更新news_blocks
                    original_data['news_blocks'] = self.video_data
                    
                    # 保存回原始JSON文件
                    with open(json_file, 'w', encoding='utf-8') as f:
                        json.dump(original_data, f, ensure_ascii=False, indent=2)
                    
                    self.progress_label.config(text="数据保存成功", fg="#27AE60")
                    messagebox.showinfo("成功", f"视频数据保存成功!\n\n已保存到: {json_file}")
                    return True
            
            # 如果没有找到原始文件，保存为video_data.json
            video_data_file = os.path.join(self.analysis_dir, "video_data.json")
            with open(video_data_file, 'w', encoding='utf-8') as f:
                json.dump(self.video_data, f, ensure_ascii=False, indent=2)
            
            self.progress_label.config(text="数据保存成功", fg="#27AE60")
            messagebox.showinfo("成功", f"视频数据保存成功!\n\n已保存到: {video_data_file}")
            
            return True
            
        except Exception as e:
            self.progress_label.config(text=f"保存失败: {str(e)}", fg="#E74C3C")
            messagebox.showerror("错误", f"保存视频数据失败:\n{str(e)}")
            return False
    
    def generate_video(self):
        """生成视频"""
        try:
            if not self.video_data:
                messagebox.showwarning("警告", "没有视频数据")
                return False
            
            if not self.current_image_file or not os.path.exists(self.current_image_file):
                messagebox.showwarning("警告", "没有选择报纸图片")
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
            
            self.progress_label.config(text="正在生成视频...")
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
                self.progress_label.config(text=f"生成中... {progress}%")
                self.root.update()
            
            # 释放资源
            out.release()
            
            self.progress_label.config(text="视频生成成功", fg="#27AE60")
            messagebox.showinfo("成功", f"视频生成成功!\n\n已保存到: {save_path}")
            
            return True
            
        except Exception as e:
            self.progress_label.config(text=f"生成失败: {str(e)}", fg="#E74C3C")
            messagebox.showerror("错误", f"生成视频失败:\n{str(e)}")
            return False
    
    def update_news_list(self):
        """更新新闻列表"""
        if self.news_listbox:
            self.news_listbox.delete(0, tk.END)
            for i, news in enumerate(self.video_data):
                content_preview = news['content'][:30] + '...' if len(news['content']) > 30 else news['content']
                self.news_listbox.insert(tk.END, f"{i+1}. {news['title']} - {content_preview}")
            if self.current_news_index >= 0 and self.current_news_index < len(self.video_data):
                self.news_listbox.select_set(self.current_news_index)

    def capture_news_screenshots(self):
        """根据新闻矩形框截图并保存"""
        try:
            if not self.video_data:
                messagebox.showwarning("警告", "没有新闻数据")
                return

            if not self.current_image_file or not os.path.exists(self.current_image_file):
                messagebox.showwarning("警告", "请先选择报纸图片")
                return

            # 加载原始图片
            from PIL import Image
            pil_image = Image.open(self.current_image_file)
            orig_width, orig_height = pil_image.size

            # 获取草稿目录路径
            image_filename = os.path.basename(self.current_image_file)
            base_name = os.path.splitext(image_filename)[0]
            today = datetime.datetime.now()
            date_str = today.strftime("%Y%m%d")
            draft_name = f"{base_name}_{date_str}"
            resources_dir = os.path.join(self.jianying_drafts_dir, draft_name, 'Resources')

            # 创建Resources目录
            os.makedirs(resources_dir, exist_ok=True)

            # 遍历所有新闻，截取对应的区域
            screenshot_count = 0
            for i, news in enumerate(self.video_data):
                position = news.get('position', [0, 0, 0, 0])
                if len(position) != 4:
                    print(f"新闻 {i+1}: 无有效位置信息，跳过")
                    continue

                x1, y1, x2, y2 = position

                # 确保坐标有效
                x1 = max(0, int(x1))
                y1 = max(0, int(y1))
                x2 = min(orig_width, int(x2))
                y2 = min(orig_height, int(y2))

                if x2 <= x1 or y2 <= y1:
                    print(f"新闻 {i+1}: 无效坐标 ({x1},{y1},{x2},{y2})，跳过")
                    continue

                # 裁剪图片
                cropped = pil_image.crop((x1, y1, x2, y2))

                # 保存图片，命名格式：P1.jpg, P2.jpg, ...
                screenshot_filename = f"P{i+1}.jpg"
                screenshot_path = os.path.join(resources_dir, screenshot_filename)

                # 保存为JPEG格式
                cropped.save(screenshot_path, 'JPEG', quality=95)
                screenshot_count += 1
                print(f"保存截图: {screenshot_path}")

            if screenshot_count > 0:
                self.progress_label.config(text=f"截图保存成功 ({screenshot_count} 张)", fg="#27AE60")
                messagebox.showinfo("成功", f"截图保存成功！\n\n共保存 {screenshot_count} 张图片\n\n目录: {resources_dir}")
            else:
                messagebox.showwarning("警告", "没有找到有效的新闻区域")

        except Exception as e:
            self.progress_label.config(text=f"截图失败: {str(e)}", fg="#E74C3C")
            messagebox.showerror("错误", f"截图失败:\n{str(e)}")

    def edit_news_inline(self, event):
        """行内编辑新闻（双击编辑）"""
        if not self.news_listbox:
            return
        
        selection = self.news_listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        if index >= len(self.video_data):
            return

        self.current_news_index = index
        news = self.video_data[index]
        
        # 创建编辑窗口
        edit_window = tk.Toplevel(self.root)
        edit_window.title(f"编辑新闻 - {news['title']}")
        edit_window.geometry("500x400")  # 增加窗口高度，确保保存按钮能够显示
        edit_window.transient(self.root)
        edit_window.grab_set()
        
        # 标题编辑
        tk.Label(edit_window, text="标题:", font=("Microsoft YaHei", 10)).pack(pady=5)
        title_entry = tk.Entry(edit_window, font=("Microsoft YaHei", 10), width=60)
        title_entry.pack(pady=5, padx=10)
        title_entry.insert(0, news['title'])
        
        # 内容编辑
        tk.Label(edit_window, text="内容:", font=("Microsoft YaHei", 10)).pack(pady=5)
        content_text = tk.Text(edit_window, font=("Microsoft YaHei", 10), width=60, height=10)
        content_text.pack(pady=5, padx=10)
        content_text.insert(tk.END, news['content'])
        
        def save_edit():
            news['title'] = title_entry.get()
            news['content'] = content_text.get(1.0, tk.END).strip()
            self.update_news_list()
            edit_window.destroy()
        
        # 保存按钮
        save_btn = tk.Button(edit_window, text="保存", font=("Microsoft YaHei", 10), 
                           bg='#27AE60', fg='white', command=save_edit)
        save_btn.pack(pady=10)
    
    def edit_news(self):
        """编辑选中的新闻"""
        if self.current_news_index >= 0 and self.current_news_index < len(self.video_data):
            news = self.video_data[self.current_news_index]
            
            # 打开编辑对话框
            title = simpledialog.askstring("编辑新闻", "请输入新闻标题:", initialvalue=news['title'])
            if title is not None:
                content = simpledialog.askstring("编辑新闻", "请输入新闻内容:", initialvalue=news['content'])
                if content is not None:
                    news['title'] = title
                    news['content'] = content
                    self.update_news_list()
                    messagebox.showinfo("成功", "新闻编辑成功!")
        else:
            messagebox.showinfo("提示", "请先选择要编辑的新闻")
    
    def move_news_up(self):
        """向上移动新闻"""
        if self.current_news_index > 0:
            # 交换位置
            self.video_data[self.current_news_index], self.video_data[self.current_news_index - 1] = \
                self.video_data[self.current_news_index - 1], self.video_data[self.current_news_index]
            
            # 更新ID
            for i, news in enumerate(self.video_data):
                news['id'] = i + 1
            
            self.update_news_list()
            # 重新选中移动后的位置
            if self.news_listbox:
                self.news_listbox.select_set(self.current_news_index - 1)
            self.current_news_index -= 1
            messagebox.showinfo("成功", "新闻已向上移动!")
        else:
            messagebox.showinfo("提示", "已经是第一条新闻")
    
    def move_news_down(self):
        """向下移动新闻"""
        if self.current_news_index < len(self.video_data) - 1:
            # 交换位置
            self.video_data[self.current_news_index], self.video_data[self.current_news_index + 1] = \
                self.video_data[self.current_news_index + 1], self.video_data[self.current_news_index]
            
            # 更新ID
            for i, news in enumerate(self.video_data):
                news['id'] = i + 1
            
            self.update_news_list()
            # 重新选中移动后的位置
            if self.news_listbox:
                self.news_listbox.select_set(self.current_news_index + 1)
            self.current_news_index += 1
            messagebox.showinfo("成功", "新闻已向下移动!")
        else:
            messagebox.showinfo("提示", "已经是最后一条新闻")
    
    def delete_news(self):
        """删除选中的新闻"""
        if self.current_news_index >= 0 and self.current_news_index < len(self.video_data):
            if messagebox.askyesno("确认删除", "确定要删除这条新闻吗?"):
                del self.video_data[self.current_news_index]
                
                # 更新ID
                for i, news in enumerate(self.video_data):
                    news['id'] = i + 1
                
                self.update_news_list()
                self.current_news_index = -1
                messagebox.showinfo("成功", "新闻已删除!")
        else:
            messagebox.showinfo("提示", "请先选择要删除的新闻")
    
    def export_news_images(self):
        """导出新闻图片"""
        try:
            if not self.video_data:
                messagebox.showwarning("警告", "没有新闻数据可导出")
                return False
            
            if not self.current_image_file or not os.path.exists(self.current_image_file):
                messagebox.showwarning("警告", "没有选择报纸图片")
                return False
            
            # 确认导出
            if not messagebox.askyesno("确认导出", f"将导出 {len(self.video_data)} 条新闻图片，是否继续?"):
                return False
            
            # 更新进度
            self.progress_label.config(text="正在导出新闻图片...")
            self.progress_bar['value'] = 0
            self.root.update()
            
            # 创建导出器
            exporter = NewsImageExporter()
            
            # 获取报纸名称
            filename = os.path.basename(self.current_image_file).lower()
            if "wall" in filename or "wsj" in filename:
                newspaper_name = "华尔街日报"
            elif "financial" in filename or "ft" in filename:
                newspaper_name = "金融时报"
            else:
                newspaper_name = "报纸"
            
            # 导出图片
            exported_paths, export_dir = exporter.export_news_images(
                self.current_image_file,
                self.video_data,
                newspaper_name
            )
            
            # 更新进度
            self.progress_bar['value'] = 100
            self.progress_label.config(text=f"导出完成: {len(exported_paths)} 张图片", fg="#27AE60")
            
            # 显示成功消息
            messagebox.showinfo("导出成功", 
                f"成功导出 {len(exported_paths)} 张新闻图片!\n\n"
                f"保存位置: {export_dir}")
            
            return True
            
        except Exception as e:
            self.progress_label.config(text=f"导出失败: {str(e)}", fg="#E74C3C")
            messagebox.showerror("错误", f"导出新闻图片失败:\n{str(e)}")
            return False
    
    def enable_region_selection(self):
        """启用区域选择模式"""
        if hasattr(self, 'preview_canvas') and self.current_image_file:
            try:
                canvas = self.preview_canvas
                
                # 绑定鼠标事件
                canvas.bind("<Button-1>", self.on_canvas_click)
                canvas.bind("<B1-Motion>", self.on_canvas_drag)
                canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
                
                # 存储选择状态
                self.selection_start = None
                self.selection_rect = None
                
                self.progress_label.config(text="区域选择模式: 点击并拖动选择新闻区域", fg="#27AE60")
                
            except Exception as e:
                print(f"启用区域选择失败: {e}")
    
    def on_canvas_click(self, event):
        """鼠标点击事件"""
        if hasattr(self, 'preview_canvas'):
            canvas = self.preview_canvas
            self.selection_start = (event.x, event.y)
            
            # 创建选择矩形
            if self.selection_rect:
                canvas.delete(self.selection_rect)
            self.selection_rect = canvas.create_rectangle(
                event.x, event.y, event.x, event.y,
                outline='#FF0000', width=2, dash=(5, 5)
            )
    
    def on_canvas_drag(self, event):
        """鼠标拖动事件"""
        if hasattr(self, 'preview_canvas') and self.selection_start:
            canvas = self.preview_canvas
            x1, y1 = self.selection_start
            x2, y2 = event.x, event.y
            
            # 更新选择矩形
            canvas.coords(self.selection_rect, min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
    
    def on_canvas_release(self, event):
        """鼠标释放事件"""
        if hasattr(self, 'preview_canvas') and self.selection_start:
            canvas = self.preview_canvas
            x1, y1 = self.selection_start
            x2, y2 = event.x, event.y
            
            # 计算实际坐标
            if hasattr(self, 'current_image_file'):
                try:
                    image = Image.open(self.current_image_file)
                    canvas_width = canvas.winfo_width()
                    canvas_height = canvas.winfo_height()
                    
                    orig_width, orig_height = image.size
                    ratio = min(canvas_width / orig_width, canvas_height / orig_height, 1.0)
                    new_size = (int(orig_width * ratio), int(orig_height * ratio))
                    x_offset = (canvas_width - new_size[0]) // 2
                    y_offset = (canvas_height - new_size[1]) // 2
                    
                    # 转换为原始图片坐标
                    real_x1 = int((min(x1, x2) - x_offset) / ratio)
                    real_y1 = int((min(y1, y2) - y_offset) / ratio)
                    real_x2 = int((max(x1, x2) - x_offset) / ratio)
                    real_y2 = int((max(y1, y2) - y_offset) / ratio)
                    
                    # 确保坐标有效
                    real_x1 = max(0, real_x1)
                    real_y1 = max(0, real_y1)
                    real_x2 = min(image.width, real_x2)
                    real_y2 = min(image.height, real_y2)
                    
                    if real_x2 > real_x1 and real_y2 > real_y1:
                        # 显示选择结果
                        self.progress_label.config(
                            text=f"选择区域: ({real_x1},{real_y1})-({real_x2},{real_y2}) 大小: {real_x2-real_x1}x{real_y2-real_y1}",
                            fg="#27AE60"
                        )
                        
                        # 保存选择的区域
                        self.selected_region = [real_x1, real_y1, real_x2, real_y2]
                        
                        # 测试导出选中区域
                        self.export_selected_region()
                    else:
                        self.progress_label.config(text="无效区域: 请选择更大的区域", fg="#E74C3C")
                        
                except Exception as e:
                    print(f"计算区域坐标失败: {e}")
            
            # 清除选择
            self.selection_start = None
    
    def export_selected_region(self):
        """导出选中的区域"""
        if hasattr(self, 'selected_region') and self.current_image_file:
            try:
                from PIL import Image
                
                # 加载图片
                image = Image.open(self.current_image_file)
                
                # 裁剪选中区域
                x1, y1, x2, y2 = self.selected_region
                selected_image = image.crop((x1, y1, x2, y2))
                
                # 保存图片
                import os
                from datetime import datetime
                
                output_dir = "selected_regions"
                os.makedirs(output_dir, exist_ok=True)
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"selected_{timestamp}.jpg"
                output_path = os.path.join(output_dir, filename)
                
                selected_image.save(output_path, 'JPEG', quality=95)
                
                self.progress_label.config(
                    text=f"选中区域已导出: {filename}",
                    fg="#27AE60"
                )
                
                # 显示成功消息
                messagebox.showinfo("导出成功", f"选中的区域已导出到:\n{output_path}")
                
            except Exception as e:
                print(f"导出选中区域失败: {e}")
                self.progress_label.config(text=f"导出失败: {str(e)}", fg="#E74C3C")
    
    def generate_jianying_draft(self):
        """生成剪映草稿目录"""
        try:
            if not self.current_image_file:
                messagebox.showwarning("警告", "请先选择一张报纸图片")
                return
            
            # 检查是否有新闻数据
            if not self.video_data:
                messagebox.showwarning("警告", "没有新闻数据，请先生成或加载视频数据")
                return
            
            # 获取图片名称（不含扩展名）
            image_filename = os.path.basename(self.current_image_file)
            base_name = os.path.splitext(image_filename)[0]
            
            # 获取当前日期
            today = datetime.datetime.now()
            date_str = today.strftime("%Y%m%d")
            
            # 生成草稿目录名称（图片名+日期）
            draft_name = f"{base_name}_{date_str}"
            
            # 生成草稿目录路径
            draft_dir = os.path.join(self.jianying_drafts_dir, draft_name)
            
            # 检查目录是否已存在
            directory_existed = os.path.exists(draft_dir)
            
            # 如果目录不存在，创建并复制sample文件
            if not directory_existed:
                os.makedirs(draft_dir)
                print(f"创建剪映草稿目录: {draft_dir}")
                
                # 根据报纸类型选择不同的样本目录
                # 金融时报使用sample，华尔街日报使用wsjsample
                if "ft" in base_name.lower():
                    sample_dir_name = "sample"  # 金融时报
                elif "wsj" in base_name.lower():
                    sample_dir_name = "wsjsample"  # 华尔街日报
                else:
                    sample_dir_name = "sample"  # 默认使用sample
                
                sample_dir = os.path.join(self.jianying_drafts_dir, sample_dir_name)
                print(f"使用样本目录: {sample_dir_name}")
                if os.path.exists(sample_dir):
                    # 复制sample目录内的所有文件
                    import shutil
                    for item in os.listdir(sample_dir):
                        source = os.path.join(sample_dir, item)
                        destination = os.path.join(draft_dir, item)
                        if os.path.isfile(source):
                            shutil.copy2(source, destination)
                            print(f"复制文件: {item}")
                        elif os.path.isdir(source):
                            if os.path.exists(destination):
                                shutil.rmtree(destination)
                            shutil.copytree(source, destination)
                            print(f"复制目录: {item}")
                else:
                    print(f"警告: {sample_dir_name}目录不存在: {sample_dir}")
                    messagebox.showwarning("警告", f"{sample_dir_name}目录不存在: {sample_dir}")
            else:
                print(f"目录已存在，跳过复制: {draft_dir}")
            
            # 替换draft_content.json中的文本内容
            draft_content_file = os.path.join(draft_dir, "draft_content.json")
            if os.path.exists(draft_content_file):
                try:
                    with open(draft_content_file, 'r', encoding='utf-8') as f:
                        draft_content = json.load(f)
                    
                    # 输出JSON的顶层键，帮助调试
                    print(f"JSON顶层键: {list(draft_content.keys())}")
                    
                    # 检查是否有texts字段（可能在不同的层级）
                    texts_found = False
                    texts_list = []
                    
                    # 尝试在materials中查找texts
                    if 'materials' in draft_content and isinstance(draft_content.get('materials'), dict):
                        materials = draft_content['materials']
                        if 'texts' in materials and isinstance(materials.get('texts'), list):
                            texts_found = True
                            texts_list = materials['texts']
                            print(f"在materials.texts中找到texts数组，长度: {len(texts_list)}")
                    
                    # 尝试在顶层查找texts
                    if not texts_found and 'texts' in draft_content and isinstance(draft_content['texts'], list):
                        texts_found = True
                        texts_list = draft_content['texts']
                        print(f"在顶层找到texts数组，长度: {len(texts_list)}")
                    
                    if texts_found:
                        # 根据新闻数据替换文本
                        for i, text_item in enumerate(texts_list):
                            if i < len(self.video_data):
                                news = self.video_data[i]
                                # 只使用新闻内容，不添加标题
                                new_text = news.get('content', '')
                                # 清理特殊字符：移除换行符，替换可能导致JSON问题的字符
                                new_text = new_text.replace('\n', ' ').replace('\r', ' ').replace('\\', '\\\\')
                                
                                # content字段是一个JSON字符串，需要解析后修改text字段
                                content_str = text_item.get('content', '')
                                if content_str:
                                    try:
                                        # 解析content中的JSON
                                        content_obj = json.loads(content_str)
                                        # 输出替换前的text
                                        old_text = content_obj.get('text', '')
                                        print(f"替换前第{i+1}条文本: {old_text[:50]}...")
                                        # 替换text字段
                                        content_obj['text'] = new_text
                                        # 重新序列化为字符串
                                        text_item['content'] = json.dumps(content_obj, ensure_ascii=False)
                                        print(f"替换后第{i+1}条文本: {new_text[:50]}...")
                                    except json.JSONDecodeError:
                                        # 如果解析失败，直接替换整个content
                                        print(f"替换前第{i+1}条content: {content_str[:50]}...")
                                        text_item['content'] = new_text
                                        print(f"替换后第{i+1}条content: {new_text[:50]}...")
                                else:
                                    text_item['content'] = new_text
                                    print(f"第{i+1}条content为空，设置为: {new_text[:50]}...")
                        
                        # 保存修改后的JSON文件
                        with open(draft_content_file, 'w', encoding='utf-8') as f:
                            json.dump(draft_content, f, ensure_ascii=False, indent=2)
                        
                        print(f"文本内容替换完成")
                        
                        if directory_existed:
                            messagebox.showinfo("成功", f"剪映草稿文本已更新!\n\n目录: {draft_dir}")
                        else:
                            messagebox.showinfo("成功", f"剪映草稿目录生成完成!\n\n目录: {draft_dir}")
                    else:
                        print(f"警告: draft_content.json中没有找到texts字段")
                        print(f"JSON结构: {str(draft_content)[:500]}...")  # 输出部分JSON结构帮助调试
                        messagebox.showwarning("警告", f"draft_content.json中没有找到texts字段")
                except Exception as e:
                    print(f"替换文本内容失败: {str(e)}")
                    messagebox.showwarning("警告", f"替换文本内容失败: {str(e)}")
            else:
                print(f"警告: draft_content.json文件不存在: {draft_content_file}")
                messagebox.showwarning("警告", f"draft_content.json文件不存在")
                
        except Exception as e:
            print(f"生成剪映草稿目录失败: {str(e)}")
            messagebox.showerror("错误", f"生成剪映草稿目录失败: {str(e)}")
    
    def sync_tts_and_subtitles(self, draft_content, news_data=None):
        """
        同步TTS音频和字幕的时序
        
        功能:
        1. 重新排布TTS音频片段的时序，每个音频之间保持0.8秒间隔
        2. 同步调整字幕片段的起止时间和时长，使其与TTS音频对齐
        3. 将贴纸定位到对应新闻矩形框的左下角
        
        Args:
            draft_content: 剪映草稿JSON数据
            news_data: 新闻数据列表，包含新闻的位置信息
            
        Returns:
            修改后的draft_content
        """
        import copy
        
        print("=" * 60)
        print("开始同步TTS音频和字幕时序...")
        print("=" * 60)
        
        # 深拷贝，避免修改原始数据
        data = copy.deepcopy(draft_content)
        
        try:
            # 获取materials中的audios
            materials = data.get('materials', {})
            audios = materials.get('audios', [])
            print(f"[步骤1] 从materials中获取到 {len(audios)} 个音频素材")
            
            # 查找所有type为"text_to_audio"的TTS音频素材
            tts_audios = []
            for idx, audio in enumerate(audios):
                audio_type = audio.get('type')
                if audio_type == 'text_to_audio':
                    tts_info = {
                        'id': audio.get('id'),
                        'resource_id': audio.get('resource_id'),
                        'duration': audio.get('duration', 0),
                        'text_id': audio.get('text_id')
                    }
                    tts_audios.append(tts_info)
                    print(f"  [TTS-{len(tts_audios)}] ID={tts_info['id']}, resource_id={tts_info['resource_id']}, text_id={tts_info['text_id']}, duration={tts_info['duration']}")
            
            if not tts_audios:
                print("[错误] 未找到text_to_audio类型的音频素材")
                return data
            
            print(f"[步骤2] 找到 {len(tts_audios)} 个TTS音频素材")
            
            # 获取tracks
            tracks = data.get('tracks', [])
            print(f"[步骤3] 获取到 {len(tracks)} 个轨道")
            
            # 查找所有文本轨道(type: "text")、所有音频轨道(type: "audio")和所有贴纸轨道(type: "sticker")
            text_tracks = []
            audio_tracks = []
            sticker_tracks = []
            
            for idx, track in enumerate(tracks):
                track_type = track.get('type')
                seg_count = len(track.get('segments', []))
                print(f"  [轨道-{idx+1}] type={track_type}, segments={seg_count}")
                if track_type == 'text':
                    text_tracks.append(track)
                elif track_type == 'audio':
                    audio_tracks.append(track)
                elif track_type == 'sticker':
                    sticker_tracks.append(track)
            
            if not text_tracks:
                print("[错误] 未找到文本轨道(type: text)")
                return data
            print(f"[步骤4] 找到 {len(text_tracks)} 个文本轨道")
            
            if not audio_tracks:
                print("[错误] 未找到音频轨道(type: audio)")
                return data
            print(f"[步骤5] 找到 {len(audio_tracks)} 个音频轨道")
            
            print(f"[步骤6] 找到 {len(sticker_tracks)} 个贴纸轨道")
            
            # 获取所有文本片段（从所有文本轨道中）
            text_segments = []
            print(f"[步骤6] 从所有文本轨道中获取文本片段:")
            for track_idx, track in enumerate(text_tracks):
                track_segments = track.get('segments', [])
                print(f"  [文本轨道-{track_idx+1}] 包含 {len(track_segments)} 个片段")
                for seg_idx, seg in enumerate(track_segments):
                    seg_id = seg.get('id')
                    print(f"    [片段-{seg_idx+1}] id={seg_id}")
                text_segments.extend(track_segments)
            print(f"  总计获取到 {len(text_segments)} 个文本片段")
            
            # 建立text_id到文本片段的映射
            text_segment_map = {}
            print(f"[步骤7] 建立text_id到文本片段的映射:")
            print(f"  TTS音频的text_id列表: {[tts.get('text_id') for tts in tts_audios]}")
            for idx, segment in enumerate(text_segments):
                seg_id = segment.get('id')
                timerange = segment.get('target_timerange', {})
                start = timerange.get('start', 0)
                duration = timerange.get('duration', 0)
                text_to_audio_ids = segment.get('text_to_audio_ids', [])
                material_id = segment.get('material_id')
                # 输出文本片段的所有关键字段
                print(f"  [文本-{idx+1}] id={seg_id}, start={start}, duration={duration}, text_to_audio_ids={text_to_audio_ids}, material_id={material_id}")
                if seg_id:
                    text_segment_map[seg_id] = segment
            print(f"  共建立 {len(text_segment_map)} 个文本片段映射")
            print(f"  文本映射中的id列表: {list(text_segment_map.keys())}")
            
            # 获取所有音频片段（从所有音频轨道中）
            audio_segments = []
            for track in audio_tracks:
                audio_segments.extend(track.get('segments', []))
            print(f"[步骤8] 从所有音频轨道中获取到 {len(audio_segments)} 个音频片段")
            
            # 获取所有贴纸片段（从所有贴纸轨道中）
            sticker_segments = []
            for track in sticker_tracks:
                sticker_segments.extend(track.get('segments', []))
            print(f"[步骤9] 从所有贴纸轨道中获取到 {len(sticker_segments)} 个贴纸片段")
            
            # 建立material_id到音频片段的映射（一个material_id可能对应多个片段）
            audio_segment_map = {}
            print(f"[步骤9] 建立material_id到音频片段的映射:")
            print(f"  TTS音频的resource_id列表: {[tts.get('resource_id') for tts in tts_audios]}")
            for idx, segment in enumerate(audio_segments):
                material_id = segment.get('material_id')
                timerange = segment.get('target_timerange', {})
                start = timerange.get('start', 0)
                duration = timerange.get('duration', 0)
                # 输出音频片段的所有关键字段
                print(f"  [音频-{idx+1}] material_id={material_id}, start={start}, duration={duration}")
                if material_id:
                    # 使用列表存储，因为一个material_id可能对应多个片段
                    if material_id not in audio_segment_map:
                        audio_segment_map[material_id] = []
                    audio_segment_map[material_id].append(segment)
            print(f"  共建立 {len(audio_segment_map)} 个material_id映射")
            print(f"  音频映射中的material_id列表: {list(audio_segment_map.keys())}")
            
            # 按时间顺序排序贴纸片段（用于与文本片段对应）
            print(f"[步骤12] 按时间顺序排序贴纸片段:")
            sorted_sticker_segments = []
            for idx, segment in enumerate(sticker_segments):
                material_id = segment.get('material_id')
                timerange = segment.get('target_timerange', {})
                start = timerange.get('start', 0)
                duration = timerange.get('duration', 0)
                # 输出贴纸片段的所有关键字段
                print(f"  [贴纸-{idx+1}] material_id={material_id}, start={start}, duration={duration}")
                sorted_sticker_segments.append({
                    'segment': segment,
                    'start': start
                })
            
            # 按start时间排序
            sorted_sticker_segments.sort(key=lambda x: x['start'])
            print(f"  排序后的贴纸片段顺序:")
            for idx, item in enumerate(sorted_sticker_segments):
                segment = item['segment']
                material_id = segment.get('material_id')
                start = item['start']
                print(f"  [排序-{idx+1}] material_id={material_id}, start={start}")
            print(f"  共找到 {len(sorted_sticker_segments)} 个贴纸片段")
                
                # 建立material_id到贴纸片段的映射（一个material_id可能对应多个片段）
            sticker_segment_map = {}
            print(f"  建立material_id到贴纸片段的映射:")
            for item in sorted_sticker_segments:
                segment = item['segment']
                material_id = segment.get('material_id')
                if material_id:
                    if material_id not in sticker_segment_map:
                        sticker_segment_map[material_id] = []
                    sticker_segment_map[material_id].append(segment)
            print(f"  共建立 {len(sticker_segment_map)} 个material_id映射")
            print(f"  贴纸映射中的material_id列表: {list(sticker_segment_map.keys())}")
            
            # 按原始出现顺序排序TTS音频
            # 根据文本片段的start时间排序
            print(f"[步骤10] 按原始出现顺序排序TTS音频:")
            tts_with_order = []
            for idx, tts in enumerate(tts_audios):
                text_id = tts.get('text_id')
                if text_id and text_id in text_segment_map:
                    text_seg = text_segment_map[text_id]
                    timerange = text_seg.get('target_timerange', {})
                    start_time = timerange.get('start', 0)
                    tts_with_order.append({
                        **tts,
                        'original_start': start_time
                    })
                    print(f"  [TTS-{idx+1}] text_id={text_id}, original_start={start_time}")
                else:
                    # 如果找不到对应的文本片段，使用0作为起始时间
                    tts_with_order.append({
                        **tts,
                        'original_start': 0
                    })
                    print(f"  [TTS-{idx+1}] text_id={text_id}, 未找到对应文本片段，使用start=0")
            
            # 按原始起始时间排序
            tts_with_order.sort(key=lambda x: x['original_start'])
            print(f"[步骤11] 排序后的TTS音频顺序:")
            for idx, tts in enumerate(tts_with_order):
                print(f"  [排序-{idx+1}] id={tts['id']}, text_id={tts['text_id']}, original_start={tts['original_start']}")
            
            # 重新计算TTS音频的时序
            # 间隔: 0.8秒 = 800,000微秒
            gap_us = 800000  # 微秒
            current_time = 0
            
            print(f"[步骤12] 重新计算TTS音频时序 (间隔={gap_us}微秒=0.8秒):")
            
            # 存储新的时间信息
            new_timing = []
            for idx, tts in enumerate(tts_with_order):
                duration = tts.get('duration', 0)
                new_timing.append({
                    'id': tts.get('id'),
                    'resource_id': tts.get('resource_id'),
                    'text_id': tts.get('text_id'),
                    'new_start': current_time,
                    'new_duration': duration
                })
                print(f"  [计算-{idx+1}] id={tts.get('id')}, new_start={current_time}, duration={duration}")
                # 下一个音频的起始时间 = 当前起始时间 + 当前时长 + 间隔
                current_time += duration + gap_us
            
            print(f"[步骤13] 共重新排布 {len(new_timing)} 个TTS音频片段")
            
            # 计算视频素材的起始和结束时间
            video_start_time = current_time  # 最后一个音频结束后+0.8秒
            print(f"[步骤17] 计算视频素材时间: start={video_start_time}")
            print(f"  最后一个音频的结束时间: {current_time - gap_us} (不包含0.8秒间隔)")
            print(f"  视频素材开始时间: {video_start_time} (包含0.8秒间隔)")
            
            # 更新音频轨道中的TTS片段
            print(f"[步骤14] 更新音频轨道中的TTS片段:")
            print(f"  音频映射中的material_id列表: {list(audio_segment_map.keys())}")
            print(f"  使用TTS音频的id进行匹配")
            update_count = 0
            for idx, timing in enumerate(new_timing):
                # 使用TTS音频的id（不是resource_id）来匹配音频片段的material_id
                tts_id = timing.get('id')
                print(f"  [处理-{idx+1}] 查找tts_id={tts_id}")
                if tts_id and tts_id in audio_segment_map:
                    # 获取该material_id对应的所有音频片段
                    audio_segs = audio_segment_map[tts_id]
                    print(f"    找到 {len(audio_segs)} 个匹配片段")
                    # 如果只有一个片段，直接更新；如果有多个，按顺序更新
                    if len(audio_segs) == 1:
                        audio_seg = audio_segs[0]
                        old_start = audio_seg.get('target_timerange', {}).get('start', 0)
                        old_duration = audio_seg.get('target_timerange', {}).get('duration', 0)
                        # 更新target_timerange
                        if 'target_timerange' not in audio_seg:
                            audio_seg['target_timerange'] = {}
                        audio_seg['target_timerange']['start'] = timing.get('new_start', 0)
                        audio_seg['target_timerange']['duration'] = timing.get('new_duration', 0)
                        update_count += 1
                        print(f"  [音频更新-{update_count}] tts_id={tts_id}")
                        print(f"    旧: start={old_start}, duration={old_duration}")
                        print(f"    新: start={timing.get('new_start')}, duration={timing.get('new_duration')}")
                    elif len(audio_segs) > 1:
                        # 如果有多个片段，需要找到与当前TTS匹配的片段
                        # 这里简化处理：更新所有匹配的片段
                        for seg_idx, audio_seg in enumerate(audio_segs):
                            old_start = audio_seg.get('target_timerange', {}).get('start', 0)
                            old_duration = audio_seg.get('target_timerange', {}).get('duration', 0)
                            if 'target_timerange' not in audio_seg:
                                audio_seg['target_timerange'] = {}
                            audio_seg['target_timerange']['start'] = timing.get('new_start', 0)
                            audio_seg['target_timerange']['duration'] = timing.get('new_duration', 0)
                            update_count += 1
                            print(f"  [音频更新-{update_count}] tts_id={tts_id}, 片段{seg_idx+1}/{len(audio_segs)}")
                            print(f"    旧: start={old_start}, duration={old_duration}")
                            print(f"    新: start={timing.get('new_start')}, duration={timing.get('new_duration')}")
                else:
                    print(f"  [音频跳过-{idx+1}] tts_id={tts_id} 未在音频片段映射中找到")
                    print(f"    可用的material_id: {list(audio_segment_map.keys())}")
            print(f"  共更新 {update_count} 个音频片段")
            
            # 更新文本轨道中的字幕片段
            print(f"[步骤15] 更新文本轨道中的字幕片段:")
            print(f"  文本映射中的id列表: {list(text_segment_map.keys())}")
            print(f"  使用TTS音频的text_id匹配文本片段的material_id")
            
            # 建立material_id到文本片段的映射
            material_to_text_map = {}
            for seg_id, seg in text_segment_map.items():
                material_id = seg.get('material_id')
                if material_id:
                    material_to_text_map[material_id] = seg
            print(f"  建立material_id到文本片段的映射: {list(material_to_text_map.keys())}")
            
            # 存储文本片段的位置信息，用于贴纸定位
            text_position_map = {}
            update_count = 0
            for idx, timing in enumerate(new_timing):
                # 使用TTS音频的text_id（不是id）来匹配文本片段的material_id
                text_id = timing.get('text_id')
                print(f"  [处理-{idx+1}] 查找text_id={text_id}（匹配文本片段的material_id）")
                if text_id and text_id in material_to_text_map:
                    text_seg = material_to_text_map[text_id]
                    old_start = text_seg.get('target_timerange', {}).get('start', 0)
                    old_duration = text_seg.get('target_timerange', {}).get('duration', 0)
                    old_material_id = text_seg.get('material_id')
                    # 更新target_timerange
                    if 'target_timerange' not in text_seg:
                        text_seg['target_timerange'] = {}
                    text_seg['target_timerange']['start'] = timing.get('new_start', 0)
                    text_seg['target_timerange']['duration'] = timing.get('new_duration', 0)
                    
                    # 确保material_id和text_to_audio_ids与TTS音频素材的id一致
                    tts_id = timing.get('id')
                    if 'text_to_audio_ids' not in text_seg:
                        text_seg['text_to_audio_ids'] = []
                    if tts_id not in text_seg['text_to_audio_ids']:
                        text_seg['text_to_audio_ids'].append(tts_id)
                    
                    # 存储文本片段的位置信息
                    position = text_seg.get('position', {})
                    size = text_seg.get('size', {})
                    text_position_map[idx] = {
                        'position': position,
                        'size': size
                    }
                    print(f"  文本片段位置: position={position}, size={size}")
                    
                    update_count += 1
                    print(f"  [字幕更新-{update_count}] text_id={text_id}")
                    print(f"    旧: start={old_start}, duration={old_duration}, material_id={old_material_id}")
                    print(f"    新: start={timing.get('new_start')}, duration={timing.get('new_duration')}, material_id={tts_id}")
                else:
                    print(f"  [字幕跳过-{idx+1}] text_id={text_id} 未在material_id映射中找到")
                    print(f"    可用的material_id: {list(material_to_text_map.keys())}")
            print(f"  共更新 {update_count} 个字幕片段")
            
            # 收集所有贴纸片段并按时间排序
            all_sticker_segments = []
            for track in sticker_tracks:
                for seg in track.get('segments', []):
                    timerange = seg.get('target_timerange', {})
                    start = timerange.get('start', 0)
                    all_sticker_segments.append({
                        'segment': seg,
                        'start': start
                    })
            
            # 按开始时间排序
            sorted_sticker_segments = sorted(all_sticker_segments, key=lambda x: x['start'])
            print(f"[步骤16] 收集并排序贴纸片段: 共 {len(sorted_sticker_segments)} 个")
            
            # 更新贴纸轨道中的贴纸片段（与文本片段对齐，按时间顺序对应）
            print(f"[步骤19] 更新贴纸轨道中的贴纸片段:")
            print(f"  按时间顺序与TTS音频对应，并定位到新闻矩形框左下角")
            
            update_count = 0
            for idx, timing in enumerate(new_timing):
                if idx < len(sorted_sticker_segments):
                    # 按顺序对应：第1个TTS音频对应第1个贴纸片段，以此类推
                    sticker_item = sorted_sticker_segments[idx]
                    sticker_seg = sticker_item['segment']
                    material_id = sticker_seg.get('material_id')
                    old_start = sticker_seg.get('target_timerange', {}).get('start', 0)
                    old_duration = sticker_seg.get('target_timerange', {}).get('duration', 0)
                    
                    # 更新target_timerange，与对应TTS音频保持一致
                    if 'target_timerange' not in sticker_seg:
                        sticker_seg['target_timerange'] = {}
                    sticker_seg['target_timerange']['start'] = timing.get('new_start', 0)
                    sticker_seg['target_timerange']['duration'] = timing.get('new_duration', 0)
                    
                    # 定位贴纸到对应新闻矩形框的左下角
                    if news_data and idx < len(news_data):
                        news = news_data[idx]
                        # 新闻位置格式: [x1, y1, x2, y2]
                        position = news.get('position', [0, 0, 0, 0])
                        if len(position) == 4:
                            x1, y1, x2, y2 = position
                            # 计算左下角坐标 (x1, y2)
                            sticker_x = x1
                            sticker_y = y2
                            
                            # 更新贴纸位置
                            if 'position' not in sticker_seg:
                                sticker_seg['position'] = {}
                            sticker_seg['position']['x'] = sticker_x
                            sticker_seg['position']['y'] = sticker_y
                            
                            print(f"  贴纸定位: 新闻矩形框左下角 ({sticker_x}, {sticker_y})")
                            print(f"  新闻位置: {position}")
                    
                    update_count += 1
                    print(f"  [贴纸更新-{update_count}] 顺序对应 TTS-{idx+1} -> 贴纸-{idx+1}")
                    print(f"    贴纸material_id={material_id}")
                    print(f"    旧: start={old_start}, duration={old_duration}")
                    print(f"    新: start={timing.get('new_start')}, duration={timing.get('new_duration')}")
                else:
                    print(f"  [贴纸跳过-{idx+1}] 没有更多贴纸片段可用")
            print(f"  共更新 {update_count} 个贴纸片段")
            
            # 处理视频素材
            print("=" * 60)
            print("开始处理视频素材...")
            print("=" * 60)
            
            # 1. 找到 local_material_id 为 "adfc1f13-688a-4cce-8472-3b31aa079b30" 的素材
            video_material_local_id = "adfc1f13-688a-4cce-8472-3b31aa079b30"
            target_video_id = "E42351AB-2F8B-4159-9C19-7CD524DD53C8"
            
            # 查找视频素材的duration和id
            video_duration = 0
            video_material_id = None
            materials = data.get('materials', {})
            videos = materials.get('videos', [])
            print(f"[步骤20] 查找视频素材: local_material_id={video_material_local_id}")
            for video in videos:
                if video.get('local_material_id') == video_material_local_id:
                    video_duration = video.get('duration', 0)
                    video_material_id = video.get('id')
                    print(f"  找到视频素材，id={video_material_id}, duration={video_duration}")
                    break
            
            if video_duration > 0 and video_material_id:
                # 2. 计算视频素材的结束时间
                video_end_time = video_start_time + video_duration
                print(f"[步骤21] 视频素材时间: start={video_start_time}, duration={video_duration}, end={video_end_time}")
                
                # 3. 查找并更新视频轨道中的视频片段
                print(f"[步骤22] 查找并更新视频片段: id={target_video_id}")
                video_track_updated = False
                for track in data.get('tracks', []):
                    if track.get('type') == 'video':
                        segments = track.get('segments', [])
                        for segment in segments:
                            if segment.get('id') == target_video_id:
                                # 更新视频片段的时间，使其与视频素材同时结束
                                old_start = segment.get('target_timerange', {}).get('start', 0)
                                old_duration = segment.get('target_timerange', {}).get('duration', 0)
                                old_end = old_start + old_duration
                                
                                # 计算视频片段的新起始时间（应该与视频素材同时结束）
                                new_video_start = video_end_time - old_duration
                                new_end = new_video_start + old_duration
                                
                                if 'target_timerange' not in segment:
                                    segment['target_timerange'] = {}
                                segment['target_timerange']['start'] = new_video_start
                                
                                print(f"  [视频片段更新] id={target_video_id}")
                                print(f"    旧位置: start={old_start}, duration={old_duration}, end={old_end}")
                                print(f"    新位置: start={new_video_start}, duration={old_duration}, end={new_end}")
                                print(f"    视频素材结束时间: {video_end_time}")
                                print(f"    时间同步: {abs(new_end - video_end_time) < 1000} (误差小于1ms)")
                                video_track_updated = True
                                break
                    if video_track_updated:
                        break
                
                # 4. 查找并更新视频素材的时间
                print(f"[步骤23] 查找并更新视频素材片段")
                video_material_updated = False
                
                # 检查所有类型的轨道，不仅仅是视频轨道
                for track_idx, track in enumerate(data.get('tracks', [])):
                    track_type = track.get('type')
                    segments = track.get('segments', [])
                    print(f"  轨道 {track_idx+1} (类型: {track_type}) 包含 {len(segments)} 个片段")
                    
                    for seg_idx, segment in enumerate(segments):
                        seg_id = segment.get('id')
                        seg_material_id = segment.get('material_id')
                        seg_timerange = segment.get('target_timerange', {})
                        seg_start = seg_timerange.get('start', 0)
                        seg_duration = seg_timerange.get('duration', 0)
                        print(f"    片段 {seg_idx+1}: id={seg_id}, material_id={seg_material_id}, start={seg_start}, duration={seg_duration}")
                        
                        # 尝试多种匹配方式
                        if seg_material_id == video_material_id:
                            old_start = seg_start
                            old_duration = seg_duration
                            old_end = old_start + old_duration
                            new_end = video_start_time + video_duration
                            
                            if 'target_timerange' not in segment:
                                segment['target_timerange'] = {}
                            segment['target_timerange']['start'] = video_start_time
                            segment['target_timerange']['duration'] = video_duration
                            
                            print(f"  [视频素材更新] material_id={video_material_id}")
                            print(f"    旧位置: start={old_start}, duration={old_duration}, end={old_end}")
                            print(f"    新位置: start={video_start_time}, duration={video_duration}, end={new_end}")
                            print(f"    计算的开始时间: {video_start_time}")
                            print(f"    计算的结束时间: {new_end}")
                            video_material_updated = True
                            break
                    if video_material_updated:
                        break
                
                if not video_material_updated:
                    print(f"[警告] 未找到视频素材片段: material_id={video_material_id}")
                    print("  尝试查找所有轨道中的所有片段...")
                    for track_idx, track in enumerate(data.get('tracks', [])):
                        track_type = track.get('type')
                        segments = track.get('segments', [])
                        print(f"  轨道 {track_idx+1} (类型: {track_type}):")
                        for segment in segments:
                            print(f"    片段: id={segment.get('id')}, material_id={segment.get('material_id')}")
                    
                    # 检查materials中的videos
                    print("  检查materials中的videos...")
                    materials = data.get('materials', {})
                    videos = materials.get('videos', [])
                    print(f"  找到 {len(videos)} 个视频素材:")
                    for idx, video in enumerate(videos):
                        print(f"    视频 {idx+1}: local_material_id={video.get('local_material_id')}, id={video.get('id')}")
            else:
                if not video_material_id:
                    print(f"[错误] 未找到视频素材: local_material_id={video_material_local_id}")
                else:
                    print(f"[错误] 视频素材duration为0: local_material_id={video_material_local_id}")
            
            print("=" * 60)
            print("TTS音频、字幕、贴纸和视频素材时序同步完成")
            print("=" * 60)
            return data
            
        except Exception as e:
            print(f"同步TTS和字幕时序失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return data
    
    def process_jianying_draft_timing(self):
        """
        处理剪映草稿文件的TTS和字幕时序
        在生成剪映草稿后调用此方法
        """
        try:
            if not self.current_image_file:
                messagebox.showwarning("警告", "请先选择一张报纸图片")
                return
            
            # 检查是否有新闻数据
            if not self.video_data:
                messagebox.showwarning("警告", "没有新闻数据，请先生成或加载视频数据")
                return
            
            # 获取图片名称（不含扩展名）
            image_filename = os.path.basename(self.current_image_file)
            base_name = os.path.splitext(image_filename)[0]
            
            # 获取当前日期
            today = datetime.datetime.now()
            date_str = today.strftime("%Y%m%d")
            
            # 生成草稿目录名称（图片名+日期）
            draft_name = f"{base_name}_{date_str}"
            
            # 生成草稿目录路径
            draft_dir = os.path.join(self.jianying_drafts_dir, draft_name)
            
            # 检查目录是否存在
            if not os.path.exists(draft_dir):
                messagebox.showwarning("警告", f"剪映草稿目录不存在: {draft_dir}\n请先点击'剪映草稿'按钮生成草稿")
                return
            
            # 读取draft_content.json文件
            draft_content_file = os.path.join(draft_dir, "draft_content.json")
            if not os.path.exists(draft_content_file):
                messagebox.showwarning("警告", f"draft_content.json文件不存在: {draft_content_file}")
                return
            
            with open(draft_content_file, 'r', encoding='utf-8') as f:
                draft_content = json.load(f)
            
            # 同步TTS和字幕时序，传递新闻位置信息
            updated_content = self.sync_tts_and_subtitles(draft_content, self.video_data)
            
            # 保存修改后的JSON文件
            with open(draft_content_file, 'w', encoding='utf-8') as f:
                json.dump(updated_content, f, ensure_ascii=False, indent=2)
            
            print(f"剪映草稿时序处理完成: {draft_content_file}")
            messagebox.showinfo("成功", f"剪映草稿时序处理完成!\n\nTTS音频和字幕已同步对齐\n目录: {draft_dir}")
            
        except Exception as e:
            print(f"处理剪映草稿时序失败: {str(e)}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("错误", f"处理剪映草稿时序失败: {str(e)}")