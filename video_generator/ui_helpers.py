# UI helpers module
# UI辅助模块

import os
import tkinter as tk
from PIL import Image, ImageTk, ImageDraw, ImageFont
class UIHelpers:
    def __init__(self, config, progress_label_widget=None, progress_bar_widget=None, root=None):
        self.preview_photo = None
        self.selection_start = None
        self.selection_rect = None
        self.selected_region = None
    
    def set_preview_canvas(self, canvas):
        self.preview_canvas = canvas
    
    def on_news_select(self, event):
        if not self.news_listbox:
            return
            
        selection = self.news_listbox.curselection()
        if selection:
            index = selection[0]
            self.current_news_index = index
            self.show_news_preview(index)
    
    def show_news_preview(self, news_index):
        if 0 <= news_index < len(self.video_data):
            news_item = self.video_data[news_index]
            self.update_progress(f"显示新闻: {news_item.get('title', '未命名')}")
            # 在图片预览中高亮显示选中的新闻块
            self.highlight_news_block(news_index)
    
    def highlight_news_block(self, news_index):
        """在图片预览中高亮显示选中的新闻块"""
        try:
            if not hasattr(self, 'preview_canvas') or not self.current_image_file:
                return
            
            if not os.path.exists(self.current_image_file):
                return
            
            canvas = self.preview_canvas
            image = Image.open(self.current_image_file)
            
            canvas.update_idletasks()
            canvas_width = canvas.winfo_width()
            canvas_height = canvas.winfo_height()
            
            if canvas_width <= 1 or canvas_height <= 1:
                canvas_width = 400
                canvas_height = 500
            
            orig_width, orig_height = image.size
            
            ratio = min(canvas_width / orig_width, canvas_height / orig_height, 1.0)
            new_size = (int(orig_width * ratio), int(orig_height * ratio))
            
            image = image.resize(new_size, Image.Resampling.LANCZOS)
            
            self.preview_photo = ImageTk.PhotoImage(image)
            
            canvas.delete("all")
            
            x_offset = (canvas_width - new_size[0]) // 2
            y_offset = (canvas_height - new_size[1]) // 2
            
            # 绘制图片
            canvas.create_image(x_offset, y_offset, anchor=tk.NW, image=self.preview_photo)
            
            # 直接从video_data中获取新闻块的位置信息
            print(f"从JSON数据中获取 {len(self.video_data)} 个新闻块的位置信息...")
            processed_regions = []
            for i, news in enumerate(self.video_data):
                position = news.get('position', [0, 0, 0, 0])
                if len(position) == 4:
                    x1, y1, x2, y2 = position
                    # 确保坐标在图片范围内
                    x1 = max(0, int(x1))
                    y1 = max(0, int(y1))
                    x2 = min(orig_width, int(x2))
                    y2 = min(orig_height, int(y2))
                    
                    if x2 > x1 and y2 > y1:
                        processed_regions.append((x1, y1, x2, y2))
                        print(f"新闻块 {i+1}: {x1},{y1}-{x2},{y2}")
                    else:
                        print(f"新闻块 {i+1}: 无效坐标，跳过")
                else:
                    print(f"新闻块 {i+1}: 无有效位置信息")
            
            # 颜色列表
            colors = ['#FF0000', '#00FF00', '#0000FF', '#FFFF00', '#FF00FF', '#00FFFF', 
                      '#FF8800', '#8800FF', '#0088FF', '#88FF00']
            
            # 为每个新闻绘制矩形框
            for i, news in enumerate(self.video_data):
                try:
                    if i < len(processed_regions):
                        # 使用处理后的区域
                        region = processed_regions[i]
                        x1, y1, x2, y2 = region
                    else:
                        # 如果区域不够，使用最后一个区域
                        if processed_regions:
                            region = processed_regions[-1]
                            x1, y1, x2, y2 = region
                        else:
                            # 没有区域，使用默认位置
                            x1, y1, x2, y2 = 0, 0, orig_width, orig_height
                    
                    # 缩放坐标到画布大小
                    x1_scaled = x_offset + int(x1 * ratio)
                    y1_scaled = y_offset + int(y1 * ratio)
                    x2_scaled = x_offset + int(x2 * ratio)
                    y2_scaled = y_offset + int(y2 * ratio)
                    
                    # 选中的新闻块用红色粗线显示，其他用细线显示
                    if i == news_index:
                        color = '#FF0000'
                        line_width = 4
                    else:
                        color = colors[i % len(colors)]
                        line_width = 2
                    
                    canvas.create_rectangle(
                        x1_scaled, y1_scaled, x2_scaled, y2_scaled,
                        outline=color, width=line_width, tags=f'news_block_{i}'
                    )
                    
                    # 显示新闻标题
                    label_text = f"{i+1}. {news['title'][:10]}..."
                    label_y = y1_scaled - 20 if y1_scaled - 20 > 0 else y1_scaled
                    canvas.create_text(
                        x1_scaled + 5, label_y,
                        text=label_text,
                        fill=color, font=("Microsoft YaHei", 9, "bold"),
                        anchor=tk.SW
                    )
                except Exception as e:
                    print(f"绘制新闻块 {i} 失败: {e}")
                    
        except Exception as e:
            print(f"高亮显示新闻块失败: {e}")
    
    def show_newspaper_image(self):
        """在视频生成页签显示报纸图片"""
        try:
            if self.current_image_file and os.path.exists(self.current_image_file):
                from PIL import Image, ImageTk
                
                if hasattr(self, 'preview_canvas'):
                    canvas = self.preview_canvas
                    image = Image.open(self.current_image_file)
                    
                    canvas.update_idletasks()
                    canvas_width = canvas.winfo_width()
                    canvas_height = canvas.winfo_height()
                    
                    if canvas_width <= 1 or canvas_height <= 1:
                        canvas_width = 400
                        canvas_height = 500
                    
                    orig_width, orig_height = image.size
                    
                    ratio = min(canvas_width / orig_width, canvas_height / orig_height, 1.0)
                    new_size = (int(orig_width * ratio), int(orig_height * ratio))
                    
                    image = image.resize(new_size, Image.Resampling.LANCZOS)
                    
                    self.preview_photo = ImageTk.PhotoImage(image)
                    
                    canvas.delete("all")
                    
                    x_offset = (canvas_width - new_size[0]) // 2
                    y_offset = (canvas_height - new_size[1]) // 2
                    
                    # 绘制图片
                    canvas.create_image(x_offset, y_offset, anchor=tk.NW, image=self.preview_photo)
                    
                    # 绘制所有新闻块的矩形框
                    colors = ['#FF0000', '#00FF00', '#0000FF', '#FFFF00', '#FF00FF', '#00FFFF', 
                              '#FF8800', '#8800FF', '#0088FF', '#88FF00']
                    
                    for i, news in enumerate(self.video_data):
                        try:
                            x1, y1, x2, y2 = news['position']
                            x1_scaled = x_offset + int(x1 * ratio)
                            y1_scaled = y_offset + int(y1 * ratio)
                            x2_scaled = x_offset + int(x2 * ratio)
                            y2_scaled = y_offset + int(y2 * ratio)
                            
                            color = colors[i % len(colors)]
                            line_width = 2
                            
                            canvas.create_rectangle(
                                x1_scaled, y1_scaled, x2_scaled, y2_scaled,
                                outline=color, width=line_width, tags=f'news_block_{i}'
                            )
                            
                            # 显示新闻标题
                            label_text = f"{i+1}. {news['title'][:10]}..."
                            label_y = y1_scaled - 20 if y1_scaled - 20 > 0 else y1_scaled
                            canvas.create_text(
                                x1_scaled + 5, label_y,
                                text=label_text,
                                fill=color, font=("Microsoft YaHei", 9, "bold"),
                                anchor=tk.SW
                            )
                        except Exception as e:
                            print(f"绘制新闻块 {i} 失败: {e}")
                            
        except Exception as e:
            print(f"显示报纸图片失败: {e}")
    
    def update_news_list(self):
        """更新新闻列表"""
        if self.news_listbox:
            self.news_listbox.delete(0, tk.END)
            for i, news in enumerate(self.video_data):
                content_preview = news['content'][:30] + '...' if len(news['content']) > 30 else news['content']
                self.news_listbox.insert(tk.END, f"{i+1}. {news['title']} - {content_preview}")
    
    def enable_region_selection(self):
        """启用区域选择模式"""
        if hasattr(self, 'preview_canvas') and self.current_image_file:
            try:
                canvas = self.preview_canvas
                
                # 绑定鼠标事件
                canvas.bind("<Button-1>", self.on_canvas_click)
                canvas.bind("<B1-Motion>", self.on_canvas_drag)
                canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
                
                # 存储选择状态
                self.selection_start = None
                self.selection_rect = None
                
                self.update_progress("区域选择模式: 点击并拖动选择新闻区域", 0, "#27AE60")
                
            except Exception as e:
                print(f"启用区域选择失败: {e}")
    
    def on_canvas_click(self, event):
        """鼠标点击事件"""
        if hasattr(self, 'preview_canvas'):
            canvas = self.preview_canvas
            self.selection_start = (event.x, event.y)
            
            # 创建选择矩形
            if self.selection_rect:
                canvas.delete(self.selection_rect)
            self.selection_rect = canvas.create_rectangle(
                event.x, event.y, event.x, event.y,
                outline='#FF0000', width=2, dash=(5, 5)
            )
    
    def on_canvas_drag(self, event):
        """鼠标拖动事件"""
        if hasattr(self, 'preview_canvas') and self.selection_start:
            canvas = self.preview_canvas
            x1, y1 = self.selection_start
            x2, y2 = event.x, event.y
            
            # 更新选择矩形
            canvas.coords(self.selection_rect, min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
    
    def on_canvas_release(self, event):
        """鼠标释放事件"""
        if hasattr(self, 'preview_canvas') and self.selection_start:
            canvas = self.preview_canvas
            x1, y1 = self.selection_start
            x2, y2 = event.x, event.y
            
            # 计算实际坐标
            if hasattr(self, 'current_image_file'):
                try:
                    image = Image.open(self.current_image_file)
                    canvas_width = canvas.winfo_width()
                    canvas_height = canvas.winfo_height()
                    
                    orig_width, orig_height = image.size
                    ratio = min(canvas_width / orig_width, canvas_height / orig_height, 1.0)
                    new_size = (int(orig_width * ratio), int(orig_height * ratio))
                    x_offset = (canvas_width - new_size[0]) // 2
                    y_offset = (canvas_height - new_size[1]) // 2
                    
                    # 转换为原始图片坐标
                    real_x1 = int((min(x1, x2) - x_offset) / ratio)
                    real_y1 = int((min(y1, y2) - y_offset) / ratio)
                    real_x2 = int((max(x1, x2) - x_offset) / ratio)
                    real_y2 = int((max(y1, y2) - y_offset) / ratio)
                    
                    # 确保坐标有效
                    real_x1 = max(0, real_x1)
                    real_y1 = max(0, real_y1)
                    real_x2 = min(image.width, real_x2)
                    real_y2 = min(image.height, real_y2)
                    
                    if real_x2 > real_x1 and real_y2 > real_y1:
                        # 显示选择结果
                        self.update_progress(
                            f"选择区域: ({real_x1},{real_y1})-({real_x2},{real_y2}) 大小: {real_x2-real_x1}x{real_y2-real_y1}",
                            0, "#27AE60"
                        )
                        
                        # 保存选择的区域
                        self.selected_region = [real_x1, real_y1, real_x2, real_y2]
                        
                        # 测试导出选中区域
                        self.export_selected_region()
                    else:
                        self.update_progress("无效区域: 请选择更大的区域", 0, "#E74C3C")
                        
                except Exception as e:
                    print(f"计算区域坐标失败: {e}")
            
            # 清除选择
            self.selection_start = None
    
    def export_selected_region(self):
        """导出选中的区域"""
        if hasattr(self, 'selected_region') and self.current_image_file:
            try:
                from PIL import Image
                
                # 加载图片
                image = Image.open(self.current_image_file)
                
                # 裁剪选中区域
                x1, y1, x2, y2 = self.selected_region
                selected_image = image.crop((x1, y1, x2, y2))
                
                # 保存图片
                import os
                from datetime import datetime
                
                output_dir = "selected_regions"
                os.makedirs(output_dir, exist_ok=True)
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"selected_{timestamp}.jpg"
                output_path = os.path.join(output_dir, filename)
                
                selected_image.save(output_path, 'JPEG', quality=95)
                
                self.update_progress(
                    f"选中区域已导出: {filename}",
                    100, "#27AE60"
                )
                
                # 显示成功消息
                self.show_info("导出成功", f"选中的区域已导出到:\n{output_path}")
                
            except Exception as e:
                print(f"导出选中区域失败: {e}")
                self.update_progress(f"导出失败: {str(e)}", 0, "#E74C3C")