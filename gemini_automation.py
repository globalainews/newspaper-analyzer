# Gemini自动化模块 - 使用Playwright实现浏览器自动化
import os
import time
from playwright.sync_api import sync_playwright


class GeminiAutomation:
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
        print(f"[Gemini] {message}")
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
            print(f"[Gemini] 连接Chrome失败: {e}")
            return False
            
    def open_gemini_and_analyze(self, prompt_text, image_path):
        """
        打开Gemini页面，粘贴prompt，上传图片，获取分析结果

        Args:
            prompt_text: 要粘贴的prompt文本
            image_path: 要上传的图片路径

        Returns:
            str: 分析结果的markdown文本，失败返回None
        """
        try:
            print("[Gemini] ===== 开始Gemini分析 =====")
            
            if not self.connect_to_chrome():
                return None
            
            self.update_status("正在获取页面...")
            self.update_progress("获取页面", 10)
            
            contexts = self.browser.contexts
            print(f"[Gemini] contexts数量: {len(contexts)}")
            
            if contexts:
                context = contexts[0]
                pages = context.pages
                print(f"[Gemini] pages数量: {len(pages)}")
                
                self.page = None
                for p in pages:
                    try:
                        url = p.url
                        if url.startswith('http'):
                            self.page = p
                            print(f"[Gemini] 使用现有页面: {url}")
                            break
                    except:
                        continue
                
                if not self.page:
                    self.page = context.new_page()
                    print(f"[Gemini] 创建新页面: {self.page}")
            else:
                self.update_status("没有可用的浏览器context")
                return None
            
            if not self.page:
                self.update_status("创建页面失败")
                print("[Gemini] 错误: 创建页面失败")
                return None
            
            target_url = 'https://aistudio.google.com/prompts/new_chat'

            self.update_status("正在导航到Gemini页面...")
            self.update_progress("导航到Gemini", 20)
            self.update_status(f"目标URL: {target_url}")

            try:
                self.update_status("正在跳转...")
                self.page.goto(target_url, timeout=60000)
                self.update_status(f"跳转后URL: {self.page.url}")
                time.sleep(3)
            except Exception as e:
                self.update_status(f"导航异常: {str(e)}")
                try:
                    self.page = context.new_page()
                    self.page.goto(target_url, wait_until='domcontentloaded', timeout=60000)
                    self.update_status(f"重试后URL: {self.page.url}")
                except Exception as e2:
                    self.update_status(f"导航失败: {str(e2)}")
                    return None
            
            self.update_status("正在查找输入框...")
            self.update_progress("查找输入框", 30)
            
            input_selectors = [
                'textarea[aria-label*="prompt"]',
                'textarea[placeholder*="Enter a prompt"]',
                'textarea[placeholder*="输入"]',
                'div[contenteditable="true"]',
                'textarea',
                '.ql-editor',
                '[data-test-id="prompt-input"]'
            ]
            
            input_element = None
            for selector in input_selectors:
                try:
                    input_element = self.page.wait_for_selector(selector, timeout=5000)
                    if input_element:
                        print(f"[Gemini] 找到输入框: {selector}")
                        break
                except:
                    continue
            
            if not input_element:
                self.update_status("未找到输入框，请手动操作...")
                self.update_progress("等待手动操作", 40)
                time.sleep(5)
                for selector in input_selectors:
                    try:
                        input_element = self.page.query_selector(selector)
                        if input_element:
                            break
                    except:
                        continue
            
            if input_element:
                self.update_status("正在粘贴Prompt...")
                self.update_progress("粘贴Prompt", 40)
                
                input_element.click()
                time.sleep(0.5)
                
                input_element.fill(prompt_text)
                time.sleep(1)
                
                self.update_status("正在上传图片...")
                self.update_progress("上传图片", 50)
                
                upload_selectors = [
                    'input[type="file"]',
                    'button[aria-label*="upload"]',
                    'button[aria-label*="image"]',
                    '[data-test-id="upload-button"]'
                ]
                
                upload_input = None
                for selector in upload_selectors:
                    try:
                        if 'input[type="file"]' in selector:
                            upload_input = self.page.query_selector(selector)
                            if upload_input:
                                break
                        else:
                            btn = self.page.query_selector(selector)
                            if btn:
                                btn.click()
                                time.sleep(1)
                                upload_input = self.page.query_selector('input[type="file"]')
                                if upload_input:
                                    break
                    except:
                        continue
                
                if upload_input:
                    upload_input.set_input_files(image_path)
                    time.sleep(2)
                    self.update_status("图片上传成功")
                    self.update_progress("图片上传成功", 60)
                else:
                    self.update_status("未找到上传按钮，请手动上传图片...")
                    self.update_progress("等待手动上传", 60)
                    time.sleep(10)
                
                self.update_status("正在提交分析...")
                self.update_progress("提交分析", 70)

                submit_selectors = [
                    'button[type="submit"].ms-button-primary',
                    'button.ms-button-primary',
                    'button:has-text("Run")',
                    'button[type="submit"]:has-text("Run")',
                    'button[aria-label*="Run"]',
                    'button:has-text("Send")',
                    'button:has-text("发送")',
                    'button[type="submit"]'
                ]

                submit_btn = None
                for selector in submit_selectors:
                    try:
                        submit_btn = self.page.query_selector(selector)
                        if submit_btn and submit_btn.is_visible():
                            self.update_status(f"点击提交按钮: {selector}")
                            submit_btn.click()
                            break
                    except:
                        continue

                if not submit_btn:
                    self.update_status("未找到提交按钮，尝试快捷键...")
                    self.page.keyboard.press('Control+Enter')

                time.sleep(3)

                self.update_status("正在等待分析结果...")
                self.update_progress("等待结果", 80)

                time.sleep(5)

                self.update_status("正在检测输出是否完成...")

                last_text = ""
                last_length = 0
                stable_count = 0
                required_stable_count = 5
                max_wait = 600
                check_interval = 3
                start_time = time.time()

                while time.time() - start_time < max_wait:
                    model_containers = self.page.query_selector_all('div.model-prompt-container[data-turn-role="Model"]')
                    current_text = ""
                    current_length = 0
                    
                    for container in model_containers:
                        try:
                            text_chunks = container.query_selector_all('ms-text-chunk')
                            for chunk in text_chunks:
                                text = chunk.inner_text()
                                if len(text) > 100 and not text.startswith('您是一位资深'):
                                    current_text = text
                                    current_length = len(text)
                                    break
                            if current_text:
                                break
                        except:
                            continue

                    elapsed = int(time.time() - start_time)
                    
                    if current_text:
                        if current_text == last_text and current_length == last_length:
                            stable_count += 1
                            self.update_status(f"输出稳定检测 ({stable_count}/{required_stable_count}) - 已等待{elapsed}秒")
                            
                            if stable_count >= required_stable_count:
                                self.update_status(f"输出已完成")
                                break
                        else:
                            stable_count = 0
                            if current_length > last_length:
                                self.update_status(f"正在输出中... 已等待{elapsed}秒")
                    else:
                        self.update_status(f"等待输出开始... ({elapsed}秒)")
                        stable_count = 0

                    last_text = current_text
                    last_length = current_length
                    time.sleep(check_interval)

                self.update_status("正在获取分析结果...")

                result_text = ""
                model_containers = self.page.query_selector_all('div.model-prompt-container[data-turn-role="Model"]')
                for container in model_containers:
                    try:
                        text_chunks = container.query_selector_all('ms-text-chunk')
                        for chunk in text_chunks:
                            text = chunk.inner_text()
                            if len(text) > 100 and not text.startswith('您是一位资深'):
                                result_text = text
                                break
                        if result_text:
                            break
                    except:
                        continue
                
                if result_text:
                    self.update_status("分析完成")
                    self.update_progress("完成", 100)
                    return result_text
                
                self.update_status("未能获取分析结果")
                return None
                
            else:
                self.update_status("未找到输入框")
                return None

        except Exception as e:
            self.update_status(f"发生错误: {str(e)}")
            print(f"[Gemini] 发生错误: {e}")
            import traceback
            traceback.print_exc()
            return None
        finally:
            try:
                if self.playwright:
                    self.playwright.stop()
            except:
                pass
