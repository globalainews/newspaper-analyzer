# Main VideoGenerator class
# 主视频生成器类

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
            news['title'] = title_entry.get()
            news['content'] = content_text.get(1.0, tk.END).strip()
            self.update_news_list()
            edit_window.destroy()
        
        # 保存按钮
        save_btn = tk.Button(edit_window, text="保存", font=("Microsoft YaHei", 10), 
                           bg='#27AE60', fg='white', command=save_edit)
        save_btn.pack(pady=10)
    
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