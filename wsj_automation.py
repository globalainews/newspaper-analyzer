# 华尔街日报下载自动化模块 - 使用Playwright实现浏览器自动化
import os
import time
from datetime import datetime
from playwright.sync_api import sync_playwright


class WSJAutomation:
    def __init__(self, config, progress_callback=None, status_callback=None):
        self.config = config
        self.progress_callback = progress_callback
        self.status_callback = status_callback
        self.browser = None
        self.page = None
        self.playwright = None
        
    def update_progress(self, message, progress=None):
        if self.progress_callback:
            self.progress_callback(message, progress)
            
    def update_status(self, message):
        print(f"[WSJ] {message}")
        if self.status_callback:
            self.status_callback(message)
    
    def connect_to_chrome(self):
        """连接到已启动的Chrome调试实例"""
        try:
            self.update_status("连接到Chrome...")
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.connect_over_cdp('http://127.0.0.1:9222')
            self.update_status("已连接到Chrome")
            return True
        except Exception as e:
            self.update_status(f"连接Chrome失败: {str(e)}")
            print(f"[WSJ] 连接Chrome失败: {e}")
            return False
            
    def download_wsj_frontpage(self, save_dir=None):
        """
        打开华尔街日报Twitter页面，下载首页图片

        Args:
            save_dir: 保存目录，默认使用配置中的下载目录

        Returns:
            str: 下载的文件路径，失败返回None
        """
        try:
            print("[WSJ] ===== 开始华尔街日报下载 =====")
            
            if not save_dir:
                save_dir = self.config.get('download_settings', {}).get('save_directory', 'download')
            
            print(f"[WSJ] 保存目录: {save_dir}")
            os.makedirs(save_dir, exist_ok=True)
            
            if not self.connect_to_chrome():
                return None
            
            self.update_status("正在获取页面...")
            self.update_progress("获取页面", 10)
            
            contexts = self.browser.contexts
            print(f"[WSJ] contexts数量: {len(contexts)}")
            
            if contexts:
                context = contexts[0]
                pages = context.pages
                print(f"[WSJ] pages数量: {len(pages)}")
                
                self.page = None
                for p in pages:
                    try:
                        url = p.url
                        if url.startswith('http'):
                            self.page = p
                            print(f"[WSJ] 使用现有页面: {url}")
                            break
                    except:
                        continue
                
                if not self.page:
                    self.page = context.new_page()
                    print(f"[WSJ] 创建新页面: {self.page}")
            else:
                self.update_status("没有可用的浏览器context")
                return None
            
            if not self.page:
                self.update_status("创建页面失败")
                print("[WSJ] 错误: 创建页面失败")
                return None
            
            self.update_status("浏览器已准备就绪")

            target_url = 'https://x.com/wsj'

            self.update_status("正在导航到华尔街日报Twitter页面...")
            self.update_progress("导航到WSJ", 20)
            self.update_status(f"目标URL: {target_url}")
            print(f"[WSJ] 目标URL: {target_url}")

            try:
                self.update_status("正在跳转...")
                self.page.goto(target_url, timeout=60000)
                print(f"[WSJ] 跳转后URL: {self.page.url}")
                self.update_status(f"跳转后URL: {self.page.url}")
                time.sleep(5)
            except Exception as e:
                self.update_status(f"导航异常: {str(e)}")
                print(f"[WSJ] 导航异常: {e}")
                import traceback
                traceback.print_exc()
                return None

            self.update_status("等待页面加载完成...")
            self.update_progress("等待页面加载", 40)
            time.sleep(5)
            
            self.update_status("正在查找包含front page的帖子...")
            self.update_progress("查找帖子", 50)
            
            target_text = "look at the front page of The Wall Street"
            
            self.update_status(f"搜索关键词: {target_text}")
            
            time.sleep(3)
            
            posts = self.page.query_selector_all('article[data-testid="tweet"]')
            print(f"[WSJ] 找到 {len(posts)} 个帖子")
            
            target_post = None
            for i, post in enumerate(posts):
                try:
                    post_text = post.inner_text()
                    print(f"[WSJ] 帖子{i}文本片段: {post_text[:100]}...")
                    
                    if target_text.lower() in post_text.lower():
                        target_post = post
                        self.update_status(f"找到目标帖子!")
                        print(f"[WSJ] 找到目标帖子: {post_text[:200]}")
                        break
                except Exception as e:
                    print(f"[WSJ] 处理帖子{i}异常: {e}")
                    continue
            
            if not target_post:
                self.update_status("未找到包含front page的帖子，尝试滚动...")
                
                for scroll_count in range(5):
                    self.page.keyboard.press('End')
                    time.sleep(2)
                    
                    posts = self.page.query_selector_all('article[data-testid="tweet"]')
                    print(f"[WSJ] 滚动后找到 {len(posts)} 个帖子")
                    
                    for i, post in enumerate(posts):
                        try:
                            post_text = post.inner_text()
                            if target_text.lower() in post_text.lower():
                                target_post = post
                                self.update_status(f"找到目标帖子!")
                                print(f"[WSJ] 找到目标帖子")
                                break
                        except:
                            continue
                    
                    if target_post:
                        break
            
            if not target_post:
                self.update_status("未找到目标帖子")
                print("[WSJ] 错误: 未找到目标帖子")
                return None
            
            self.update_status("正在查找帖子中的图片...")
            self.update_progress("查找图片", 60)
            
            img_elements = target_post.query_selector_all('img')
            print(f"[WSJ] 帖子中找到 {len(img_elements)} 个图片元素")
            
            img_src = None
            img_element = None
            
            for img in img_elements:
                try:
                    src = img.get_attribute('src')
                    alt = img.get_attribute('alt') or ''
                    
                    print(f"[WSJ] 图片: src={src}, alt={alt[:50] if alt else 'None'}")
                    
                    if src and ('media' in src or 'pbs.twimg.com' in src or 'profile_images' not in src):
                        if 'profile' not in src.lower() and 'avatar' not in src.lower():
                            img_src = src
                            img_element = img
                            self.update_status(f"找到帖子图片: {src[:60]}...")
                            break
                except Exception as e:
                    print(f"[WSJ] 处理图片异常: {e}")
                    continue
            
            if not img_src:
                self.update_status("未找到帖子图片")
                print("[WSJ] 错误: 未找到帖子图片")
                return None
            
            if img_src.startswith('//'):
                img_src = 'https:' + img_src
            
            self.update_status(f"图片URL: {img_src}")
            print(f"[WSJ] 最终图片URL: {img_src}")
            
            self.update_status("正在打开图片页面...")
            self.update_progress("打开图片页面", 70)
            
            try:
                self.page.goto(img_src, timeout=30000)
                print(f"[WSJ] 已打开图片页面: {self.page.url}")
                time.sleep(2)
            except Exception as e:
                self.update_status(f"打开图片页面失败: {str(e)}")
                print(f"[WSJ] 打开图片页面失败: {e}")
            
            self.update_status("正在下载图片...")
            self.update_progress("下载图片", 80)
            
            try:
                print(f"[WSJ] 使用浏览器context下载图片...")
                context = self.browser.contexts[0] if self.browser.contexts else None
                
                if context:
                    api_request = context.request
                    response = api_request.get(img_src)
                    
                    if response.ok:
                        img_data = response.body()
                        print(f"[WSJ] 图片数据大小: {len(img_data)} bytes")
                        
                        today = datetime.now()
                        date_filename = today.strftime('%Y%m%d')
                        filename = f"wsj_{date_filename}.jpg"
                        filepath = os.path.join(save_dir, filename)
                        
                        with open(filepath, 'wb') as f:
                            f.write(img_data)
                        
                        self.update_status(f"图片已保存: {filepath}")
                        self.update_progress("保存完成", 90)
                        print(f"[WSJ] 图片已保存: {filepath}")
                        
                        return filepath
                    else:
                        self.update_status(f"下载失败: HTTP {response.status}")
                        print(f"[WSJ] 下载失败: HTTP {response.status}")
                else:
                    self.update_status("无法获取浏览器context")
                    print("[WSJ] 错误: 无法获取浏览器context")
                    
            except Exception as e:
                self.update_status(f"下载图片失败: {str(e)}")
                print(f"[WSJ] 下载图片异常: {e}")
                import traceback
                traceback.print_exc()
                return None

            print("[WSJ] 返回 None")
            return None

        except Exception as e:
            self.update_status(f"发生错误: {str(e)}")
            print(f"[WSJ] 发生错误: {e}")
            import traceback
            traceback.print_exc()
            return None
        finally:
            try:
                if self.playwright:
                    self.playwright.stop()
            except:
                pass
