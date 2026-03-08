import tkinter as tk
from tkinter import filedialog, messagebox
import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime

class WSJFrontPageDownloader:
    def __init__(self, root):
        self.root = root
        self.root.title("华尔街日报首页下载器")
        self.root.geometry("600x400")
        
        self.proxy_port = 1080
        self.proxy_host = "127.0.0.1"
        self.proxies = {
            'http': f'http://{self.proxy_host}:{self.proxy_port}',
            'https': f'http://{self.proxy_host}:{self.proxy_port}'
        }
        
        self.create_widgets()
    
    def create_widgets(self):
        tk.Label(self.root, text="华尔街日报首页图片下载器", font=("Arial", 16)).pack(pady=20)
        
        # 代理设置区域
        proxy_frame = tk.Frame(self.root)
        proxy_frame.pack(pady=10)
        
        tk.Label(proxy_frame, text="代理设置:", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="w", padx=5)
        
        tk.Label(proxy_frame, text="主机:").grid(row=1, column=0, sticky="w", padx=5)
        self.proxy_host_entry = tk.Entry(proxy_frame, width=15)
        self.proxy_host_entry.insert(0, self.proxy_host)
        self.proxy_host_entry.grid(row=1, column=1, padx=5)
        
        tk.Label(proxy_frame, text="端口:").grid(row=1, column=2, sticky="w", padx=5)
        self.proxy_port_entry = tk.Entry(proxy_frame, width=8)
        self.proxy_port_entry.insert(0, str(self.proxy_port))
        self.proxy_port_entry.grid(row=1, column=3, padx=5)
        
        # 测试连接按钮
        self.test_btn = tk.Button(proxy_frame, text="测试连接", command=self.test_connection,
                                 font=("Arial", 9), bg="#2196F3", fg="white")
        self.test_btn.grid(row=1, column=4, padx=10)
        
        self.status_label = tk.Label(self.root, text="准备就绪", font=("Arial", 10), fg="blue")
        self.status_label.pack(pady=10)
        
        self.download_btn = tk.Button(self.root, text="下载今天的首页", command=self.download_front_page, 
                                      font=("Arial", 12), bg="#4CAF50", fg="white", padx=20, pady=10)
        self.download_btn.pack(pady=20)
        
        self.save_path = tk.StringVar()
        self.save_path.set(os.path.join(os.path.expanduser("~"), "Desktop"))
        
        path_frame = tk.Frame(self.root)
        path_frame.pack(pady=10)
        
        tk.Label(path_frame, text="保存位置:").pack(side=tk.LEFT)
        tk.Entry(path_frame, textvariable=self.save_path, width=30).pack(side=tk.LEFT, padx=5)
        tk.Button(path_frame, text="浏览", command=self.browse_path).pack(side=tk.LEFT)
    
    def browse_path(self):
        directory = filedialog.askdirectory()
        if directory:
            self.save_path.set(directory)
    
    def update_status(self, message, color="blue"):
        self.status_label.config(text=message, fg=color)
        self.root.update()
    
    def test_connection(self):
        """测试代理连接"""
        self.test_btn.config(state=tk.DISABLED)
        self.update_status("正在测试连接...", "blue")
        
        try:
            # 更新代理设置
            self.proxy_host = self.proxy_host_entry.get().strip()
            self.proxy_port = int(self.proxy_port_entry.get().strip())
            self.proxies = {
                'http': f'http://{self.proxy_host}:{self.proxy_port}',
                'https': f'http://{self.proxy_host}:{self.proxy_port}'
            }
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            
            # 测试连接
            response = requests.get("https://x.com/wsj", headers=headers, proxies=self.proxies, timeout=10)
            
            if response.status_code == 200:
                self.update_status("连接测试成功!", "green")
                messagebox.showinfo("连接测试", "代理连接测试成功!")
            else:
                raise Exception(f"连接失败，状态码: {response.status_code}")
                
        except Exception as e:
            error_msg = f"连接测试失败: {str(e)}\n\n请检查:\n1. 代理服务是否正在运行\n2. 主机和端口设置是否正确"
            self.update_status("连接测试失败", "red")
            messagebox.showerror("连接测试", error_msg)
        finally:
            self.test_btn.config(state=tk.NORMAL)
    
    def download_front_page(self):
        self.download_btn.config(state=tk.DISABLED)
        self.update_status("正在连接...", "blue")
        
        try:
            # 更新代理设置
            self.proxy_host = self.proxy_host_entry.get().strip()
            self.proxy_port = int(self.proxy_port_entry.get().strip())
            self.proxies = {
                'http': f'http://{self.proxy_host}:{self.proxy_port}',
                'https': f'http://{self.proxy_host}:{self.proxy_port}'
            }
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
            }
            
            # 获取今天的日期并构建推文URL
            today = datetime.now().strftime('%Y-%m-%d')
            
            # 方法1: 直接访问WSJ账号页面，查找最新的推文
            self.update_status("正在获取最新推文...", "blue")
            wsj_url = "https://x.com/wsj"
            response = requests.get(wsj_url, headers=headers, proxies=self.proxies, timeout=30)
            
            if response.status_code != 200:
                raise Exception(f"无法访问WSJ页面，状态码: {response.status_code}")
            
            self.update_status("正在解析推文...", "blue")
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 查找最新的推文链接
            tweet_url = self.find_latest_tweet_url(soup)
            
            if not tweet_url:
                # 如果找不到推文链接，使用默认的图片获取方法
                image_url = self.find_image_url(soup)
            else:
                # 访问具体的推文页面获取高质量图片
                self.update_status("正在获取推文详情...", "blue")
                tweet_response = requests.get(tweet_url, headers=headers, proxies=self.proxies, timeout=30)
                
                if tweet_response.status_code != 200:
                    raise Exception(f"无法访问推文页面，状态码: {tweet_response.status_code}")
                
                tweet_soup = BeautifulSoup(tweet_response.text, 'html.parser')
                image_url = self.find_tweet_image_url(tweet_soup)
            
            if not image_url:
                raise Exception("未找到首页图片")
            
            self.update_status("正在下载图片...", "blue")
            
            if not image_url.startswith('http'):
                image_url = 'https:' + image_url
            
            img_response = requests.get(image_url, headers=headers, proxies=self.proxies, timeout=30)
            
            if img_response.status_code != 200:
                raise Exception(f"图片下载失败，状态码: {img_response.status_code}")
            
            filename = f"wsj_front_page_{today}.jpg"
            filepath = os.path.join(self.save_path.get(), filename)
            
            with open(filepath, 'wb') as f:
                f.write(img_response.content)
            
            self.update_status(f"下载成功! 已保存到: {filepath}", "green")
            messagebox.showinfo("成功", f"华尔街日报首页已下载!\n\n保存位置: {filepath}")
            
        except Exception as e:
            error_msg = f"错误: {str(e)}\n\n请检查:\n1. 代理服务是否正在运行\n2. 网络连接是否正常\n3. 先点击'测试连接'按钮验证代理设置"
            self.update_status("下载失败", "red")
            messagebox.showerror("错误", error_msg)
        finally:
            self.download_btn.config(state=tk.NORMAL)
    
    def find_image_url(self, soup):
        image_url = None
        
        img_tags = soup.find_all('img')
        
        # 策略1: 查找包含特定关键词的图片
        for img in img_tags:
            src = img.get('src', '')
            alt = img.get('alt', '').lower()
            
            if any(keyword in alt for keyword in ['wall street journal', 'front page', 'wsj', 'today\'s front page', 'today front page']):
                image_url = src
                break
        
        # 策略2: 查找推文中的媒体图片
        if not image_url:
            for img in img_tags:
                src = img.get('src', '')
                if 'pbs.twimg.com/media' in src:
                    # 检查是否是高质量图片
                    if 'name=' in src and 'large' in src:
                        image_url = src
                        break
                    elif image_url is None:
                        image_url = src
        
        # 策略3: 查找推文卡片中的图片
        if not image_url:
            for img in img_tags:
                src = img.get('src', '')
                if 'pbs.twimg.com' in src and ('profile' not in src):
                    # 尝试获取更高分辨率的图片
                    if 'small' in src:
                        image_url = src.replace('small', 'large')
                    elif 'medium' in src:
                        image_url = src.replace('medium', 'large')
                    else:
                        image_url = src
                    break
        
        # 策略4: 查找data-src属性中的图片
        if not image_url:
            for img in img_tags:
                data_src = img.get('data-src', '')
                if data_src and 'pbs.twimg.com' in data_src:
                    image_url = data_src
                    break
        
        # 策略5: 查找所有可能的图片链接
        if not image_url:
            possible_images = []
            for img in img_tags:
                src = img.get('src', '')
                if src and ('pbs.twimg.com' in src or 'twimg.com' in src):
                    possible_images.append(src)
            
            if possible_images:
                # 选择最大的图片（通常质量更高）
                image_url = possible_images[0]
                for img_src in possible_images:
                    if 'large' in img_src or 'orig' in img_src:
                        image_url = img_src
                        break
        
        return image_url
    
    def find_latest_tweet_url(self, soup):
        """查找最新的推文链接"""
        tweet_url = None
        
        # 查找推文链接
        links = soup.find_all('a', href=True)
        
        for link in links:
            href = link.get('href', '')
            # 查找包含状态ID的推文链接
            if '/status/' in href and '/wsj' in href:
                tweet_url = 'https://x.com' + href
                break
        
        return tweet_url
    
    def find_tweet_image_url(self, soup):
        """从推文页面查找图片URL"""
        image_url = None
        
        # 查找推文中的图片
        img_tags = soup.find_all('img')
        
        for img in img_tags:
            src = img.get('src', '')
            alt = img.get('alt', '').lower()
            
            # 查找高质量的图片
            if 'pbs.twimg.com/media' in src:
                # 优先选择高质量图片
                if 'large' in src or 'orig' in src:
                    image_url = src
                    break
                elif image_url is None:
                    image_url = src
        
        # 如果没找到，使用默认方法
        if not image_url:
            image_url = self.find_image_url(soup)
        
        return image_url

if __name__ == "__main__":
    root = tk.Tk()
    app = WSJFrontPageDownloader(root)
    root.mainloop()
