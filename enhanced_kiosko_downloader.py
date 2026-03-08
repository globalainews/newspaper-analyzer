import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import requests
import os
import json
import base64
from datetime import datetime, timedelta
import google.generativeai as genai
from PIL import Image, ImageTk

class EnhancedKioskoDownloader:
    def __init__(self, root):
        self.root = root
        self.root.title("新闻报纸下载与分析工具")
        self.root.geometry("800x700")
        
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
            proxies = {
                'http': f'http://{proxy_config["host"]}:{proxy_config["port"]}',
                'https': f'http://{proxy_config["host"]}:{proxy_config["port"]}'
            }
            
            # 配置Gemini
            genai.configure(api_key=api_key, transport=proxies)
            self.model = genai.GenerativeModel(self.config['gemini']['model'])
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
        """创建分析标签页"""
        # 标题
        tk.Label(self.analysis_frame, text="报纸图片分析工具", 
                font=("Arial", 16, "bold")).pack(pady=20)
        
        # Gemini状态
        gemini_status = "可用" if self.gemini_available else "未配置"
        status_color = "green" if self.gemini_available else "red"
        tk.Label(self.analysis_frame, text=f"Gemini模型状态: {gemini_status}", 
                font=("Arial", 10), fg=status_color).pack(pady=5)
        
        # 图片选择区域
        select_frame = tk.Frame(self.analysis_frame)
        select_frame.pack(fill='x', padx=20, pady=10)
        
        tk.Label(select_frame, text="选择图片:", font=("Arial", 10, "bold")).pack(anchor='w')
        
        # 图片列表和预览
        list_preview_frame = tk.Frame(select_frame)
        list_preview_frame.pack(fill='x', pady=10)
        
        # 图片列表
        list_frame = tk.Frame(list_preview_frame)
        list_frame.pack(side='left', fill='y', padx=(0, 10))
        
        tk.Label(list_frame, text="下载的图片:").pack(anchor='w')
        
        self.image_listbox = tk.Listbox(list_frame, width=30, height=8)
        self.image_listbox.pack(fill='y')
        
        # 刷新按钮
        refresh_btn = tk.Button(list_frame, text="刷新列表", command=self.refresh_image_list)
        refresh_btn.pack(pady=5)
        
        # 图片预览
        preview_frame = tk.Frame(list_preview_frame)
        preview_frame.pack(side='left', fill='both', expand=True)
        
        tk.Label(preview_frame, text="图片预览:").pack(anchor='w')
        
        self.preview_label = tk.Label(preview_frame, text="选择图片查看预览", 
                                     bg='white', relief='solid', width=40, height=15)
        self.preview_label.pack(fill='both', expand=True)
        
        # 绑定选择事件
        self.image_listbox.bind('<<ListboxSelect>>', self.on_image_select)
        
        # 分析按钮
        analyze_btn = tk.Button(self.analysis_frame, text="分析选中图片", 
                               command=self.analyze_image,
                               font=("Arial", 12), bg="#9C27B0", fg="white",
                               padx=20, pady=10)
        analyze_btn.pack(pady=10)
        
        # 分析结果区域
        result_frame = tk.Frame(self.analysis_frame)
        result_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        tk.Label(result_frame, text="分析结果:", font=("Arial", 10, "bold")).pack(anchor='w')
        
        self.result_text = tk.Text(result_frame, height=10, wrap='word')
        self.result_text.pack(fill='both', expand=True)
        
        # 滚动条
        scrollbar = tk.Scrollbar(self.result_text)
        scrollbar.pack(side='right', fill='y')
        self.result_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.result_text.yview)
        
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
    
    def show_image_preview(self, filepath):
        """显示图片预览"""
        try:
            # 加载并调整图片大小
            image = Image.open(filepath)
            
            # 调整大小以适应预览区域
            preview_size = (300, 200)
            image.thumbnail(preview_size, Image.Resampling.LANCZOS)
            
            # 转换为Tkinter可用的格式
            photo = ImageTk.PhotoImage(image)
            
            # 更新预览标签
            self.preview_label.config(image=photo, text="")
            self.preview_label.image = photo  # 保持引用
            
        except Exception as e:
            self.preview_label.config(image=None, text=f"预览失败: {str(e)}")
    
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
            
            # 调用Gemini模型
            response = self.model.generate_content([
                prompt,
                {
                    "mime_type": "image/jpeg",
                    "data": image_data
                }
            ])
            
            # 显示分析结果
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, f"图片分析结果 - {filename}\n")
            self.result_text.insert(tk.END, "=" * 50 + "\n\n")
            self.result_text.insert(tk.END, response.text)
            
            messagebox.showinfo("分析完成", "图片分析完成!")
            
        except Exception as e:
            error_msg = f"分析失败: {str(e)}"
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, error_msg)
            messagebox.showerror("错误", error_msg)

if __name__ == "__main__":
    root = tk.Tk()
    app = EnhancedKioskoDownloader(root)
    root.mainloop()