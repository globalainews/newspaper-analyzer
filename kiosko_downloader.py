import tkinter as tk
from tkinter import filedialog, messagebox
import requests
import os
from datetime import datetime

class KioskoNewsDownloader:
    def __init__(self, root):
        self.root = root
        self.root.title("新闻报纸首页下载器")
        self.root.geometry("600x500")
        
        # 报纸配置
        self.newspapers = {
            'wsj': {
                'name': '华尔街日报',
                'country': 'us',
                'code': 'wsj',
                'url_pattern': 'https://img.kiosko.net/{date}/{country}/{code}.750.jpg'
            },
            'ft': {
                'name': '金融时报',
                'country': 'uk',
                'code': 'ft_uk',
                'url_pattern': 'https://img.kiosko.net/{date}/{country}/{code}.750.jpg'
            }
        }
        
        self.create_widgets()
    
    def create_widgets(self):
        # 标题
        tk.Label(self.root, text="新闻报纸首页下载器", font=("Arial", 16, "bold")).pack(pady=20)
        
        # 说明文字
        tk.Label(self.root, text="从 kiosko.net 下载今日报纸首页", font=("Arial", 10)).pack(pady=5)
        
        # 状态显示
        self.status_label = tk.Label(self.root, text="准备就绪", font=("Arial", 10), fg="blue")
        self.status_label.pack(pady=10)
        
        # 下载按钮区域
        button_frame = tk.Frame(self.root)
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
        date_frame = tk.Frame(self.root)
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
        
        # 保存位置设置
        save_frame = tk.Frame(self.root)
        save_frame.pack(pady=10)
        
        tk.Label(save_frame, text="保存位置:", font=("Arial", 10)).pack(side=tk.LEFT)
        
        self.save_path = tk.StringVar()
        self.save_path.set(os.getcwd())  # 默认保存到当前目录
        
        path_entry = tk.Entry(save_frame, textvariable=self.save_path, width=40)
        path_entry.pack(side=tk.LEFT, padx=5)
        
        browse_btn = tk.Button(save_frame, text="浏览", command=self.browse_path)
        browse_btn.pack(side=tk.LEFT, padx=5)
    
    def on_date_change(self, *args):
        """日期选项变化处理"""
        if self.date_var.get() == "custom":
            self.custom_date_entry.config(state='normal')
        else:
            self.custom_date_entry.config(state='disabled')
    
    def browse_path(self):
        """选择保存路径"""
        directory = filedialog.askdirectory()
        if directory:
            self.save_path.set(directory)
    
    def update_status(self, message, color="blue"):
        """更新状态显示"""
        self.status_label.config(text=message, fg=color)
        self.root.update()
    
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
                # 支持多种日期格式
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
        url = paper['url_pattern'].format(
            date=date_str.replace('/', '/'),
            country=paper['country'],
            code=paper['code']
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
            
            # 生成文件名
            date_part = date_str.replace('/', '-')
            filename = f"{paper['code']}_{date_part}.jpg"
            filepath = os.path.join(self.save_path.get(), filename)
            
            # 保存文件
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            file_size = os.path.getsize(filepath)
            
            self.update_status(f"{paper['name']}下载成功!", "green")
            messagebox.showinfo("成功", f"{paper['name']}首页已下载!\n\n文件: {filename}\n大小: {file_size} 字节\n位置: {filepath}")
            
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
                        # 生成文件名
                        date_part = date_str.replace('/', '-')
                        filename = f"{paper['code']}_{date_part}.jpg"
                        filepath = os.path.join(self.save_path.get(), filename)
                        
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
            
        except Exception as e:
            self.update_status("批量下载失败", "red")
            messagebox.showerror("错误", f"批量下载失败: {str(e)}")
        finally:
            # 重新启用按钮
            self.wsj_btn.config(state=tk.NORMAL)
            self.ft_btn.config(state=tk.NORMAL)
            self.batch_btn.config(state=tk.NORMAL)

# 导入timedelta
from datetime import timedelta

if __name__ == "__main__":
    root = tk.Tk()
    app = KioskoNewsDownloader(root)
    root.mainloop()