# UI helpers module
# UI辅助模块

import os
import glob
import datetime
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk, ImageDraw, ImageFont

class UIHelpers:
    def __init__(self, config, progress_label_widget=None, progress_bar_widget=None, root=None, main_app=None):
        self.preview_photo = None
        self.selection_start = None
        self.selection_rect = None
        self.selected_region = None
        self.progress_window = None
        self.progress_frame = None  # 进度层框架
        self.progress_label = None
        self.progress_bar_widget = None
        self.main_app = main_app
    
    def show_fullscreen_progress(self, title, message, progress=0):
        """显示在当前窗口中间的进度层
        
        Args:
            title: 标题
            message: 消息内容
            progress: 进度百分比 (0-100)
        """
        if not self.root:
            return
        
        # 如果进度层不存在，创建一个
        if self.progress_frame is None or not self.progress_frame.winfo_exists():
            # 创建进度层框架，覆盖在主窗口上
            self.progress_frame = tk.Frame(self.root, bg='#2C3E50', relief=tk.FLAT)
            self.progress_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER, 
                                   width=400, height=200)
            
            # 创建标题标签
            self.progress_title_label = tk.Label(self.progress_frame, text=title, 
                                                 font=('Microsoft YaHei', 16, 'bold'),
                                                 bg='#2C3E50', fg='white')
            self.progress_title_label.pack(pady=(30, 15))
            
            # 创建消息标签
            self.progress_message_label = tk.Label(self.progress_frame, text=message,
                                                   font=('Microsoft YaHei', 12),
                                                   bg='#2C3E50', fg='white')
            self.progress_message_label.pack(pady=5)
            
            # 创建进度条
            self.progress_bar = ttk.Progressbar(self.progress_frame, length=300, 
                                               mode='determinate', maximum=100)
            self.progress_bar.pack(pady=15)
            
            # 创建进度百分比标签
            self.progress_percent_label = tk.Label(self.progress_frame, text="0%",
                                                   font=('Microsoft YaHei', 10),
                                                   bg='#2C3E50', fg='white')
            self.progress_percent_label.pack(pady=5)
        else:
            # 更新现有进度层
            self.progress_title_label.config(text=title)
            self.progress_message_label.config(text=message)
            self.progress_bar['value'] = progress
            self.progress_percent_label.config(text=f"{progress}%")
        
        # 强制更新界面
        self.root.update()
    
    def close_fullscreen_progress(self):
        """关闭进度层"""
        if self.progress_frame and self.progress_frame.winfo_exists():
            self.progress_frame.destroy()
            self.progress_frame = None
        # 兼容旧代码
        if self.progress_window and self.progress_window.winfo_exists():
            self.progress_window.destroy()
            self.progress_window = None
    
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
                    canvas.bind("<Double-1>", lambda e: self.on_preview_double_click(e))
                    
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
                               bg='#f8f9fa', height=1, width=70, wrap=tk.WORD, borderwidth=0)
            title_text.insert(tk.END, news['title'])
            title_text.pack(side=tk.TOP, padx=5, pady=(2, 1))
            title_text.bind('<FocusOut>', lambda e, idx=i, key='title': self.on_news_text_change(e, idx, key))
            
            # 内容文本框
            content_text = tk.Text(news_item, font=("Microsoft YaHei", 11), 
                                 bg='white', height=3, width=70, wrap=tk.WORD, borderwidth=0)
            content_text.insert(tk.END, news['content'])
            content_text.pack(side=tk.TOP, padx=5, pady=(1, 2))
            content_text.bind('<FocusOut>', lambda e, idx=i, key='content': self.on_news_text_change(e, idx, key))
            
            # 按钮容器
            btn_container = tk.Frame(news_item, bg='white')
            btn_container.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=(0, 5))
            
            # 播放按钮
            play_btn = tk.Button(btn_container, text="▶️ 播放语音", 
                               font=("Microsoft YaHei", 9), bg='#3498DB', fg='white',
                               relief=tk.FLAT, padx=8, pady=2, cursor='hand2',
                               command=lambda idx=i: self.play_news_audio(idx))
            play_btn.pack(side=tk.LEFT, padx=(0, 5))
            
            # 生成语音按钮
            generate_btn = tk.Button(btn_container, text="🎤 生成语音", 
                                   font=("Microsoft YaHei", 9), bg='#27AE60', fg='white',
                                   relief=tk.FLAT, padx=8, pady=2, cursor='hand2',
                                   command=lambda idx=i: self.generate_news_audio(idx))
            generate_btn.pack(side=tk.LEFT)
            
            # 图片路径显示标签（可点击高亮）
            news_pic_path = news.get('news_pic', '')
            pic_label_text = f"📷 {os.path.basename(news_pic_path)}" if news_pic_path else "📷 未设置图片"
            news_pic_label = tk.Label(btn_container, text=pic_label_text,
                                     font=("Microsoft YaHei", 8), bg='white', fg='#3498DB',
                                     anchor='w', cursor='hand2')
            news_pic_label.pack(side=tk.RIGHT, padx=(5, 0))
            # 绑定点击事件
            news_pic_label.bind('<Button-1>', lambda e, path=news_pic_path, label=news_pic_label: self.highlight_image_in_browser(path, label))
            # 绑定双击事件 - 清空图片路径
            news_pic_label.bind('<Double-1>', lambda e, index=i, label=news_pic_label: self.clear_news_pic_path(index, label))
            
            # 存储文本框引用
            self.news_textboxes.append({
                'frame': news_item,
                'title': title_text,
                'content': content_text,
                'play_btn': play_btn,
                'generate_btn': generate_btn,
                'news_pic_label': news_pic_label
            })
            self.news_selections.append(False)
        
        # 恢复选中状态
        if self.current_news_index >= 0 and self.current_news_index < len(self.news_selections):
            self.news_selections[self.current_news_index] = True
            self.update_selection_display()
        
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
        
        # 更新矩形框的高亮状态
        self.update_rectangle_highlight()
    
    def update_rectangle_highlight(self):
        """更新矩形框的高亮状态"""
        if not hasattr(self, 'preview_canvas'):
            return
        
        canvas = self.preview_canvas
        
        # 颜色列表
        colors = ['#FF0000', '#00FF00', '#0000FF', '#FFFF00', '#FF00FF', '#00FFFF', 
                  '#FF8800', '#8800FF', '#0088FF', '#88FF00']
        
        # 更新每个矩形框的样式
        for i in range(len(self.video_data)):
            # 获取矩形框
            rect_tags = canvas.find_withtag(f'news_block_{i}')
            
            if rect_tags:
                # 根据选中状态设置颜色和线宽
                if i < len(self.news_selections) and self.news_selections[i]:
                    color = '#FF0000'  # 选中时使用红色
                    line_width = 4
                else:
                    color = colors[i % len(colors)]
                    line_width = 2
                
                # 更新矩形框样式
                canvas.itemconfig(rect_tags[0], outline=color, width=line_width)
                
                # 更新控制点颜色
                for j in range(8):
                    handle_tags = canvas.find_withtag(f'handle_{i}_{j}')
                    if handle_tags:
                        handle_color = '#FF0000' if (i < len(self.news_selections) and self.news_selections[i]) else colors[i % len(colors)]
                        canvas.itemconfig(handle_tags[0], fill=handle_color)
                
                # 更新标签颜色
                label_tags = canvas.find_withtag(f'label_{i}')
                if label_tags:
                    label_color = '#FF0000' if (i < len(self.news_selections) and self.news_selections[i]) else colors[i % len(colors)]
                    canvas.itemconfig(label_tags[0], fill=label_color)
    
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
                # 使用与剪映草稿功能相同的参数：text_frontend=False
                cosyvoice_config = self.config.get('cosyvoice', {})
                instruct = cosyvoice_config.get('test_instruct')
                seed = cosyvoice_config.get('seed', 888)
                
                import torch
                torch.manual_seed(seed)
                if torch.cuda.is_available():
                    torch.cuda.manual_seed_all(seed)
                
                success = cloner.generate_voice(news['content'], output_file, speed=cloner.speed, silent=False, text_frontend=False, instruct=instruct)
                
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
    
    def refresh_download_images(self):
        """刷新下载目录图片列表，显示缩略图"""
        download_dir = r'F:\Administrator\Downloads'
        
        # 获取主窗口中的 Canvas
        canvas = None
        if hasattr(self, 'main_app') and self.main_app:
            if hasattr(self.main_app, 'download_images_canvas'):
                canvas = self.main_app.download_images_canvas
        
        if not canvas:
            return
        
        # 清空 Canvas
        canvas.delete('all')
        
        # 清除旧的缩略图引用
        if hasattr(self.main_app, 'download_thumbnail_images'):
            self.main_app.download_thumbnail_images.clear()
        
        # 超大缩略图配置（放大50%）
        thumb_width = 210
        thumb_height = 158
        padding = 8
        columns = 2  # 每行显示2个缩略图
        
        # 获取今天的日期
        today = datetime.datetime.now().date()
        
        # 查找下载目录中的图片文件（只显示今天的）
        if os.path.exists(download_dir):
            image_files = []
            for ext in ['*.jpg', '*.jpeg', '*.png', '*.gif', '*.bmp']:
                image_files.extend(glob.glob(os.path.join(download_dir, ext)))
            
            # 过滤只保留今天的图片
            today_image_files = []
            for filepath in image_files:
                try:
                    file_mtime = datetime.datetime.fromtimestamp(os.path.getmtime(filepath)).date()
                    if file_mtime == today:
                        today_image_files.append(filepath)
                except:
                    continue
            
            image_files = today_image_files
            
            # 按修改时间倒序排列
            image_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            
            row = 0
            col = 0
            x_offset = padding
            y_offset = padding
            
            for filepath in image_files:
                try:
                    # 打开原图
                    img = Image.open(filepath)
                    img.thumbnail((thumb_width, thumb_height), Image.LANCZOS)
                    
                    # 转换为 PhotoImage
                    photo = ImageTk.PhotoImage(img)
                    
                    # 存储引用防止垃圾回收
                    if hasattr(self.main_app, 'download_thumbnail_images'):
                        self.main_app.download_thumbnail_images[filepath] = photo
                    
                    # 计算位置
                    x = x_offset + col * (thumb_width + padding * 2)
                    y = y_offset + row * (thumb_height + padding * 3 + 20)
                    
                    # 在 Canvas 上创建图片
                    img_id = canvas.create_image(x + thumb_width/2, y + thumb_height/2, image=photo)
                    
                    # 存储文件路径到图片 ID 的映射
                    if not hasattr(canvas, 'img_path_map'):
                        canvas.img_path_map = {}
                    canvas.img_path_map[img_id] = filepath
                    
                    # 添加文件名文本
                    filename = os.path.basename(filepath)
                    if len(filename) > 15:
                        filename = filename[:12] + '...'
                    canvas.create_text(x + thumb_width/2, y + thumb_height + 10, 
                                       text=filename, font=('Microsoft YaHei', 8),
                                       fill='#2C3E50')
                    
                    col += 1
                    if col >= columns:
                        col = 0
                        row += 1
                        
                except Exception as e:
                    continue
            
            # 更新 Canvas 滚动区域
            total_height = (row + 1) * (thumb_height + padding * 3 + 20) + padding
            canvas.config(scrollregion=(0, 0, 200, total_height))
        
    def on_download_image_double_click(self, event):
        """双击下载目录中的图片 - 在中间预览区域显示"""
        canvas = event.widget
        # 查找点击位置下的图片
        items = canvas.find_overlapping(event.x, event.y, event.x, event.y)
        img_map = getattr(canvas, 'img_path_map', {})
        for item_id in items:
            filepath = img_map.get(item_id)
            if filepath and os.path.exists(filepath):
                # 设置为当前图片文件
                self.current_image_file = filepath
                
                # 在中间预览区域显示图片
                if hasattr(self, 'preview_canvas') and self.preview_canvas:
                    try:
                        image = Image.open(filepath)
                        
                        canvas_widget = self.preview_canvas
                        canvas_widget.update_idletasks()
                        canvas_width = canvas_widget.winfo_width()
                        canvas_height = canvas_widget.winfo_height()
                        
                        if canvas_width <= 1 or canvas_height <= 1:
                            canvas_width = 400
                            canvas_height = 500
                        
                        orig_width, orig_height = image.size
                        ratio = min(canvas_width / orig_width, canvas_height / orig_height, 1.0)
                        new_size = (int(orig_width * ratio), int(orig_height * ratio))
                        
                        image = image.resize(new_size, Image.Resampling.LANCZOS)
                        self.preview_photo = ImageTk.PhotoImage(image)
                        
                        canvas_widget.delete("all")
                        
                        x_offset = (canvas_width - new_size[0]) // 2
                        y_offset = (canvas_height - new_size[1]) // 2
                        
                        canvas_widget.create_image(x_offset, y_offset, anchor=tk.NW, image=self.preview_photo)
                        
                        # 绑定鼠标事件
                        canvas_widget.bind("<Button-1>", lambda e: self.on_preview_click(e, canvas_widget, orig_width, orig_height, ratio, x_offset, y_offset))
                        canvas_widget.bind("<B1-Motion>", lambda e: self.on_preview_drag(e, canvas_widget, orig_width, orig_height, ratio, x_offset, y_offset))
                        canvas_widget.bind("<ButtonRelease-1>", self.on_preview_release)
                        canvas_widget.bind("<Double-1>", lambda e: self.on_preview_double_click(e))
                    except Exception as e:
                        print(f"预览图片失败: {e}")
                
                # 尝试加载对应的JSON文件
                if hasattr(self, 'silent_load_json'):
                    self.silent_load_json(os.path.basename(filepath))
                break
    
    def on_preview_double_click(self, event):
        """双击预览区域 - 显示选中报纸的图片"""
        # 检查是否有保存的原始报纸图片
        if hasattr(self, 'original_image_file') and self.original_image_file and os.path.exists(self.original_image_file):
            self.current_image_file = self.original_image_file
            if hasattr(self, 'show_newspaper_image'):
                self.show_newspaper_image()
        elif hasattr(self, 'show_newspaper_image'):
            # 如果没有原始图片，重新调用 show_newspaper_image
            self.show_newspaper_image()
    
    def on_download_image_drag_start(self, event):
        """开始拖动下载目录中的图片"""
        canvas = event.widget
        img_map = getattr(canvas, 'img_path_map', {})
        
        # 首先尝试 find_closest 获取最近的 item
        closest_id = canvas.find_closest(event.x, event.y)
        if closest_id and closest_id[0] in img_map:
            filepath = img_map.get(closest_id[0])
            if filepath and os.path.exists(filepath):
                self.dragged_image_path = filepath
                self._create_drag_window(filepath, event)
                return
        
        # 如果最近的 item 不是图片，查找所有重叠的 items 中的图片
        items = canvas.find_overlapping(event.x, event.y, event.x, event.y)
        for item_id in items:
            if item_id in img_map:
                filepath = img_map.get(item_id)
                if filepath and os.path.exists(filepath):
                    self.dragged_image_path = filepath
                    self._create_drag_window(filepath, event)
                    return
    
    def _create_drag_window(self, filepath, event):
        """创建拖动窗口显示缩略图"""
        try:
            img = Image.open(filepath)
            img.thumbnail((80, 60), Image.LANCZOS)
            self.dragged_photo = ImageTk.PhotoImage(img)
            # 创建一个临时顶层窗口显示拖动的图片
            self.drag_window = tk.Toplevel(self.root if hasattr(self, 'root') else None)
            self.drag_window.overrideredirect(True)
            self.drag_window.attributes('-topmost', True)
            self.drag_label = tk.Label(self.drag_window, image=self.dragged_photo, bg='white', bd=2, relief=tk.SUNKEN)
            self.drag_label.pack()
            # 初始位置
            self.drag_window.geometry(f'+{event.x_root}+{event.y_root}')
        except Exception as e:
            print(f"创建拖动图像失败: {e}")
    
    def on_download_image_drag(self, event):
        """拖动图片 - 更新拖动窗口位置"""
        if hasattr(self, 'drag_window') and self.drag_window:
            self.drag_window.geometry(f'+{event.x_root}+{event.y_root}')
    
    def clear_news_pic_path(self, news_index, label_widget):
        """清空指定新闻条目的图片路径"""
        if news_index >= 0 and news_index < len(self.video_data):
            # 清空视频数据中的图片路径
            self.video_data[news_index]['news_pic'] = ''
            # 更新标签显示
            if label_widget:
                label_widget.config(text="📷 未设置图片", fg='#3498DB')
            # 显示提示
            self.show_info("提示", "已清空图片路径")
    
    def highlight_front_pic(self):
        """点击首页图片路径输入框时，在下载目录面板中高亮显示对应的图片"""
        if hasattr(self, 'front_pic_entry') and self.front_pic_entry:
            filepath = self.front_pic_entry.get().strip()
            if filepath:
                self.highlight_image_in_browser(filepath)

    def highlight_front_pic(self):
        """点击首页图片路径输入框时，在下载目录面板中高亮显示对应的图片"""
        if hasattr(self, 'front_pic_entry') and self.front_pic_entry:
            filepath = self.front_pic_entry.get().strip()
            if filepath:
                self.highlight_image_in_browser(filepath)

    def highlight_image_in_browser(self, filepath, label_widget=None):
        """在下载目录面板中高亮显示指定的图片"""
        # 首先高亮标签作为反馈
        if label_widget:
            original_bg = label_widget.cget('bg')
            original_fg = label_widget.cget('fg')
            label_widget.config(bg='#2ECC71', fg='white')
            
            def restore_label():
                try:
                    label_widget.config(bg=original_bg, fg=original_fg)
                except:
                    pass
            if hasattr(self, 'root') and self.root:
                self.root.after(3000, restore_label)
        
        if not filepath:
            return
        
        # 获取下载目录面板的 Canvas
        canvas = None
        if hasattr(self, 'main_app') and self.main_app:
            if hasattr(self.main_app, 'download_images_canvas'):
                canvas = self.main_app.download_images_canvas
        
        if not canvas:
            return
        
        # 查找对应的图片并高亮
        img_map = getattr(canvas, 'img_path_map', {})
        found = False
        for img_id, path in img_map.items():
            if path == filepath:
                found = True
                # 获取图片坐标
                coords = canvas.coords(img_id)
                if coords and len(coords) >= 2:
                    x, y = coords[0], coords[1]
                    # 获取缩略图尺寸
                    thumb_width = 210
                    thumb_height = 158
                    # 计算矩形边界
                    x1 = x - thumb_width/2 - 5
                    y1 = y - thumb_height/2 - 5
                    x2 = x + thumb_width/2 + 5
                    y2 = y + thumb_height/2 + 25
                    
                    # 创建高亮矩形
                    highlight_id = canvas.create_rectangle(
                        x1, y1, x2, y2,
                        outline='#E74C3C',
                        width=4,
                        fill='#F1948A',
                        stipple='gray25',
                        tags=('highlight',)
                    )
                    
                    # 滚动到图片位置
                    bbox = canvas.bbox("all")
                    if bbox:
                        total_height = bbox[3] - bbox[1]
                        canvas.yview_moveto(max(0, (y1 - 30) / total_height if total_height > 0 else 0))
                    
                    # 3秒后取消高亮
                    def remove_highlight():
                        try:
                            canvas.delete(highlight_id)
                        except:
                            pass
                    if hasattr(self, 'root') and self.root:
                        self.root.after(3000, remove_highlight)
                break
        
        # 如果没有找到，显示提示
        if not found:
            self.show_info("提示", f"未在下载目录中找到图片: {os.path.basename(filepath)}")
    
    def on_download_image_drag_end(self, event):
        """结束拖动图片"""
        if hasattr(self, 'dragged_image_path') and self.dragged_image_path:
            # 首先检查是否拖到了首页图片路径输入框上
            if hasattr(self, 'front_pic_entry') and self.front_pic_entry:
                try:
                    entry_x = self.front_pic_entry.winfo_rootx()
                    entry_y = self.front_pic_entry.winfo_rooty()
                    entry_width = self.front_pic_entry.winfo_width()
                    entry_height = self.front_pic_entry.winfo_height()
                    x, y = event.x_root, event.y_root
                    
                    if (entry_x <= x <= entry_x + entry_width and
                        entry_y <= y <= entry_y + entry_height):
                        # 设置首页图片路径
                        self.front_pic_entry.delete(0, tk.END)
                        self.front_pic_entry.insert(0, self.dragged_image_path)
                        self.show_info("成功", f"已设置首页图片路径: {os.path.basename(self.dragged_image_path)}")
                        
                        # 关闭拖动窗口并清除状态
                        if hasattr(self, 'drag_window') and self.drag_window:
                            try:
                                self.drag_window.destroy()
                            except:
                                pass
                        self.dragged_image_path = None
                        return
                except Exception as e:
                    print(f"检查首页图片输入框失败: {e}")
            
            # 然后检查是否拖到了新闻条目上
            if hasattr(self, 'news_frame') and self.news_frame:
                # 获取鼠标位置对应的新闻条目
                x, y = event.x_root, event.y_root
                
                # 检查是否在新闻文本框区域内
                for i, textbox_info in enumerate(self.news_textboxes):
                    frame = textbox_info['frame']
                    try:
                        frame_x = frame.winfo_rootx()
                        frame_y = frame.winfo_rooty()
                        frame_width = frame.winfo_width()
                        frame_height = frame.winfo_height()
                        
                        if (frame_x <= x <= frame_x + frame_width and
                            frame_y <= y <= frame_y + frame_height):
                            # 设置该新闻的图片路径
                            self.video_data[i]['news_pic'] = self.dragged_image_path
                            
                            # 更新UI显示
                            if 'news_pic_label' in textbox_info:
                                textbox_info['news_pic_label'].config(text=f"📷 {os.path.basename(self.dragged_image_path)}")
                            
                            self.show_info("成功", f"已为新闻 {i+1} 设置图片: {os.path.basename(self.dragged_image_path)}")
                            break
                    except Exception as e:
                        print(f"检查拖放目标失败: {e}")
            
            # 清除拖动状态
            self.dragged_image_path = None
            self.drag_start_index = -1
            
            # 关闭拖动窗口
            if hasattr(self, 'drag_window') and self.drag_window:
                try:
                    self.drag_window.destroy()
                except:
                    pass
                del self.drag_window