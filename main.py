import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from datetime import datetime
from PIL import Image, ImageTk
import os
import threading

from downloader import NewspaperDownloader
from analyzer import ImageAnalyzer
from video_generator.main import VideoGenerator
from utils import load_config, refresh_image_list
from gemini_automation import GeminiAutomation
from ft_automation import FTAutomation
from wsj_automation import WSJAutomation
from browser_manager import browser_manager


class EnhancedKioskoDownloader:
    def __init__(self, root):
        self.root = root
        self.root.title("新闻报纸下载与分析工具")
        self.root.geometry("{0}x{1}+0+0".format(self.root.winfo_screenwidth(), self.root.winfo_screenheight()))
        self.root.state('zoomed')
        
        self.config = load_config()
        
        self.download_dir = self.config['download_settings']['save_directory']
        self.analysis_dir = self.config.get('analysis_settings', {}).get('analysis_directory', 'analysis_results')
        
        self.saved_image_selection = None
        
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
        self.video_generator.set_news_listbox(self.news_frame)
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
        
        self.network_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.network_frame, text='网络发布')
        self.create_network_publishing_tab()
        
        # 绑定页签切换事件
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)
    
    def create_home_tab(self):
        main_frame = tk.Frame(self.home_frame, bg='#F8F9FA')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        main_paned = tk.PanedWindow(main_frame, orient=tk.HORIZONTAL, 
                                    sashrelief=tk.FLAT, sashwidth=6,
                                    bg='#F8F9FA')
        main_paned.pack(fill=tk.BOTH, expand=True)
        
        left_column = tk.Frame(main_paned, bg='white', width=380)
        main_paned.add(left_column, minsize=260)
        
        middle_column = tk.Frame(main_paned, bg='white')
        main_paned.add(middle_column, minsize=400)
        
        right_column = tk.Frame(main_paned, bg='white')
        main_paned.add(right_column, minsize=400)
        
        self._create_left_column(left_column)
        self._create_middle_column(middle_column)
        self._create_right_column(right_column)
        
        self.refresh_image_list()
    
    def _create_left_column(self, parent):
        parent.pack_propagate(False)
        
        download_section = tk.Frame(parent, bg='white')
        download_section.pack(fill=tk.X, padx=10, pady=10)
        
        header = tk.Frame(download_section, bg='#2C3E50')
        header.pack(fill=tk.X)
        tk.Label(header, text="📥 下载中心", 
                font=("Microsoft YaHei", 12, "bold"),
                bg='#2C3E50', fg='white').pack(pady=10)
        
        btn_frame = tk.Frame(download_section, bg='white')
        btn_frame.pack(fill=tk.X, pady=10)
        
        row1 = tk.Frame(btn_frame, bg='white')
        row1.pack(fill=tk.X, pady=2)
        
        self.browser_btn = tk.Button(row1, text="打开浏览器",
                                     font=("Microsoft YaHei", 9),
                                     bg='#27AE60', fg='white',
                                     relief=tk.FLAT, padx=10, pady=6,
                                     cursor='hand2',
                                     command=self.on_open_browser)
        self.browser_btn.pack(side=tk.LEFT, padx=2, expand=True, fill=tk.X)
        
        self.wsj_browser_btn = tk.Button(row1, text="华尔街日报(浏览器)",
                                         font=("Microsoft YaHei", 9),
                                         bg='#E74C3C', fg='white',
                                         relief=tk.FLAT, padx=10, pady=6,
                                         cursor='hand2',
                                         command=self.on_wsj_browser_download)
        self.wsj_browser_btn.pack(side=tk.LEFT, padx=2, expand=True, fill=tk.X)
        
        self.ft_browser_btn = tk.Button(row1, text="金融时报(浏览器)",
                                        font=("Microsoft YaHei", 9),
                                        bg='#9B59B6', fg='white',
                                        relief=tk.FLAT, padx=10, pady=6,
                                        cursor='hand2',
                                        command=self.on_ft_browser_download)
        self.ft_browser_btn.pack(side=tk.LEFT, padx=2, expand=True, fill=tk.X)
        
        row2 = tk.Frame(btn_frame, bg='white')
        row2.pack(fill=tk.X, pady=2)
        
        self.batch_btn = tk.Button(row2, text="批量下载",
                                  font=("Microsoft YaHei", 9),
                                  bg='#F39C12', fg='white',
                                  relief=tk.FLAT, padx=10, pady=6,
                                  cursor='hand2',
                                  command=self.on_batch_download_click)
        self.batch_btn.pack(side=tk.LEFT, padx=2, expand=True, fill=tk.X)
        
        date_frame = tk.Frame(download_section, bg='#F8F9FA')
        date_frame.pack(fill=tk.X, pady=5, padx=5)
        
        tk.Label(date_frame, text="📅 日期:",
                font=("Microsoft YaHei", 9),
                bg='#F8F9FA').pack(side=tk.LEFT, padx=5)
        
        self.date_var = tk.StringVar(value="today")
        
        tk.Radiobutton(date_frame, text="今日", variable=self.date_var, value="today", 
                      font=("Microsoft YaHei", 9), bg='#F8F9FA').pack(side=tk.LEFT, padx=2)
        tk.Radiobutton(date_frame, text="昨日", variable=self.date_var, value="yesterday", 
                      font=("Microsoft YaHei", 9), bg='#F8F9FA').pack(side=tk.LEFT, padx=2)
        tk.Radiobutton(date_frame, text="自定义", variable=self.date_var, value="custom", 
                      font=("Microsoft YaHei", 9), bg='#F8F9FA').pack(side=tk.LEFT, padx=2)
        
        self.custom_date_entry = tk.Entry(date_frame, width=10, font=("Microsoft YaHei", 9))
        self.custom_date_entry.pack(side=tk.LEFT, padx=5)
        self.custom_date_entry.insert(0, datetime.now().strftime('%Y/%m/%d'))
        self.custom_date_entry.config(state='disabled')
        
        self.date_var.trace('w', self.on_date_change)
        
        self.status_label = tk.Label(download_section, text="✅ 准备就绪",
                                    font=("Microsoft YaHei", 9),
                                    bg='white', fg='#27AE60')
        self.status_label.pack(pady=5)
        
        separator = tk.Frame(parent, bg='#E9ECEF', height=2)
        separator.pack(fill=tk.X, padx=10, pady=5)
        
        list_section = tk.Frame(parent, bg='white')
        list_section.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        list_header = tk.Frame(list_section, bg='#34495E')
        list_header.pack(fill=tk.X)
        
        tk.Label(list_header, text="📰 图片列表",
                font=("Microsoft YaHei", 12, "bold"),
                bg='#34495E', fg='white').pack(side=tk.LEFT, padx=10, pady=8)
        
        self.image_count_label = tk.Label(list_header, text="共 0 张",
                                         font=("Microsoft YaHei", 9),
                                         bg='#34495E', fg='#BDC3C7')
        self.image_count_label.pack(side=tk.RIGHT, padx=10)
        
        status_bar = tk.Frame(list_section, bg='#F8F9FA')
        status_bar.pack(fill=tk.X)
        
        self.gemini_status_label = tk.Label(status_bar, text="初始化中...",
                                           font=("Microsoft YaHei", 9),
                                           bg='#F8F9FA', fg='#95A5A6')
        self.gemini_status_label.pack(side=tk.LEFT, padx=10, pady=5)
        
        list_frame = tk.Frame(list_section, bg='#E9ECEF')
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.image_listbox = tk.Listbox(list_frame,
                                        font=("Microsoft YaHei", 10),
                                        yscrollcommand=scrollbar.set,
                                        bg='white',
                                        selectbackground='#3498DB',
                                        selectforeground='white',
                                        relief=tk.FLAT,
                                        highlightthickness=0)
        self.image_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=1, pady=1)
        scrollbar.config(command=self.image_listbox.yview)
        
        self.image_listbox.bind('<<ListboxSelect>>', self.on_image_select)
        self.image_listbox.bind('<Double-1>', self.on_image_double_click)
        
        action_frame = tk.Frame(list_section, bg='#F8F9FA')
        action_frame.pack(fill=tk.X, pady=5)
        
        actions = [
            ("🔄 刷新", '#3498DB', self.on_refresh_list),
            ("📊 分析", '#9B59B6', self.on_analyze_click),
            ("🌐 Gemini", '#E67E22', self.on_open_gemini),
            ("💾 保存图片", '#27AE60', self.on_download_image),
        ]
        
        for text, color, cmd in actions:
            tk.Button(action_frame, text=text, command=cmd,
                     font=("Microsoft YaHei", 9),
                     bg=color, fg='white',
                     relief=tk.FLAT, padx=8, pady=5,
                     cursor='hand2').pack(side=tk.LEFT, padx=2)
    
    def _create_middle_column(self, parent):
        preview_section = tk.Frame(parent, bg='white')
        preview_section.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        header = tk.Frame(preview_section, bg='#2C3E50')
        header.pack(fill=tk.X)
        
        tk.Label(header, text="🖼️ 图片预览",
                font=("Microsoft YaHei", 12, "bold"),
                bg='#2C3E50', fg='white').pack(pady=10)
        
        canvas_frame = tk.Frame(preview_section, bg='#E9ECEF')
        canvas_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        self.preview_canvas = tk.Canvas(canvas_frame, bg='white', highlightthickness=0)
        self.preview_canvas.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        
        self.preview_text_id = self.preview_canvas.create_text(
            200, 300, text="选择左侧图片查看预览",
            font=("Microsoft YaHei", 14), fill='#95A5A6'
        )
        
        self.preview_canvas.bind('<Configure>', self._on_preview_resize)
    
    def _on_preview_resize(self, event):
        self.preview_canvas.coords(self.preview_text_id, event.width // 2, event.height // 2)
    
    def _create_right_column(self, parent):
        right_paned = tk.PanedWindow(parent, orient=tk.VERTICAL,
                                     sashrelief=tk.FLAT, sashwidth=6,
                                     bg='white')
        right_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        prompt_section = tk.Frame(right_paned, bg='white')
        right_paned.add(prompt_section, minsize=200, height=200)
        
        prompt_header = tk.Frame(prompt_section, bg='#34495E')
        prompt_header.pack(fill=tk.X)
        
        tk.Label(prompt_header, text="💬 Prompt",
                font=("Microsoft YaHei", 12, "bold"),
                bg='#34495E', fg='white').pack(side=tk.LEFT, padx=10, pady=8)
        
        btn_frame = tk.Frame(prompt_header, bg='#34495E')
        btn_frame.pack(side=tk.RIGHT, padx=10)
        
        tk.Button(btn_frame, text="� 生成",
                 font=("Microsoft YaHei", 9),
                 bg='#27AE60', fg='white',
                 relief=tk.FLAT, padx=10, pady=3,
                 cursor='hand2',
                 command=self.on_generate_prompt).pack(side=tk.LEFT, padx=2)
        
        tk.Button(btn_frame, text="💾",
                 font=("Microsoft YaHei", 9),
                 bg='#27AE60', fg='white',
                 relief=tk.FLAT, padx=8, pady=3,
                 cursor='hand2',
                 command=self.on_save_prompt).pack(side=tk.LEFT, padx=2)
        
        prompt_text_frame = tk.Frame(prompt_section, bg='#E9ECEF')
        prompt_text_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        prompt_scroll = tk.Scrollbar(prompt_text_frame)
        prompt_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.prompt_text = tk.Text(prompt_text_frame,
                                  font=("Microsoft YaHei", 10),
                                  wrap=tk.WORD,
                                  bg='white',
                                  relief=tk.FLAT,
                                  padx=10, pady=10,
                                  yscrollcommand=prompt_scroll.set)
        self.prompt_text.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        prompt_scroll.config(command=self.prompt_text.yview)
        
        self.prompt_text.bind('<FocusIn>', self.on_text_focus_in)
        self.prompt_text.bind('<FocusOut>', self.on_text_focus_out)
        self.prompt_text.bind('<Button-1>', self.on_text_mouse_down)
        self.prompt_text.bind('<B1-Motion>', self.on_text_mouse_drag)
        self.prompt_text.bind('<ButtonRelease-1>', self.on_text_mouse_up)
        
        result_section = tk.Frame(right_paned, bg='white')
        right_paned.add(result_section, minsize=400, height=400)
        
        result_header = tk.Frame(result_section, bg='#2C3E50')
        result_header.pack(fill=tk.X)
        
        tk.Label(result_header, text="📝 分析结果",
                font=("Microsoft YaHei", 12, "bold"),
                bg='#2C3E50', fg='white').pack(side=tk.LEFT, padx=10, pady=8)
        
        tk.Button(result_header, text="💾 保存",
                 font=("Microsoft YaHei", 9),
                 bg='#27AE60', fg='white',
                 relief=tk.FLAT, padx=10, pady=3,
                 cursor='hand2',
                 command=self.on_save_result).pack(side=tk.RIGHT, padx=10)
        
        result_text_frame = tk.Frame(result_section, bg='#E9ECEF')
        result_text_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        scrollbar = tk.Scrollbar(result_text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.result_text = tk.Text(result_text_frame,
                                  font=("Microsoft YaHei", 10),
                                  wrap=tk.WORD,
                                  bg='white',
                                  relief=tk.FLAT,
                                  padx=10, pady=10,
                                  yscrollcommand=scrollbar.set)
        self.result_text.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        scrollbar.config(command=self.result_text.yview)
        
        self.result_text.bind('<FocusIn>', self.on_text_focus_in)
        self.result_text.bind('<FocusOut>', self.on_text_focus_out)
        self.result_text.bind('<Button-1>', self.on_text_mouse_down)
        self.result_text.bind('<B1-Motion>', self.on_text_mouse_drag)
        self.result_text.bind('<ButtonRelease-1>', self.on_text_mouse_up)
    
    def create_video_tab(self):
        main_paned = tk.PanedWindow(self.video_frame, orient=tk.HORIZONTAL, sashrelief=tk.RAISED, sashwidth=4)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        left_frame = tk.Frame(main_paned, width=1200)
        main_paned.add(left_frame, minsize=800)
        
        title_frame = tk.Frame(left_frame, bg='#2C3E50')
        title_frame.pack(fill=tk.X)
        tk.Label(title_frame, text="📰 新闻编辑", font=("Microsoft YaHei", 12, "bold"), 
                bg='#2C3E50', fg='white').pack(pady=8)
        
        # 新闻编辑区域 - 使用多个文本框
        news_container = tk.Frame(left_frame, bg='#BDC3C7', relief=tk.SUNKEN, bd=1)
        news_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 滚动条
        news_scroll = tk.Scrollbar(news_container)
        news_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 使用Canvas来实现滚动
        self.news_canvas = tk.Canvas(news_container, yscrollcommand=news_scroll.set)
        self.news_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 内部框架，用于放置文本框
        self.news_frame = tk.Frame(self.news_canvas)
        self.news_canvas.create_window((0, 0), window=self.news_frame, anchor='nw')
        
        # 配置滚动条
        news_scroll.config(command=self.news_canvas.yview)
        
        # 绑定事件以更新滚动区域
        def update_scrollregion(event):
            self.news_canvas.configure(scrollregion=self.news_canvas.bbox('all'))
        
        self.news_frame.bind('<Configure>', update_scrollregion)
        
        # 存储新闻文本框和选择状态
        self.news_textboxes = []
        self.news_selections = []
        
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
        delete_btn = tk.Button(edit_frame, text="🗑️ 删除选中", 
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

        # 加载CosyVoice模型按钮
        load_model_btn = tk.Button(btn_frame, text="🔊 加载模型",
                            font=("Microsoft YaHei", 10), bg='#16A085', fg='white',
                            relief=tk.FLAT, padx=10, pady=5, cursor='hand2',
                            command=lambda: self.video_generator.load_cosyvoice_model() if self.video_generator else None)
        load_model_btn.pack(side=tk.LEFT, padx=5)

        # 测试音色按钮
        test_voice_btn = tk.Button(btn_frame, text="🎵 测试音色",
                            font=("Microsoft YaHei", 10), bg='#E67E22', fg='white',
                            relief=tk.FLAT, padx=10, pady=5, cursor='hand2',
                            command=lambda: self.video_generator.test_voice_clone() if self.video_generator else None)
        test_voice_btn.pack(side=tk.LEFT, padx=5)

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

        # 截图按钮
        screenshot_btn = tk.Button(btn_frame, text="📷 截图",
                            font=("Microsoft YaHei", 10), bg='#16A085', fg='white',
                            relief=tk.FLAT, padx=10, pady=5, cursor='hand2',
                            command=lambda: self.video_generator.capture_news_screenshots() if self.video_generator else None)
        screenshot_btn.pack(side=tk.RIGHT, padx=5)
        
        # 完美矩形按钮
        perfect_rect_btn = tk.Button(btn_frame, text="📐 完美矩形",
                            font=("Microsoft YaHei", 10), bg='#1ABC9C', fg='white',
                            relief=tk.FLAT, padx=10, pady=5, cursor='hand2',
                            command=lambda: self.video_generator.adjust_to_perfect_rectangle() if self.video_generator else None)
        perfect_rect_btn.pack(side=tk.RIGHT, padx=5)

        video_btn = tk.Button(btn_frame, text="🎬 生成视频",
                            font=("Microsoft YaHei", 10), bg='#E74C3C', fg='white',
                            relief=tk.FLAT, padx=10, pady=5, cursor='hand2',
                            command=lambda: self.video_generator.generate_video() if self.video_generator else None)
        video_btn.pack(side=tk.RIGHT)

        right_frame = tk.Frame(main_paned, width=400)
        main_paned.add(right_frame, minsize=300)
        
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
    
    def create_network_publishing_tab(self):
        """创建网络发布页签内容"""
        main_frame = tk.Frame(self.network_frame, bg='#F5F6FA')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        main_paned = tk.PanedWindow(main_frame, orient=tk.VERTICAL, 
                                    sashrelief=tk.RIDGE, sashwidth=8,
                                    bg='#F5F6FA', showhandle=True)
        main_paned.pack(fill=tk.BOTH, expand=True)
        
        video_container = tk.Frame(main_paned, bg='#F5F6FA')
        main_paned.add(video_container, minsize=260, height=280)
        
        video_header = tk.Frame(video_container, bg='#E74C3C', height=40)
        video_header.pack(fill=tk.X)
        video_header.pack_propagate(False)
        tk.Label(video_header, text="📹 视频发布", 
                font=("Microsoft YaHei", 12, "bold"),
                bg='#E74C3C', fg='white').pack(side=tk.LEFT, padx=15, pady=8)
        
        video_publish_btn = tk.Button(video_header, 
                                      text="视频号发布", 
                                      command=self.open_video_publishing_page,
                                      font=("Microsoft YaHei", 9), 
                                      bg='white', fg='#E74C3C', 
                                      relief=tk.FLAT, padx=12, pady=3,
                                      cursor='hand2', activebackground='#FADBD8')
        video_publish_btn.pack(side=tk.RIGHT, padx=10, pady=6)
        
        video_content = tk.Frame(video_container, bg='white', relief=tk.FLAT)
        video_content.pack(fill=tk.BOTH, expand=True)
        
        video_file_frame = tk.Frame(video_content, bg='white')
        video_file_frame.pack(fill=tk.X, padx=15, pady=(12, 8))
        
        tk.Label(video_file_frame, text="视频文件", bg='white', 
                font=("Microsoft YaHei", 9), fg='#7F8C8D').pack(anchor=tk.W)
        
        file_input_frame = tk.Frame(video_file_frame, bg='white')
        file_input_frame.pack(fill=tk.X, pady=3)
        
        self.video_path_var = tk.StringVar(value="output/*.mp4")
        video_path_entry = tk.Entry(file_input_frame, textvariable=self.video_path_var, 
                                    font=("Microsoft YaHei", 10), 
                                    relief=tk.SOLID, bd=1, highlightthickness=0)
        video_path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4)
        
        browse_btn = tk.Button(file_input_frame, text="浏览", 
                              command=self.browse_video_file,
                              font=("Microsoft YaHei", 9), 
                              bg='#3498DB', fg='white', 
                              relief=tk.FLAT, padx=15, pady=4,
                              cursor='hand2')
        browse_btn.pack(side=tk.LEFT, padx=(8, 0))
        
        video_info_frame = tk.Frame(video_content, bg='white')
        video_info_frame.pack(fill=tk.X, padx=15, pady=(4, 12))
        
        video_desc_label_frame = tk.Frame(video_info_frame, bg='white')
        video_desc_label_frame.pack(fill=tk.X)
        tk.Label(video_desc_label_frame, text="视频描述", bg='white', 
                font=("Microsoft YaHei", 9), fg='#7F8C8D').pack(side=tk.LEFT)
        tk.Button(video_desc_label_frame, text="📋", 
                 command=lambda: self.copy_text_to_clipboard(self.video_desc_text),
                 font=("Segoe UI Emoji", 10), bg='#3498DB', fg='white',
                 relief=tk.FLAT, padx=5, pady=0, cursor='hand2').pack(side=tk.LEFT, padx=6)
        
        self.video_desc_text = tk.Text(video_info_frame, height=2, 
                                       font=("Microsoft YaHei", 10),
                                       wrap=tk.WORD, relief=tk.SOLID, bd=1,
                                       highlightthickness=0, bg='#FAFAFA')
        self.video_desc_text.pack(fill=tk.X, pady=3, ipady=2)
        
        short_title_label_frame = tk.Frame(video_info_frame, bg='white')
        short_title_label_frame.pack(fill=tk.X)
        tk.Label(short_title_label_frame, text="短标题", bg='white', 
                font=("Microsoft YaHei", 9), fg='#7F8C8D').pack(side=tk.LEFT)
        tk.Button(short_title_label_frame, text="📋", 
                 command=lambda: self.copy_var_to_clipboard(self.short_title_var),
                 font=("Segoe UI Emoji", 10), bg='#3498DB', fg='white',
                 relief=tk.FLAT, padx=5, pady=0, cursor='hand2').pack(side=tk.LEFT, padx=6)
        
        self.short_title_var = tk.StringVar()
        short_title_entry = tk.Entry(video_info_frame, 
                                     textvariable=self.short_title_var, 
                                     font=("Microsoft YaHei", 10),
                                     relief=tk.SOLID, bd=1, highlightthickness=0)
        short_title_entry.pack(fill=tk.X, pady=3, ipady=4)
        
        wechat_container = tk.Frame(main_paned, bg='#F5F6FA')
        main_paned.add(wechat_container, minsize=280)
        
        wechat_header = tk.Frame(wechat_container, bg='#27AE60', height=40)
        wechat_header.pack(fill=tk.X)
        wechat_header.pack_propagate(False)
        tk.Label(wechat_header, text="📝 公众号发布", 
                font=("Microsoft YaHei", 12, "bold"),
                bg='#27AE60', fg='white').pack(side=tk.LEFT, padx=15, pady=8)
        
        wechat_publish_btn = tk.Button(wechat_header, 
                                       text="公众号发布", 
                                       command=self.open_wechat_publishing_page,
                                       font=("Microsoft YaHei", 9), 
                                       bg='white', fg='#27AE60', 
                                       relief=tk.FLAT, padx=12, pady=3,
                                       cursor='hand2', activebackground='#D5F5E3')
        wechat_publish_btn.pack(side=tk.RIGHT, padx=10, pady=6)
        
        wechat_content = tk.Frame(wechat_container, bg='white', relief=tk.FLAT)
        wechat_content.pack(fill=tk.BOTH, expand=True)
        
        title_frame = tk.Frame(wechat_content, bg='white')
        title_frame.pack(fill=tk.X, padx=15, pady=(12, 4))
        
        title_label_frame = tk.Frame(title_frame, bg='white')
        title_label_frame.pack(fill=tk.X)
        tk.Label(title_label_frame, text="标题", bg='white', 
                font=("Microsoft YaHei", 9), fg='#7F8C8D').pack(side=tk.LEFT)
        tk.Button(title_label_frame, text="📋", 
                 command=lambda: self.copy_var_to_clipboard(self.wechat_title_var),
                 font=("Segoe UI Emoji", 10), bg='#27AE60', fg='white',
                 relief=tk.FLAT, padx=5, pady=0, cursor='hand2').pack(side=tk.LEFT, padx=6)
        
        self.wechat_title_var = tk.StringVar()
        title_entry = tk.Entry(title_frame, 
                              textvariable=self.wechat_title_var, 
                              font=("Microsoft YaHei", 10),
                              relief=tk.SOLID, bd=1, highlightthickness=0)
        title_entry.pack(fill=tk.X, pady=3, ipady=4)
        
        content_frame = tk.Frame(wechat_content, bg='white')
        content_frame.pack(fill=tk.BOTH, padx=15, pady=(4, 12), expand=True)
        
        content_label_frame = tk.Frame(content_frame, bg='white')
        content_label_frame.pack(fill=tk.X)
        tk.Label(content_label_frame, text="正文", bg='white', 
                font=("Microsoft YaHei", 9), fg='#7F8C8D').pack(side=tk.LEFT)
        tk.Button(content_label_frame, text="📋", 
                 command=lambda: self.copy_text_to_clipboard(self.wechat_content_text),
                 font=("Segoe UI Emoji", 10), bg='#27AE60', fg='white',
                 relief=tk.FLAT, padx=5, pady=0, cursor='hand2').pack(side=tk.LEFT, padx=6)
        
        content_text_frame = tk.Frame(content_frame, relief=tk.SOLID, bd=1)
        content_text_frame.pack(fill=tk.BOTH, expand=True, pady=3)
        
        self.wechat_content_text = tk.Text(content_text_frame, 
                                           font=("Microsoft YaHei", 10),
                                           wrap=tk.WORD, bg='#FAFAFA',
                                           relief=tk.FLAT, highlightthickness=0)
        self.wechat_content_text.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
    
    def copy_text_to_clipboard(self, text_widget):
        """复制Text控件内容到剪贴板"""
        content = text_widget.get("1.0", tk.END).strip()
        self.root.clipboard_clear()
        self.root.clipboard_append(content)
        self.show_auto_dismiss_message("复制成功", "内容已复制到剪贴板", 1500)
    
    def copy_var_to_clipboard(self, var):
        """复制StringVar内容到剪贴板"""
        content = var.get()
        self.root.clipboard_clear()
        self.root.clipboard_append(content)
        self.show_auto_dismiss_message("复制成功", "内容已复制到剪贴板", 1500)
    
    def browse_video_file(self):
        """浏览选择视频文件"""
        initial_dir = os.path.join(os.getcwd(), "output")
        if not os.path.exists(initial_dir):
            initial_dir = os.getcwd()
        
        file_path = filedialog.askopenfilename(
            title="选择视频文件",
            initialdir=initial_dir,
            filetypes=[("视频文件", "*.mp4 *.avi *.mov"), ("所有文件", "*.*")]
        )
        
        if file_path:
            self.video_path_var.set(file_path)
    
    def open_video_publishing_page(self):
        """打开微信视频号发布网页"""
        import webbrowser
        url = "https://channels.weixin.qq.com/platform/post/create"
        webbrowser.open(url)
        self.show_auto_dismiss_message("提示", "已在浏览器中打开视频号发布页面", 2000)
    
    def open_wechat_publishing_page(self):
        """打开公众号发布网页"""
        import webbrowser
        url = "https://mp.weixin.qq.com/cgi-bin/appmsg?t=media/appmsg_edit_v2&action=edit&isNew=1&type=77&token=1147579328&lang=zh_CN"
        webbrowser.open(url)
        self.show_auto_dismiss_message("提示", "已在浏览器中打开公众号发布页面", 2000)
    
    def load_network_publishing_data(self, json_file):
        """从JSON文件加载数据到网络发布页签"""
        try:
            import json
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if 'video_description' in data:
                self.video_desc_text.delete(1.0, tk.END)
                self.video_desc_text.insert(tk.END, data['video_description'])
            
            if 'short_title' in data:
                self.short_title_var.set(data['short_title'])
            
            if 'wechat_article' in data:
                article = data['wechat_article']
                if 'title' in article:
                    self.wechat_title_var.set(article['title'])
                # 公众号正文包含summary和content
                content_parts = []
                if 'summary' in article:
                    content_parts.append(article['summary'])
                if 'content' in article:
                    content_parts.append(article['content'])
                if content_parts:
                    self.wechat_content_text.delete(1.0, tk.END)
                    self.wechat_content_text.insert(tk.END, '\n\n'.join(content_parts))
                    
        except Exception as e:
            print(f"加载网络发布数据失败: {str(e)}")
    
    def update_status(self, message, color="blue"):
        self.status_label.config(text=message, fg=color)
        self.root.update()
    
    def on_tab_changed(self, event):
        """处理页签切换事件"""
        selected_tab = self.notebook.select()
        tab_text = self.notebook.tab(selected_tab, "text")
        
        # 获取当前图片选择状态（仅在首页有图片列表焦点时有效）
        selection = self.image_listbox.curselection()
        if selection:
            self.saved_image_selection = selection[0]
        
        # 当切换到视频生成页签时，根据当前选中的新闻图片加载JSON文件
        if tab_text == "视频生成" and self.video_generator:
            if selection:
                image_filename = self.image_listbox.get(selection[0])
                self.video_generator.silent_load_json(image_filename)
        
        # 当切换到网络发布页签时，加载JSON数据
        if tab_text == "网络发布":
            if selection:
                image_filename = self.image_listbox.get(selection[0])
                base_name = os.path.splitext(image_filename)[0]
                json_file = os.path.join(self.analysis_dir, f"{base_name}.json")
                if os.path.exists(json_file):
                    self.load_network_publishing_data(json_file)
        
        # 当切换回首页时，恢复图片列表的选择状态
        if tab_text == "首页":
            if hasattr(self, 'saved_image_selection') and self.saved_image_selection is not None:
                try:
                    idx = self.saved_image_selection
                    self.image_listbox.selection_clear(0, tk.END)
                    self.image_listbox.selection_set(idx)
                    self.image_listbox.activate(idx)
                    self.image_listbox.see(idx)
                    self.image_listbox.event_generate('<<ListboxSelect>>')
                except:
                    pass
    
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
            
            # 同时加载网络发布页签的JSON数据
            json_file = os.path.join(self.analysis_dir, f"{base_name}.json")
            if os.path.exists(json_file):
                self.load_network_publishing_data(json_file)
    
    def on_image_double_click(self, event):
        selection = self.image_listbox.curselection()
        if selection:
            filename = self.image_listbox.get(selection[0])
            filepath = os.path.join(self.download_dir, filename)
            # 双击打开可缩放的图片预览
            self.analyzer.show_image_preview(filepath)
    
    def show_auto_dismiss_message(self, title, message, duration=2000):
        """显示自动消失的消息提示
        
        Args:
            title: 标题
            message: 消息内容
            duration: 显示时长（毫秒），默认2秒
        """
        # 创建顶级窗口
        popup = tk.Toplevel(self.root)
        popup.title(title)
        popup.geometry("300x80")
        
        # 计算位置（在主窗口中央）
        popup.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - popup.winfo_width()) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - popup.winfo_height()) // 2
        popup.geometry(f"+{x}+{y}")
        
        # 设置为工具窗口样式（无任务栏图标）
        popup.attributes('-toolwindow', True)
        popup.attributes('-topmost', True)
        
        # 添加消息内容
        tk.Label(popup, text=message, font=("Microsoft YaHei", 10), 
                justify='center', wraplength=280).pack(expand=True)
        
        # 自动关闭
        popup.after(duration, popup.destroy)
    
    def on_refresh_list(self):
        self.refresh_image_list()
    
    def on_open_browser(self):
        """打开Chrome浏览器"""
        def run_open_browser():
            try:
                self.update_status("正在启动浏览器...", "blue")
                
                def status_callback(message):
                    self.update_status(message, "blue")
                    self.root.update()
                
                result = browser_manager.start_chrome(status_callback=status_callback)
                
                if result:
                    self.update_status("浏览器已启动", "green")
                else:
                    self.update_status("浏览器启动失败", "red")
                    messagebox.showerror("错误", "无法启动浏览器")
                    
            except Exception as e:
                import traceback
                error_details = traceback.format_exc()
                self.update_status(f"发生错误: {str(e)}", "red")
                print(f"[异常] 浏览器启动失败: {str(e)}")
                print(error_details)
        
        thread = threading.Thread(target=run_open_browser, daemon=True)
        thread.start()
    
    def on_ft_browser_download(self):
        """通过浏览器下载金融时报首页"""
        def run_ft_automation():
            try:
                self.update_status("正在启动金融时报下载...", "blue")
                
                def progress_callback(message, progress):
                    if progress:
                        pass
                    self.update_status(message, "blue")
                    self.root.update()
                
                def status_callback(message):
                    self.update_status(message, "blue")
                    self.root.update()
                
                ft = FTAutomation(
                    self.config,
                    progress_callback=progress_callback,
                    status_callback=status_callback
                )
                
                result = ft.download_ft_frontpage(self.download_dir)
                
                if result:
                    self.update_status(f"金融时报下载完成: {result}", "green")
                    self.refresh_image_list()
                    messagebox.showinfo("成功", f"金融时报首页已下载到:\n{result}")
                else:
                    self.update_status("金融时报下载失败", "red")
                    messagebox.showerror("错误", "未能下载金融时报首页，请手动操作")
                    
            except Exception as e:
                import traceback
                error_details = traceback.format_exc()
                self.update_status(f"发生错误: {str(e)}", "red")
                print(f"[异常] 金融时报下载失败: {str(e)}")
                print(error_details)
        
        thread = threading.Thread(target=run_ft_automation, daemon=True)
        thread.start()
    
    def on_wsj_browser_download(self):
        """通过浏览器下载华尔街日报首页"""
        def run_wsj_automation():
            try:
                self.update_status("正在启动华尔街日报下载...", "blue")
                
                def progress_callback(message, progress):
                    if progress:
                        pass
                    self.update_status(message, "blue")
                    self.root.update()
                
                def status_callback(message):
                    self.update_status(message, "blue")
                    self.root.update()
                
                wsj = WSJAutomation(
                    self.config,
                    progress_callback=progress_callback,
                    status_callback=status_callback
                )
                
                result = wsj.download_wsj_frontpage(self.download_dir)
                
                if result:
                    self.update_status(f"华尔街日报下载完成: {result}", "green")
                    self.refresh_image_list()
                    messagebox.showinfo("成功", f"华尔街日报首页已下载到:\n{result}")
                else:
                    self.update_status("华尔街日报下载失败", "red")
                    messagebox.showerror("错误", "未能下载华尔街日报首页，请手动操作")
                    
            except Exception as e:
                import traceback
                error_details = traceback.format_exc()
                self.update_status(f"发生错误: {str(e)}", "red")
                print(f"[异常] 华尔街日报下载失败: {str(e)}")
                print(error_details)
        
        thread = threading.Thread(target=run_wsj_automation, daemon=True)
        thread.start()
    
    def on_open_gemini(self):
        """打开Gemini页面并自动分析"""
        selection = self.image_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一张图片")
            return
        
        filename = self.image_listbox.get(selection[0])
        image_path = os.path.join(self.download_dir, filename)
        
        if not os.path.exists(image_path):
            messagebox.showerror("错误", f"图片文件不存在: {image_path}")
            return
        
        prompt_text = self.prompt_text.get("1.0", tk.END).strip()
        if not prompt_text:
            try:
                with open('prompt.txt', 'r', encoding='utf-8') as f:
                    prompt_text = f.read()
            except:
                messagebox.showwarning("警告", "请先生成或输入Prompt")
                return
        
        def run_gemini_automation():
            try:
                self.update_status("正在启动Gemini自动化...", "blue")

                def progress_callback(message, progress):
                    if progress:
                        self.progress_bar['value'] = progress
                    self.update_status(message, "blue")
                    self.root.update()
                    print(f"[进度] {message} - {progress}%")

                def status_callback(message):
                    self.update_status(message, "blue")
                    self.root.update()
                    print(f"[状态] {message}")

                gemini = GeminiAutomation(
                    self.config,
                    progress_callback=progress_callback,
                    status_callback=status_callback
                )

                result = gemini.open_gemini_and_analyze(prompt_text, image_path)

                if result:
                    self.result_text.delete(1.0, tk.END)
                    self.result_text.insert(tk.END, result)
                    self.update_status("Gemini分析完成", "green")
                    print("[成功] Gemini分析完成")
                else:
                    error_msg = "未能获取Gemini分析结果"
                    self.update_status("Gemini分析失败", "red")
                    print(f"[错误] {error_msg}")

            except Exception as e:
                import traceback
                error_details = traceback.format_exc()
                self.update_status(f"发生错误: {str(e)}", "red")
                print(f"[异常] Gemini自动化失败: {str(e)}")
                print(error_details)
        
        thread = threading.Thread(target=run_gemini_automation, daemon=True)
        thread.start()
    
    def on_analyze_click(self):
        selection = self.image_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一张图片")
            return
        
        filename = self.image_listbox.get(selection[0])
        self.analyzer.analyze_image(filename, self.download_dir)
    
    def on_download_image(self):
        """下载选中的图片到导出目录"""
        selection = self.image_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一张图片")
            return
        
        filename = self.image_listbox.get(selection[0])
        source_path = os.path.join(self.download_dir, filename)
        
        # 确定导出目录
        export_dir = self.config.get('export_settings', {}).get('export_directory', 'export')
        os.makedirs(export_dir, exist_ok=True)
        
        # 根据文件名确定报纸类型和目标文件名
        import re
        if 'wsj' in filename.lower() or 'wall street journal' in filename.lower():
            target_filename = '华尔街日报0318.jpg'
        elif 'ft' in filename.lower() or 'financial times' in filename.lower():
            target_filename = '金融时报0318.jpg'
        else:
            messagebox.showwarning("警告", "无法识别报纸类型")
            return
        
        target_path = os.path.join(export_dir, target_filename)
        
        try:
            import shutil
            shutil.copy2(source_path, target_path)
            messagebox.showinfo("成功", f"图片已下载到：{target_path}")
        except Exception as e:
            messagebox.showerror("错误", f"下载失败：{str(e)}")
    
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
            
            # 复制到系统剪贴板
            self.root.clipboard_clear()
            self.root.clipboard_append(prompt)
            
            # 显示自动消失的提示
            self.show_auto_dismiss_message("生成成功", f"Prompt已生成、保存并复制到剪贴板")
            
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
        self.image_count_label.config(text=f"共 {len(image_files)} 张")
        if image_files:
            self.image_listbox.selection_set(0)
            self.image_listbox.activate(0)
            self.root.after(100, lambda: self.image_listbox.event_generate('<<ListboxSelect>>'))
    
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