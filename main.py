import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import requests
import os
import json
import base64
from datetime import datetime, timedelta
from PIL import Image, ImageTk

class EnhancedKioskoDownloader:
    def __init__(self, root):
        self.root = root
        self.root.title("新闻报纸下载与分析工具")
        self.root.geometry("{0}x{1}+0+0".format(self.root.winfo_screenwidth(), self.root.winfo_screenheight()))
        self.root.state('zoomed')
        
        # 加载配置
        self.load_config()
        
        # 报纸配置
        self.newspapers = {
            'wsj': {
                'name': '华尔街日报',
                'country': 'us',
                'code': 'wsj',
                'url_pattern': 'https://img.kiosko.net/{date}/{country}/{code}.{quality}.jpg'
            },
            'ft': {
                'name': '金融时报',
                'country': 'uk',
                'code': 'ft_uk',
                'url_pattern': 'https://img.kiosko.net/{date}/{country}/{code}.{quality}.jpg'
            }
        }
        
        # 创建下载目录
        self.download_dir = self.config['download_settings']['save_directory']
        os.makedirs(self.download_dir, exist_ok=True)
        
        # 创建分析结果目录
        self.analysis_dir = self.config.get('analysis_settings', {}).get('analysis_directory', 'analysis_results')
        os.makedirs(self.analysis_dir, exist_ok=True)
        
        # 初始化Gemini
        self.init_gemini()
        
        # 创建界面
        self.create_interface()
    
    def load_config(self):
        """加载配置文件"""
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        except FileNotFoundError:
            # 创建默认配置
            self.config = {
                "gemini": {
                    "api_key": "YOUR_GEMINI_API_KEY_HERE",
                    "model": "gemini-2.5-flash",
                    "proxy": {
                        "host": "127.0.0.1",
                        "port": 1080
                    }
                },
                "analysis_prompt": "请分析这张报纸首页图片，重点关注以下内容：\n\n1. 主要新闻标题和主题\n2. 重要的财经数据和市场信息\n3. 商业和金融领域的重点报道\n4. 国际新闻和重要事件\n5. 图片中的关键图表和数据可视化\n\n请用中文回答，分析要详细且专业。",
                "download_settings": {
                    "save_directory": "downloaded_images",
                    "image_quality": "750"
                },
                "export_settings": {
                    "export_directory": "E:\\中文听见\\报纸头版"
                },
                "analysis_settings": {
                    "analysis_directory": "analysis_results"
                }
            }
            # 保存默认配置
            with open('config.json', 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
    
    def init_gemini(self):
        """初始化Gemini API"""
        try:
            api_key = self.config['gemini']['api_key']
            if api_key == "YOUR_GEMINI_API_KEY_HERE":
                self.gemini_available = False
                return
            
            # 配置代理
            proxy_config = self.config['gemini']['proxy']
            self.proxy_url = f'http://{proxy_config["host"]}:{proxy_config["port"]}'
            self.gemini_api_key = api_key
            self.gemini_model = self.config['gemini']['model']
            self.gemini_available = True
            
        except Exception as e:
            print(f"Gemini初始化失败: {e}")
            self.gemini_available = False
    
    def create_interface(self):
        """创建界面"""
        # 创建标签页
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # 下载标签页
        self.download_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.download_frame, text='下载报纸')
        self.create_download_tab()
        
        # 分析标签页
        self.analysis_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.analysis_frame, text='分析图片')
        self.create_analysis_tab()
    
    def create_download_tab(self):
        """创建下载标签页"""
        # 标题
        tk.Label(self.download_frame, text="新闻报纸首页下载器", 
                font=("Arial", 16, "bold")).pack(pady=20)
        
        # 说明文字
        tk.Label(self.download_frame, text=f"从 kiosko.net 下载今日报纸首页 (保存到: {self.download_dir})", 
                font=("Arial", 10)).pack(pady=5)
        
        # 状态显示
        self.status_label = tk.Label(self.download_frame, text="准备就绪", 
                                   font=("Arial", 10), fg="blue")
        self.status_label.pack(pady=10)
        
        # 下载按钮区域
        button_frame = tk.Frame(self.download_frame)
        button_frame.pack(pady=20)
        
        # 华尔街日报按钮
        self.wsj_btn = tk.Button(button_frame, text="下载华尔街日报", 
                                command=lambda: self.download_newspaper('wsj'),
                                font=("Arial", 12), bg="#4CAF50", fg="white", 
                                padx=20, pady=10, width=15)
        self.wsj_btn.grid(row=0, column=0, padx=20, pady=10)
        
        # 金融时报按钮
        self.ft_btn = tk.Button(button_frame, text="下载金融时报", 
                               command=lambda: self.download_newspaper('ft'),
                               font=("Arial", 12), bg="#2196F3", fg="white", 
                               padx=20, pady=10, width=15)
        self.ft_btn.grid(row=0, column=1, padx=20, pady=10)
        
        # 批量下载按钮
        self.batch_btn = tk.Button(button_frame, text="批量下载全部", 
                                  command=self.download_all_newspapers,
                                  font=("Arial", 12), bg="#FF9800", fg="white", 
                                  padx=20, pady=10, width=15)
        self.batch_btn.grid(row=1, column=0, columnspan=2, pady=10)
        
        # 日期选择区域
        date_frame = tk.Frame(self.download_frame)
        date_frame.pack(pady=10)
        
        tk.Label(date_frame, text="日期设置:", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="w", padx=5)
        
        # 日期选项
        self.date_var = tk.StringVar(value="today")
        
        tk.Radiobutton(date_frame, text="今日", variable=self.date_var, value="today").grid(row=1, column=0, padx=5)
        tk.Radiobutton(date_frame, text="昨日", variable=self.date_var, value="yesterday").grid(row=1, column=1, padx=5)
        tk.Radiobutton(date_frame, text="自定义", variable=self.date_var, value="custom").grid(row=1, column=2, padx=5)
        
        # 自定义日期输入
        self.custom_date_entry = tk.Entry(date_frame, width=10)
        self.custom_date_entry.grid(row=1, column=3, padx=5)
        self.custom_date_entry.insert(0, datetime.now().strftime('%Y/%m/%d'))
        self.custom_date_entry.config(state='disabled')
        
        # 绑定日期选项变化
        self.date_var.trace('w', self.on_date_change)
    
    def create_analysis_tab(self):
        """创建分析标签页 - 专业界面设计"""
        # 主容器使用PanedWindow分隔左右区域
        main_paned = tk.PanedWindow(self.analysis_frame, orient=tk.HORIZONTAL, sashrelief=tk.RAISED, sashwidth=4)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # ========== 左侧区域：图片列表 ==========
        left_frame = tk.Frame(main_paned, width=280)
        main_paned.add(left_frame, minsize=250)
        
        # 标题栏
        title_frame = tk.Frame(left_frame, bg='#2C3E50')
        title_frame.pack(fill=tk.X)
        tk.Label(title_frame, text="📰 图片列表", font=("Microsoft YaHei", 12, "bold"), 
                bg='#2C3E50', fg='white').pack(pady=10)
        
        # Gemini状态
        status_frame = tk.Frame(left_frame, bg='#ECF0F1')
        status_frame.pack(fill=tk.X, padx=10, pady=5)
        gemini_status = "✅ Gemini已连接" if self.gemini_available else "❌ Gemini未配置"
        status_color = "#27AE60" if self.gemini_available else "#E74C3C"
        tk.Label(status_frame, text=gemini_status, font=("Microsoft YaHei", 9), 
                bg='#ECF0F1', fg=status_color).pack(anchor='w', pady=5)
        
        # 图片列表容器
        list_container = tk.Frame(left_frame, bg='#BDC3C7', relief=tk.SUNKEN, bd=1)
        list_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 滚动条
        list_scroll = tk.Scrollbar(list_container)
        list_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.image_listbox = tk.Listbox(list_container, font=("Microsoft YaHei", 10), 
                                        yscrollcommand=list_scroll.set, 
                                        bg='white', selectbackground='#3498DB',
                                        selectforeground='white', borderwidth=0)
        self.image_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        list_scroll.config(command=self.image_listbox.yview)
        
        # 绑定选择事件
        self.image_listbox.bind('<<ListboxSelect>>', self.on_image_select)
        
        # 按钮栏
        btn_frame = tk.Frame(left_frame, bg='#ECF0F1')
        btn_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        refresh_btn = tk.Button(btn_frame, text="🔄 刷新列表", command=self.refresh_image_list,
                              font=("Microsoft YaHei", 10), bg='#3498DB', fg='white',
                              relief=tk.FLAT, padx=10, pady=5, cursor='hand2')
        refresh_btn.pack(side=tk.LEFT)
        
        analyze_btn = tk.Button(btn_frame, text="🔍 分析图片", command=self.analyze_image,
                               font=("Microsoft YaHei", 10), bg='#9B59B6', fg='white',
                               relief=tk.FLAT, padx=10, pady=5, cursor='hand2')
        analyze_btn.pack(side=tk.RIGHT)
        
        # 导出按钮
        export_btn = tk.Button(btn_frame, text="📤 导出图片", command=self.export_image,
                              font=("Microsoft YaHei", 10), bg='#27AE60', fg='white',
                              relief=tk.FLAT, padx=10, pady=5, cursor='hand2')
        export_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        # ========== 右侧区域：预览和分析结果（上下排列）==========
        right_frame = tk.Frame(main_paned)
        main_paned.add(right_frame, minsize=500)
        
        # 右侧使用水平PanedWindow分隔预览和分析结果（左右结构）
        right_paned = tk.PanedWindow(right_frame, orient=tk.HORIZONTAL, sashrelief=tk.RAISED, sashwidth=4)
        right_paned.pack(fill=tk.BOTH, expand=True)
        
        # ----- 左侧：图片预览 -----
        preview_container = tk.Frame(right_paned)
        right_paned.add(preview_container, minsize=350)
        
        # 预览区标题栏
        preview_title = tk.Frame(preview_container, bg='#2C3E50')
        preview_title.pack(fill=tk.X)
        tk.Label(preview_title, text="🖼️ 图片预览", font=("Microsoft YaHei", 12, "bold"), 
                bg='#2C3E50', fg='white').pack(pady=10)
        
        # 预览画布
        preview_canvas_frame = tk.Frame(preview_container, bg='#BDC3C7', relief=tk.SUNKEN, bd=1)
        preview_canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        self.preview_canvas = tk.Canvas(preview_canvas_frame, bg='white', highlightthickness=0)
        self.preview_canvas.pack(fill=tk.BOTH, expand=True)
        
        # 预览提示文字
        self.preview_text_id = self.preview_canvas.create_text(
            175, 200, text="选择左侧图片查看预览", 
            font=("Microsoft YaHei", 12), fill='#95A5A6'
        )
        
        # ----- 右侧：分析结果 -----
        result_container = tk.Frame(right_paned)
        right_paned.add(result_container, minsize=400)
        
        # 分析结果区标题栏
        result_title = tk.Frame(result_container, bg='#2C3E50')
        result_title.pack(fill=tk.X)
        tk.Label(result_title, text="📝 分析结果", font=("Microsoft YaHei", 12, "bold"), 
                bg='#2C3E50', fg='white').pack(pady=10)
        
        # 结果文本框容器
        result_text_container = tk.Frame(result_container, bg='#BDC3C7', relief=tk.SUNKEN, bd=1)
        result_text_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # 滚动条
        result_scroll = tk.Scrollbar(result_text_container)
        result_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.result_text = tk.Text(result_text_container, font=("Microsoft YaHei", 10), 
                                   wrap=tk.WORD, yscrollcommand=result_scroll.set,
                                   bg='white', borderwidth=0)
        self.result_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        result_scroll.config(command=self.result_text.yview)
        
        # 初始刷新图片列表
        self.refresh_image_list()
    
    def on_date_change(self, *args):
        """日期选项变化处理"""
        if self.date_var.get() == "custom":
            self.custom_date_entry.config(state='normal')
        else:
            self.custom_date_entry.config(state='disabled')
    
    def get_target_date(self):
        """获取目标日期"""
        date_option = self.date_var.get()
        
        if date_option == "today":
            target_date = datetime.now()
        elif date_option == "yesterday":
            target_date = datetime.now() - timedelta(days=1)
        else:  # custom
            date_str = self.custom_date_entry.get().strip()
            try:
                if '/' in date_str:
                    target_date = datetime.strptime(date_str, '%Y/%m/%d')
                elif '-' in date_str:
                    target_date = datetime.strptime(date_str, '%Y-%m-%d')
                else:
                    raise ValueError("日期格式不正确")
            except ValueError:
                messagebox.showerror("错误", "日期格式不正确，请使用 YYYY/MM/DD 或 YYYY-MM-DD 格式")
                return None
        
        return target_date.strftime('%Y/%m/%d').replace('/', '/')
    
    def construct_image_url(self, newspaper_code, date_str):
        """构造图片URL"""
        paper = self.newspapers[newspaper_code]
        quality = self.config['download_settings']['image_quality']
        url = paper['url_pattern'].format(
            date=date_str.replace('/', '/'),
            country=paper['country'],
            code=paper['code'],
            quality=quality
        )
        return url
    
    def download_newspaper(self, newspaper_code):
        """下载指定报纸"""
        # 禁用按钮
        self.wsj_btn.config(state=tk.DISABLED)
        self.ft_btn.config(state=tk.DISABLED)
        self.batch_btn.config(state=tk.DISABLED)
        
        paper = self.newspapers[newspaper_code]
        
        try:
            # 获取日期
            date_str = self.get_target_date()
            if not date_str:
                return
            
            self.update_status(f"正在下载{paper['name']}...", "blue")
            
            # 构造URL
            image_url = self.construct_image_url(newspaper_code, date_str)
            
            self.update_status(f"正在连接: {image_url}", "blue")
            
            # 下载图片
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://en.kiosko.net/'
            }
            
            response = requests.get(image_url, headers=headers, timeout=30)
            
            if response.status_code != 200:
                raise Exception(f"下载失败，状态码: {response.status_code}")
            
            # 生成文件名并保存到子目录
            date_part = date_str.replace('/', '-')
            filename = f"{paper['code']}_{date_part}.jpg"
            filepath = os.path.join(self.download_dir, filename)
            
            # 保存文件
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            file_size = os.path.getsize(filepath)
            
            self.update_status(f"{paper['name']}下载成功!", "green")
            messagebox.showinfo("成功", f"{paper['name']}首页已下载!\n\n文件: {filename}\n大小: {file_size} 字节\n位置: {self.download_dir}")
            
            # 刷新分析页面的图片列表
            self.refresh_image_list()
            
        except Exception as e:
            error_msg = f"下载{paper['name']}失败: {str(e)}"
            self.update_status("下载失败", "red")
            messagebox.showerror("错误", error_msg)
        finally:
            # 重新启用按钮
            self.wsj_btn.config(state=tk.NORMAL)
            self.ft_btn.config(state=tk.NORMAL)
            self.batch_btn.config(state=tk.NORMAL)
    
    def download_all_newspapers(self):
        """批量下载所有报纸"""
        # 禁用所有按钮
        self.wsj_btn.config(state=tk.DISABLED)
        self.ft_btn.config(state=tk.DISABLED)
        self.batch_btn.config(state=tk.DISABLED)
        
        try:
            # 获取日期
            date_str = self.get_target_date()
            if not date_str:
                return
            
            success_count = 0
            total_count = len(self.newspapers)
            
            for newspaper_code in self.newspapers:
                paper = self.newspapers[newspaper_code]
                
                self.update_status(f"正在下载{paper['name']} ({success_count+1}/{total_count})...", "blue")
                
                try:
                    # 构造URL
                    image_url = self.construct_image_url(newspaper_code, date_str)
                    
                    # 下载图片
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                        'Referer': 'https://en.kiosko.net/'
                    }
                    
                    response = requests.get(image_url, headers=headers, timeout=30)
                    
                    if response.status_code == 200:
                        # 生成文件名并保存到子目录
                        date_part = date_str.replace('/', '-')
                        filename = f"{paper['code']}_{date_part}.jpg"
                        filepath = os.path.join(self.download_dir, filename)
                        
                        # 保存文件
                        with open(filepath, 'wb') as f:
                            f.write(response.content)
                        
                        success_count += 1
                        print(f"✓ {paper['name']} 下载成功")
                    else:
                        print(f"✗ {paper['name']} 下载失败，状态码: {response.status_code}")
                        
                except Exception as e:
                    print(f"✗ {paper['name']} 下载错误: {str(e)}")
            
            self.update_status(f"批量下载完成: {success_count}/{total_count} 成功", "green")
            messagebox.showinfo("完成", f"批量下载完成!\n成功: {success_count}/{total_count}")
            
            # 刷新分析页面的图片列表
            self.refresh_image_list()
            
        except Exception as e:
            self.update_status("批量下载失败", "red")
            messagebox.showerror("错误", f"批量下载失败: {str(e)}")
        finally:
            # 重新启用按钮
            self.wsj_btn.config(state=tk.NORMAL)
            self.ft_btn.config(state=tk.NORMAL)
            self.batch_btn.config(state=tk.NORMAL)
    
    def update_status(self, message, color="blue"):
        """更新状态显示"""
        self.status_label.config(text=message, fg=color)
        self.root.update()
    
    def refresh_image_list(self):
        """刷新图片列表"""
        self.image_listbox.delete(0, tk.END)
        
        if os.path.exists(self.download_dir):
            image_files = [f for f in os.listdir(self.download_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
            for filename in sorted(image_files):
                self.image_listbox.insert(tk.END, filename)
    
    def on_image_select(self, event):
        """图片选择事件"""
        selection = self.image_listbox.curselection()
        if selection:
            filename = self.image_listbox.get(selection[0])
            filepath = os.path.join(self.download_dir, filename)
            self.show_image_preview(filepath)
            self.load_analysis_result(filename)
    
    def show_image_preview(self, filepath):
        """显示图片预览 - Canvas版本"""
        try:
            # 加载图片
            image = Image.open(filepath)
            
            # 获取画布大小
            canvas_width = self.preview_canvas.winfo_width()
            canvas_height = self.preview_canvas.winfo_height()
            
            if canvas_width <= 1 or canvas_height <= 1:
                canvas_width = 350
                canvas_height = 400
            
            # 获取原始图片尺寸
            orig_width, orig_height = image.size
            
            # 计算缩放比例，保持原始宽高比，同时适应画布
            ratio = min(canvas_width / orig_width, canvas_height / orig_height, 1.0)
            new_size = (int(orig_width * ratio), int(orig_height * ratio))
            
            # 调整图片大小
            image = image.resize(new_size, Image.Resampling.LANCZOS)
            
            # 转换为Tkinter可用的格式
            self.preview_photo = ImageTk.PhotoImage(image)
            
            # 清除画布
            self.preview_canvas.delete("all")
            
            # 计算居中位置
            x = (canvas_width - new_size[0]) // 2
            y = (canvas_height - new_size[1]) // 2
            
            # 在画布上绘制图片
            self.preview_canvas.create_image(x, y, anchor=tk.NW, image=self.preview_photo)
            
        except Exception as e:
            self.preview_canvas.delete("all")
            self.preview_canvas.create_text(
                175, 200, text=f"预览失败: {str(e)}", 
                font=("Microsoft YaHei", 11), fill='#E74C3C'
            )
    
    def load_analysis_result(self, filename):
        """加载已保存的分析结果"""
        base_name = os.path.splitext(filename)[0]
        analysis_file = os.path.join(self.analysis_dir, f"{base_name}.txt")
        
        self.result_text.delete(1.0, tk.END)
        
        if os.path.exists(analysis_file):
            try:
                with open(analysis_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.result_text.insert(tk.END, content)
            except Exception as e:
                self.result_text.insert(tk.END, f"读取分析结果失败: {str(e)}")
        else:
            self.result_text.insert(tk.END, "暂无分析结果\n\n点击\"分析图片\"按钮开始分析")
    
    def analyze_image(self):
        """分析选中的图片"""
        if not self.gemini_available:
            messagebox.showerror("错误", "Gemini API未配置，请检查config.json文件中的api_key设置")
            return
        
        selection = self.image_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一张图片")
            return
        
        filename = self.image_listbox.get(selection[0])
        filepath = os.path.join(self.download_dir, filename)
        
        try:
            # 清空结果文本框
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, "正在分析图片，请稍候...\n")
            self.root.update()
            
            # 读取图片并编码为base64
            with open(filepath, "rb") as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')
            
            # 准备提示词
            prompt = self.config['analysis_prompt']
            
            # 使用URL方式调用API
            api_key = self.config['gemini']['api_key']
            model_name = self.config['gemini']['model']
            
            url = f"https://generativelanguage.googleapis.com/v1/models/{model_name}:generateContent?key={api_key}"
            
            headers = {"Content-Type": "application/json"}
            
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": prompt},
                            {
                                "inline_data": {
                                    "mime_type": "image/jpeg",
                                    "data": image_data
                                }
                            }
                        ]
                    }
                ]
            }
            
            proxies = {
                'http': self.proxy_url,
                'https': self.proxy_url
            }
            
            resp = requests.post(url, headers=headers, json=payload, proxies=proxies, timeout=60)
            
            if resp.status_code == 200:
                result_data = resp.json()
                if 'candidates' in result_data and len(result_data['candidates']) > 0:
                    result_text = result_data['candidates'][0]['content']['parts'][0]['text']
                else:
                    raise Exception("API返回格式异常")
            else:
                raise Exception(f"API请求失败: {resp.status_code} - {resp.text}")
            
            # 保存分析结果到文件
            base_name = os.path.splitext(filename)[0]
            analysis_file = os.path.join(self.analysis_dir, f"{base_name}.txt")
            full_result = f"图片分析结果 - {filename}\n{'=' * 50}\n\n{result_text}"
            with open(analysis_file, 'w', encoding='utf-8') as f:
                f.write(full_result)
            
            # 显示分析结果
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, f"图片分析结果 - {filename}\n")
            self.result_text.insert(tk.END, "=" * 50 + "\n\n")
            self.result_text.insert(tk.END, result_text)
            
            messagebox.showinfo("分析完成", f"图片分析完成!\n\n结果已保存到:\n{analysis_file}")
            
        except Exception as e:
            error_msg = f"分析失败: {str(e)}"
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, error_msg)
            messagebox.showerror("错误", error_msg)
    
    def export_image(self):
        """导出选中的图片到指定目录"""
        selection = self.image_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一张图片")
            return
        
        filename = self.image_listbox.get(selection[0])
        source_filepath = os.path.join(self.download_dir, filename)
        
        if not os.path.exists(source_filepath):
            messagebox.showerror("错误", f"源文件不存在: {source_filepath}")
            return
        
        try:
            export_dir = self.config.get('export_settings', {}).get('export_directory', 'E:\\中文听见\\报纸头版')
            
            if not os.path.exists(export_dir):
                os.makedirs(export_dir, exist_ok=True)
            
            base_name = os.path.splitext(filename)[0]
            
            if 'wsj' in base_name.lower():
                export_filename = "华尔街日报.jpg"
            elif 'ft' in base_name.lower() or 'ft_uk' in base_name.lower():
                export_filename = "金融时报.jpg"
            else:
                export_filename = filename
            
            export_filepath = os.path.join(export_dir, export_filename)
            
            import shutil
            shutil.copy2(source_filepath, export_filepath)
            
            messagebox.showinfo("导出成功", f"图片已导出到:\n{export_filepath}")
            
        except Exception as e:
            messagebox.showerror("导出失败", f"导出图片时出错:\n{str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = EnhancedKioskoDownloader(root)
    root.mainloop()