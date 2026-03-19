# UI helpers module
# UI辅助模块

import os
import tkinter as tk
from PIL import Image, ImageTk, ImageDraw, ImageFont
class UIHelpers:
    def __init__(self, config, progress_label_widget=None, progress_bar_widget=None, root=None):
        self.preview_photo = None
        self.selection_start = None
        self.selection_rect = None
        self.selected_region = None
    
    def set_preview_canvas(self, canvas):
        self.preview_canvas = canvas
    
    def on_news_select(self, event):
        """新闻选择事件"""
        # 这个方法现在由on_news_textbox_click处理
        pass
    
    def show_news_preview(self, news_index):
        if 0 <= news_index < len(self.video_data):
            news_item = self.video_data[news_index]
            self.update_progress(f"显示新闻: {news_item.get('title', '未命名')}")
            # 在图片预览中高亮显示选中的新闻块
            self.highlight_news_block(news_index)
    
    def highlight_news_block(self, news_index):
        """在图片预览中高亮显示选中的新闻块"""
        try:
            if not hasattr(self, 'preview_canvas') or not self.current_image_file:
                return
            
            if not os.path.exists(self.current_image_file):
                return
            
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
            
            # 绑定鼠标事件
            canvas.bind("<Button-1>", lambda e: self.on_preview_click(e, canvas, orig_width, orig_height, ratio, x_offset, y_offset))
            canvas.bind("<B1-Motion>", lambda e: self.on_preview_drag(e, canvas, orig_width, orig_height, ratio, x_offset, y_offset))
            canvas.bind("<ButtonRelease-1>", self.on_preview_release)
            
            # 存储当前状态
            self.drag_data = {
                'is_dragging': False,
                'is_resizing': False,
                'drag_type': None,  # 'move', 'resize'
                'start_x': 0,
                'start_y': 0,
                'news_index': -1,
                'handle_index': -1,
                'original_position': [],
                'original_size': ()
            }
            
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
                    
                    # 创建矩形框
                    rect_id = canvas.create_rectangle(
                        x1_scaled, y1_scaled, x2_scaled, y2_scaled,
                        outline=color, width=line_width, tags=f'news_block_{i}'
                    )
                    
                    # 添加调整大小的控制点
                    handles = [
                        (x1_scaled, y1_scaled),  # 左上
                        (x2_scaled, y1_scaled),  # 右上
                        (x1_scaled, y2_scaled),  # 左下
                        (x2_scaled, y2_scaled),  # 右下
                        ((x1_scaled + x2_scaled) // 2, y1_scaled),  # 上中
                        ((x1_scaled + x2_scaled) // 2, y2_scaled),  # 下中
                        (x1_scaled, (y1_scaled + y2_scaled) // 2),  # 左中
                        (x2_scaled, (y1_scaled + y2_scaled) // 2)   # 右中
                    ]
                    
                    for j, (hx, hy) in enumerate(handles):
                        handle_size = 8  # 增大控制点大小
                        canvas.create_oval(
                            hx-handle_size, hy-handle_size, hx+handle_size, hy+handle_size,
                            fill='#FF0000' if i == news_index else '#00FF00',
                            outline='white', width=1,
                            tags=f'handle_{i}_{j}'
                        )
                    
                    # 显示新闻标题
                    label_text = f"{i+1}. {news['title'][:10]}..."
                    label_y = y1_scaled - 20 if y1_scaled - 20 > 0 else y1_scaled
                    canvas.create_text(
                        x1_scaled + 5, label_y,
                        text=label_text,
                        fill=color, font=("Microsoft YaHei", 9, "bold"),
                        anchor=tk.SW,
                        tags=f'label_{i}'
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
                    
                    # 绑定鼠标事件
                    canvas.bind("<Button-1>", lambda e: self.on_preview_click(e, canvas, orig_width, orig_height, ratio, x_offset, y_offset))
                    canvas.bind("<B1-Motion>", lambda e: self.on_preview_drag(e, canvas, orig_width, orig_height, ratio, x_offset, y_offset))
                    canvas.bind("<ButtonRelease-1>", self.on_preview_release)
                    
                    # 存储当前状态
                    self.drag_data = {
                        'is_dragging': False,
                        'is_resizing': False,
                        'drag_type': None,
                        'start_x': 0,
                        'start_y': 0,
                        'news_index': -1,
                        'handle_index': -1,
                        'original_position': [],
                        'original_size': ()
                    }
                    
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
                            
                            # 添加调整大小的控制点
                            handles = [
                                (x1_scaled, y1_scaled),  # 左上
                                (x2_scaled, y1_scaled),  # 右上
                                (x1_scaled, y2_scaled),  # 左下
                                (x2_scaled, y2_scaled),  # 右下
                                ((x1_scaled + x2_scaled) // 2, y1_scaled),  # 上中
                                ((x1_scaled + x2_scaled) // 2, y2_scaled),  # 下中
                                (x1_scaled, (y1_scaled + y2_scaled) // 2),  # 左中
                                (x2_scaled, (y1_scaled + y2_scaled) // 2)   # 右中
                            ]
                            
                            for j, (hx, hy) in enumerate(handles):
                                handle_size = 8  # 增大控制点大小
                                canvas.create_oval(
                                    hx-handle_size, hy-handle_size, hx+handle_size, hy+handle_size,
                                    fill=color,
                                    outline='white', width=1,
                                    tags=f'handle_{i}_{j}'
                                )
                            
                            # 显示新闻标题
                            label_text = f"{i+1}. {news['title'][:10]}..."
                            label_y = y1_scaled - 20 if y1_scaled - 20 > 0 else y1_scaled
                            canvas.create_text(
                                x1_scaled + 5, label_y,
                                text=label_text,
                                fill=color, font=("Microsoft YaHei", 9, "bold"),
                                anchor=tk.SW,
                                tags=f'label_{i}'
                            )
                        except Exception as e:
                            print(f"绘制新闻块 {i} 失败: {e}")
                            
        except Exception as e:
            print(f"显示报纸图片失败: {e}")
    
    def update_news_list(self):
        """更新新闻列表 - 使用多个文本框"""
        if not hasattr(self, 'news_frame') or not self.news_frame:
            return
        
        # 清空现有的文本框
        for widget in self.news_frame.winfo_children():
            widget.destroy()
        
        self.news_textboxes = []
        self.news_selections = []
        
        for i, news in enumerate(self.video_data):
            # 创建新闻项容器
            news_item = tk.Frame(self.news_frame, bg='white', relief=tk.RAISED, bd=1)
            news_item.pack(fill=tk.X, padx=5, pady=3)
            news_item.bind('<Button-1>', lambda e, idx=i: self.on_news_textbox_click(e, idx))
            news_item.bind('<Shift-Button-1>', lambda e, idx=i: self.on_news_textbox_shift_click(e, idx))
            
            # 序号标签
            idx_label = tk.Label(news_item, text=f"{i+1}.", font=("Microsoft YaHei", 11, "bold"), 
                               bg='white', width=3, anchor='w')
            idx_label.pack(side=tk.LEFT, padx=5, pady=2)
            
            # 标题文本框
            title_text = tk.Text(news_item, font=("Microsoft YaHei", 12, "bold"), 
                               bg='#f8f9fa', height=1, wrap=tk.WORD, borderwidth=0)
            title_text.insert(tk.END, news['title'])
            title_text.pack(side=tk.TOP, fill=tk.X, padx=5, pady=(2, 1))
            title_text.bind('<FocusOut>', lambda e, idx=i, key='title': self.on_news_text_change(e, idx, key))
            
            # 内容文本框
            content_text = tk.Text(news_item, font=("Microsoft YaHei", 11), 
                                 bg='white', height=3, wrap=tk.WORD, borderwidth=0)
            content_text.insert(tk.END, news['content'])
            content_text.pack(side=tk.TOP, fill=tk.X, padx=5, pady=(1, 2))
            content_text.bind('<FocusOut>', lambda e, idx=i, key='content': self.on_news_text_change(e, idx, key))
            
            # 播放按钮
            play_btn = tk.Button(news_item, text="▶️ 播放语音", 
                               font=("Microsoft YaHei", 9), bg='#3498DB', fg='white',
                               relief=tk.FLAT, padx=8, pady=2, cursor='hand2',
                               command=lambda idx=i: self.play_news_audio(idx))
            play_btn.pack(side=tk.BOTTOM, anchor='w', padx=5, pady=(0, 5))
            
            # 生成语音按钮
            generate_btn = tk.Button(news_item, text="🎤 生成语音", 
                                   font=("Microsoft YaHei", 9), bg='#27AE60', fg='white',
                                   relief=tk.FLAT, padx=8, pady=2, cursor='hand2',
                                   command=lambda idx=i: self.generate_news_audio(idx))
            generate_btn.pack(side=tk.BOTTOM, anchor='w', padx=5, pady=(0, 5))
            
            # 存储文本框引用
            self.news_textboxes.append({
                'frame': news_item,
                'title': title_text,
                'content': content_text,
                'play_btn': play_btn,
                'generate_btn': generate_btn
            })
            self.news_selections.append(False)
        
        # 更新滚动区域
        self.news_frame.update_idletasks()
        # 找到canvas并更新scrollregion
        canvas = self.news_frame.master
        if hasattr(canvas, 'configure') and 'scrollregion' in canvas.config():
            canvas.configure(scrollregion=canvas.bbox('all'))
    
    def on_news_textbox_click(self, event, index):
        """新闻文本框点击事件"""
        # 处理单选
        for i in range(len(self.news_selections)):
            self.news_selections[i] = (i == index)
        self.update_selection_display()
        self.current_news_index = index
    
    def on_news_textbox_shift_click(self, event, index):
        """新闻文本框Shift点击事件（多选）"""
        if self.current_news_index >= 0:
            start = min(self.current_news_index, index)
            end = max(self.current_news_index, index)
            for i in range(start, end + 1):
                self.news_selections[i] = True
            self.update_selection_display()
    
    def update_selection_display(self):
        """更新选择状态显示"""
        for i, textbox_info in enumerate(self.news_textboxes):
            if self.news_selections[i]:
                textbox_info['frame'].config(bg='#e3f2fd')
                textbox_info['title'].config(bg='#e3f2fd')
                textbox_info['content'].config(bg='#e3f2fd')
            else:
                textbox_info['frame'].config(bg='white')
                textbox_info['title'].config(bg='#f8f9fa')
                textbox_info['content'].config(bg='white')
    
    def on_news_text_change(self, event, index, key):
        """新闻文本修改事件"""
        if 0 <= index < len(self.video_data):
            text_widget = event.widget
            content = text_widget.get(1.0, tk.END).strip()
            self.video_data[index][key] = content
    
    def play_news_audio(self, index):
        """播放新闻的语音文件"""
        if not hasattr(self, 'current_image_file') or not self.current_image_file:
            self.show_info("提示", "请先选择一张报纸图片")
            return
        
        # 获取草稿目录
        import os
        import datetime
        image_filename = os.path.basename(self.current_image_file)
        base_name = os.path.splitext(image_filename)[0]
        today = datetime.datetime.now()
        date_str = today.strftime("%Y%m%d")
        draft_name = f"{base_name}_{date_str}"
        
        # 从配置获取剪映草稿目录
        jianying_drafts_dir = self.config.get('jianying_settings', {}).get('drafts_directory', 'E:/剪映5.9/JianyingPro Drafts')
        draft_dir = os.path.join(jianying_drafts_dir, draft_name)
        
        # 构建音频文件路径
        audio_filename = f"audio{index+1:02d}.wav"
        audio_path = os.path.join(draft_dir, 'textReading', audio_filename)
        
        if not os.path.exists(audio_path):
            self.show_info("提示", f"语音文件不存在: {audio_filename}\n请先生成剪映草稿")
            return
        
        # 播放音频
        try:
            import pygame
            pygame.mixer.init()
            pygame.mixer.music.load(audio_path)
            pygame.mixer.music.play()
            self.show_info("播放", f"正在播放: {audio_filename}")
        except ImportError:
            # 如果没有pygame，使用系统默认播放器
            import subprocess
            import platform
            system = platform.system()
            try:
                if system == 'Windows':
                    subprocess.Popen(['start', audio_path], shell=True)
                elif system == 'Darwin':  # macOS
                    subprocess.Popen(['open', audio_path])
                else:  # Linux
                    subprocess.Popen(['xdg-open', audio_path])
                self.show_info("播放", f"已打开: {audio_filename}")
            except Exception as e:
                self.show_info("错误", f"播放失败: {str(e)}")
        except Exception as e:
            self.show_info("错误", f"播放失败: {str(e)}")
    
    def generate_news_audio(self, index):
        """生成新闻的语音文件"""
        if not hasattr(self, 'current_image_file') or not self.current_image_file:
            self.show_info("提示", "请先选择一张报纸图片")
            return
        
        # 检查语音克隆模块是否可用
        try:
            from voice_clone import get_cosyvoice_cloner
            VOICE_CLONE_AVAILABLE = True
        except ImportError:
            VOICE_CLONE_AVAILABLE = False
        
        if not VOICE_CLONE_AVAILABLE:
            self.show_error("错误", "语音克隆模块不可用")
            return
        
        # 加载语音克隆器
        cloner = get_cosyvoice_cloner(self.config)
        if not cloner.model_loaded:
            self.show_info("提示", "请先加载CosyVoice模型")
            return
        
        if 0 <= index < len(self.video_data):
            news = self.video_data[index]
            
            # 获取草稿目录
            import os
            import datetime
            image_filename = os.path.basename(self.current_image_file)
            base_name = os.path.splitext(image_filename)[0]
            today = datetime.datetime.now()
            date_str = today.strftime("%Y%m%d")
            draft_name = f"{base_name}_{date_str}"
            
            # 从配置获取剪映草稿目录
            jianying_drafts_dir = self.config.get('jianying_settings', {}).get('drafts_directory', 'E:/剪映5.9/JianyingPro Drafts')
            draft_dir = os.path.join(jianying_drafts_dir, draft_name)
            output_dir = os.path.join(draft_dir, 'textReading')
            os.makedirs(output_dir, exist_ok=True)
            
            # 构建音频文件名（使用实际的新闻索引）
            audio_filename = f"audio{index+1:02d}.wav"
            output_file = os.path.join(output_dir, audio_filename)
            
            # 生成语音
            try:
                self.update_progress(f"正在生成第{index+1}条新闻的语音...", 0)
                
                # 直接调用generate_voice方法，避免批量处理的索引问题
                success = cloner.generate_voice(news['content'], output_file, speed=cloner.speed, silent=True)
                
                if success:
                    self.update_progress("语音生成成功", 100, "#27AE60")
                    self.show_info("成功", f"第{index+1}条新闻的语音生成成功！")
                else:
                    self.update_progress("生成失败", 0, "#E74C3C")
                    self.show_error("错误", "生成语音失败")
            except Exception as e:
                self.update_progress(f"生成失败: {str(e)}", 0, "#E74C3C")
                self.show_error("错误", f"生成语音失败: {str(e)}")
    
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
                
                self.update_progress("区域选择模式: 点击并拖动选择新闻区域", 0, "#27AE60")
                
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
                        self.update_progress(
                            f"选择区域: ({real_x1},{real_y1})-({real_x2},{real_y2}) 大小: {real_x2-real_x1}x{real_y2-real_y1}",
                            0, "#27AE60"
                        )
                        
                        # 保存选择的区域
                        self.selected_region = [real_x1, real_y1, real_x2, real_y2]
                        
                        # 测试导出选中区域
                        self.export_selected_region()
                    else:
                        self.update_progress("无效区域: 请选择更大的区域", 0, "#E74C3C")
                        
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
                
                self.update_progress(
                    f"选中区域已导出: {filename}",
                    100, "#27AE60"
                )
                
                # 显示成功消息
                self.show_info("导出成功", f"选中的区域已导出到:\n{output_path}")
                
            except Exception as e:
                print(f"导出选中区域失败: {e}")
                self.update_progress(f"导出失败: {str(e)}", 0, "#E74C3C")
    
    def on_preview_click(self, event, canvas, orig_width, orig_height, ratio, x_offset, y_offset):
        """预览画布鼠标点击事件"""
        # 检查是否点击了控制点（增大点击检测范围）
        click_range = 15  # 点击检测范围
        for i in range(len(self.video_data)):
            for j in range(8):  # 8个控制点
                handles = canvas.find_withtag(f'handle_{i}_{j}')
                if handles:
                    handle_id = handles[0]
                    bbox = canvas.bbox(handle_id)
                    if bbox:
                        # 扩大检测范围
                        expanded_bbox = (bbox[0]-click_range, bbox[1]-click_range, 
                                       bbox[2]+click_range, bbox[3]+click_range)
                        if self._point_in_bbox((event.x, event.y), expanded_bbox):
                            # 点击了控制点，开始调整大小
                            self.drag_data['is_resizing'] = True
                            self.drag_data['drag_type'] = 'resize'
                            self.drag_data['start_x'] = event.x
                            self.drag_data['start_y'] = event.y
                            self.drag_data['news_index'] = i
                            self.drag_data['handle_index'] = j
                            
                            # 保存原始位置
                            news = self.video_data[i]
                            self.drag_data['original_position'] = news.get('position', [0, 0, 0, 0])
                            print(f"开始调整大小: 新闻{i+1}, 控制点{j}")
                            return
        
        # 检查是否点击了矩形框
        for i in range(len(self.video_data)):
            rects = canvas.find_withtag(f'news_block_{i}')
            if rects:
                rect_id = rects[0]
                bbox = canvas.bbox(rect_id)
                if bbox and self._point_in_bbox((event.x, event.y), bbox):
                    # 点击了矩形框，开始移动
                    self.drag_data['is_dragging'] = True
                    self.drag_data['drag_type'] = 'move'
                    self.drag_data['start_x'] = event.x
                    self.drag_data['start_y'] = event.y
                    self.drag_data['news_index'] = i
                    
                    # 保存原始位置
                    news = self.video_data[i]
                    self.drag_data['original_position'] = news.get('position', [0, 0, 0, 0])
                    print(f"开始移动: 新闻{i+1}")
                    return
    
    def on_preview_drag(self, event, canvas, orig_width, orig_height, ratio, x_offset, y_offset):
        """预览画布鼠标拖动事件"""
        if not (self.drag_data['is_dragging'] or self.drag_data['is_resizing']):
            return
        
        news_index = self.drag_data['news_index']
        if news_index < 0 or news_index >= len(self.video_data):
            return
        
        dx = event.x - self.drag_data['start_x']
        dy = event.y - self.drag_data['start_y']
        
        # 转换为原始图片坐标
        dx_real = int(dx / ratio)
        dy_real = int(dy / ratio)
        
        # 获取原始位置
        original_pos = self.drag_data['original_position']
        if len(original_pos) != 4:
            return
        
        x1, y1, x2, y2 = original_pos
        
        if self.drag_data['is_dragging']:
            # 移动矩形框
            new_x1 = max(0, x1 + dx_real)
            new_y1 = max(0, y1 + dy_real)
            new_x2 = min(orig_width, x2 + dx_real)
            new_y2 = min(orig_height, y2 + dy_real)
        else:
            # 调整大小
            handle_index = self.drag_data['handle_index']
            if handle_index == 0:  # 左上
                new_x1 = max(0, x1 + dx_real)
                new_y1 = max(0, y1 + dy_real)
                new_x2 = x2
                new_y2 = y2
            elif handle_index == 1:  # 右上
                new_x1 = x1
                new_y1 = max(0, y1 + dy_real)
                new_x2 = min(orig_width, x2 + dx_real)
                new_y2 = y2
            elif handle_index == 2:  # 左下
                new_x1 = max(0, x1 + dx_real)
                new_y1 = y1
                new_x2 = x2
                new_y2 = min(orig_height, y2 + dy_real)
            elif handle_index == 3:  # 右下
                new_x1 = x1
                new_y1 = y1
                new_x2 = min(orig_width, x2 + dx_real)
                new_y2 = min(orig_height, y2 + dy_real)
            elif handle_index == 4:  # 上中
                new_x1 = x1
                new_y1 = max(0, y1 + dy_real)
                new_x2 = x2
                new_y2 = y2
            elif handle_index == 5:  # 下中
                new_x1 = x1
                new_y1 = y1
                new_x2 = x2
                new_y2 = min(orig_height, y2 + dy_real)
            elif handle_index == 6:  # 左中
                new_x1 = max(0, x1 + dx_real)
                new_y1 = y1
                new_x2 = x2
                new_y2 = y2
            elif handle_index == 7:  # 右中
                new_x1 = x1
                new_y1 = y1
                new_x2 = min(orig_width, x2 + dx_real)
                new_y2 = y2
            else:
                return
        
        # 确保坐标有效
        if new_x2 > new_x1 and new_y2 > new_y1:
            # 更新视频数据中的位置
            self.video_data[news_index]['position'] = [new_x1, new_y1, new_x2, new_y2]
            
            # 只更新当前拖动的矩形框和控制点，不重新绘制整个画布
            x1_scaled = x_offset + int(new_x1 * ratio)
            y1_scaled = y_offset + int(new_y1 * ratio)
            x2_scaled = x_offset + int(new_x2 * ratio)
            y2_scaled = y_offset + int(new_y2 * ratio)
            
            # 更新矩形框
            rects = canvas.find_withtag(f'news_block_{news_index}')
            if rects:
                canvas.coords(rects[0], x1_scaled, y1_scaled, x2_scaled, y2_scaled)
            
            # 更新控制点
            handles = [
                (x1_scaled, y1_scaled),  # 左上
                (x2_scaled, y1_scaled),  # 右上
                (x1_scaled, y2_scaled),  # 左下
                (x2_scaled, y2_scaled),  # 右下
                ((x1_scaled + x2_scaled) // 2, y1_scaled),  # 上中
                ((x1_scaled + x2_scaled) // 2, y2_scaled),  # 下中
                (x1_scaled, (y1_scaled + y2_scaled) // 2),  # 左中
                (x2_scaled, (y1_scaled + y2_scaled) // 2)   # 右中
            ]
            
            for j, (hx, hy) in enumerate(handles):
                handle_size = 8
                handle_items = canvas.find_withtag(f'handle_{news_index}_{j}')
                if handle_items:
                    canvas.coords(handle_items[0], hx-handle_size, hy-handle_size, hx+handle_size, hy+handle_size)
            
            # 更新标题位置
            label_items = canvas.find_withtag(f'label_{news_index}')
            if label_items:
                label_y = y1_scaled - 20 if y1_scaled - 20 > 0 else y1_scaled
                canvas.coords(label_items[0], x1_scaled + 5, label_y)
    
    def on_preview_release(self, event):
        """预览画布鼠标释放事件"""
        if hasattr(self, 'drag_data') and (self.drag_data['is_dragging'] or self.drag_data['is_resizing']):
            # 完成拖动或调整大小
            self.drag_data['is_dragging'] = False
            self.drag_data['is_resizing'] = False
            self.drag_data['drag_type'] = None
            self.drag_data['news_index'] = -1
            self.drag_data['handle_index'] = -1
    
    def _point_in_bbox(self, point, bbox):
        """检查点是否在边界框内"""
        x, y = point
        x1, y1, x2, y2 = bbox
        return x1 <= x <= x2 and y1 <= y <= y2