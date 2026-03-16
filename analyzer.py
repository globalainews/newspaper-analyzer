import tkinter as tk
from tkinter import messagebox
import requests
import os
import json
import base64
import re
from PIL import Image, ImageTk


class ImageAnalyzer:
    def __init__(self, config, root, result_text_widget, preview_canvas_widget):
        self.config = config
        self.root = root
        self.result_text = result_text_widget
        self.preview_canvas = preview_canvas_widget
        
        self.analysis_dir = self.config.get('analysis_settings', {}).get('analysis_directory', 'analysis_results')
        os.makedirs(self.analysis_dir, exist_ok=True)
        
        self.gemini_available = False
        self.proxy_url = None
        self.init_gemini()
    
    def init_gemini(self):
        try:
            api_key = self.config['gemini']['api_key']
            if api_key == "YOUR_GEMINI_API_KEY_HERE":
                self.gemini_available = False
                return
            
            proxy_config = self.config['gemini']['proxy']
            self.proxy_url = f'http://{proxy_config["host"]}:{proxy_config["port"]}'
            self.gemini_api_key = api_key
            self.gemini_model = self.config['gemini']['model']
            self.gemini_available = True
            
        except Exception as e:
            print(f"Gemini初始化失败: {e}")
            self.gemini_available = False
    
    def parse_news_blocks(self, content):
        news_blocks = []
        try:
            lines = content.split('\n')
            
            in_news_blocks = False
            for i, line in enumerate(lines):
                if '【新闻块位置信息】' in line:
                    in_news_blocks = True
                    continue
                
                if in_news_blocks:
                    if line.strip().startswith('---') or (line.strip().startswith('【') and '新闻块位置信息' not in line):
                        break
                    
                    if line.strip().startswith(('0.', '1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.', '10.')):
                        try:
                            title_line = line.strip()
                            if '新闻标题:' in title_line:
                                title = title_line.split('新闻标题:')[-1].strip()
                            elif '报纸内容区域' in title_line:
                                title = '报纸内容区域'
                            else:
                                continue
                                
                            if i + 1 < len(lines):
                                pos_line = lines[i + 1].strip()
                                if '位置:' in pos_line:
                                    pos_str = pos_line.split('位置:')[-1].strip()
                                    coords = []
                                    for part in pos_str.split(','):
                                        match = re.search(r'\d+', part.strip())
                                        if match:
                                            coords.append(int(match.group()))
                                    if len(coords) == 4:
                                        news_blocks.append({
                                            'title': title,
                                            'position': coords
                                        })
                        except Exception as e:
                            print(f"解析新闻块行失败: {e}")
                            continue
        except Exception as e:
            print(f"解析新闻块位置信息失败: {e}")
        
        return news_blocks
    
    def show_image_preview(self, filepath, news_blocks=None):
        try:
            # 存储原始图片和缩放比例
            self.original_image = Image.open(filepath)
            self.current_scale = 1.0
            self.news_blocks = news_blocks
            
            # 创建预览窗口
            preview_window = tk.Toplevel(self.root)
            preview_window.title("图片预览")
            preview_window.geometry("800x600")
            
            # 创建工具栏
            toolbar = tk.Frame(preview_window, bg='#f0f0f0', relief=tk.RAISED, bd=1)
            toolbar.pack(fill=tk.X, padx=5, pady=5)
            
            # 创建画布
            canvas_frame = tk.Frame(preview_window, bg='#bdbdbd', relief=tk.SUNKEN, bd=1)
            canvas_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            preview_canvas = tk.Canvas(canvas_frame, bg='white', highlightthickness=0)
            preview_canvas.pack(fill=tk.BOTH, expand=True)
            
            # 存储画布引用
            self.preview_canvas = preview_canvas
            
            # 重新创建工具栏按钮（现在preview_canvas已定义）
            toolbar.destroy()
            toolbar = tk.Frame(preview_window, bg='#f0f0f0', relief=tk.RAISED, bd=1)
            toolbar.pack(fill=tk.X, padx=5, pady=5)
            
            # 缩放按钮
            zoom_in_btn = tk.Button(toolbar, text="放大", command=lambda: self.zoom_image(preview_canvas, 1.2))
            zoom_in_btn.pack(side=tk.LEFT, padx=5)
            
            zoom_out_btn = tk.Button(toolbar, text="缩小", command=lambda: self.zoom_image(preview_canvas, 0.8))
            zoom_out_btn.pack(side=tk.LEFT, padx=5)
            
            reset_btn = tk.Button(toolbar, text="重置", command=lambda: self.reset_image(preview_canvas))
            reset_btn.pack(side=tk.LEFT, padx=5)
            
            # 状态标签
            self.zoom_label = tk.Label(toolbar, text="缩放: 100%")
            self.zoom_label.pack(side=tk.RIGHT, padx=10)
            
            # 初始显示图片
            self.update_image_display(preview_canvas)
            
            # 绑定鼠标滚轮事件
            preview_canvas.bind("<MouseWheel>", lambda e: self.on_mouse_wheel(e, preview_canvas))
            
        except Exception as e:
            self.preview_canvas.delete("all")
            self.preview_canvas.create_text(
                175, 200, text=f"预览失败: {str(e)}", 
                font=("Microsoft YaHei", 11), fill='#E74C3C'
            )
    
    def update_image_display(self, canvas):
        """更新图片显示"""
        try:
            canvas.delete("all")
            
            # 获取画布尺寸
            canvas_width = canvas.winfo_width()
            canvas_height = canvas.winfo_height()
            
            if canvas_width <= 1 or canvas_height <= 1:
                canvas_width = 700
                canvas_height = 500
            
            # 计算缩放后的图片尺寸
            orig_width, orig_height = self.original_image.size
            new_width = int(orig_width * self.current_scale)
            new_height = int(orig_height * self.current_scale)
            
            # 调整图片大小
            resized_image = self.original_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            self.preview_photo = ImageTk.PhotoImage(resized_image)
            
            # 居中显示
            x_offset = (canvas_width - new_width) // 2
            y_offset = (canvas_height - new_height) // 2
            
            # 绘制图片
            canvas.create_image(x_offset, y_offset, anchor=tk.NW, image=self.preview_photo)
            
            # 绘制新闻块
            if self.news_blocks:
                colors = ['#FF0000', '#00FF00', '#0000FF', '#FFFF00', '#FF00FF', '#00FFFF', 
                          '#FF8800', '#8800FF', '#0088FF', '#88FF00']
                for i, block in enumerate(self.news_blocks):
                    try:
                        x1, y1, x2, y2 = block['position']
                        x1_scaled = x_offset + int(x1 * self.current_scale)
                        y1_scaled = y_offset + int(y1 * self.current_scale)
                        x2_scaled = x_offset + int(x2 * self.current_scale)
                        y2_scaled = y_offset + int(y2 * self.current_scale)
                        
                        if block['title'] == '报纸内容区域':
                            color = '#000000'
                            line_width = 3
                            dash_pattern = (5, 5)
                        else:
                            color = colors[i % len(colors)]
                            line_width = 2
                            dash_pattern = None
                        
                        kwargs = {
                            'outline': color, 
                            'width': line_width, 
                            'tags': f'news_block_{i}'
                        }
                        if dash_pattern:
                            kwargs['dash'] = dash_pattern
                        
                        canvas.create_rectangle(
                            x1_scaled, y1_scaled, x2_scaled, y2_scaled,
                            **kwargs
                        )
                        
                        label_text = '报纸内容区域' if block['title'] == '报纸内容区域' else f"{i+1}. {block['title'][:10]}..."
                        label_y = y1_scaled - 20 if y1_scaled - 20 > 0 else y1_scaled
                        canvas.create_text(
                            x1_scaled + 5, label_y,
                            text=label_text,
                            fill=color, font=("Microsoft YaHei", 9, "bold"),
                            anchor=tk.SW
                        )
                    except Exception as e:
                        print(f"绘制新闻块 {i} 失败: {e}")
            
            # 更新缩放标签
            if hasattr(self, 'zoom_label'):
                self.zoom_label.config(text=f"缩放: {int(self.current_scale * 100)}%")
                
        except Exception as e:
            print(f"更新图片显示失败: {e}")
    
    def zoom_image(self, canvas, factor):
        """缩放图片"""
        try:
            # 限制缩放范围
            new_scale = self.current_scale * factor
            if 0.1 <= new_scale <= 5.0:
                self.current_scale = new_scale
                self.update_image_display(canvas)
        except Exception as e:
            print(f"缩放失败: {e}")
    
    def reset_image(self, canvas):
        """重置图片缩放"""
        try:
            self.current_scale = 1.0
            self.update_image_display(canvas)
        except Exception as e:
            print(f"重置失败: {e}")
    
    def on_mouse_wheel(self, event, canvas):
        """鼠标滚轮缩放"""
        try:
            # 向上滚动放大，向下滚动缩小
            factor = 1.1 if event.delta > 0 else 0.9
            self.zoom_image(canvas, factor)
        except Exception as e:
            print(f"鼠标滚轮缩放失败: {e}")
    
    def show_simple_preview(self, filepath, canvas):
        """显示简单的图片预览（用于首页）"""
        try:
            image = Image.open(filepath)
            
            # 强制更新canvas尺寸
            canvas.update_idletasks()
            canvas_width = canvas.winfo_width()
            canvas_height = canvas.winfo_height()
            
            if canvas_width <= 1 or canvas_height <= 1:
                canvas_width = 350
                canvas_height = 400
            
            orig_width, orig_height = image.size
            
            ratio = min(canvas_width / orig_width, canvas_height / orig_height, 1.0)
            new_size = (int(orig_width * ratio), int(orig_height * ratio))
            
            image = image.resize(new_size, Image.Resampling.LANCZOS)
            
            self.preview_photo = ImageTk.PhotoImage(image)
            
            canvas.delete("all")
            
            x_offset = (canvas_width - new_size[0]) // 2
            y_offset = (canvas_height - new_size[1]) // 2
            
            canvas.create_image(x_offset, y_offset, anchor=tk.NW, image=self.preview_photo)
            
        except Exception as e:
            canvas.delete("all")
            canvas.create_text(
                175, 200, text=f"预览失败: {str(e)}", 
                font=("Microsoft YaHei", 11), fill='#E74C3C'
            )
    
    def show_preview_with_blocks(self, filepath, news_blocks=None):
        """在首页显示带新闻块标记的图片预览"""
        try:
            image = Image.open(filepath)
            
            # 强制更新canvas尺寸
            self.preview_canvas.update_idletasks()
            canvas_width = self.preview_canvas.winfo_width()
            canvas_height = self.preview_canvas.winfo_height()
            
            if canvas_width <= 1 or canvas_height <= 1:
                canvas_width = 350
                canvas_height = 400
            
            orig_width, orig_height = image.size
            
            ratio = min(canvas_width / orig_width, canvas_height / orig_height, 1.0)
            new_size = (int(orig_width * ratio), int(orig_height * ratio))
            
            image = image.resize(new_size, Image.Resampling.LANCZOS)
            
            self.preview_photo = ImageTk.PhotoImage(image)
            
            self.preview_canvas.delete("all")
            
            x_offset = (canvas_width - new_size[0]) // 2
            y_offset = (canvas_height - new_size[1]) // 2
            
            # 绘制图片
            self.preview_canvas.create_image(x_offset, y_offset, anchor=tk.NW, image=self.preview_photo)
            
            # 绘制新闻块
            if news_blocks:
                colors = ['#FF0000', '#00FF00', '#0000FF', '#FFFF00', '#FF00FF', '#00FFFF', 
                          '#FF8800', '#8800FF', '#0088FF', '#88FF00']
                for i, block in enumerate(news_blocks):
                    try:
                        x1, y1, x2, y2 = block['position']
                        x1_scaled = x_offset + int(x1 * ratio)
                        y1_scaled = y_offset + int(y1 * ratio)
                        x2_scaled = x_offset + int(x2 * ratio)
                        y2_scaled = y_offset + int(y2 * ratio)
                        
                        if block['title'] == '报纸内容区域':
                            color = '#000000'
                            line_width = 3
                            dash_pattern = (5, 5)
                        else:
                            color = colors[i % len(colors)]
                            line_width = 2
                            dash_pattern = None
                        
                        kwargs = {
                            'outline': color, 
                            'width': line_width, 
                            'tags': f'news_block_{i}'
                        }
                        if dash_pattern:
                            kwargs['dash'] = dash_pattern
                        
                        self.preview_canvas.create_rectangle(
                            x1_scaled, y1_scaled, x2_scaled, y2_scaled,
                            **kwargs
                        )
                        
                        label_text = '报纸内容区域' if block['title'] == '报纸内容区域' else f"{i+1}. {block['title'][:10]}..."
                        label_y = y1_scaled - 20 if y1_scaled - 20 > 0 else y1_scaled
                        self.preview_canvas.create_text(
                            x1_scaled + 5, label_y,
                            text=label_text,
                            fill=color, font=("Microsoft YaHei", 9, "bold"),
                            anchor=tk.SW
                        )
                    except Exception as e:
                        print(f"绘制新闻块 {i} 失败: {e}")
            
        except Exception as e:
            self.preview_canvas.delete("all")
            self.preview_canvas.create_text(
                175, 200, text=f"预览失败: {str(e)}", 
                font=("Microsoft YaHei", 11), fill='#E74C3C'
            )
    
    def load_analysis_result(self, filename, download_dir):
        """加载分析结果文本（不显示图片预览）"""
        base_name = os.path.splitext(filename)[0]
        analysis_file = os.path.join(self.analysis_dir, f"{base_name}.txt")
        
        self.result_text.delete(1.0, tk.END)
        news_blocks = []
        
        if os.path.exists(analysis_file):
            try:
                with open(analysis_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.result_text.insert(tk.END, content)
                news_blocks = self.parse_news_blocks(content)
            except Exception as e:
                self.result_text.insert(tk.END, f"读取分析结果失败: {str(e)}")
        else:
            self.result_text.insert(tk.END, "暂无分析结果\n\n点击\"分析图片\"按钮开始分析")
        
        return news_blocks
    
    def analyze_image(self, filename, download_dir):
        if not self.gemini_available:
            messagebox.showerror("错误", "Gemini API未配置，请检查config.json文件中的api_key设置")
            return False
        
        filepath = os.path.join(download_dir, filename)
        
        try:
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, "正在分析图片，请稍候...\n")
            self.root.update()
            
            # 读取图片宽高
            image = Image.open(filepath)
            width, height = image.size
            
            # 在控制台输出图片宽高信息
            print(f"[图片分析] 图片尺寸: 宽度={width} 像素, 高度={height} 像素")
            
            with open(filepath, "rb") as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')
            
            # 读取prompt.txt文件内容
            # 优先使用图片特定的prompt文件
            base_name = os.path.splitext(filename)[0]
            image_prompt_file = os.path.join(self.analysis_dir, f"{base_name}_prompt.txt")
            
            if os.path.exists(image_prompt_file):
                prompt_file = image_prompt_file
                print(f"使用图片特定的Prompt文件: {prompt_file}")
            else:
                prompt_file = self.config.get('analysis_prompt_file', 'prompt.txt')
                print(f"使用默认Prompt文件: {prompt_file}")
            
            with open(prompt_file, 'r', encoding='utf-8') as f:
                prompt_template = f.read()
            
            # 动态填入图片宽高到Prompt（使用[]格式）
            prompt = prompt_template.replace('[WIDTH]', str(width)).replace('[HEIGHT]', str(height))
            
            # 在控制台输出替换后的prompt片段（前500字符）
            print(f"[图片分析] Prompt已填入宽高信息")
            print(f"[图片分析] Prompt前500字符:\n{prompt[:500]}...")
            
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
            
            # 解析JSON响应
            try:
                # 尝试直接解析JSON
                json_result = json.loads(result_text)
            except json.JSONDecodeError:
                # 如果直接解析失败，尝试从文本中提取JSON部分
                try:
                    import re
                    
                    # 方法1: 查找```json和```标记之间的JSON内容
                    json_match = re.search(r'```json\s*([\s\S]*?)\s*```', result_text)
                    
                    if not json_match:
                        # 方法2: 查找包含"newspaper"的完整JSON对象
                        json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', result_text, re.DOTALL)
                    
                    if not json_match:
                        # 方法3: 查找最后一个完整的JSON对象
                        json_match = re.search(r'\{[\s\S]*\}(?=\s*$)', result_text)
                    
                    if json_match:
                        json_str = json_match.group(1) if '```json' in result_text else json_match.group(0)
                        
                        # 尝试解析提取的JSON
                        try:
                            json_result = json.loads(json_str)
                        except json.JSONDecodeError as e:
                            # 如果解析失败，尝试修复常见的JSON格式问题
                            # 移除末尾的逗号
                            json_str = re.sub(r',\s*([}\]])', r'\1', json_str)
                            
                            # 尝试再次解析
                            try:
                                json_result = json.loads(json_str)
                            except json.JSONDecodeError as e2:
                                # 如果还是失败，显示详细的错误信息
                                print(f"JSON解析失败: {e2}")
                                print(f"提取的JSON字符串: {json_str[:500]}...")
                                raise Exception(f"JSON解析失败: {e2}")
                    else:
                        raise Exception("无法从响应中提取JSON数据")
                except Exception as e:
                    # 显示原始响应以便调试
                    self.result_text.delete(1.0, tk.END)
                    self.result_text.insert(tk.END, f"JSON解析失败: {str(e)}\n\n")
                    self.result_text.insert(tk.END, "原始API响应:\n")
                    self.result_text.insert(tk.END, "=" * 50 + "\n")
                    self.result_text.insert(tk.END, result_text)
                    self.result_text.insert(tk.END, "\n" + "=" * 50)
                    messagebox.showerror("错误", f"JSON解析失败: {str(e)}\n\n原始响应已显示在结果区域")
                    return False
            
            # 验证JSON结构
            try:
                # 确保json_result是一个字典
                if not isinstance(json_result, dict):
                    raise Exception(f"JSON结果不是字典类型: {type(json_result)}")
                
                # 检查必要的字段
                required_fields = ['newspaper', 'date', 'title', 'intro', 'news_blocks']
                for field in required_fields:
                    if field not in json_result:
                        print(f"警告: JSON结果缺少字段 {field}")
                
            except Exception as e:
                # 显示JSON结构错误
                self.result_text.delete(1.0, tk.END)
                self.result_text.insert(tk.END, f"JSON结构验证失败: {str(e)}\n\n")
                self.result_text.insert(tk.END, "当前JSON结果:\n")
                self.result_text.insert(tk.END, "=" * 50 + "\n")
                self.result_text.insert(tk.END, str(json_result))
                self.result_text.insert(tk.END, "\n" + "=" * 50)
                messagebox.showerror("错误", f"JSON结构验证失败: {str(e)}\n\n详细信息已显示在结果区域")
                return False
            
            # 保存为JSON文件（自动覆盖已存在的文件）
            base_name = os.path.splitext(filename)[0]
            json_file = os.path.join(self.analysis_dir, f"{base_name}.json")
            
            # 检查文件是否存在
            json_file_existed = os.path.exists(json_file)
            
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(json_result, f, ensure_ascii=False, indent=2)
            
            # 保存为TXT文件（自动覆盖已存在的文件）
            txt_file = os.path.join(self.analysis_dir, f"{base_name}.txt")
            
            # 检查文件是否存在
            txt_file_existed = os.path.exists(txt_file)
            
            with open(txt_file, 'w', encoding='utf-8') as f:
                # 保存大模型的完整原始输出
                f.write("=" * 80 + "\n")
                f.write("大模型完整输出\n")
                f.write("=" * 80 + "\n\n")
                f.write(result_text)
                f.write("\n\n")
                
                # 保存JSON解析结果（方便查看结构化数据）
                f.write("=" * 80 + "\n")
                f.write("JSON解析结果\n")
                f.write("=" * 80 + "\n\n")
                f.write(f"报纸: {json_result.get('newspaper', '未知')}\n")
                f.write(f"日期: {json_result.get('date', '未知')}\n\n")
                f.write(f"说明内容第一行: {json_result.get('title', {}).get('line1', '无')}\n")
                f.write(f"说明内容第二行: {json_result.get('title', {}).get('line2', '无')}\n\n")
                f.write(f"概述内容: {json_result.get('intro', '无')}\n\n")
                f.write("【新闻块位置信息】\n")
                for i, news in enumerate(json_result.get('news_blocks', [])):
                    f.write(f"{i+1}. 新闻标题: {news.get('title', '无')}\n")
                    f.write(f"   位置: {news.get('position', [])}\n")
                    f.write(f"   内容: {news.get('content', '无')}\n\n")
            
            # 显示保存结果
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, f"图片分析完成!\n")
            
            # 显示文件覆盖信息
            if json_file_existed:
                self.result_text.insert(tk.END, f"JSON文件已更新（覆盖原有文件）: {json_file}\n")
            else:
                self.result_text.insert(tk.END, f"JSON文件已保存到: {json_file}\n")
            
            if txt_file_existed:
                self.result_text.insert(tk.END, f"TXT文件已更新（覆盖原有文件）: {txt_file}\n")
            else:
                self.result_text.insert(tk.END, f"TXT文件已保存到: {txt_file}\n")
            
            # 读取并显示TXT文件的内容
            self.result_text.insert(tk.END, "\n" + "=" * 50 + "\n")
            self.result_text.insert(tk.END, "分析结果内容:\n")
            self.result_text.insert(tk.END, "=" * 50 + "\n\n")
            
            with open(txt_file, 'r', encoding='utf-8') as f:
                txt_content = f.read()
                self.result_text.insert(tk.END, txt_content)
            
            # 在首页显示带新闻块标记的图片预览
            self.show_preview_with_blocks(filepath, json_result.get('news_blocks', []))
            
            messagebox.showinfo("分析完成", f"图片分析完成!\n\nJSON结果已保存到:\n{json_file}")
            
            return json_result
                
        except Exception as e:
            error_msg = f"分析失败: {str(e)}"
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, error_msg)
            messagebox.showerror("错误", error_msg)
            return False