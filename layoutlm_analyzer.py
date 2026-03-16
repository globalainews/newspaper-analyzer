import cv2
import numpy as np
from PIL import Image
import os
import json
import requests

class LayoutLMAnalyzer:
    """LayoutLMv3 文档布局分析器 - 通过本地服务调用"""
    
    def __init__(self, service_url="http://127.0.0.1:5000"):
        self.service_url = service_url
        self.check_service()
    
    def check_service(self):
        """检查服务是否可用"""
        try:
            response = requests.get(f"{self.service_url}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get("model_loaded"):
                    print(f"✅ LayoutLMv3-large 服务连接成功: {self.service_url}")
                    print(f"   模型状态: 已加载")
                    return True
                else:
                    print(f"⚠️ 服务已连接但模型未加载")
                    return False
            else:
                print(f"⚠️ 服务响应异常: {response.status_code}")
                return False
        except Exception as e:
            print(f"⚠️ 无法连接到 LayoutLMv3-large 服务: {e}")
            print(f"   请确保服务已启动: python layoutlmv3_service.py")
            return False
    
    def analyze_layout(self, image_path, words=None, boxes=None):
        """
        使用 LayoutLMv3 分析文档布局
        
        Args:
            image_path: 图片路径
            words: 文本列表
            boxes: 边界框列表
            
        Returns:
            list: 新闻区域坐标列表
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"图片不存在: {image_path}")
        
        # 尝试通过服务分析
        try:
            return self._analyze_with_service(image_path, words, boxes)
        except Exception as e:
            print(f"服务调用失败: {e}")
            print("使用本地备用方法")
            return self._analyze_with_cv(image_path)
    
    def _analyze_with_service(self, image_path, words=None, boxes=None):
        """
        通过 HTTP 服务进行布局分析
        
        Args:
            image_path: 图片路径
            words: 文本列表
            boxes: 边界框列表
            
        Returns:
            list: 新闻区域坐标列表
        """
        try:
            # 构建请求数据
            data = {"image_path": image_path}
            if words:
                data["words"] = words
            if boxes:
                data["boxes"] = boxes
            
            # 调用本地服务
            response = requests.post(
                f"{self.service_url}/analyze",
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("success"):
                    regions = result.get("regions", [])
                    print(f"LayoutLM 服务分析完成，检测到 {len(regions)} 个新闻区域")
                    
                    # 转换为坐标列表格式 [x1, y1, x2, y2]
                    coordinates = [region["coordinates"] for region in regions]
                    return coordinates
                else:
                    error = result.get("error", "未知错误")
                    raise Exception(f"服务返回错误: {error}")
            else:
                raise Exception(f"服务响应异常: {response.status_code}")
                
        except Exception as e:
            raise Exception(f"服务调用失败: {e}")
    
    def _analyze_with_cv(self, image):
        """
        使用 OpenCV 进行布局分析（备用方法）
        
        Args:
            image: PIL Image 对象或图片路径
            
        Returns:
            list: 新闻区域坐标列表
        """
        # 如果传入的是路径，加载图片
        if isinstance(image, str):
            image = Image.open(image)
        
        # 转换为 OpenCV 格式
        image_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(image_cv, cv2.COLOR_BGR2GRAY)
        
        # 二值化
        _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
        
        # 形态学操作
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (10, 10))
        dilated = cv2.dilate(binary, kernel, iterations=3)
        
        # 查找轮廓
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # 筛选新闻区域
        regions = []
        image_width, image_height = image.size
        
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            
            # 筛选条件
            if (w > 150 and h > 100 and 
                w < image_width * 0.9 and 
                h < image_height * 0.4 and
                x > 20 and y > 20 and
                x + w < image_width - 20 and
                y + h < image_height - 20):
                
                regions.append([x, y, x + w, y + h])
        
        # 按 y 坐标排序
        regions.sort(key=lambda r: r[1])
        
        # 合并重叠区域
        regions = self._merge_overlapping_regions(regions)
        
        print(f"OpenCV 分析完成，检测到 {len(regions)} 个新闻区域")
        return regions
    
    def _merge_overlapping_regions(self, regions):
        """
        合并重叠的区域
        
        Args:
            regions: 区域列表
            
        Returns:
            list: 合并后的区域列表
        """
        if not regions:
            return []
        
        # 按 y 坐标排序
        regions.sort(key=lambda r: r[1])
        
        merged = [regions[0]]
        
        for current in regions[1:]:
            last = merged[-1]
            
            # 检查是否重叠
            if not (current[0] > last[2] or current[2] < last[0] or 
                    current[1] > last[3] or current[3] < last[1]):
                # 合并区域
                new_region = [
                    min(last[0], current[0]),
                    min(last[1], current[1]),
                    max(last[2], current[2]),
                    max(last[3], current[3])
                ]
                merged[-1] = new_region
            else:
                merged.append(current)
        
        return merged
    
    def export_news_regions(self, image_path, output_dir="layoutlm_results"):
        """
        导出新闻区域
        
        Args:
            image_path: 图片路径
            output_dir: 输出目录
            
        Returns:
            list: 导出的图片路径列表
        """
        os.makedirs(output_dir, exist_ok=True)
        
        # 分析布局
        regions = self.analyze_layout(image_path)
        
        # 加载图片
        image = Image.open(image_path)
        
        # 导出区域
        exported_paths = []
        for i, region in enumerate(regions):
            try:
                x1, y1, x2, y2 = region
                
                # 裁剪区域
                news_image = image.crop((x1, y1, x2, y2))
                
                # 生成文件名
                filename = f"region_{i+1:02d}.jpg"
                output_path = os.path.join(output_dir, filename)
                
                # 保存图片
                news_image.save(output_path, 'JPEG', quality=95)
                exported_paths.append(output_path)
                
                print(f"导出区域 {i+1}: {region}")
                
            except Exception as e:
                print(f"导出区域 {i+1} 失败: {e}")
                continue
        
        # 保存区域信息
        info_path = os.path.join(output_dir, "regions_info.json")
        with open(info_path, 'w', encoding='utf-8') as f:
            json.dump({
                "image_path": image_path,
                "regions": regions,
                "exported_count": len(exported_paths)
            }, f, ensure_ascii=False, indent=2)
        
        return exported_paths


# 测试代码
if __name__ == "__main__":
    analyzer = LayoutLMAnalyzer()
    
    # 测试图片路径
    test_image = "test_newspaper.png"
    
    if os.path.exists(test_image):
        print(f"分析图片: {test_image}")
        regions = analyzer.analyze_layout(test_image)
        print(f"检测到 {len(regions)} 个新闻区域")
        for i, region in enumerate(regions):
            print(f"区域 {i+1}: {region}")
        
        # 导出区域
        exported = analyzer.export_news_regions(test_image)
        print(f"导出了 {len(exported)} 个区域图片")
    else:
        print(f"测试图片不存在: {test_image}")
