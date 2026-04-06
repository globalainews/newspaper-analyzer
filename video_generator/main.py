# Main VideoGenerator class
# 主视频生成器类

import os
import datetime
import tkinter as tk
from tkinter import messagebox, simpledialog
from .base import VideoGeneratorBase
from .data_management import DataManager
from .ui_helpers import UIHelpers
from .video_creation import VideoCreator
from .jianying_draft import JianyingDraftManager
from .timing_sync import TimingSynchronizer

class VideoGenerator(VideoGeneratorBase, DataManager, UIHelpers, VideoCreator, JianyingDraftManager, TimingSynchronizer):
    def __init__(self, config, progress_label_widget=None, progress_bar_widget=None, root=None):
        # 调用所有父类的初始化
        VideoGeneratorBase.__init__(self, config, progress_label_widget, progress_bar_widget, root)
        UIHelpers.__init__(self, config, progress_label_widget, progress_bar_widget, root)
        TimingSynchronizer.__init__(self, config, progress_label_widget, progress_bar_widget, root)
    
    def edit_news_inline(self, event):
        """行内编辑新闻（双击编辑）"""
        if not self.news_listbox:
            return
        
        selection = self.news_listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        if index >= len(self.video_data):
            return

        self.current_news_index = index
        news = self.video_data[index]
        
        # 创建编辑窗口
        edit_window = tk.Toplevel(self.root)
        edit_window.title(f"编辑新闻 - {news['title']}")
        edit_window.geometry("500x400")  # 增加窗口高度，确保保存按钮能够显示
        edit_window.transient(self.root)
        edit_window.grab_set()
        
        # 标题编辑
        tk.Label(edit_window, text="标题:", font=("Microsoft YaHei", 10)).pack(pady=5)
        title_entry = tk.Entry(edit_window, font=("Microsoft YaHei", 10), width=60)
        title_entry.pack(pady=5, padx=10)
        title_entry.insert(0, news['title'])
        
        # 内容编辑
        tk.Label(edit_window, text="内容:", font=("Microsoft YaHei", 10)).pack(pady=5)
        content_text = tk.Text(edit_window, font=("Microsoft YaHei", 10), width=60, height=10)
        content_text.pack(pady=5, padx=10)
        content_text.insert(tk.END, news['content'])
        
        def save_edit():
            # 先让编辑窗口获得焦点，确保Text widget内容已提交
            edit_window.focus_set()
            edit_window.update()

            # 延迟100ms后执行保存，确保UI更新完成
            def do_save():
                print(f"[DEBUG save_edit] 开始保存，news['content'] = {news['content'][:50]}...")
                print(f"[DEBUG save_edit] Text widget content = {content_text.get(1.0, tk.END)[:50]}...")
                news['title'] = title_entry.get()
                news['content'] = content_text.get(1.0, tk.END).strip()
                print(f"[DEBUG save_edit] 修改后，news['content'] = {news['content'][:50]}...")
                self.update_news_list()
                print(f"[DEBUG save_edit] 调用 save_video_data()")
                self.save_video_data()
                edit_window.destroy()

            edit_window.after(100, do_save)

        # 保存按钮
        save_btn = tk.Button(edit_window, text="保存", font=("Microsoft YaHei", 10),
                           bg='#27AE60', fg='white', command=save_edit)
        save_btn.pack(pady=10)

        # Text widget 焦点事件 - 按Tab离开时确保内容提交
        def on_text_focus_out(event):
            content_text.update()

        content_text.bind('<FocusOut>', on_text_focus_out)
    
    def edit_news(self):
        """编辑选中的新闻"""
        if self.current_news_index >= 0 and self.current_news_index < len(self.video_data):
            news = self.video_data[self.current_news_index]
            
            # 打开编辑对话框
            title = simpledialog.askstring("编辑新闻", "请输入新闻标题:", initialvalue=news['title'])
            if title is not None:
                content = simpledialog.askstring("编辑新闻", "请输入新闻内容:", initialvalue=news['content'])
                if content is not None:
                    news['title'] = title
                    news['content'] = content
                    self.update_news_list()
                    self.show_info("成功", "新闻编辑成功!")
        else:
            self.show_info("提示", "请先选择要编辑的新闻")
    
    def move_news_up(self):
        """向上移动新闻"""
        if self.current_news_index > 0:
            # 交换位置
            self.video_data[self.current_news_index], self.video_data[self.current_news_index - 1] = \
                self.video_data[self.current_news_index - 1], self.video_data[self.current_news_index]
            
            # 更新ID
            for i, news in enumerate(self.video_data):
                news['id'] = i + 1
            
            self.update_news_list()
            # 重新选中移动后的位置
            if self.news_listbox:
                self.news_listbox.select_set(self.current_news_index - 1)
            self.current_news_index -= 1
            self.show_info("成功", "新闻已向上移动!")
        else:
            self.show_info("提示", "已经是第一条新闻")
    
    def move_news_down(self):
        """向下移动新闻"""
        if self.current_news_index < len(self.video_data) - 1:
            # 交换位置
            self.video_data[self.current_news_index], self.video_data[self.current_news_index + 1] = \
                self.video_data[self.current_news_index + 1], self.video_data[self.current_news_index]
            
            # 更新ID
            for i, news in enumerate(self.video_data):
                news['id'] = i + 1
            
            self.update_news_list()
            # 重新选中移动后的位置
            if self.news_listbox:
                self.news_listbox.select_set(self.current_news_index + 1)
            self.current_news_index += 1
            self.show_info("成功", "新闻已向下移动!")
        else:
            self.show_info("提示", "已经是最后一条新闻")

    def test_voice_clone(self):
        """测试音色克隆，生成10个不同seed的测试音频"""
        import threading
        import random

        def do_test():
            try:
                from voice_clone import get_cosyvoice_cloner
                import os

                self.update_progress("正在加载模型...", 10)
                cloner = get_cosyvoice_cloner(self.config)

                if not cloner.model_loaded:
                    if not cloner.load_model():
                        self.show_error("错误", "模型加载失败")
                        return

                self.update_progress("模型加载完成，开始生成测试音频...", 30)

                output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'output')
                os.makedirs(output_dir, exist_ok=True)

                test_text = "特朗普向德黑兰发出最后通牒，威胁若周二前不重新开放霍尔木兹海峡，将摧毁伊朗所有发电厂。此举极大地加剧了地区紧张局势。"

                seeds = [random.randint(0, 65535) for _ in range(100)]

                for i, seed in enumerate(seeds):
                    import torch
                    torch.manual_seed(seed)
                    if torch.cuda.is_available():
                        torch.cuda.manual_seed_all(seed)

                    filename = f"test{seed:05d}.wav"
                    output_path = os.path.join(output_dir, filename)

                    progress = 30 + int((i + 1) / 10 * 60)
                    self.update_progress(f"生成中... {i+1}/100 (seed={seed}, speed={cloner.speed})", progress)

                    success = cloner.generate_voice(
                        test_text,
                        output_path,
                        silent=False,
                        text_frontend=False
                    )

                    if success:
                        print(f"生成成功: {filename} (seed={seed}, speed={cloner.speed})")
                    else:
                        print(f"生成失败: {filename}")

                self.update_progress("测试完成!", 100)
                self.show_info("完成", f"已在 output 文件夹生成10个测试音频:\n" + "\n".join([f"test{seed:05d}.wav" for seed in seeds]))

            except Exception as e:
                import traceback
                traceback.print_exc()
                self.show_error("错误", f"测试失败: {str(e)}")

        threading.Thread(target=do_test, daemon=True).start()

    def delete_news(self):
        """删除选中的新闻（支持多选）"""
        if not hasattr(self, 'news_selections') or not self.news_selections:
            self.show_info("提示", "新闻列表未初始化")
            return
        
        # 收集选中的索引
        selected_indices = [i for i, selected in enumerate(self.news_selections) if selected]
        if not selected_indices:
            self.show_info("提示", "请先选择要删除的新闻")
            return
        
        selected_count = len(selected_indices)
        if messagebox.askyesno("确认删除", f"确定要删除选中的 {selected_count} 条新闻吗?"):
            # 按索引倒序删除，避免索引变化问题
            for index in sorted(selected_indices, reverse=True):
                if 0 <= index < len(self.video_data):
                    del self.video_data[index]
            
            # 更新ID
            for i, news in enumerate(self.video_data):
                news['id'] = i + 1
            
            self.update_news_list()
            self.current_news_index = -1
            self.show_info("成功", f"已删除 {selected_count} 条新闻!")

    def capture_news_screenshots(self):
        """根据新闻矩形框截图并保存"""
        try:
            if not self.video_data:
                self.show_warning("警告", "没有新闻数据")
                return

            if not self.current_image_file or not os.path.exists(self.current_image_file):
                self.show_warning("警告", "请先选择报纸图片")
                return

            # 加载原始图片
            from PIL import Image
            pil_image = Image.open(self.current_image_file)
            orig_width, orig_height = pil_image.size

            # 获取草稿目录路径
            image_filename = os.path.basename(self.current_image_file)
            base_name = os.path.splitext(image_filename)[0]
            today = datetime.datetime.now()
            date_str = today.strftime("%Y%m%d")
            draft_name = f"{base_name}_{date_str}"
            resources_dir = os.path.join(self.jianying_drafts_dir, draft_name, 'Resources')

            # 创建Resources目录
            os.makedirs(resources_dir, exist_ok=True)

            # 遍历所有新闻，截取对应的区域
            screenshot_count = 0
            for i, news in enumerate(self.video_data):
                position = news.get('position', [0, 0, 0, 0])
                if len(position) != 4:
                    print(f"新闻 {i+1}: 无有效位置信息，跳过")
                    continue

                x1, y1, x2, y2 = position

                # 确保坐标有效
                x1 = max(0, int(x1))
                y1 = max(0, int(y1))
                x2 = min(orig_width, int(x2))
                y2 = min(orig_height, int(y2))

                if x2 <= x1 or y2 <= y1:
                    print(f"新闻 {i+1}: 无效坐标 ({x1},{y1},{x2},{y2})，跳过")
                    continue

                # 裁剪图片
                cropped = pil_image.crop((x1, y1, x2, y2))

                # 保存图片，命名格式：P1.jpg, P2.jpg, ...
                screenshot_filename = f"P{i+1}.jpg"
                screenshot_path = os.path.join(resources_dir, screenshot_filename)

                # 保存为JPEG格式
                cropped.save(screenshot_path, 'JPEG', quality=95)
                screenshot_count += 1
                print(f"保存截图: {screenshot_path}")

            if screenshot_count > 0:
                self.update_progress(f"截图保存成功 ({screenshot_count} 张)", 100, "#27AE60")
                self.show_info("成功", f"截图保存成功！\n\n共保存 {screenshot_count} 张图片\n\n目录: {resources_dir}")
            else:
                self.show_warning("警告", "没有找到有效的新闻区域")

        except Exception as e:
            self.update_progress(f"截图失败: {str(e)}", 0, "#E74C3C")
            self.show_error("错误", f"截图失败:\n{str(e)}")

    def export_news_images(self):
        """导出新闻图片"""
        try:
            if not self.video_data:
                self.show_warning("警告", "没有新闻数据可导出")
                return False
            
            if not self.current_image_file or not os.path.exists(self.current_image_file):
                self.show_warning("警告", "没有选择报纸图片")
                return False
            
            # 确认导出
            if not messagebox.askyesno("确认导出", f"将导出 {len(self.video_data)} 条新闻图片，是否继续?"):
                return False
            
            # 更新进度
            self.update_progress("正在导出新闻图片...")
            self.progress_bar['value'] = 0
            if self.root:
                self.root.update()
            
            # 创建导出器
            from news_image_exporter import NewsImageExporter
            exporter = NewsImageExporter()
            
            # 获取报纸名称
            filename = os.path.basename(self.current_image_file).lower()
            if "wall" in filename or "wsj" in filename:
                newspaper_name = "华尔街日报"
            elif "financial" in filename or "ft" in filename:
                newspaper_name = "金融时报"
            else:
                newspaper_name = "报纸"
            
            # 导出图片
            exported_paths, export_dir = exporter.export_news_images(
                self.current_image_file,
                self.video_data,
                newspaper_name
            )
            
            # 更新进度
            self.progress_bar['value'] = 100
            self.update_progress(f"导出完成: {len(exported_paths)} 张图片", 100, "#27AE60")
            
            # 显示成功消息
            self.show_info("导出成功", 
                f"成功导出 {len(exported_paths)} 张新闻图片!\n\n" 
                f"保存位置: {export_dir}")
            
            return True
            
        except Exception as e:
            self.update_progress(f"导出失败: {str(e)}", 0, "#E74C3C")
            self.show_error("错误", f"导出新闻图片失败:\n{str(e)}")
            return False