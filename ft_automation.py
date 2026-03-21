# 金融时报下载自动化模块 - 使用Playwright实现浏览器自动化
import os
import time
import requests
from datetime import datetime
from playwright.sync_api import sync_playwright


class FTAutomation:
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
        print(f"[FT] {message}")
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
            print(f"[FT] 连接Chrome失败: {e}")
            return None
            
    def download_ft_frontpage(self, save_dir=None):
        """
        打开金融时报网页，下载首页图片

        Args:
            save_dir: 保存目录，默认使用配置中的下载目录

        Returns:
            str: 下载的文件路径，失败返回None
        """
        try:
            print("[FT] ===== 开始金融时报下载 =====")
            
            if not save_dir:
                save_dir = self.config.get('download_settings', {}).get('save_directory', 'download')
            
            print(f"[FT] 保存目录: {save_dir}")
            os.makedirs(save_dir, exist_ok=True)
            
            if not self.connect_to_chrome():
                return None
            
            self.update_status("正在获取页面...")
            self.update_progress("获取页面", 10)
            
            contexts = self.browser.contexts
            print(f"[FT] contexts数量: {len(contexts)}")
            
            if contexts:
                context = contexts[0]
                pages = context.pages
                print(f"[FT] pages数量: {len(pages)}")
                
                self.page = None
                for p in pages:
                    try:
                        url = p.url
                        if url.startswith('http'):
                            self.page = p
                            print(f"[FT] 使用现有页面: {url}")
                            break
                    except:
                        continue
                
                if not self.page:
                    self.page = context.new_page()
                    print(f"[FT] 创建新页面: {self.page}")
            else:
                self.update_status("没有可用的浏览器context")
                return None
            
            if not self.page:
                self.update_status("创建页面失败")
                print("[FT] 错误: 创建页面失败")
                return None
            
            self.update_status("浏览器已准备就绪")

            today = datetime.now()
            date_str = today.strftime('%Y-%m-%d')
            target_url = f'https://www.tomorrowspapers.co.uk/financial-times-front-page-{date_str}/'

            self.update_status("正在导航到金融时报页面...")
            self.update_progress("导航到金融时报", 20)
            self.update_status(f"目标URL: {target_url}")
            print(f"[FT] 目标URL: {target_url}")

            try:
                self.update_status("正在跳转...")
                self.page.goto(target_url, timeout=60000)
                print(f"[FT] 跳转后URL: {self.page.url}")
                self.update_status(f"跳转后URL: {self.page.url}")
                time.sleep(5)
            except Exception as e:
                self.update_status(f"导航异常: {str(e)}")
                print(f"[FT] 导航异常: {e}")
                import traceback
                traceback.print_exc()
                return None

            self.update_status("等待页面加载完成...")
            self.update_progress("等待页面加载", 40)
            time.sleep(5)
            
            self.update_status("检测是否有安全验证...")
            page_content = self.page.content()
            print(f"[FT] 页面内容长度: {len(page_content)}")
            
            if '安全验证' in page_content or 'security' in page_content.lower() or '验证' in page_content:
                self.update_status("检测到安全验证页面，请手动完成验证...")
                print("[FT] 检测到安全验证页面")
                self.update_status("等待用户完成验证 (30秒)...")
                time.sleep(30)
                
                print(f"[FT] 验证后URL: {self.page.url}")
                self.update_status(f"验证后URL: {self.page.url}")
                page_content = self.page.content()

            self.update_status("正在查找首页图片...")
            self.update_progress("查找图片", 50)

            all_imgs = self.page.query_selector_all('img')
            print(f"[FT] 页面上共有 {len(all_imgs)} 个图片元素")
            self.update_status(f"页面上共有 {len(all_imgs)} 个图片元素")

            img_element = None
            img_src = None
            img_candidates = []

            for i, img in enumerate(all_imgs):
                try:
                    src = img.get_attribute('src')
                    alt = img.get_attribute('alt') or ''
                    box = img.bounding_box()
                    
                    if src and box:
                        area = box['width'] * box['height']
                        if area > 1000:
                            img_candidates.append({
                                'src': src,
                                'alt': alt,
                                'area': area,
                                'element': img
                            })
                            print(f"[FT] 候选图片: {src[:50]}... 面积={int(area)}")
                except Exception as e:
                    continue

            print(f"[FT] 找到 {len(img_candidates)} 个候选图片")
            img_candidates.sort(key=lambda x: x['area'], reverse=True)

            for candidate in img_candidates:
                src = candidate['src']
                alt = candidate['alt']
                
                if 'financial' in src.lower() or 'times' in src.lower() or 'front' in src.lower():
                    img_element = candidate['element']
                    img_src = src
                    self.update_status(f"找到金融时报相关图片: {src}")
                    print(f"[FT] 匹配成功(src): {src}")
                    break
                
                if 'financial' in alt.lower() or 'times' in alt.lower() or 'front' in alt.lower():
                    img_element = candidate['element']
                    img_src = src
                    self.update_status(f"找到金融时报相关图片(alt): {src}")
                    print(f"[FT] 匹配成功(alt): {src}")
                    break

            if not img_element and img_candidates:
                self.update_status("使用页面上最大的图片...")
                img_element = img_candidates[0]['element']
                img_src = img_candidates[0]['src']
                print(f"[FT] 使用最大图片: {img_src}")
                self.update_status(f"最大图片: {img_src}")

            if not img_element:
                self.update_status("未找到图片元素")
                print("[FT] 错误: 未找到图片元素")
                return None

            self.update_status("正在下载图片...")
            self.update_progress("下载图片", 70)

            if img_src:
                if img_src.startswith('//'):
                    img_src = 'https:' + img_src
                elif not img_src.startswith('http'):
                    base_url = self.page.url
                    img_src = base_url.rstrip('/') + '/' + img_src.lstrip('/')

                self.update_status(f"图片URL: {img_src}")
                print(f"[FT] 最终图片URL: {img_src}")

                try:
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        'Referer': self.page.url
                    }
                    print(f"[FT] 开始下载图片...")
                    response = requests.get(img_src, headers=headers, timeout=30)
                    print(f"[FT] 下载响应状态码: {response.status_code}")
                    
                    if response.status_code == 200:
                        img_data = response.content
                        print(f"[FT] 图片数据大小: {len(img_data)} bytes")
                        
                        date_filename = today.strftime('%Y%m%d')
                        filename = f"ft_{date_filename}.jpg"
                        filepath = os.path.join(save_dir, filename)
                        
                        with open(filepath, 'wb') as f:
                            f.write(img_data)
                        
                        self.update_status(f"图片已保存: {filepath}")
                        self.update_progress("保存完成", 90)
                        print(f"[FT] 图片已保存: {filepath}")
                        
                        return filepath
                    else:
                        self.update_status(f"下载失败: HTTP {response.status_code}")
                        print(f"[FT] 下载失败: HTTP {response.status_code}")
                except Exception as e:
                    self.update_status(f"下载图片失败: {str(e)}")
                    print(f"[FT] 下载图片异常: {e}")
                    
                    try:
                        self.update_status("尝试使用截图方式保存...")
                        print("[FT] 尝试截图方式...")
                        if img_element:
                            screenshot_path = os.path.join(save_dir, f"ft_{today.strftime('%Y%m%d')}.jpg")
                            img_element.screenshot(path=screenshot_path)
                            filepath = screenshot_path
                            self.update_status(f"截图已保存: {filepath}")
                            print(f"[FT] 截图已保存: {filepath}")
                            return filepath
                    except Exception as e2:
                        self.update_status(f"截图失败: {str(e2)}")
                        print(f"[FT] 截图失败: {e2}")

            print("[FT] 返回 None")
            return None

        except Exception as e:
            self.update_status(f"发生错误: {str(e)}")
            print(f"[FT] 发生错误: {e}")
            import traceback
            traceback.print_exc()
            return None
        finally:
            try:
                if self.playwright:
                    self.playwright.stop()
            except:
                pass
