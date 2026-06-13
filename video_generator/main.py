# Main VideoGenerator class
# 主视频生成器类

import os
import json
import datetime
import tkinter as tk
from tkinter import messagebox, simpledialog
from .base import VideoGeneratorBase
from .data_management import DataManager
from .ui_helpers import UIHelpers
from .video_creation import VideoCreator
from .jianying_draft import JianyingDraftManager
from .timing_sync import TimingSynchronizer
from .image_processor import process_screenshot

class VideoGenerator(VideoGeneratorBase, DataManager, UIHelpers, VideoCreator, JianyingDraftManager, TimingSynchronizer):
    def __init__(self, config, progress_label_widget=None, progress_bar_widget=None, root=None, main_app=None):
        # 调用所有父类的初始化
        VideoGeneratorBase.__init__(self, config, progress_label_widget, progress_bar_widget, root, main_app)
        DataManager.__init__(self, config, progress_label_widget, progress_bar_widget, root, main_app)
        UIHelpers.__init__(self, config, progress_label_widget, progress_bar_widget, root, main_app)
        VideoCreator.__init__(self, config, progress_label_widget, progress_bar_widget, root, main_app)
        JianyingDraftManager.__init__(self, config, progress_label_widget, progress_bar_widget, root, main_app)
        TimingSynchronizer.__init__(self, config, progress_label_widget, progress_bar_widget, root, main_app)
    
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

    def generate_prompt(self):
        """生成首页Prompt并弹出编辑窗口"""
        # 提取新闻短标题
        short_titles = []
        for news in self.video_data:
            title = news.get('title', '').strip()
            if title:
                # 截取前30个字符作为短标题
                short_title = title[:30] + '...' if len(title) > 30 else title
                short_titles.append(short_title)
        
        # 获取报纸名称
        newspaper_name = "未知报纸"
        if hasattr(self, 'current_image_file') and self.current_image_file:
            filename = os.path.basename(self.current_image_file)
            # 尝试从文件名提取报纸名称
            if 'WSJ' in filename:
                newspaper_name = "华尔街日报"
            elif 'FT' in filename:
                newspaper_name = "金融时报"
        
        # 构建Prompt模板
        prompt_template = f"大标题：{newspaper_name}\n"
        
        # 添加短标题
        for i, title in enumerate(short_titles[:4], 1):
            prompt_template += f"短标题{i}：{title}\n"
        
        # 添加风格描述
        prompt_template += """
一款专业的短视频封面布局，3:4的比例，采用复古报纸评论风格。构图中心是一个手绘讽刺漫画板，具有粗犷的墨水轮廓和有限的配色（经典新闻纸奶油色、黑色墨水和点缀的红色）。漫画顶部是醒目且具有冲击力的新闻标题，使用优雅的衬线字体。纹理包含半色调网点、细微的纸张褶皱和墨水晕染效果。整体氛围尖锐、具有分析性且风趣，让人联想起经典的政治杂志封面。高对比度，适合社交媒体显示的简洁布局。画面中尽量不用文字，如果用要用中文。
"""
        
        # 读取已保存的Prompt（如果存在）
        existing_prompt = ''
        json_file = ''
        if self.current_image_file and os.path.exists(self.current_image_file):
            base_name = os.path.splitext(os.path.basename(self.current_image_file))[0]
            json_file = os.path.join(self.analysis_dir, f"{base_name}.json")
        
        if json_file and os.path.exists(json_file):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    existing_prompt = data.get('prompt', '')
            except:
                pass
        
        # 使用已保存的Prompt或新生成的
        initial_text = existing_prompt if existing_prompt else prompt_template
        
        # 创建弹出窗口
        prompt_window = tk.Toplevel(self.root)
        prompt_window.title("首页Prompt")
        prompt_window.geometry("700x500")
        prompt_window.resizable(True, True)
        
        # 添加按钮区域（移到顶部）
        btn_frame = tk.Frame(prompt_window, padx=10, pady=5)
        btn_frame.pack(fill=tk.X)
        
        def save_prompt():
            """保存Prompt到JSON文件"""
            prompt_text = text_widget.get(1.0, tk.END).strip()
            
            if os.path.exists(json_file):
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                data = {}
            
            data['prompt'] = prompt_text
            
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            self.show_info("成功", "Prompt已保存!")
            prompt_window.destroy()
        
        def regenerate_prompt():
            """重新生成Prompt"""
            text_widget.delete(1.0, tk.END)
            text_widget.insert(tk.END, prompt_template)
        
        def copy_prompt():
            """复制Prompt内容到剪贴板"""
            prompt_text = text_widget.get(1.0, tk.END).strip()
            prompt_window.clipboard_clear()
            prompt_window.clipboard_append(prompt_text)
            prompt_window.update()  # 确保剪贴板更新
        
        copy_btn = tk.Button(btn_frame, text="📋 复制",
                             font=("Microsoft YaHei", 9), bg='#E67E22', fg='white',
                             relief=tk.FLAT, padx=10, pady=3,
                             command=copy_prompt)
        copy_btn.pack(side=tk.LEFT, padx=5)
        
        regenerate_btn = tk.Button(btn_frame, text="🔄 重新生成",
                                   font=("Microsoft YaHei", 9), bg='#3498DB', fg='white',
                                   relief=tk.FLAT, padx=10, pady=3,
                                   command=regenerate_prompt)
        regenerate_btn.pack(side=tk.LEFT, padx=5)
        
        save_btn = tk.Button(btn_frame, text="💾 保存",
                             font=("Microsoft YaHei", 9), bg='#27AE60', fg='white',
                             relief=tk.FLAT, padx=10, pady=3,
                             command=save_prompt)
        save_btn.pack(side=tk.LEFT, padx=5)
        
        cancel_btn = tk.Button(btn_frame, text="❌ 取消",
                               font=("Microsoft YaHei", 9), bg='#95A5A6', fg='white',
                               relief=tk.FLAT, padx=10, pady=3,
                               command=prompt_window.destroy)
        cancel_btn.pack(side=tk.LEFT, padx=5)
        
        # 添加文本编辑区域
        text_frame = tk.Frame(prompt_window, padx=10, pady=5)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        text_label = tk.Label(text_frame, text="Prompt内容：", font=("Microsoft YaHei", 10))
        text_label.pack(anchor=tk.W)
        
        text_widget = tk.Text(text_frame, font=("Microsoft YaHei", 10), wrap=tk.WORD)
        text_widget.pack(fill=tk.BOTH, expand=True, pady=5)
        text_widget.insert(tk.END, initial_text)
        text_widget.focus_set()
    
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

                cosyvoice_config = self.config.get('cosyvoice', {})
                test_text = cosyvoice_config.get('test_text')
                test_instruct = cosyvoice_config.get('test_instruct')
                original_instruct = cloner.instruct
                cloner.instruct = test_instruct

                seeds = [random.randint(0, 65535) for _ in range(5)]

                for i, seed in enumerate(seeds):
                    import torch
                    torch.manual_seed(seed)
                    if torch.cuda.is_available():
                        torch.cuda.manual_seed_all(seed)

                    filename = f"test{seed:05d}.wav"
                    output_path = os.path.join(output_dir, filename)

                    progress = 30 + int((i + 1) / 10 * 60)
                    self.update_progress(f"生成中... {i+1}/100 (seed={seed}, speed={cloner.speed}, instruct={test_instruct[:30]}...)", progress)

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

                cloner.instruct = original_instruct

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
        """根据新闻矩形框截图并保存，同时更新草稿素材的宽高"""
        try:
            if not self.video_data:
                self.show_warning("警告", "没有新闻数据")
                return

            if not self.current_image_file or not os.path.exists(self.current_image_file):
                self.show_warning("警告", "请先选择报纸图片")
                return

            # 获取草稿目录路径
            image_filename = os.path.basename(self.current_image_file)
            base_name = os.path.splitext(image_filename)[0]
            today = datetime.datetime.now()
            date_str = today.strftime("%Y%m%d")
            draft_name = f"{base_name}_{date_str}"
            resources_dir = os.path.join(self.jianying_drafts_dir, draft_name, 'Resources')

            # 创建Resources目录
            os.makedirs(resources_dir, exist_ok=True)

            # 检查是否有新闻条目设置了图片路径或首页图片路径
            has_news_pic = any(news.get('news_pic', '') for news in self.video_data)
            has_front_pic = False
            if hasattr(self, 'front_pic_entry') and self.front_pic_entry:
                front_pic_path = self.front_pic_entry.get().strip()
                has_front_pic = front_pic_path and os.path.exists(front_pic_path)
            
            # 如果有新闻条目设置了图片路径或首页图片路径，先备份原有文件
            if has_news_pic or has_front_pic:
                bak_dir = os.path.join(resources_dir, 'bak')
                os.makedirs(bak_dir, exist_ok=True)
                
                # 备份P?.jpg文件
                import glob
                for p_file in glob.glob(os.path.join(resources_dir, 'P?.jpg')):
                    if os.path.exists(p_file):
                        import shutil
                        bak_path = os.path.join(bak_dir, os.path.basename(p_file))
                        shutil.copy2(p_file, bak_path)
                        print(f"备份文件: {p_file} -> {bak_path}")
                
                # 备份front.png文件
                front_png = os.path.join(resources_dir, 'front.png')
                if os.path.exists(front_png):
                    import shutil
                    bak_path = os.path.join(bak_dir, 'front.png')
                    shutil.copy2(front_png, bak_path)
                    print(f"备份文件: {front_png} -> {bak_path}")

            # 保存每张截图的实际尺寸
            screenshot_sizes = {}

            # 首先处理首页图片
            if has_front_pic:
                import shutil
                front_pic_path = self.front_pic_entry.get().strip()
                front_png_path = os.path.join(resources_dir, 'front.png')
                
                # 复制首页图片为 front.png
                shutil.copy2(front_pic_path, front_png_path)
                print(f"复制首页图片: {front_pic_path} -> {front_png_path}")

            # 遍历所有新闻，处理图片
            screenshot_count = 0
            for i, news in enumerate(self.video_data):
                news_pic_path = news.get('news_pic', '').strip()
                
                if news_pic_path and os.path.exists(news_pic_path):
                    # 如果新闻条目设置了图片路径，直接复制该图片到P?.jpg
                    import shutil
                    screenshot_filename = f"P{i+1}.jpg"
                    screenshot_path = os.path.join(resources_dir, screenshot_filename)
                    
                    shutil.copy2(news_pic_path, screenshot_path)
                    
                    # 获取图片尺寸
                    from PIL import Image
                    with Image.open(screenshot_path) as img:
                        actual_width, actual_height = img.size
                    
                    screenshot_sizes[screenshot_filename] = {'width': actual_width, 'height': actual_height}
                    screenshot_count += 1
                    print(f"复制图片: {news_pic_path} -> {screenshot_path} (尺寸: {actual_width}x{actual_height})")
                else:
                    # 否则执行现有的截图操作
                    position = news.get('position', [0, 0, 0, 0])
                    if len(position) != 4:
                        print(f"新闻 {i+1}: 无有效位置信息且未设置图片路径，跳过")
                        continue

                    # 加载原始图片（按需加载）
                    from PIL import Image
                    pil_image = Image.open(self.current_image_file)
                    orig_width, orig_height = pil_image.size

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
                    
                    # 图片增强处理：扩展到3:4比例 + 文字清晰化
                    cropped = process_screenshot(cropped, target_ratio=(3, 4), sharpness=1.5, contrast=1.2)
                    
                    # 记录实际尺寸（处理后的尺寸）
                    actual_width, actual_height = cropped.size
                    screenshot_sizes[f"P{i+1}.jpg"] = {'width': actual_width, 'height': actual_height}

                    # 保存图片，命名格式：P1.jpg, P2.jpg, ...
                    screenshot_filename = f"P{i+1}.jpg"
                    screenshot_path = os.path.join(resources_dir, screenshot_filename)

                    # JPEG不支持RGBA，需要转换
                    if cropped.mode == 'RGBA':
                        cropped = cropped.convert('RGB')

                    # 保存为JPEG格式
                    cropped.save(screenshot_path, 'JPEG', quality=95)
                    screenshot_count += 1
                    print(f"保存截图: {screenshot_path} (尺寸: {actual_width}x{actual_height})")

            if screenshot_count > 0:
                # 更新草稿素材的宽高
                self.update_draft_material_sizes(draft_name, screenshot_sizes)
                
                self.update_progress(f"截图保存成功 ({screenshot_count} 张)", 100, "#27AE60")
                self.show_info("成功", f"截图保存成功！\n\n共保存 {screenshot_count} 张图片\n\n目录: {resources_dir}")
            else:
                self.show_warning("警告", "没有找到有效的新闻区域")

        except Exception as e:
            self.update_progress(f"截图失败: {str(e)}", 0, "#E74C3C")
            self.show_error("错误", f"截图失败:\n{str(e)}")
    
    def update_draft_material_sizes(self, draft_name, screenshot_sizes):
        """更新草稿素材中P图片的宽高"""
        try:
            draft_dir = os.path.join(self.jianying_drafts_dir, draft_name)
            draft_content_path = os.path.join(draft_dir, 'draft_content.json')
            
            if not os.path.exists(draft_content_path):
                print(f"[警告] 草稿文件不存在: {draft_content_path}")
                return
            
            # 读取草稿文件
            with open(draft_content_path, 'r', encoding='utf-8') as f:
                draft_content = json.load(f)
            
            # 更新videos素材中的P图片宽高
            materials = draft_content.get('materials', {})
            videos = materials.get('videos', [])
            
            updated_count = 0
            for video in videos:
                material_name = video.get('material_name', '')
                if material_name in screenshot_sizes:
                    size_info = screenshot_sizes[material_name]
                    video['width'] = size_info['width']
                    video['height'] = size_info['height']
                    print(f"[已更新] 素材 {material_name}: width={size_info['width']}, height={size_info['height']}")
                    updated_count += 1
            
            # 保存更新后的草稿文件
            with open(draft_content_path, 'w', encoding='utf-8') as f:
                json.dump(draft_content, f, ensure_ascii=False, indent=4)
            
            print(f"[成功] 已更新 {updated_count} 个素材的尺寸")
            
        except Exception as e:
            print(f"[错误] 更新草稿素材尺寸失败: {str(e)}")

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

    def adjust_to_perfect_rectangle(self):
        """将所有新闻区域调整为3:4比例的完美矩形"""
        try:
            if not self.video_data:
                self.show_warning("警告", "没有新闻数据")
                return
            
            if not self.current_image_file or not os.path.exists(self.current_image_file):
                self.show_warning("警告", "请先选择报纸图片")
                return
            
            from PIL import Image
            pil_image = Image.open(self.current_image_file)
            img_width, img_height = pil_image.size
            
            adjusted_count = 0
            for i, news in enumerate(self.video_data):
                position = news.get('position', [0, 0, 0, 0])
                if len(position) != 4:
                    continue
                
                x1, y1, x2, y2 = position
                current_width = x2 - x1
                current_height = y2 - y1
                
                if current_width <= 0 or current_height <= 0:
                    continue
                
                center_x = (x1 + x2) / 2
                center_y = (y1 + y2) / 2
                
                target_ratio = 3 / 4
                current_ratio = current_width / current_height
                
                if current_ratio > target_ratio:
                    new_width = current_width
                    new_height = new_width / target_ratio
                else:
                    new_height = current_height
                    new_width = new_height * target_ratio
                
                new_x1 = center_x - new_width / 2
                new_y1 = center_y - new_height / 2
                new_x2 = center_x + new_width / 2
                new_y2 = center_y + new_height / 2
                
                new_x1 = max(0, int(new_x1))
                new_y1 = max(0, int(new_y1))
                new_x2 = min(img_width, int(new_x2))
                new_y2 = min(img_height, int(new_y2))
                
                # 检查是否靠边导致尺寸不对，如果是则移动矩形
                actual_width = new_x2 - new_x1
                actual_height = new_y2 - new_y1
                if actual_width < new_width * 0.95 or actual_height < new_height * 0.95:
                    # 需要移动矩形
                    target_width = min(new_width, img_width * 0.95)
                    target_height = target_width / target_ratio
                    
                    if target_height > img_height * 0.95:
                        target_height = min(new_height, img_height * 0.95)
                        target_width = target_height * target_ratio
                    
                    # 尝试向中间移动
                    offset_x = 0
                    offset_y = 0
                    
                    if new_x1 == 0:
                        offset_x = (new_width - actual_width) / 2
                    elif new_x2 == img_width:
                        offset_x = -(new_width - actual_width) / 2
                    
                    if new_y1 == 0:
                        offset_y = (new_height - actual_height) / 2
                    elif new_y2 == img_height:
                        offset_y = -(new_height - actual_height) / 2
                    
                    # 如果单边靠，尝试向反方向移动
                    if offset_x == 0 and offset_y == 0:
                        # 尝试整体移动
                        if center_x < img_width / 2:
                            offset_x = min((img_width - new_width) - center_x + new_width / 2, new_width / 2)
                        else:
                            offset_x = max(center_x - new_width / 2 - 0, -new_width / 2)
                    
                    new_x1 = max(0, min(img_width - target_width, int(center_x - target_width / 2 + offset_x)))
                    new_y1 = max(0, min(img_height - target_height, int(center_y - target_height / 2 + offset_y)))
                    new_x2 = int(new_x1 + target_width)
                    new_y2 = int(new_y1 + target_height)
                
                news['position'] = [new_x1, new_y1, new_x2, new_y2]
                adjusted_count += 1
                print(f"新闻 {i+1}: 调整为3:4比例 [{new_x1}, {new_y1}, {new_x2}, {new_y2}]")
            
            self.highlight_news_block(self.current_news_index if self.current_news_index >= 0 else 0)
            
            self.show_info("成功", f"已将 {adjusted_count} 个新闻区域调整为3:4比例")
            
        except Exception as e:
            print(f"调整完美矩形失败: {str(e)}")
            import traceback
            traceback.print_exc()
            self.show_error("错误", f"调整完美矩形失败: {str(e)}")