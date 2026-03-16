import os
import cv2
import numpy as np
from PIL import Image
import json
from datetime import datetime
from layoutlm_analyzer import LayoutLMAnalyzer


class NewsImageExporter:
    """新闻图片导出器 - 使用LayoutLMv3进行文档布局分析并导出新闻区域图片"""
    
    def __init__(self, output_dir="exported_news_images"):
        self.output_dir = output_dir
        # 确保输出目录存在
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            print(f"创建输出目录: {output_dir}")
        else:
            print(f"输出目录已存在: {output_dir}")
        
        # 初始化LayoutLM分析器
        self.layoutlm_analyzer = LayoutLMAnalyzer()
    
    def _filter_overlapping_news(self, news_data):
        """
        过滤重叠的新闻区域，保留面积较大的区域
        
        Args:
            news_data: 新闻数据列表
            
        Returns:
            list: 过滤后的新闻数据列表
        """
        if not news_data:
            return []
        
        # 计算每个新闻区域的面积
        news_with_area = []
        for news in news_data:
            position = news.get('position', [0, 0, 0, 0])
            if len(position) == 4:
                x1, y1, x2, y2 = position
                area = (x2 - x1) * (y2 - y1)
                news_with_area.append((news, area))
        
        # 按面积降序排序
        news_with_area.sort(key=lambda x: x[1], reverse=True)
        
        # 过滤重叠区域
        filtered = []
        for news, area in news_with_area:
            position = news.get('position', [0, 0, 0, 0])
            x1, y1, x2, y2 = position
            
            # 检查是否与已保留的区域重叠
            overlap = False
            for existing_news in filtered:
                existing_pos = existing_news.get('position', [0, 0, 0, 0])
                ex_x1, ex_y1, ex_x2, ex_y2 = existing_pos
                
                # 检查是否重叠
                if not (x2 <= ex_x1 or x1 >= ex_x2 or y2 <= ex_y1 or y1 >= ex_y2):
                    # 计算重叠面积
                    overlap_x1 = max(x1, ex_x1)
                    overlap_y1 = max(y1, ex_y1)
                    overlap_x2 = min(x2, ex_x2)
                    overlap_y2 = min(y2, ex_y2)
                    overlap_area = (overlap_x2 - overlap_x1) * (overlap_y2 - overlap_y1)
                    
                    # 如果重叠面积超过当前区域的30%，则认为是重叠
                    if overlap_area > area * 0.3:
                        overlap = True
                        break
            
            if not overlap:
                filtered.append(news)
        
        # 按y坐标排序
        filtered.sort(key=lambda x: x.get('position', [0, 0, 0, 0])[1])
        
        return filtered
    
    def export_news_images(self, image_path, news_data=None, newspaper_name="报纸"):
        """
        根据新闻数据导出新闻区域图片
        
        Args:
            image_path: 报纸图片路径
            news_data: 新闻数据列表（可选，使用LayoutLM分析时可忽略）
            newspaper_name: 报纸名称
        
        Returns:
            tuple: (导出的图片路径列表, 导出目录路径)
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"图片不存在: {image_path}")
        
        # 加载原始图片
        image = Image.open(image_path)
        image_cv = cv2.imread(image_path)
        
        if image_cv is None:
            raise ValueError(f"无法读取图片: {image_path}")
        
        # 创建输出子目录
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        export_dir = os.path.join(self.output_dir, f"{base_name}_{timestamp}")
        os.makedirs(export_dir, exist_ok=True)
        print(f"创建导出目录: {export_dir}")
        
        exported_paths = []
        
        # 从新闻数据中提取文本和边界框
        words = []
        boxes = []
        if news_data:
            for news in news_data:
                # 提取标题作为文本
                title = news.get('title', '')
                if title:
                    words.append(title)
                    # 提取位置作为边界框
                    position = news.get('position', [0, 0, 0, 0])
                    if len(position) == 4:
                        boxes.append(position)
        
        # 使用LayoutLM分析布局
        print("使用LayoutLM分析新闻区域...")
        regions = self.layoutlm_analyzer.analyze_layout(image_path, words, boxes)
        print(f"LayoutLM检测到 {len(regions)} 个新闻区域")
        
        # 确定要导出的新闻数量
        if news_data and len(news_data) > 0:
            target_count = len(news_data)
            print(f"新闻列表中有 {target_count} 条新闻")
        else:
            target_count = len(regions)
            print(f"使用LayoutLM检测的区域数量: {target_count}")
        
        # 如果检测到的区域少于新闻数量，需要将区域分配给新闻
        if len(regions) < target_count:
            print(f"警告: 检测到的区域({len(regions)})少于新闻数量({target_count})")
            print("将尝试将检测到的区域分配给新闻...")
            
            # 方法：基于检测到的区域进行智能分割
            assigned_regions = []
            
            if regions:
                # 计算总高度
                total_height = sum(r[3] - r[1] for r in regions)
                
                # 为每个新闻分配区域
                for i in range(target_count):
                    if i < len(regions):
                        # 使用检测到的区域
                        assigned_regions.append(regions[i])
                    else:
                        # 从检测到的区域中分割
                        # 找到最大的区域
                        largest_region = max(regions, key=lambda r: r[3] - r[1])
                        x1, y1, x2, y2 = largest_region
                        height = y2 - y1
                        
                        # 计算分割点
                        split_point = y1 + height // 2
                        
                        # 分割成两个区域
                        new_region1 = (x1, y1, x2, split_point)
                        new_region2 = (x1, split_point, x2, y2)
                        
                        # 替换原区域
                        regions.remove(largest_region)
                        regions.extend([new_region1, new_region2])
                        regions.sort(key=lambda r: r[1])
                        
                        # 添加新区域
                        assigned_regions.append(new_region1)
                        
                        # 如果还有需要，继续分割
                        if i + 1 < target_count:
                            assigned_regions.append(new_region2)
                            i += 1
            else:
                # 如果没有检测到区域，使用基于文本密度的分割
                print("使用基于文本密度的分割...")
                segment_height = image.height // target_count
                
                for i in range(target_count):
                    y1 = i * segment_height
                    y2 = min((i + 1) * segment_height, image.height)
                    x1 = 10
                    x2 = image.width - 10
                    assigned_regions.append((x1, y1, x2, y2))
            
            regions = assigned_regions[:target_count]  # 确保数量正确
            print(f"分配后的区域数量: {len(regions)}")
        
        # 为每个新闻导出图片
        for i, region in enumerate(regions):
            try:
                x1, y1, x2, y2 = region
                
                # 确保坐标在图片范围内
                x1 = max(0, int(x1))
                y1 = max(0, int(y1))
                x2 = min(image.width, int(x2))
                y2 = min(image.height, int(y2))
                
                if x2 <= x1 or y2 <= y1:
                    print(f"跳过无效区域: 区域 {i+1}")
                    continue
                
                # 计算区域面积
                area = (x2 - x1) * (y2 - y1)
                print(f"区域 {i+1} - 原始区域: {x1},{y1}-{x2},{y2} (面积: {area})")
                
                # 扩展区域以包含更多内容
                # 水平方向保持不变，垂直方向向下扩展
                extended_y2 = y2 + 300  # 向下扩展300像素以包含更多内容
                extended_y2 = min(image.height, extended_y2)
                
                # 检查其他区域的位置，避免重叠
                for j, other_region in enumerate(regions):
                    if j == i:
                        continue
                    other_x1, other_y1, other_x2, other_y2 = other_region
                    
                    # 如果其他区域在当前区域的下方且有重叠
                    if other_y1 > y1 and other_y1 < extended_y2:
                        # 调整扩展区域
                        extended_y2 = other_y1 - 15  # 留出15像素边距
                        break
                
                # 确保扩展后的区域有足够的高度
                if extended_y2 - y1 < 150:
                    extended_y2 = min(y1 + 300, image.height)
                
                print(f"区域 {i+1} - 扩展区域: {x1},{y1}-{x2},{extended_y2} (高度: {extended_y2 - y1})")
                
                # 裁剪新闻区域
                news_image = image.crop((x1, y1, x2, extended_y2))
                
                # 生成文件名
                title = f'新闻区域{i+1}'
                if news_data and i < len(news_data):
                    title = news_data[i].get('title', title)
                
                # 清理文件名中的非法字符
                safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
                safe_title = safe_title[:30]  # 限制长度
                
                filename = f"{i+1:02d}_{safe_title}.jpg"
                output_path = os.path.join(export_dir, filename)
                
                # 保存图片
                news_image.save(output_path, 'JPEG', quality=95)
                exported_paths.append(output_path)
                
                print(f"导出成功: {filename} (尺寸: {news_image.size})")
                
            except Exception as e:
                print(f"导出区域 {i+1} 失败: {e}")
                continue
        
        # 保存导出信息
        info_path = os.path.join(export_dir, "export_info.json")
        export_info = {
            "newspaper_name": newspaper_name,
            "source_image": image_path,
            "export_time": timestamp,
            "total_regions": len(regions),
            "exported_count": len(exported_paths),
            "regions": regions,
            "news_list": [
                {
                    "index": i+1,
                    "title": f'新闻区域{i+1}' if not news_data or i >= len(news_data) else news_data[i].get('title', f'新闻区域{i+1}'),
                    "position": regions[i],
                    "filename": os.path.basename(path)
                }
                for i, path in enumerate(exported_paths)
            ]
        }
        
        with open(info_path, 'w', encoding='utf-8') as f:
            json.dump(export_info, f, ensure_ascii=False, indent=2)
        
        return exported_paths, export_dir
    
    def export_with_layoutlm(self, image_path, newspaper_name="报纸"):
        """
        使用LayoutLMv3模型进行布局分析并导出新闻区域
        
        Args:
            image_path: 报纸图片路径
            newspaper_name: 报纸名称
        
        Returns:
            list: 导出的图片路径列表
        """
        try:
            from transformers import AutoModel, AutoTokenizer
            from layoutlmv3.layoutlmv3.layoutlmft.data.image_utils import load_image
            
            # 加载LayoutLMv3模型
            model_name = "microsoft/layoutlmv3-base-chinese"
            print(f"正在加载LayoutLMv3模型: {model_name}")
            
            # 这里我们使用简化版本，直接使用OCR和位置信息
            # 实际使用时可以集成更复杂的布局分析
            
            # 加载图片
            image = Image.open(image_path)
            
            # 使用简单的图像处理来检测文本区域
            # 实际项目中可以使用LayoutLMv3进行更精确的布局分析
            news_regions = self._detect_news_regions(image)
            
            # 创建新闻数据
            news_data = []
            for i, region in enumerate(news_regions):
                news_data.append({
                    'title': f'新闻区域{i+1}',
                    'content': '',
                    'position': region
                })
            
            # 导出图片
            return self.export_news_images(image_path, news_data, newspaper_name)
            
        except Exception as e:
            print(f"LayoutLMv3分析失败: {e}")
            print("使用备用方法导出...")
            # 如果LayoutLMv3失败，使用备用方法
            return self._export_with_fallback(image_path, newspaper_name)
    
    def _detect_news_regions(self, image):
        """
        使用图像处理检测新闻区域
        
        Args:
            image: PIL Image对象
        
        Returns:
            list: 新闻区域坐标列表 [(x1, y1, x2, y2), ...]
        """
        # 转换为OpenCV格式
        image_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(image_cv, cv2.COLOR_BGR2GRAY)
        
        # 二值化
        _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
        
        # 形态学操作
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        dilated = cv2.dilate(binary, kernel, iterations=2)
        
        # 查找轮廓
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # 筛选新闻区域
        regions = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            
            # 筛选条件：区域大小适中
            if w > 100 and h > 100 and w < image.width * 0.9 and h < image.height * 0.5:
                regions.append([x, y, x + w, y + h])
        
        # 按y坐标排序
        regions.sort(key=lambda r: r[1])
        
        return regions
    
    def _export_with_fallback(self, image_path, newspaper_name="报纸"):
        """
        备用导出方法 - 当LayoutLMv3失败时使用
        
        Args:
            image_path: 报纸图片路径
            newspaper_name: 报纸名称
        
        Returns:
            list: 导出的图片路径列表
        """
        # 加载图片
        image = Image.open(image_path)
        
        # 检测新闻区域
        news_regions = self._detect_news_regions(image)
        
        # 创建新闻数据
        news_data = []
        for i, region in enumerate(news_regions):
            news_data.append({
                'title': f'新闻区域{i+1}',
                'content': '',
                'position': region
            })
        
        # 导出图片
        return self.export_news_images(image_path, news_data, newspaper_name)


# 测试代码
if __name__ == "__main__":
    # 创建导出器
    exporter = NewsImageExporter()
    
    # 测试数据
    test_news_data = [
        {
            'title': '测试新闻1',
            'content': '这是测试内容1',
            'position': [50, 50, 300, 200]
        },
        {
            'title': '测试新闻2',
            'content': '这是测试内容2',
            'position': [50, 250, 300, 400]
        }
    ]
    
    print("新闻图片导出模块已加载")
    print("使用方法:")
    print("  exporter = NewsImageExporter()")
    print("  exporter.export_news_images(image_path, news_data)")
