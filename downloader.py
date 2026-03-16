import tkinter as tk
from tkinter import messagebox
import requests
import os
from datetime import datetime, timedelta
import re


class NewspaperDownloader:
    def __init__(self, config, status_callback=None):
        self.config = config
        self.status_callback = status_callback
        
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
                'url_pattern': 'https://img.kiosko.net/{date}/{country}/{code}.{quality}.jpg',
                'alt_url_pattern': 'https://www.tomorrowspapers.co.uk/financial-times-front-page-{date}/'
            }
        }
        
        self.download_dir = self.config['download_settings']['save_directory']
        os.makedirs(self.download_dir, exist_ok=True)
    
    def update_status(self, message, color="blue"):
        if self.status_callback:
            self.status_callback(message, color)
    
    def get_target_date(self, date_var, custom_date_entry):
        date_option = date_var.get()
        
        if date_option == "today":
            target_date = datetime.now()
        elif date_option == "yesterday":
            target_date = datetime.now() - timedelta(days=1)
        else:
            date_str = custom_date_entry.get().strip()
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
        
        return target_date
    
    def construct_image_url(self, newspaper_code, target_date):
        paper = self.newspapers[newspaper_code]
        quality = self.config['download_settings']['image_quality']
        date_str = target_date.strftime('%Y/%m/%d')
        url = paper['url_pattern'].format(
            date=date_str.replace('/', '/'),
            country=paper['country'],
            code=paper['code'],
            quality=quality
        )
        return url
    
    def download_ft_from_tomorrowspapers(self, target_date):
        """从tomorrowspapers.co.uk下载金融时报"""
        try:
            date_str = target_date.strftime('%Y-%m-%d')
            page_url = f"https://www.tomorrowspapers.co.uk/financial-times-front-page-{date_str}/"
            
            self.update_status(f"正在访问: {page_url}", "blue")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Referer': 'https://www.tomorrowspapers.co.uk/'
            }
            
            response = requests.get(page_url, headers=headers, timeout=30)
            
            if response.status_code != 200:
                return None, f"页面访问失败，状态码: {response.status_code}"
            
            html_content = response.text
            
            image_patterns = [
                r'https?://[^\s"\'<>]+?\.jpg',
                r'https?://[^\s"\'<>]+?\.jpeg',
                r'https?://[^\s"\'<>]+?\.png',
                r'src=["\']([^"\']+)["\']'
            ]
            
            image_urls = []
            for pattern in image_patterns:
                matches = re.findall(pattern, html_content, re.IGNORECASE)
                image_urls.extend(matches)
            
            for url in image_urls:
                if 'financial' in url.lower() or 'ft' in url.lower() or 'front' in url.lower():
                    if url.startswith('http'):
                        return url, None
            
            for url in image_urls:
                if url.startswith('http') and ('.jpg' in url.lower() or '.jpeg' in url.lower() or '.png' in url.lower()):
                    return url, None
            
            return None, "未找到图片URL"
            
        except Exception as e:
            return None, f"获取图片URL失败: {str(e)}"
    
    def download_newspaper(self, newspaper_code, date_var, custom_date_entry, refresh_callback=None):
        paper = self.newspapers[newspaper_code]
        
        try:
            target_date = self.get_target_date(date_var, custom_date_entry)
            if not target_date:
                return False
            
            self.update_status(f"正在下载{paper['name']}...", "blue")
            
            if newspaper_code == 'ft':
                image_url, error = self.download_ft_from_tomorrowspapers(target_date)
                
                if image_url:
                    self.update_status(f"正在下载图片: {image_url}", "blue")
                    
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                        'Referer': 'https://www.tomorrowspapers.co.uk/'
                    }
                    
                    response = requests.get(image_url, headers=headers, timeout=30)
                    
                    if response.status_code == 200:
                        date_part = target_date.strftime('%Y-%m-%d')
                        filename = f"{paper['code']}_{date_part}.jpg"
                        filepath = os.path.join(self.download_dir, filename)
                        
                        with open(filepath, 'wb') as f:
                            f.write(response.content)
                        
                        file_size = os.path.getsize(filepath)
                        
                        self.update_status(f"{paper['name']}下载成功!", "green")
                        messagebox.showinfo("成功", f"{paper['name']}首页已下载!\n\n文件: {filename}\n大小: {file_size} 字节\n位置: {self.download_dir}")
                        
                        if refresh_callback:
                            refresh_callback()
                        
                        return True
                    else:
                        self.update_status("从tomorrowspapers下载失败，尝试kiosko...", "orange")
            
            image_url = self.construct_image_url(newspaper_code, target_date)
            self.update_status(f"正在连接: {image_url}", "blue")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://en.kiosko.net/'
            }
            
            response = requests.get(image_url, headers=headers, timeout=30)
            
            if response.status_code != 200:
                raise Exception(f"下载失败，状态码: {response.status_code}")
            
            date_part = target_date.strftime('%Y-%m-%d')
            filename = f"{paper['code']}_{date_part}.jpg"
            filepath = os.path.join(self.download_dir, filename)
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            file_size = os.path.getsize(filepath)
            
            self.update_status(f"{paper['name']}下载成功!", "green")
            messagebox.showinfo("成功", f"{paper['name']}首页已下载!\n\n文件: {filename}\n大小: {file_size} 字节\n位置: {self.download_dir}")
            
            if refresh_callback:
                refresh_callback()
            
            return True
            
        except Exception as e:
            error_msg = f"下载{paper['name']}失败: {str(e)}"
            self.update_status("下载失败", "red")
            messagebox.showerror("错误", error_msg)
            return False
    
    def download_all_newspapers(self, date_var, custom_date_entry, refresh_callback=None):
        try:
            target_date = self.get_target_date(date_var, custom_date_entry)
            if not target_date:
                return False
            
            success_count = 0
            total_count = len(self.newspapers)
            
            for newspaper_code in self.newspapers:
                paper = self.newspapers[newspaper_code]
                
                self.update_status(f"正在下载{paper['name']} ({success_count+1}/{total_count})...", "blue")
                
                try:
                    image_url = self.construct_image_url(newspaper_code, target_date)
                    
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                        'Referer': 'https://en.kiosko.net/'
                    }
                    
                    response = requests.get(image_url, headers=headers, timeout=30)
                    
                    if response.status_code == 200:
                        date_part = target_date.strftime('%Y-%m-%d')
                        filename = f"{paper['code']}_{date_part}.jpg"
                        filepath = os.path.join(self.download_dir, filename)
                        
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
            
            if refresh_callback:
                refresh_callback()
            
            return True
            
        except Exception as e:
            self.update_status("批量下载失败", "red")
            messagebox.showerror("错误", f"批量下载失败: {str(e)}")
            return False