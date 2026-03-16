#!/usr/bin/env python3
"""
布局分析服务
使用Gemini识别结果进行布局分析
"""

import os
import cv2
import numpy as np
from PIL import Image
from flask import Flask, request, jsonify

app = Flask(__name__)

print("✅ 布局分析服务启动成功")
print("============================================================")
print("布局分析服务")
print("============================================================")
print("服务模式: 本地离线模式（使用Gemini识别结果）")
print("============================================================")
print("")
print("服务接口:")
print("  GET  /health      - 健康检查")
print("  GET  /model_info  - 模型信息")
print("  POST /analyze     - 分析文档布局")
print("")

def normalize_coordinates(bbox, image_width, image_height):
    """
    归一化坐标到 [0, 1000] 范围
    
    Args:
        bbox: 边界框坐标 [x1, y1, x2, y2]
        image_width: 图像宽度
        image_height: 图像高度
        
    Returns:
        归一化后的边界框坐标
    """
    x1, y1, x2, y2 = bbox
    
    # 确保坐标在图像范围内
    x1 = max(0, min(x1, image_width))
    y1 = max(0, min(y1, image_height))
    x2 = max(0, min(x2, image_width))
    y2 = max(0, min(y2, image_height))
    
    # 归一化到 [0, 1000] 范围
    norm_x1 = int((x1 / image_width) * 1000)
    norm_y1 = int((y1 / image_height) * 1000)
    norm_x2 = int((x2 / image_width) * 1000)
    norm_y2 = int((y2 / image_height) * 1000)
    
    return [norm_x1, norm_y1, norm_x2, norm_y2]

def denormalize_coordinates(norm_bbox, image_width, image_height):
    """
    将归一化坐标转换回原始图像坐标
    
    Args:
        norm_bbox: 归一化边界框坐标 [x1, y1, x2, y2]
        image_width: 图像宽度
        image_height: 图像高度
        
    Returns:
        原始图像坐标
    """
    norm_x1, norm_y1, norm_x2, norm_y2 = norm_bbox
    
    # 转换回原始坐标
    x1 = int((norm_x1 / 1000) * image_width)
    y1 = int((norm_y1 / 1000) * image_height)
    x2 = int((norm_x2 / 1000) * image_width)
    y2 = int((norm_y2 / 1000) * image_height)
    
    # 确保坐标在图像范围内
    x1 = max(0, min(x1, image_width))
    y1 = max(0, min(y1, image_height))
    x2 = max(0, min(x2, image_width))
    y2 = max(0, min(y2, image_height))
    
    return [x1, y1, x2, y2]

def calculate_iou(box1, box2):
    """
    计算两个边界框的 IOU（交并比）
    
    Args:
        box1: 第一个边界框 [x1, y1, x2, y2]
        box2: 第二个边界框 [x1, y1, x2, y2]
        
    Returns:
        IOU 值
    """
    # 计算交集
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])
    
    # 计算交集面积
    intersection = max(0, x2 - x1) * max(0, y2 - y1)
    
    # 计算两个边界框的面积
    area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
    area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
    
    # 计算并集面积
    union = area1 + area2 - intersection
    
    # 计算 IOU
    if union == 0:
        return 0
    
    return intersection / union

def nms(boxes, scores, iou_threshold=0.4):
    """
    非极大值抑制
    
    Args:
        boxes: 边界框列表
        scores: 边界框得分列表
        iou_threshold: IOU 阈值
        
    Returns:
        保留的边界框索引
    """
    if len(boxes) == 0:
        return []
    
    # 按得分排序
    sorted_indices = np.argsort(scores)[::-1]
    keep = []
    
    while len(sorted_indices) > 0:
        # 保留得分最高的边界框
        current = sorted_indices[0]
        keep.append(current)
        
        # 计算与其他边界框的 IOU
        ious = [calculate_iou(boxes[current], boxes[i]) for i in sorted_indices[1:]]
        
        # 保留 IOU 小于阈值的边界框
        filtered_indices = np.where(np.array(ious) < iou_threshold)[0]
        sorted_indices = sorted_indices[filtered_indices + 1]
    
    return keep

def clahe_enhancement(image):
    """
    应用 CLAHE 自适应对比度增强
    
    Args:
        image: 输入图像
        
    Returns:
        增强后的图像
    """
    # 转换为灰度图像
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image
    
    # 应用 CLAHE
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    
    # 转换回彩色图像（如果输入是彩色的）
    if len(image.shape) == 3:
        enhanced = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)
    
    return enhanced

def merge_title_boxes(boxes, labels):
    """
    合并相邻的标题框
    
    Args:
        boxes: 边界框列表
        labels: 标签列表
        
    Returns:
        合并后的边界框和标签
    """
    if len(boxes) == 0:
        return boxes, labels
    
    # 按 y 坐标排序
    sorted_indices = np.argsort([box[1] for box in boxes])
    sorted_boxes = [boxes[i] for i in sorted_indices]
    sorted_labels = [labels[i] for i in sorted_indices]
    
    merged_boxes = []
    merged_labels = []
    
    current_box = sorted_boxes[0]
    current_label = sorted_labels[0]
    
    for i in range(1, len(sorted_boxes)):
        box = sorted_boxes[i]
        label = sorted_labels[i]
        
        # 检查是否是标题且在垂直方向上高度重合度超过 80%
        if label == "TITLE" and current_label == "TITLE":
            # 计算高度重合度
            y_overlap = max(0, min(current_box[3], box[3]) - max(current_box[1], box[1]))
            min_height = min(current_box[3] - current_box[1], box[3] - box[1])
            overlap_ratio = y_overlap / min_height if min_height > 0 else 0
            
            if overlap_ratio > 0.8:
                # 合并边界框
                current_box = [
                    min(current_box[0], box[0]),
                    min(current_box[1], box[1]),
                    max(current_box[2], box[2]),
                    max(current_box[3], box[3])
                ]
                continue
        
        # 不是相邻标题或重合度不足，保存当前边界框并开始新的
        merged_boxes.append(current_box)
        merged_labels.append(current_label)
        current_box = box
        current_label = label
    
    # 保存最后一个边界框
    merged_boxes.append(current_box)
    merged_labels.append(current_label)
    
    return merged_boxes, merged_labels

def generate_debug_image(image, model_boxes, ocr_boxes, final_boxes):
    """
    生成调试图像
    
    Args:
        image: 输入图像
        model_boxes: 模型预测框
        ocr_boxes: OCR 文字框
        final_boxes: 最终合并框
        
    Returns:
        调试图像
    """
    # 复制图像
    debug_image = image.copy()
    
    # 绘制模型预测框（红色）
    for box in model_boxes:
        x1, y1, x2, y2 = box
        cv2.rectangle(debug_image, (x1, y1), (x2, y2), (0, 0, 255), 2)
    
    # 绘制 OCR 文字框（绿色）
    for box in ocr_boxes:
        x1, y1, x2, y2 = box
        cv2.rectangle(debug_image, (x1, y1), (x2, y2), (0, 255, 0), 1)
    
    # 绘制最终合并框（蓝色）
    for box in final_boxes:
        x1, y1, x2, y2 = box
        cv2.rectangle(debug_image, (x1, y1), (x2, y2), (255, 0, 0), 2)
    
    return debug_image

def analyze_document_layout(image_path, words=None, boxes=None):
    """
    分析文档布局，检测新闻块
    使用Gemini识别结果进行布局分析
    """
    try:
        # 加载图像
        image = Image.open(image_path)
        image_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(image_cv, cv2.COLOR_BGR2GRAY)
        
        # 应用 CLAHE 增强
        enhanced_image = clahe_enhancement(image_cv)
        
        image_width, image_height = image.size
        
        print(f"图像尺寸: {image_width}x{image_height}")
        
        # 使用Gemini识别结果进行布局分析
        print("=== 使用Gemini识别结果进行布局分析 ===")
        
        model_regions = []
        
        if words and boxes:
            print(f"使用Gemini识别结果: {len(words)} 个单词")
            
            # 处理每个识别结果
            for i, (word, box) in enumerate(zip(words, boxes)):
                if len(box) == 4:
                    x1, y1, x2, y2 = box
                    
                    # 确保坐标在图像范围内
                    x1 = max(0, min(x1, image_width))
                    y1 = max(0, min(y1, image_height))
                    x2 = max(0, min(x2, image_width))
                    y2 = max(0, min(y2, image_height))
                    
                    width = x2 - x1
                    height = y2 - y1
                    
                    # 只添加面积大于100的区域
                    if width * height > 100:
                        # 根据单词长度和位置判断是否为标题
                        label = "TITLE" if len(word) > 10 else "TEXT"
                        
                        model_regions.append({
                            "x": x1,
                            "y": y1,
                            "width": width,
                            "height": height,
                            "coordinates": [x1, y1, x2, y2],
                            "label": label
                        })
        else:
            print("没有提供Gemini识别结果，使用备用方法")
            # 备用方法：使用文本行检测
            blurred = cv2.GaussianBlur(gray, (3, 3), 0)
            _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            horizontal_proj = np.sum(binary, axis=1)
            max_proj = np.max(horizontal_proj)
            threshold = max_proj * 0.05
            in_text = False
            start_y = 0
            
            for y, proj in enumerate(horizontal_proj):
                if proj > threshold:
                    if not in_text:
                        in_text = True
                        start_y = y
                else:
                    if in_text:
                        in_text = False
                        end_y = y
                        if end_y - start_y > 5:
                            x1, y1, x2, y2 = 10, start_y, image_width-10, end_y
                            model_regions.append({
                                "x": x1,
                                "y": y1,
                                "width": x2 - x1,
                                "height": y2 - y1,
                                "coordinates": [x1, y1, x2, y2],
                                "label": "TEXT"
                            })
        
        print(f"识别到 {len(model_regions)} 个区域")
        
        # 合并相邻的标题框
        print("=== 合并相邻的标题框 ===")
        title_boxes = []
        title_labels = []
        text_boxes = []
        text_labels = []
        
        for region in model_regions:
            if region["label"] == "TITLE":
                title_boxes.append(region["coordinates"])
                title_labels.append(region["label"])
            else:
                text_boxes.append(region["coordinates"])
                text_labels.append(region["label"])
        
        # 合并标题框
        if title_boxes:
            merged_title_boxes, merged_title_labels = merge_title_boxes(title_boxes, title_labels)
            # 转换回区域格式
            merged_regions = []
            for box, label in zip(merged_title_boxes, merged_title_labels):
                x1, y1, x2, y2 = box
                merged_regions.append({
                    "x": x1,
                    "y": y1,
                    "width": x2 - x1,
                    "height": y2 - y1,
                    "coordinates": [x1, y1, x2, y2],
                    "label": label
                })
            # 添加文本区域
            for box, label in zip(text_boxes, text_labels):
                x1, y1, x2, y2 = box
                merged_regions.append({
                    "x": x1,
                    "y": y1,
                    "width": x2 - x1,
                    "height": y2 - y1,
                    "coordinates": [x1, y1, x2, y2],
                    "label": label
                })
        else:
            merged_regions = model_regions
        
        print(f"合并后区域数量: {len(merged_regions)}")
        
        # 应用 NMS
        if merged_regions:
            print("=== 应用 NMS ===")
            # 提取边界框和得分
            boxes = [region["coordinates"] for region in merged_regions]
            # 使用区域面积作为得分
            scores = [region["width"] * region["height"] for region in merged_regions]
            
            # 应用 NMS
            keep_indices = nms(boxes, scores, iou_threshold=0.4)
            merged_regions = [merged_regions[i] for i in keep_indices]
            print(f"NMS 后区域数量: {len(merged_regions)}")
        
        # 确保至少有6个区域
        while len(merged_regions) < 6:
            # 找到最大的区域
            if not merged_regions:
                # 如果没有区域，创建一个默认区域
                merged_regions.append({
                    "x": 0,
                    "y": 0,
                    "width": image_width,
                    "height": image_height // 6,
                    "coordinates": [0, 0, image_width, image_height // 6],
                    "label": "TEXT"
                })
            else:
                max_region = max(merged_regions, key=lambda r: r["width"] * r["height"])
                
                # 计算拆分点
                mid = (max_region["y"] + max_region["coordinates"][3]) // 2
                
                # 拆分区域
                x = max_region["x"]
                w = max_region["width"]
                y = max_region["y"]
                h = max_region["height"]
                
                # 上半部分
                top_region = {
                    "x": x,
                    "y": y,
                    "width": w,
                    "height": mid - y,
                    "coordinates": [x, y, x+w, mid],
                    "label": "TEXT"
                }
                
                # 下半部分
                bottom_region = {
                    "x": x,
                    "y": mid,
                    "width": w,
                    "height": y + h - mid,
                    "coordinates": [x, mid, x+w, y+h],
                    "label": "TEXT"
                }
                
                # 替换最大区域为两个新区域
                merged_regions.remove(max_region)
                merged_regions.append(top_region)
                merged_regions.append(bottom_region)
        
        # 确保最多有6个区域
        if len(merged_regions) > 6:
            # 按面积排序
            merged_regions.sort(key=lambda r: r["width"] * r["height"], reverse=True)
            # 取前6个
            merged_regions = merged_regions[:6]
        
        # 按y坐标排序
        merged_regions.sort(key=lambda r: r["y"])
        
        # 生成调试图像
        print("=== 生成调试图像 ===")
        # 提取模型预测框
        model_boxes = [region["coordinates"] for region in model_regions]
        # 提取最终框
        final_boxes = [region["coordinates"] for region in merged_regions]
        # OCR文字框（使用文本行检测）
        text_lines = []
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        horizontal_proj = np.sum(binary, axis=1)
        max_proj = np.max(horizontal_proj)
        threshold = max_proj * 0.05
        in_text = False
        start_y = 0
        for y, proj in enumerate(horizontal_proj):
            if proj > threshold:
                if not in_text:
                    in_text = True
                    start_y = y
            else:
                if in_text:
                    in_text = False
                    end_y = y
                    if end_y - start_y > 5:
                        text_lines.append([10, start_y, image_width-10, end_y])
        
        # 生成调试图像
        debug_image = generate_debug_image(image_cv, model_boxes, text_lines, final_boxes)
        debug_path = os.path.join(os.path.dirname(image_path), "debug_result.jpg")
        cv2.imwrite(debug_path, debug_image)
        print(f"调试图像已保存到: {debug_path}")
        
        print(f"最终检测到 {len(merged_regions)} 个新闻区域")
        for i, region in enumerate(merged_regions):
            x1, y1, x2, y2 = region["coordinates"]
            print(f" 区域 {i+1}: x={x1}, y={y1}, 宽={x2-x1}, 高={y2-y1}, 标签={region.get('label', '未知')}")
        
        # 转换为客户端期望的格式
        result_regions = []
        for region in merged_regions:
            result_regions.append({
                "x": region["x"],
                "y": region["y"],
                "width": region["width"],
                "height": region["height"],
                "coordinates": region["coordinates"],
                "label": region.get("label", "TEXT")
            })
        
        return {
            "success": True,
            "image_size": {"width": image_width, "height": image_height},
            "regions": result_regions,
            "regions_count": len(result_regions)
        }
        
    except Exception as e:
        print(f"分析失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e)
        }

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok", "model": "Gemini-based layout analysis"})

@app.route('/model_info', methods=['GET'])
def model_info():
    return jsonify({
        "model": "Gemini-based layout analysis",
        "status": "loaded",
        "mode": "offline"
    })

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.json
        image_path = data.get('image_path')
        words = data.get('words', [])
        boxes = data.get('boxes', [])
        
        if not image_path:
            return jsonify({"success": False, "error": "缺少image_path参数"}), 400
        
        if not os.path.exists(image_path):
            return jsonify({"success": False, "error": f"图像文件不存在: {image_path}"}), 404
        
        # 分析文档布局
        result = analyze_document_layout(image_path, words, boxes)
        
        return jsonify(result)
        
    except Exception as e:
        print(f"API 错误: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)