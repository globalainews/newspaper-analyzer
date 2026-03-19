# Base class for Video Generator
# 视频生成器基类

import os
import json
import tkinter as tk
from tkinter import messagebox

class VideoGeneratorBase:
    def __init__(self, config, progress_label_widget=None, progress_bar_widget=None, root=None):
        self.config = config
        self.progress_label = progress_label_widget
        self.progress_bar = progress_bar_widget
        self.root = root
        
        self.video_data = []
        self.current_news_index = -1
        self.analysis_dir = self.config.get('analysis_settings', {}).get('analysis_directory', 'analysis_results')
        self.download_dir = self.config['download_settings']['save_directory']
        self.current_image_file = None
        # 剪映草稿文件夹配置
        self.jianying_drafts_dir = self.config.get('jianying_settings', {}).get('drafts_directory', 'E:/剪映5.9/JianyingPro Drafts')
    
    def set_news_listbox(self, news_frame):
        self.news_frame = news_frame
        self.news_textboxes = []
        self.news_selections = []
        self.current_news_index = -1
    
    def update_progress(self, text, value=0, fg="#3498DB"):
        """更新进度信息"""
        if self.progress_label:
            self.progress_label.config(text=text, fg=fg)
        if self.progress_bar and value >= 0:
            self.progress_bar['value'] = value
        if self.root:
            self.root.update()
    
    def show_error(self, title, message):
        """显示错误信息"""
        messagebox.showerror(title, message)
    
    def show_info(self, title, message):
        """显示信息"""
        messagebox.showinfo(title, message)
    
    def show_warning(self, title, message):
        """显示警告信息"""
        messagebox.showwarning(title, message)