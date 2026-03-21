# 浏览器管理模块 - 管理Chrome浏览器实例
import os
import time
import subprocess
import threading
from playwright.sync_api import sync_playwright


class BrowserManager:
    _instance = None
    _browser = None
    _context = None
    _playwright = None
    _debug_port = 9222
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        pass
    
    @property
    def is_connected(self):
        return self._browser is not None and self._browser.is_connected()
    
    def start_chrome(self, status_callback=None):
        """启动Chrome调试模式"""
        def update_status(message):
            if status_callback:
                status_callback(message)
        
        with self._lock:
            if self.is_connected:
                update_status("浏览器已连接")
                return True
            
            try:
                self._playwright = sync_playwright().start()
                
                for attempt in range(3):
                    try:
                        self._browser = self._playwright.chromium.connect_over_cdp(
                            f'http://127.0.0.1:{self._debug_port}'
                        )
                        update_status("已连接到Chrome调试实例")
                        return True
                    except Exception as e:
                        if attempt == 0:
                            update_status("尝试连接Chrome调试实例...")
                        time.sleep(1)
                
                update_status("正在启动Chrome调试模式...")
                
                subprocess.Popen(
                    'taskkill /F /IM chrome.exe',
                    shell=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                time.sleep(2)
                
                chrome_path = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
                user_data_dir = r'E:\temp_profile'
                
                cmd = f'"{chrome_path}" --remote-debugging-port={self._debug_port} --remote-allow-origins=* --user-data-dir="{user_data_dir}"'
                update_status("启动Chrome...")
                subprocess.Popen(cmd, shell=True)
                time.sleep(5)
                
                for attempt in range(10):
                    try:
                        self._browser = self._playwright.chromium.connect_over_cdp(
                            f'http://127.0.0.1:{self._debug_port}'
                        )
                        update_status("已连接到Chrome调试实例")
                        return True
                    except Exception as e:
                        if attempt < 9:
                            update_status(f"等待Chrome启动... ({attempt + 1}/10)")
                            time.sleep(2)
                        else:
                            update_status(f"启动Chrome失败: {str(e)}")
                            return False
                
            except Exception as e:
                update_status(f"启动浏览器失败: {str(e)}")
                return False
        
        return False
    
    def get_browser(self):
        """获取浏览器实例"""
        return self._browser
    
    def get_page(self, url_pattern=None):
        """获取或创建页面"""
        if not self.is_connected:
            return None
        
        try:
            contexts = self._browser.contexts
            if contexts:
                context = contexts[0]
                pages = context.pages
                
                if url_pattern:
                    for page in pages:
                        try:
                            if url_pattern in page.url:
                                return page
                        except:
                            continue
                
                for page in pages:
                    try:
                        if page.url.startswith('http'):
                            return page
                    except:
                        continue
                
                return context.new_page()
            else:
                context = self._browser.new_context(
                    viewport={'width': 1280, 'height': 800},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                )
                return context.new_page()
        except Exception as e:
            return None
    
    def new_page(self):
        """创建新页面"""
        if not self.is_connected:
            print("[BrowserManager] 错误: 浏览器未连接")
            return None
        
        try:
            contexts = self._browser.contexts
            print(f"[BrowserManager] contexts数量: {len(contexts)}")
            
            if contexts:
                context = contexts[0]
                print(f"[BrowserManager] 使用现有context, pages数量: {len(context.pages)}")
                page = context.new_page()
                print(f"[BrowserManager] 创建新页面成功: {page}")
                return page
            else:
                print("[BrowserManager] 没有现有context，创建新context")
                context = self._browser.new_context(
                    viewport={'width': 1280, 'height': 800},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                )
                page = context.new_page()
                print(f"[BrowserManager] 创建新页面成功: {page}")
                return page
        except Exception as e:
            print(f"[BrowserManager] 创建页面异常: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def close(self):
        """关闭浏览器"""
        with self._lock:
            try:
                if self._browser:
                    self._browser.close()
            except:
                pass
            
            try:
                if self._playwright:
                    self._playwright.stop()
            except:
                pass
            
            self._browser = None
            self._context = None
            self._playwright = None


browser_manager = BrowserManager()
