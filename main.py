import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from datetime import datetime
from PIL import Image, ImageTk
import os

from downloader import NewspaperDownloader
from analyzer import ImageAnalyzer
from video_generator.main import VideoGenerator
from utils import load_config, export_image, refresh_image_list


class EnhancedKioskoDownloader:
    def __init__(self, root):
        self.root = root
        self.root.title("新闻报纸下载与分析工具")
        self.root.geometry("{0}x{1}+0+0".format(self.root.winfo_screenwidth(), self.root.winfo_screenheight()))
        self.root.state('zoomed')
        
        self.config = load_config()
        
        self.download_dir = self.config['download_settings']['save_directory']
        self.analysis_dir = self.config.get('analysis_settings', {}).get('analysis_directory', 'analysis_results')
        
        self.init_modules()
        self.create_interface()
    
    def init_modules(self):
        pass
    
    def finalize_modules(self):
        self.downloader = NewspaperDownloader(self.config, self.update_status)
        
        self.analyzer = ImageAnalyzer(
            self.config, 
            self.root, 
            self.result_text, 
            self.preview_canvas
        )
        
        self.video_generator = VideoGenerator(
            self.config,
            self.progress_label,
            self.progress_bar,
            self.root
        )
        self.video_generator.set_news_listbox(self.news_listbox)
        self.video_generator.preview_canvas = self.video_preview_canvas
        
        gemini_status = "✅ Gemini已连接" if self.analyzer.gemini_available else "❌ Gemini未配置"
        status_color = "#27AE60" if self.analyzer.gemini_available else "#E74C3C"
        self.gemini_status_label.config(text=gemini_status, fg=status_color)
    
    def create_interface(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.home_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.home_frame, text='首页')
        self.create_home_tab()
        
        self.video_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.video_frame, text='视频生成')
        self.create_video_tab()
        
        # 绑定页签切换事件
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)
    
    def create_home_tab(self):
        main_paned = tk.PanedWindow(self.home_frame, orient=tk.VERTICAL, sashrelief=tk.RAISED, sashwidth=4)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        download_frame = tk.Frame(main_paned)
        main_paned.add(download_frame, minsize=250)
        
        tk.Label(download_frame, text="新闻报纸首页下载器", 
                font=("Arial", 14, "bold")).pack(pady=5)
        
        tk.Label(download_frame, text=f"从 kiosko.net 下载今日报纸首页 (保存到: {self.download_dir})", 
                font=("Arial", 9)).pack(pady=2)
        
        self.status_label = tk.Label(download_frame, text="准备就绪", 
                                   font=("Arial", 9), fg="blue")
        self.status_label.pack(pady=3)
        
        button_frame = tk.Frame(download_frame)
        button_frame.pack(pady=5)
        
        button_container = tk.Frame(button_frame)
        button_container.pack()
        
        self.wsj_btn = tk.Button(button_container, text="下载华尔街日报", 
                                command=lambda: self.on_download_click('wsj'),
                                font=("Arial", 9), bg="#4CAF50", fg="white", 
                                padx=10, pady=6, width=12)
        self.wsj_btn.grid(row=0, column=0, padx=8, pady=3)
        
        self.ft_btn = tk.Button(button_container, text="下载金融时报", 
                               command=lambda: self.on_download_click('ft'),
                               font=("Arial", 9), bg="#2196F3", fg="white", 
                               padx=10, pady=6, width=12)
        self.ft_btn.grid(row=0, column=1, padx=8, pady=3)
        
        self.batch_btn = tk.Button(button_container, text="批量下载全部", 
                                  command=self.on_batch_download_click,
                                  font=("Arial", 9), bg="#FF9800", fg="white", 
                                  padx=10, pady=6, width=12)
        self.batch_btn.grid(row=0, column=2, padx=8, pady=3)
        
        date_frame = tk.Frame(download_frame)
        date_frame.pack(pady=3)
        
        date_inner_frame = tk.Frame(date_frame)
        date_inner_frame.pack(anchor='center')
        
        tk.Label(date_inner_frame, text="日期设置:", font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=5, pady=2)
        
        self.date_var = tk.StringVar(value="today")
        
        tk.Radiobutton(date_inner_frame, text="今日", variable=self.date_var, value="today", font=("Arial", 9)).pack(side=tk.LEFT, padx=3, pady=2)
        tk.Radiobutton(date_inner_frame, text="昨日", variable=self.date_var, value="yesterday", font=("Arial", 9)).pack(side=tk.LEFT, padx=3, pady=2)
        tk.Radiobutton(date_inner_frame, text="自定义", variable=self.date_var, value="custom", font=("Arial", 9)).pack(side=tk.LEFT, padx=3, pady=2)
        
        self.custom_date_entry = tk.Entry(date_inner_frame, width=10, font=("Arial", 9))
        self.custom_date_entry.pack(side=tk.LEFT, padx=5, pady=2)
        self.custom_date_entry.insert(0, datetime.now().strftime('%Y/%m/%d'))
        self.custom_date_entry.config(state='disabled')
        
        self.date_var.trace('w', self.on_date_change)
        
        analysis_frame = tk.Frame(main_paned)
        main_paned.add(analysis_frame, minsize=400)
        
        analysis_paned = tk.PanedWindow(analysis_frame, orient=tk.HORIZONTAL, sashrelief=tk.RAISED, sashwidth=4)
        analysis_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        left_frame = tk.Frame(analysis_paned, width=280)
        analysis_paned.add(left_frame, minsize=250)
        
        title_frame = tk.Frame(left_frame, bg='#2C3E50')
        title_frame.pack(fill=tk.X)
        tk.Label(title_frame, text="📰 图片列表", font=("Microsoft YaHei", 12, "bold"), 
                bg='#2C3E50', fg='white').pack(pady=8)
        
        status_frame = tk.Frame(left_frame, bg='#ECF0F1')
        status_frame.pack(fill=tk.X, padx=10, pady=3)
        self.gemini_status_label = tk.Label(status_frame, text="初始化中...", font=("Microsoft YaHei", 9), 
                bg='#ECF0F1', fg='#95A5A6')
        self.gemini_status_label.pack(anchor='w', pady=3)
        
        list_container = tk.Frame(left_frame, bg='#BDC3C7', relief=tk.SUNKEN, bd=1)
        list_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        list_scroll = tk.Scrollbar(list_container)
        list_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.image_listbox = tk.Listbox(list_container, font=("Microsoft YaHei", 10), 
                                        yscrollcommand=list_scroll.set, 
                                        bg='white', selectbackground='#3498DB',
                                        selectforeground='white', borderwidth=0)
        self.image_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        list_scroll.config(command=self.image_listbox.yview)
        
        self.image_listbox.bind('<<ListboxSelect>>', self.on_image_select)
        self.image_listbox.bind('<Double-1>', self.on_image_double_click)
        
        btn_frame = tk.Frame(left_frame, bg='#ECF0F1')
        btn_frame.pack(fill=tk.X, padx=10, pady=(0, 5))
        
        refresh_btn = tk.Button(btn_frame, text="🔄 刷新列表", command=self.on_refresh_list,
                              font=("Microsoft YaHei", 10), bg='#3498DB', fg='white',
                              relief=tk.FLAT, padx=10, pady=5, cursor='hand2')
        refresh_btn.pack(side=tk.LEFT)
        
        generate_prompt_btn = tk.Button(btn_frame, text="📝 生成Prompt", command=self.on_generate_prompt,
                               font=('Microsoft YaHei', 10), bg='#F39C12', fg='white',
                               relief=tk.FLAT, padx=10, pady=5, cursor='hand2')
        generate_prompt_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        analyze_btn = tk.Button(btn_frame, text="🔍 分析图片", command=self.on_analyze_click,
                               font=('Microsoft YaHei', 10), bg='#9B59B6', fg='white',
                               relief=tk.FLAT, padx=10, pady=5, cursor='hand2')
        analyze_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        export_btn = tk.Button(btn_frame, text="📤 导出图片", command=self.on_export_click,
                              font=('Microsoft YaHei', 10), bg='#27AE60', fg='white',
                              relief=tk.FLAT, padx=10, pady=5, cursor='hand2')
        export_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        right_frame = tk.Frame(analysis_paned)
        analysis_paned.add(right_frame, minsize=500)
        
        right_paned = tk.PanedWindow(right_frame, orient=tk.HORIZONTAL, sashrelief=tk.RAISED, sashwidth=4)
        right_paned.pack(fill=tk.BOTH, expand=True)
        
        preview_container = tk.Frame(right_paned)
        right_paned.add(preview_container, minsize=350)
        
        preview_title = tk.Frame(preview_container, bg='#2C3E50')
        preview_title.pack(fill=tk.X)
        tk.Label(preview_title, text="🖼️ 图片预览", font=("Microsoft YaHei", 12, "bold"), 
                bg='#2C3E50', fg='white').pack(pady=8)
        
        preview_canvas_frame = tk.Frame(preview_container, bg='#BDC3C7', relief=tk.SUNKEN, bd=1)
        preview_canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 5))
        
        self.preview_canvas = tk.Canvas(preview_canvas_frame, bg='white', highlightthickness=0)
        self.preview_canvas.pack(fill=tk.BOTH, expand=True)
        
        self.preview_text_id = self.preview_canvas.create_text(
            175, 200, text="选择左侧图片查看预览", 
            font=("Microsoft YaHei", 12), fill='#95A5A6'
        )
        
        result_container = tk.Frame(right_paned)
        right_paned.add(result_container, minsize=400)
        
        # Prompt文本框
        prompt_title = tk.Frame(result_container, bg='#34495E')
        prompt_title.pack(fill=tk.X)
        prompt_frame = tk.Frame(prompt_title, bg='#34495E')
        prompt_frame.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(prompt_frame, text="💬 Prompt", font=('Microsoft YaHei', 10, 'bold'), 
                bg='#34495E', fg='white').pack(side=tk.LEFT, padx=5)
        save_prompt_btn = tk.Button(prompt_frame, text="💾 保存", command=self.on_save_prompt,
                                   font=('Microsoft YaHei', 8), bg='#27AE60', fg='white',
                                   relief=tk.FLAT, padx=8, pady=2, cursor='hand2')
        save_prompt_btn.pack(side=tk.RIGHT, padx=5)
        
        prompt_text_container = tk.Frame(result_container, bg='#BDC3C7', relief=tk.SUNKEN, bd=1)
        prompt_text_container.pack(fill=tk.X, padx=10, pady=(0, 5))
        
        prompt_scroll = tk.Scrollbar(prompt_text_container)
        prompt_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.prompt_text = tk.Text(prompt_text_container, font=('Microsoft YaHei', 10), 
                                   wrap=tk.WORD, yscrollcommand=prompt_scroll.set,
                                   bg='white', borderwidth=0, height=8)
        self.prompt_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        prompt_scroll.config(command=self.prompt_text.yview)
        
        # 为prompt_text添加事件处理，确保编辑时保持图片列表的选中状态
        self.prompt_text.bind('<FocusIn>', self.on_text_focus_in)
        self.prompt_text.bind('<FocusOut>', self.on_text_focus_out)
        # 添加鼠标事件处理，确保选择文本时保持选中状态
        self.prompt_text.bind('<Button-1>', self.on_text_mouse_down)
        self.prompt_text.bind('<B1-Motion>', self.on_text_mouse_drag)
        self.prompt_text.bind('<ButtonRelease-1>', self.on_text_mouse_up)
        
        # 分析结果文本框
        result_title = tk.Frame(result_container, bg='#2C3E50')
        result_title.pack(fill=tk.X)
        result_frame = tk.Frame(result_title, bg='#2C3E50')
        result_frame.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(result_frame, text="📝 分析结果", font=('Microsoft YaHei', 12, 'bold'), 
                bg='#2C3E50', fg='white').pack(side=tk.LEFT, padx=5)
        save_result_btn = tk.Button(result_frame, text="💾 保存", command=self.on_save_result,
                                   font=('Microsoft YaHei', 8), bg='#27AE60', fg='white',
                                   relief=tk.FLAT, padx=8, pady=2, cursor='hand2')
        save_result_btn.pack(side=tk.RIGHT, padx=5)
        
        result_text_container = tk.Frame(result_container, bg='#BDC3C7', relief=tk.SUNKEN, bd=1)
        result_text_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 5))
        
        result_scroll = tk.Scrollbar(result_text_container)
        result_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.result_text = tk.Text(result_text_container, font=('Microsoft YaHei', 10), 
                                   wrap=tk.WORD, yscrollcommand=result_scroll.set,
                                   bg='white', borderwidth=0)
        self.result_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        result_scroll.config(command=self.result_text.yview)
        
        # 为result_text添加事件处理，确保编辑时保持图片列表的选中状态
        self.result_text.bind('<FocusIn>', self.on_text_focus_in)
        self.result_text.bind('<FocusOut>', self.on_text_focus_out)
        # 添加鼠标事件处理，确保选择文本时保持选中状态
        self.result_text.bind('<Button-1>', self.on_text_mouse_down)
        self.result_text.bind('<B1-Motion>', self.on_text_mouse_drag)
        self.result_text.bind('<ButtonRelease-1>', self.on_text_mouse_up)
        
        self.refresh_image_list()
    
    def create_video_tab(self):
        main_paned = tk.PanedWindow(self.video_frame, orient=tk.HORIZONTAL, sashrelief=tk.RAISED, sashwidth=4)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        left_frame = tk.Frame(main_paned, width=450)
        main_paned.add(left_frame, minsize=450)
        
        title_frame = tk.Frame(left_frame, bg='#2C3E50')
        title_frame.pack(fill=tk.X)
        tk.Label(title_frame, text="📰 新闻编辑", font=("Microsoft YaHei", 12, "bold"), 
                bg='#2C3E50', fg='white').pack(pady=8)
        
        list_container = tk.Frame(left_frame, bg='#BDC3C7', relief=tk.SUNKEN, bd=1)
        list_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        list_scroll = tk.Scrollbar(list_container)
        list_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.news_listbox = tk.Listbox(list_container, font=("Microsoft YaHei", 10), 
                                       yscrollcommand=list_scroll.set, 
                                       bg='white', selectbackground='#3498DB',
                                       selectforeground='white', borderwidth=0)
        self.news_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        list_scroll.config(command=self.news_listbox.yview)
        
        self.news_listbox.bind('<<ListboxSelect>>', self.on_news_select)
        self.news_listbox.bind('<Double-1>', self.on_news_double_click)
        
        # 操作按钮
        edit_frame = tk.Frame(left_frame, bg='#ECF0F1')
        edit_frame.pack(fill=tk.X, padx=10, pady=3)
        
        # 上移按钮
        up_btn = tk.Button(edit_frame, text="⬆️ 上移", 
                          font=("Microsoft YaHei", 9), bg='#27AE60', fg='white',
                          relief=tk.FLAT, padx=8, pady=4, cursor='hand2',
                          command=lambda: self.video_generator.move_news_up() if self.video_generator else None)
        up_btn.pack(side=tk.LEFT)
        
        # 下移按钮
        down_btn = tk.Button(edit_frame, text="⬇️ 下移", 
                            font=("Microsoft YaHei", 9), bg='#27AE60', fg='white',
                            relief=tk.FLAT, padx=8, pady=4, cursor='hand2',
                            command=lambda: self.video_generator.move_news_down() if self.video_generator else None)
        down_btn.pack(side=tk.LEFT, padx=5)
        
        # 删除按钮
        delete_btn = tk.Button(edit_frame, text="🗑️ 删除", 
                             font=("Microsoft YaHei", 9), bg='#E74C3C', fg='white',
                             relief=tk.FLAT, padx=8, pady=4, cursor='hand2',
                             command=lambda: self.video_generator.delete_news() if self.video_generator else None)
        delete_btn.pack(side=tk.RIGHT)
        
        btn_frame = tk.Frame(left_frame, bg='#ECF0F1')
        btn_frame.pack(fill=tk.X, padx=10, pady=(0, 5))
        
        generate_btn = tk.Button(btn_frame, text="📊 生成数据", 
                               font=("Microsoft YaHei", 10), bg='#3498DB', fg='white',
                               relief=tk.FLAT, padx=10, pady=5, cursor='hand2',
                               command=lambda: self.video_generator.generate_video_data() if self.video_generator else None)
        generate_btn.pack(side=tk.LEFT)
        
        save_btn = tk.Button(btn_frame, text="💾 保存数据", 
                           font=("Microsoft YaHei", 10), bg='#27AE60', fg='white',
                           relief=tk.FLAT, padx=10, pady=5, cursor='hand2',
                           command=lambda: self.video_generator.save_video_data() if self.video_generator else None)
        save_btn.pack(side=tk.LEFT, padx=5)
        
        export_btn = tk.Button(btn_frame, text="📤 导出图片", 
                              font=('Microsoft YaHei', 10), bg='#9B59B6', fg='white',
                              relief=tk.FLAT, padx=10, pady=5, cursor='hand2',
                              command=lambda: self.video_generator.export_news_images() if self.video_generator else None)
        export_btn.pack(side=tk.LEFT, padx=5)
        
        # 区域选择按钮
        select_btn = tk.Button(btn_frame, text="🎯 区域选择", 
                              font=('Microsoft YaHei', 10), bg='#3498DB', fg='white',
                              relief=tk.FLAT, padx=10, pady=5, cursor='hand2',
                              command=lambda: self.video_generator.enable_region_selection() if self.video_generator else None)
        select_btn.pack(side=tk.LEFT, padx=5)
        
        # 生成剪映草稿按钮
        jianying_btn = tk.Button(btn_frame, text="🎬 剪映草稿", 
                               font=("Microsoft YaHei", 10), bg='#F39C12', fg='white',
                               relief=tk.FLAT, padx=10, pady=5, cursor='hand2',
                               command=lambda: self.video_generator.generate_jianying_draft() if self.video_generator else None)
        jianying_btn.pack(side=tk.RIGHT, padx=5)
        
        # 同步TTS和字幕时序按钮
        sync_btn = tk.Button(btn_frame, text="⏱️ 同步时序", 
                           font=("Microsoft YaHei", 10), bg='#9B59B6', fg='white',
                           relief=tk.FLAT, padx=10, pady=5, cursor='hand2',
                           command=lambda: self.video_generator.process_jianying_draft_timing() if self.video_generator else None)
        sync_btn.pack(side=tk.RIGHT, padx=5)
        
        video_btn = tk.Button(btn_frame, text="🎬 生成视频", 
                            font=("Microsoft YaHei", 10), bg='#E74C3C', fg='white',
                            relief=tk.FLAT, padx=10, pady=5, cursor='hand2',
                            command=lambda: self.video_generator.generate_video() if self.video_generator else None)
        video_btn.pack(side=tk.RIGHT)
        
        right_frame = tk.Frame(main_paned)
        main_paned.add(right_frame, minsize=450)
        
        preview_title = tk.Frame(right_frame, bg='#2C3E50')
        preview_title.pack(fill=tk.X)
        tk.Label(preview_title, text="🖼️ 图片预览", font=("Microsoft YaHei", 12, "bold"), 
                bg='#2C3E50', fg='white').pack(pady=8)
        
        preview_canvas_frame = tk.Frame(right_frame, bg='#BDC3C7', relief=tk.SUNKEN, bd=1)
        preview_canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.video_preview_canvas = tk.Canvas(preview_canvas_frame, bg='white', highlightthickness=0)
        self.video_preview_canvas.pack(fill=tk.BOTH, expand=True)
        
        self.video_preview_canvas.create_text(
            200, 200, text="选择新闻条目查看预览", 
            font=("Microsoft YaHei", 12), fill='#95A5A6'
        )
        
        progress_frame = tk.Frame(right_frame, bg='#ECF0F1')
        progress_frame.pack(fill=tk.X, padx=10, pady=(0, 5))
        
        self.progress_label = tk.Label(progress_frame, text="就绪", font=("Microsoft YaHei", 9), 
                                     bg='#ECF0F1', fg='#34495E')
        self.progress_label.pack(side=tk.LEFT, padx=10, pady=3)
        
        self.progress_bar = ttk.Progressbar(progress_frame, length=200, mode='determinate')
        self.progress_bar.pack(side=tk.RIGHT, padx=10, pady=3, fill=tk.X, expand=True)
        
        self.finalize_modules()
    
    def update_status(self, message, color="blue"):
        self.status_label.config(text=message, fg=color)
        self.root.update()
    
    def on_tab_changed(self, event):
        """处理页签切换事件"""
        selected_tab = self.notebook.select()
        tab_text = self.notebook.tab(selected_tab, "text")
        
        # 当切换到视频生成页签时，根据当前选中的新闻图片加载JSON文件
        if tab_text == "视频生成" and self.video_generator:
            # 获取当前选中的图片文件名
            selection = self.image_listbox.curselection()
            if selection:
                image_filename = self.image_listbox.get(selection[0])
                self.video_generator.silent_load_json(image_filename)
    
    def on_date_change(self, *args):
        if self.date_var.get() == "custom":
            self.custom_date_entry.config(state='normal')
        else:
            self.custom_date_entry.config(state='disabled')
    
    def on_download_click(self, newspaper_code):
        self.wsj_btn.config(state=tk.DISABLED)
        self.ft_btn.config(state=tk.DISABLED)
        self.batch_btn.config(state=tk.DISABLED)
        
        self.downloader.download_newspaper(
            newspaper_code, 
            self.date_var, 
            self.custom_date_entry, 
            self.refresh_image_list
        )
        
        self.wsj_btn.config(state=tk.NORMAL)
        self.ft_btn.config(state=tk.NORMAL)
        self.batch_btn.config(state=tk.NORMAL)
    
    def on_batch_download_click(self):
        self.wsj_btn.config(state=tk.DISABLED)
        self.ft_btn.config(state=tk.DISABLED)
        self.batch_btn.config(state=tk.DISABLED)
        
        self.downloader.download_all_newspapers(
            self.date_var, 
            self.custom_date_entry, 
            self.refresh_image_list
        )
        
        self.wsj_btn.config(state=tk.NORMAL)
        self.ft_btn.config(state=tk.NORMAL)
        self.batch_btn.config(state=tk.NORMAL)
    
    def on_image_select(self, event):
        selection = self.image_listbox.curselection()
        if selection:
            filename = self.image_listbox.get(selection[0])
            filepath = os.path.join(self.download_dir, filename)
            # 加载分析结果文本
            news_blocks = self.analyzer.load_analysis_result(filename, self.download_dir)
            # 在首页显示图片预览（如果有分析结果，显示带标记的图片）
            if news_blocks:
                self.analyzer.show_preview_with_blocks(filepath, news_blocks)
            else:
                self.analyzer.show_simple_preview(filepath, self.preview_canvas)
            
            # 加载对应的prompt.txt文件（如果存在）
            base_name = os.path.splitext(filename)[0]
            image_prompt_file = os.path.join(self.analysis_dir, f"{base_name}_prompt.txt")
            if os.path.exists(image_prompt_file):
                try:
                    with open(image_prompt_file, 'r', encoding='utf-8') as f:
                        prompt_content = f.read()
                    # 在prompt文本框中显示
                    self.prompt_text.delete(1.0, tk.END)
                    self.prompt_text.insert(tk.END, prompt_content)
                except Exception as e:
                    print(f"加载prompt文件失败: {str(e)}")
            else:
                # 如果没有prompt.txt文件，清空prompt文本框
                self.prompt_text.delete(1.0, tk.END)
                self.prompt_text.insert(tk.END, "暂无Prompt文件\n\n点击'生成Prompt'按钮创建")
    
    def on_image_double_click(self, event):
        selection = self.image_listbox.curselection()
        if selection:
            filename = self.image_listbox.get(selection[0])
            filepath = os.path.join(self.download_dir, filename)
            # 双击打开可缩放的图片预览
            self.analyzer.show_image_preview(filepath)
    
    def on_refresh_list(self):
        self.refresh_image_list()
    
    def on_analyze_click(self):
        selection = self.image_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一张图片")
            return
        
        filename = self.image_listbox.get(selection[0])
        self.analyzer.analyze_image(filename, self.download_dir)
    
    def on_export_click(self):
        selection = self.image_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一张图片")
            return
        
        filename = self.image_listbox.get(selection[0])
        source_filepath = os.path.join(self.download_dir, filename)
        export_dir = self.config.get('export_settings', {}).get('export_directory', 'E:\中文听见\报纸头版')
        
        success, message = export_image(source_filepath, export_dir, filename)
        if success:
            messagebox.showinfo("导出成功", message)
        else:
            messagebox.showerror("导出失败", message)
    
    def on_generate_prompt(self):
        """生成prompt并保存到prompt.txt"""
        selection = self.image_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一张图片")
            return
        
        filename = self.image_listbox.get(selection[0])
        filepath = os.path.join(self.download_dir, filename)
        
        try:
            # 读取图片宽高
            image = Image.open(filepath)
            width, height = image.size
            
            # 读取prompt.txt模板
            prompt_file = self.config.get('analysis_prompt_file', 'prompt.txt')
            with open(prompt_file, 'r', encoding='utf-8') as f:
                prompt_template = f.read()
            
            # 动态填入图片宽高
            prompt = prompt_template.replace('[WIDTH]', str(width)).replace('[HEIGHT]', str(height))
            
            # 保存到该图片的prompt.txt
            base_name = os.path.splitext(filename)[0]
            image_prompt_file = os.path.join(self.analysis_dir, f"{base_name}_prompt.txt")
            
            with open(image_prompt_file, 'w', encoding='utf-8') as f:
                f.write(prompt)
            
            # 在prompt文本框中显示
            self.prompt_text.delete(1.0, tk.END)
            self.prompt_text.insert(tk.END, prompt)
            
            messagebox.showinfo("生成成功", f"Prompt已生成并保存到:\n{image_prompt_file}")
            
        except Exception as e:
            messagebox.showerror("错误", f"生成Prompt失败: {str(e)}")
    
    def on_save_prompt(self):
        """保存修改后的prompt"""
        selection = self.image_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一张图片")
            return
        
        filename = self.image_listbox.get(selection[0])
        prompt_content = self.prompt_text.get(1.0, tk.END)
        
        # 保存到该图片的prompt.txt
        base_name = os.path.splitext(filename)[0]
        image_prompt_file = os.path.join(self.analysis_dir, f"{base_name}_prompt.txt")
        
        try:
            with open(image_prompt_file, 'w', encoding='utf-8') as f:
                f.write(prompt_content)
            
            messagebox.showinfo("保存成功", f"Prompt已保存到:\n{image_prompt_file}")
            
        except Exception as e:
            messagebox.showerror("错误", f"保存Prompt失败: {str(e)}")
    
    def on_text_focus_in(self, event):
        """文本框获得焦点时，保持图片列表的选中状态"""
        selection = self.image_listbox.curselection()
        if selection:
            # 记录当前选择的索引
            self.current_selected_index = selection[0]
    
    def on_text_focus_out(self, event):
        """文本框失去焦点时，恢复图片列表的选中状态"""
        if hasattr(self, 'current_selected_index'):
            # 恢复选择状态
            self.image_listbox.selection_set(self.current_selected_index)
            self.image_listbox.activate(self.current_selected_index)
            self.image_listbox.see(self.current_selected_index)
    
    def on_text_mouse_down(self, event):
        """文本框鼠标按下时，记录当前选中状态"""
        selection = self.image_listbox.curselection()
        if selection:
            # 记录当前选择的索引
            self.current_selected_index = selection[0]
    
    def on_text_mouse_drag(self, event):
        """文本框鼠标拖动时，保持选中状态"""
        if hasattr(self, 'current_selected_index'):
            # 保持选择状态
            self.image_listbox.selection_set(self.current_selected_index)
            self.image_listbox.activate(self.current_selected_index)
    
    def on_text_mouse_up(self, event):
        """文本框鼠标释放时，恢复选中状态"""
        if hasattr(self, 'current_selected_index'):
            # 恢复选择状态
            self.image_listbox.selection_set(self.current_selected_index)
            self.image_listbox.activate(self.current_selected_index)
            self.image_listbox.see(self.current_selected_index)
    
    def on_save_result(self):
        """保存修改后的分析结果"""
        selection = self.image_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一张图片")
            return
        
        # 记录当前选择的索引
        selected_index = selection[0]
        filename = self.image_listbox.get(selected_index)
        result_content = self.result_text.get(1.0, tk.END)
        
        # 保存到txt文件
        base_name = os.path.splitext(filename)[0]
        txt_file = os.path.join(self.analysis_dir, f"{base_name}.txt")
        
        try:
            with open(txt_file, 'w', encoding='utf-8') as f:
                f.write(result_content)
            
            # 尝试从txt内容中提取JSON数据并保存
            json_file = os.path.join(self.analysis_dir, f"{base_name}.json")
            
            # 简单的JSON提取逻辑
            import re
            import json
            json_match = re.search(r'\{[\s\S]*\}', result_content)
            if json_match:
                try:
                    json_str = json_match.group(0)
                    json_data = json.loads(json_str)
                    with open(json_file, 'w', encoding='utf-8') as f:
                        json.dump(json_data, f, ensure_ascii=False, indent=2)
                    messagebox.showinfo("保存成功", f"分析结果已保存到:\nTXT文件: {txt_file}\nJSON文件: {json_file}")
                except Exception as e:
                    messagebox.showinfo("部分保存成功", f"TXT文件已保存，但JSON提取失败: {str(e)}")
            else:
                messagebox.showinfo("保存成功", f"TXT文件已保存到:\n{txt_file}")
            
            # 恢复选择状态
            self.image_listbox.selection_set(selected_index)
            self.image_listbox.activate(selected_index)
            self.image_listbox.see(selected_index)
            
        except Exception as e:
            messagebox.showerror("错误", f"保存分析结果失败: {str(e)}")
            # 即使出错也要恢复选择状态
            self.image_listbox.selection_set(selected_index)
            self.image_listbox.activate(selected_index)
            self.image_listbox.see(selected_index)
    
    def refresh_image_list(self):
        self.image_listbox.delete(0, tk.END)
        image_files = refresh_image_list(self.download_dir)
        for filename in image_files:
            self.image_listbox.insert(tk.END, filename)
    
    def on_news_select(self, event):
        if self.video_generator:
            self.video_generator.on_news_select(event)
    
    def on_news_double_click(self, event):
        if self.video_generator:
            self.video_generator.edit_news_inline(event)


if __name__ == "__main__":
    root = tk.Tk()
    app = EnhancedKioskoDownloader(root)
    root.mainloop()