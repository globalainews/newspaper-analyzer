# Data management module
# 数据管理模块

import os
import json
import tkinter as tk
from tkinter import filedialog
class DataManager:
    def __init__(self, config, progress_label_widget=None, progress_bar_widget=None, root=None):
        pass
    
    def silent_load_json(self, image_filename):
        """静默加载JSON文件（不显示提示框）"""
        try:
            if not image_filename:
                return
            
            base_name = os.path.splitext(image_filename)[0]
            json_filename = f"{base_name}.json"
            json_file_path = os.path.join(self.analysis_dir, json_filename)
            
            if os.path.exists(json_file_path):
                self.current_image_file = os.path.join(self.download_dir, image_filename)
                self.load_json_file(json_file_path)
                # 显示报纸图片
                if hasattr(self, 'show_newspaper_image'):
                    self.show_newspaper_image()
        except Exception as e:
            print(f"静默加载JSON文件失败: {str(e)}")
    
    def load_json_files(self, image_filename=None):
        """加载分析目录中的JSON文件"""
        try:
            json_files = []
            if os.path.exists(self.analysis_dir):
                for file in os.listdir(self.analysis_dir):
                    if file.endswith('.json'):
                        json_files.append(file)
            
            if json_files:
                # 如果提供了图片文件名，尝试加载对应的JSON文件
                if image_filename:
                    base_name = os.path.splitext(image_filename)[0]
                    json_filename = f"{base_name}.json"
                    json_file_path = os.path.join(self.analysis_dir, json_filename)
                    
                    if os.path.exists(json_file_path):
                        self.current_image_file = os.path.join(self.download_dir, image_filename)
                        self.load_json_file(json_file_path)
                        # 显示报纸图片
                        if hasattr(self, 'show_newspaper_image'):
                            self.show_newspaper_image()
                        return
                
                # 否则显示文件选择对话框
                selected_file = filedialog.askopenfilename(
                    initialdir=self.analysis_dir,
                    title="选择JSON文件",
                    filetypes=[("JSON文件", "*.json"), ("所有文件", "*")]
                )
                
                if selected_file:
                    # 尝试找到对应的图片文件
                    base_name = os.path.splitext(os.path.basename(selected_file))[0]
                    image_filename = f"{base_name}.jpg"
                    image_filepath = os.path.join(self.download_dir, image_filename)
                    if os.path.exists(image_filepath):
                        self.current_image_file = image_filepath
                    self.load_json_file(selected_file)
                    # 显示报纸图片
                    if hasattr(self, 'show_newspaper_image'):
                        self.show_newspaper_image()
            else:
                self.show_info("提示", "没有找到JSON文件，请先分析图片")
        except Exception as e:
            self.show_error("错误", f"加载JSON文件失败: {str(e)}")
    
    def load_json_file(self, json_file):
        """加载指定的JSON文件"""
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 提取新闻块数据
            self.video_data = []
            if 'news_blocks' in data:
                for i, news in enumerate(data['news_blocks']):
                    self.video_data.append({
                        "id": i + 1,
                        "title": news.get('title', f"新闻{i+1}"),
                        "content": news.get('content', ""),
                        "position": news.get('position', [0, 0, 0, 0])
                    })
            
            # 更新新闻列表
            if hasattr(self, 'update_news_list'):
                self.update_news_list()
            
            self.update_progress("JSON文件加载成功", 100, "#27AE60")
            
        except Exception as e:
            self.update_progress(f"加载失败: {str(e)}", 0, "#E74C3C")
            self.show_error("错误", f"加载JSON文件失败:\n{str(e)}")
    
    def generate_video_data(self):
        """从分析结果中提取视频数据"""
        try:
            # 加载最新的JSON文件
            json_files = []
            if os.path.exists(self.analysis_dir):
                for file in os.listdir(self.analysis_dir):
                    if file.endswith('.json'):
                        file_path = os.path.join(self.analysis_dir, file)
                        json_files.append((file_path, os.path.getmtime(file_path)))
            
            if json_files:
                # 按修改时间排序，取最新的
                json_files.sort(key=lambda x: x[1], reverse=True)
                latest_file = json_files[0][0]
                
                with open(latest_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 提取新闻块数据
                self.video_data = []
                if 'news_blocks' in data:
                    for i, news in enumerate(data['news_blocks']):
                        self.video_data.append({
                            "id": i + 1,
                            "title": news.get('title', f"新闻{i+1}"),
                            "content": news.get('content', ""),
                            "position": news.get('position', [0, 0, 0, 0])
                        })
                
                # 更新新闻列表
                if hasattr(self, 'update_news_list'):
                    self.update_news_list()
                
                # 保存为视频数据JSON文件
                video_data_file = os.path.join(self.analysis_dir, "video_data.json")
                with open(video_data_file, 'w', encoding='utf-8') as f:
                    json.dump(self.video_data, f, ensure_ascii=False, indent=2)
                
                self.update_progress("视频数据生成成功", 100, "#27AE60")
                self.show_info("成功", f"视频数据生成成功!\n\n已保存到: {video_data_file}")
                
                return True
            else:
                self.update_progress("没有找到JSON文件", 0, "#E74C3C")
                self.show_info("提示", "没有找到JSON文件，请先分析图片")
                return False
                
        except Exception as e:
            self.update_progress(f"生成失败: {str(e)}", 0, "#E74C3C")
            self.show_error("错误", f"生成视频数据失败:\n{str(e)}")
            return False
    
    def save_video_data(self):
        """保存视频数据为JSON文件"""
        try:
            if not self.video_data:
                self.show_warning("警告", "没有视频数据可保存")
                return False
            
            # 查找原始JSON文件
            if self.current_image_file:
                base_name = os.path.splitext(os.path.basename(self.current_image_file))[0]
                json_file = os.path.join(self.analysis_dir, f"{base_name}.json")
                
                # 读取原始JSON文件
                if os.path.exists(json_file):
                    with open(json_file, 'r', encoding='utf-8') as f:
                        original_data = json.load(f)
                    
                    # 更新news_blocks
                    original_data['news_blocks'] = self.video_data
                    
                    # 保存回原始JSON文件
                    with open(json_file, 'w', encoding='utf-8') as f:
                        json.dump(original_data, f, ensure_ascii=False, indent=2)
                    
                    self.update_progress("数据保存成功", 100, "#27AE60")
                    self.show_info("成功", f"视频数据保存成功!\n\n已保存到: {json_file}")
                    return True
            
            # 如果没有找到原始文件，保存为video_data.json
            video_data_file = os.path.join(self.analysis_dir, "video_data.json")
            with open(video_data_file, 'w', encoding='utf-8') as f:
                json.dump(self.video_data, f, ensure_ascii=False, indent=2)
            
            self.update_progress("数据保存成功", 100, "#27AE60")
            self.show_info("成功", f"视频数据保存成功!\n\n已保存到: {video_data_file}")
            
            return True
            
        except Exception as e:
            self.update_progress(f"保存失败: {str(e)}", 0, "#E74C3C")
            self.show_error("错误", f"保存视频数据失败:\n{str(e)}")
            return False