# Jianying draft management module
# 剪映草稿管理模块

import os
import json
import shutil
import datetime
import tkinter as tk
from tkinter import messagebox
class JianyingDraftManager:
    def __init__(self, config, progress_label_widget=None, progress_bar_widget=None, root=None):
        pass
    
    def generate_jianying_draft(self):
        """生成剪映草稿目录"""
        try:
            if not self.current_image_file:
                self.show_warning("警告", "请先选择一张报纸图片")
                return
            
            # 检查是否有新闻数据
            if not self.video_data:
                self.show_warning("警告", "没有新闻数据，请先生成或加载视频数据")
                return
            
            # 获取图片名称（不含扩展名）
            image_filename = os.path.basename(self.current_image_file)
            base_name = os.path.splitext(image_filename)[0]
            
            # 获取当前日期
            today = datetime.datetime.now()
            date_str = today.strftime("%Y%m%d")
            
            # 生成草稿目录名称（图片名+日期）
            draft_name = f"{base_name}_{date_str}"
            
            # 生成草稿目录路径
            draft_dir = os.path.join(self.jianying_drafts_dir, draft_name)
            
            # 检查目录是否已存在
            directory_existed = os.path.exists(draft_dir)
            
            # 如果目录不存在，创建并复制sample文件
            if not directory_existed:
                os.makedirs(draft_dir)
                print(f"创建剪映草稿目录: {draft_dir}")
                
                # 根据报纸类型选择不同的样本目录
                # 金融时报使用sample，华尔街日报使用wsjsample
                if "ft" in base_name.lower():
                    sample_dir_name = "sample"  # 金融时报
                elif "wsj" in base_name.lower():
                    sample_dir_name = "wsjsample"  # 华尔街日报
                else:
                    sample_dir_name = "sample"  # 默认使用sample
                
                sample_dir = os.path.join(self.jianying_drafts_dir, sample_dir_name)
                print(f"使用样本目录: {sample_dir_name}")
                if os.path.exists(sample_dir):
                    # 复制sample目录内的所有文件
                    import shutil
                    for item in os.listdir(sample_dir):
                        source = os.path.join(sample_dir, item)
                        destination = os.path.join(draft_dir, item)
                        if os.path.isfile(source):
                            shutil.copy2(source, destination)
                            print(f"复制文件: {item}")
                        elif os.path.isdir(source):
                            if os.path.exists(destination):
                                shutil.rmtree(destination)
                            shutil.copytree(source, destination)
                            print(f"复制目录: {item}")
                else:
                    print(f"警告: {sample_dir_name}目录不存在: {sample_dir}")
                    self.show_warning("警告", f"{sample_dir_name}目录不存在: {sample_dir}")
            else:
                print(f"目录已存在，跳过复制: {draft_dir}")
            
            # 替换draft_content.json中的文本内容
            draft_content_file = os.path.join(draft_dir, "draft_content.json")
            if os.path.exists(draft_content_file):
                try:
                    with open(draft_content_file, 'r', encoding='utf-8') as f:
                        draft_content = json.load(f)
                    
                    # 输出JSON的顶层键，帮助调试
                    print(f"JSON顶层键: {list(draft_content.keys())}")
                    
                    # 检查是否有texts字段（可能在不同的层级）
                    texts_found = False
                    texts_list = []
                    
                    # 尝试在materials中查找texts
                    if 'materials' in draft_content and isinstance(draft_content.get('materials'), dict):
                        materials = draft_content['materials']
                        if 'texts' in materials and isinstance(materials.get('texts'), list):
                            texts_found = True
                            texts_list = materials['texts']
                            print(f"在materials.texts中找到texts数组，长度: {len(texts_list)}")
                    
                    # 尝试在顶层查找texts
                    if not texts_found and 'texts' in draft_content and isinstance(draft_content['texts'], list):
                        texts_found = True
                        texts_list = draft_content['texts']
                        print(f"在顶层找到texts数组，长度: {len(texts_list)}")
                    
                    if texts_found:
                        # 根据新闻数据替换文本
                        for i, text_item in enumerate(texts_list):
                            if i < len(self.video_data):
                                news = self.video_data[i]
                                # 只使用新闻内容，不添加标题
                                new_text = news.get('content', '')
                                # 清理特殊字符：移除换行符，替换可能导致JSON问题的字符
                                new_text = new_text.replace('\n', ' ').replace('\r', ' ').replace('\\', '\\\\')
                                
                                # content字段是一个JSON字符串，需要解析后修改text字段
                                content_str = text_item.get('content', '')
                                if content_str:
                                    try:
                                        # 解析content中的JSON
                                        content_obj = json.loads(content_str)
                                        # 输出替换前的text
                                        old_text = content_obj.get('text', '')
                                        print(f"替换前第{i+1}条文本: {old_text[:50]}...")
                                        # 替换text字段
                                        content_obj['text'] = new_text
                                        # 重新序列化为字符串
                                        text_item['content'] = json.dumps(content_obj, ensure_ascii=False)
                                        print(f"替换后第{i+1}条文本: {new_text[:50]}...")
                                    except json.JSONDecodeError:
                                        # 如果解析失败，直接替换整个content
                                        print(f"替换前第{i+1}条content: {content_str[:50]}...")
                                        text_item['content'] = new_text
                                        print(f"替换后第{i+1}条content: {new_text[:50]}...")
                                else:
                                    text_item['content'] = new_text
                                    print(f"第{i+1}条content为空，设置为: {new_text[:50]}...")
                        
                        # 补充：替换id为7453700C-DD8B-44d8-91DA-05690591DCA9的TEXT内容为当前日期和星期
                        for text_item in texts_list:
                            text_id = text_item.get('id')
                            if text_id == '7453700C-DD8B-44d8-91DA-05690591DCA9':
                                # 获取当前日期和星期
                                today = datetime.datetime.now()
                                # 格式：2026年3月16日周一
                                date_str = today.strftime('%Y年%m月%d日')
                                # 获取星期几（1-7，1=周一）
                                weekday = today.weekday() + 1
                                weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
                                weekday_str = weekdays[weekday % 7]
                                date_week_str = f"{date_str}{weekday_str}"
                                
                                # 替换content中的text
                                content_str = text_item.get('content', '')
                                if content_str:
                                    try:
                                        content_obj = json.loads(content_str)
                                        old_text = content_obj.get('text', '')
                                        print(f"替换前日期文本: {old_text}")
                                        content_obj['text'] = date_week_str
                                        text_item['content'] = json.dumps(content_obj, ensure_ascii=False)
                                        print(f"替换后日期文本: {date_week_str}")
                                    except json.JSONDecodeError:
                                        # 如果解析失败，直接替换整个content
                                        print(f"替换前日期content: {content_str[:50]}...")
                                        text_item['content'] = date_week_str
                                        print(f"替换后日期content: {date_week_str}")
                                else:
                                    text_item['content'] = date_week_str
                                    print(f"日期content为空，设置为: {date_week_str}")
                                break
                        
                        # 保存修改后的JSON文件
                        with open(draft_content_file, 'w', encoding='utf-8') as f:
                            json.dump(draft_content, f, ensure_ascii=False, indent=2)
                        
                        print(f"文本内容替换完成")
                        
                        if directory_existed:
                            self.show_info("成功", f"剪映草稿文本已更新!\n\n目录: {draft_dir}")
                        else:
                            self.show_info("成功", f"剪映草稿目录生成完成!\n\n目录: {draft_dir}")
                    else:
                        print(f"警告: draft_content.json中没有找到texts字段")
                        print(f"JSON结构: {str(draft_content)[:500]}...")  # 输出部分JSON结构帮助调试
                        self.show_warning("警告", f"draft_content.json中没有找到texts字段")
                except Exception as e:
                    print(f"替换文本内容失败: {str(e)}")
                    self.show_warning("警告", f"替换文本内容失败: {str(e)}")
            else:
                print(f"警告: draft_content.json文件不存在: {draft_content_file}")
                self.show_warning("警告", f"draft_content.json文件不存在")
                
        except Exception as e:
            print(f"生成剪映草稿目录失败: {str(e)}")
            self.show_error("错误", f"生成剪映草稿目录失败: {str(e)}")