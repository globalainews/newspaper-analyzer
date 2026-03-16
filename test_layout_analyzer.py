#!/usr/bin/env python3
"""
独立测试布局分析功能
"""

import cv2
import numpy as np
from PIL import Image


def analyze_layout(image_path):
    """分析文档布局"""
    try:
        # 加载图像
        image = Image.open(image_path)
        image_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(image_cv, cv2.COLOR_BGR2GRAY)
        
        image_width, image_height = image.size
        
        print(f"图像尺寸: {image_width}x{image_height}")
        
        # 方法1: 文本行检测
        print("=== 文本行检测 ===")
        # 使用高斯模糊
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        
        # 使用Otsu阈值二值化
        _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # 形态学操作
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        dilated = cv2.dilate(binary, kernel, iterations=1)
        
        # 水平投影
        horizontal_proj = np.sum(dilated, axis=1)
        
        # 检测文本行
        text_lines = []
        in_text = False
        start_y = 0
        
        # 计算阈值
        max_proj = np.max(horizontal_proj)
        mean_proj = np.mean(horizontal_proj)
        threshold = max_proj * 0.05  # 使用最大值的5%作为阈值
        
        print(f"文本行检测 - 最大值: {max_proj:.1f}, 平均值: {mean_proj:.1f}, 阈值: {threshold:.1f} (最大值的5%)")
        
        for y, proj in enumerate(horizontal_proj):
            if proj > threshold:
                if not in_text:
                    in_text = True
                    start_y = y
            else:
                if in_text:
                    in_text = False
                    end_y = y
                    if end_y - start_y > 5:  # 最小高度5像素
                        text_lines.append((start_y, end_y))
        
        print(f"检测到 {len(text_lines)} 个文本行")
        if text_lines:
            print(f"文本行分布: {text_lines[:10]}...")  # 显示前10个
        
        # 方法3: 基于文本行的新闻块合并
        print("=== 新闻块合并 ===")
        regions = []
        
        if text_lines:
            # 智能文本行分组
            # 首先计算所有相邻文本行之间的间距
            gaps = []
            for i in range(1, len(text_lines)):
                prev_end = text_lines[i-1][1]
                curr_start = text_lines[i][0]
                gap = curr_start - prev_end
                gaps.append(gap)
            
            # 计算间距的统计信息
            if gaps:
                gap_mean = np.mean(gaps)
                gap_std = np.std(gaps)
                print(f"文本行间距统计: 平均={gap_mean:.1f}, 标准差={gap_std:.1f}")
                
                # 找到显著的间距（大于平均+1.2*标准差）
                threshold_gap = gap_mean + 1.2 * gap_std
                print(f"间距阈值: {threshold_gap:.1f}")
                
                # 基于显著间距进行分组
                current_group = [text_lines[0]]
                
                for i in range(1, len(text_lines)):
                    prev_end = current_group[-1][1]
                    curr_start = text_lines[i][0]
                    gap = curr_start - prev_end
                    
                    print(f"行 {i-1} 到行 {i} 间距: {gap:.1f} (阈值: {threshold_gap:.1f})")
                    
                    if gap > threshold_gap:  # 间距超过阈值，认为是不同新闻块
                        # 保存当前组
                        if current_group:
                            group_start = current_group[0][0]
                            group_end = current_group[-1][1]
                            group_height = group_end - group_start
                            
                            if group_height > 30:  # 最小高度30像素
                                x1 = 10
                                y1 = max(0, group_start - 10)
                                x2 = image_width - 10
                                y2 = min(image_height, group_end + 10)
                                
                                regions.append({
                                    "x": x1,
                                    "y": y1,
                                    "width": x2 - x1,
                                    "height": y2 - y1,
                                    "coordinates": [x1, y1, x2, y2]
                                })
                                print(f"  -> 新闻块: y={y1}-{y2}, 高度={y2-y1}")
                        
                        current_group = [text_lines[i]]
                    else:
                        current_group.append(text_lines[i])
                
                # 处理最后一组
                if current_group:
                    group_start = current_group[0][0]
                    group_end = current_group[-1][1]
                    group_height = group_end - group_start
                    
                    if group_height > 30:
                        x1 = 10
                        y1 = max(0, group_start - 10)
                        x2 = image_width - 10
                        y2 = min(image_height, group_end + 10)
                        
                        regions.append({
                            "x": x1,
                            "y": y1,
                            "width": x2 - x1,
                            "height": y2 - y1,
                            "coordinates": [x1, y1, x2, y2]
                        })
                        print(f"  -> 新闻块: y={y1}-{y2}, 高度={y2-y1}")
            else:
                # 只有一行文本，直接作为一个新闻块
                if text_lines:
                    group_start = text_lines[0][0]
                    group_end = text_lines[0][1]
                    x1 = 10
                    y1 = max(0, group_start - 10)
                    x2 = image_width - 10
                    y2 = min(image_height, group_end + 10)
                    
                    regions.append({
                        "x": x1,
                        "y": y1,
                        "width": x2 - x1,
                        "height": y2 - y1,
                        "coordinates": [x1, y1, x2, y2]
                    })
                    print(f"  -> 新闻块: y={y1}-{y2}, 高度={y2-y1}")
        
        # 方法3.1: 合并邻近的新闻块
        if len(regions) > 1:
            print("=== 合并邻近区域 ===")
            merged_regions = [regions[0]]
            
            for current_region in regions[1:]:
                last_region = merged_regions[-1]
                last_y2 = last_region["coordinates"][3]
                current_y1 = current_region["coordinates"][1]
                
                # 计算两个区域之间的间距
                gap = current_y1 - last_y2
                print(f"区域间距: {gap:.1f}")
                
                # 如果间距小于40像素，合并两个区域
                if gap < 40:
                    # 合并区域
                    merged_x1 = min(last_region["x"], current_region["x"])
                    merged_y1 = last_region["y"]
                    merged_x2 = max(last_region["coordinates"][2], current_region["coordinates"][2])
                    merged_y2 = current_region["coordinates"][3]
                    
                    merged_region = {
                        "x": merged_x1,
                        "y": merged_y1,
                        "width": merged_x2 - merged_x1,
                        "height": merged_y2 - merged_y1,
                        "coordinates": [merged_x1, merged_y1, merged_x2, merged_y2]
                    }
                    
                    merged_regions.pop()
                    merged_regions.append(merged_region)
                    print(f"  -> 合并区域: y={merged_y1}-{merged_y2}, 高度={merged_y2-merged_y1}")
                else:
                    merged_regions.append(current_region)
            
            regions = merged_regions
            print(f"合并后区域数量: {len(regions)}")
        
        # 方法3.2: 拆分过大的区域
        if regions:
            print("=== 拆分过大区域 ===")
            final_regions = []
            
            for region in regions:
                y1, y2 = region["y"], region["coordinates"][3]
                height = y2 - y1
                
                print(f"区域高度: {height}")
                
                if height > 400:  # 如果区域高度超过400像素，尝试拆分
                    # 计算该区域内的文本行
                    region_text_lines = []
                    for line in text_lines:
                        line_y1, line_y2 = line
                        if line_y1 >= y1 and line_y2 <= y2:
                            region_text_lines.append(line)
                    
                    if len(region_text_lines) > 1:
                        # 计算区域内文本行的间距
                        region_gaps = []
                        for i in range(1, len(region_text_lines)):
                            prev_end = region_text_lines[i-1][1]
                            curr_start = region_text_lines[i][0]
                            gap = curr_start - prev_end
                            region_gaps.append(gap)
                        
                        if region_gaps:
                            # 找到最大的间距作为拆分点
                            max_gap_index = region_gaps.index(max(region_gaps))
                            split_line = region_text_lines[max_gap_index + 1][0]
                            
                            print(f"拆分点: {split_line}")
                            
                            # 拆分区域
                            x = region["x"]
                            w = region["width"]
                            
                            # 上半部分
                            top_region = {
                                "x": x,
                                "y": y1,
                                "width": w,
                                "height": split_line - y1,
                                "coordinates": [x, y1, x+w, split_line]
                            }
                            
                            # 下半部分
                            bottom_region = {
                                "x": x,
                                "y": split_line,
                                "width": w,
                                "height": y2 - split_line,
                                "coordinates": [x, split_line, x+w, y2]
                            }
                            
                            final_regions.extend([top_region, bottom_region])
                            print(f"  -> 拆分区域: 上半部分 y={y1}-{split_line}, 下半部分 y={split_line}-{y2}")
                        else:
                            final_regions.append(region)
                    else:
                        final_regions.append(region)
                else:
                    final_regions.append(region)
            
            regions = final_regions
            print(f"拆分后区域数量: {len(regions)}")
        
        # 方法4: 基于密度的分割作为补充
        if len(regions) < 4:
            print("=== 密度分割 ===")
            print(f"当前区域数量不足({len(regions)}), 使用密度分割...")
            
            # 计算文本密度
            text_density = np.sum(dilated, axis=1) / image_width
            
            # 寻找密度谷值（分割点）
            valleys = []
            for i in range(1, len(text_density) - 1):
                if text_density[i] < text_density[i-1] and text_density[i] < text_density[i+1]:
                    valleys.append((i, text_density[i]))
            
            # 按密度排序，取前几个最小的谷值
            valleys.sort(key=lambda x: x[1])
            top_valleys = [v[0] for v in valleys[:3]]  # 取前3个谷值作为分割点
            top_valleys.sort()
            
            print(f"找到 {len(top_valleys)} 个分割点: {top_valleys}")
            
            if top_valleys:
                # 基于谷值分割
                if len(top_valleys) == 1:
                    # 分为上下两部分
                    mid = top_valleys[0]
                    density_regions = [
                        {"x": 10, "y": 0, "width": image_width-20, "height": mid+50, "coordinates": [10, 0, image_width-10, mid+50]},
                        {"x": 10, "y": mid-50, "width": image_width-20, "height": image_height - (mid-50), "coordinates": [10, mid-50, image_width-10, image_height]}
                    ]
                elif len(top_valleys) == 2:
                    # 分为三段
                    density_regions = [
                        {"x": 10, "y": 0, "width": image_width-20, "height": top_valleys[0]+50, "coordinates": [10, 0, image_width-10, top_valleys[0]+50]},
                        {"x": 10, "y": top_valleys[0]-50, "width": image_width-20, "height": top_valleys[1] - (top_valleys[0]-50) + 50, "coordinates": [10, top_valleys[0]-50, image_width-10, top_valleys[1]+50]},
                        {"x": 10, "y": top_valleys[1]-50, "width": image_width-20, "height": image_height - (top_valleys[1]-50), "coordinates": [10, top_valleys[1]-50, image_width-10, image_height]}
                    ]
                elif len(top_valleys) >= 3:
                    # 分为四段
                    density_regions = [
                        {"x": 10, "y": 0, "width": image_width-20, "height": top_valleys[0]+50, "coordinates": [10, 0, image_width-10, top_valleys[0]+50]},
                        {"x": 10, "y": top_valleys[0]-50, "width": image_width-20, "height": top_valleys[1] - (top_valleys[0]-50) + 50, "coordinates": [10, top_valleys[0]-50, image_width-10, top_valleys[1]+50]},
                        {"x": 10, "y": top_valleys[1]-50, "width": image_width-20, "height": top_valleys[2] - (top_valleys[1]-50) + 50, "coordinates": [10, top_valleys[1]-50, image_width-10, top_valleys[2]+50]},
                        {"x": 10, "y": top_valleys[2]-50, "width": image_width-20, "height": image_height - (top_valleys[2]-50), "coordinates": [10, top_valleys[2]-50, image_width-10, image_height]}
                    ]
            else:
                # 基于密度百分位的分割
                print("使用密度百分位分割...")
                density_sorted = np.argsort(text_density)
                low_density_indices = density_sorted[:len(density_sorted)//4]  # 最低25%的密度
                low_density_indices.sort()
                
                if len(low_density_indices) >= 3:
                    # 选择三个分割点
                    split_points = [
                        low_density_indices[len(low_density_indices)//4],
                        low_density_indices[len(low_density_indices)//2],
                        low_density_indices[3*len(low_density_indices)//4]
                    ]
                    split_points.sort()
                    
                    density_regions = [
                        {"x": 10, "y": 0, "width": image_width-20, "height": split_points[0]+40, "coordinates": [10, 0, image_width-10, split_points[0]+40]},
                        {"x": 10, "y": split_points[0]-40, "width": image_width-20, "height": split_points[1] - (split_points[0]-40) + 40, "coordinates": [10, split_points[0]-40, image_width-10, split_points[1]+40]},
                        {"x": 10, "y": split_points[1]-40, "width": image_width-20, "height": split_points[2] - (split_points[1]-40) + 40, "coordinates": [10, split_points[1]-40, image_width-10, split_points[2]+40]},
                        {"x": 10, "y": split_points[2]-40, "width": image_width-20, "height": image_height - (split_points[2]-40), "coordinates": [10, split_points[2]-40, image_width-10, image_height]}
                    ]
                else:
                    # 最后的备用方案 - 智能分割
                    print("使用智能分割...")
                    # 基于图像高度的比例分割
                    total_height = image_height
                    segment_heights = [
                        int(total_height * 0.25),  # 上部分25%
                        int(total_height * 0.2),   # 中上部20%
                        int(total_height * 0.25),  # 中下部25%
                        total_height - int(total_height * 0.25) - int(total_height * 0.2) - int(total_height * 0.25)  # 剩余部分
                    ]
                    current_y = 0
                    density_regions = []
                    
                    for h in segment_heights:
                        y1 = current_y
                        y2 = min(current_y + h, image_height)
                        density_regions.append({
                            "x": 10,
                            "y": y1,
                            "width": image_width-20,
                            "height": y2 - y1,
                            "coordinates": [10, y1, image_width-10, y2]
                        })
                        current_y = y2
            
            # 只在没有足够区域时添加密度分割区域
            # 确保文本行检测生成的区域优先
            if len(regions) == 0:
                regions.extend(density_regions)
            else:
                # 计算现有区域覆盖的高度范围
                existing_heights = []
                for region in regions:
                    y1, y2 = region["y"], region["coordinates"][3]
                    existing_heights.extend(range(y1, y2))
                
                # 只添加现有区域未覆盖的密度区域
                for density_region in density_regions:
                    dr_y1, dr_y2 = density_region["y"], density_region["coordinates"][3]
                    # 检查密度区域是否与现有区域重叠
                    overlap = False
                    for y in range(dr_y1, dr_y2):
                        if y in existing_heights:
                            overlap = True
                            break
                    if not overlap:
                        regions.append(density_region)
                        existing_heights.extend(range(dr_y1, dr_y2))
        
        # 去重和排序
        print("=== 后处理 ===")
        # 按y坐标排序
        regions.sort(key=lambda r: r["y"])
        
        # 去重 - 移除重叠严重的区域
        unique_regions = []
        for region in regions:
            x1, y1, x2, y2 = region["coordinates"]
            region_area = (x2 - x1) * (y2 - y1)
            
            # 检查是否与已添加的区域重叠
            overlapping = False
            for existing in unique_regions:
                ex_x1, ex_y1, ex_x2, ex_y2 = existing["coordinates"]
                ex_area = (ex_x2 - ex_x1) * (ex_y2 - ex_y1)
                
                # 计算重叠面积
                overlap_x = max(0, min(x2, ex_x2) - max(x1, ex_x1))
                overlap_y = max(0, min(y2, ex_y2) - max(y1, ex_y1))
                overlap_area = overlap_x * overlap_y
                
                if overlap_area > 0.5 * min(region_area, ex_area):  # 重叠超过50%
                    overlapping = True
                    # 保留文本行检测生成的区域（通常更精确）
                    # 不替换现有区域
                    break
            
            if not overlapping:
                unique_regions.append(region)
        
        regions = unique_regions
        
        # 确保至少有4个区域（但只在没有足够区域时）
        if len(regions) < 4:
            print(f"区域数量不足({len(regions)}), 使用补充分割...")
            
            # 补充分割
            while len(regions) < 4:
                # 找到最大的区域并分割
                if regions:
                    largest_region = max(regions, key=lambda r: r["height"])
                    x, y, w, h = largest_region["x"], largest_region["y"], largest_region["width"], largest_region["height"]
                    
                    # 从中间分割
                    mid = y + h // 2
                    
                    # 移除原区域
                    regions.remove(largest_region)
                    
                    # 添加两个新区域
                    regions.append({"x": x, "y": y, "width": w, "height": mid - y, "coordinates": [x, y, x+w, mid]})
                    regions.append({"x": x, "y": mid, "width": w, "height": y + h - mid, "coordinates": [x, mid, x+w, y+h]})
                else:
                    # 没有区域，创建默认区域
                    # 使用智能分割，而不是固定高度
                    print("使用智能分割创建默认区域...")
                    # 基于图像高度的比例分割
                    total_height = image_height
                    segment_heights = [
                        int(total_height * 0.25),  # 上部分25%
                        int(total_height * 0.2),   # 中上部20%
                        int(total_height * 0.25),  # 中下部25%
                        total_height - int(total_height * 0.25) - int(total_height * 0.2) - int(total_height * 0.25)  # 剩余部分
                    ]
                    current_y = 0
                    for h in segment_heights:
                        y1 = current_y
                        y2 = min(current_y + h, image_height)
                        regions.append({
                            "x": 10,
                            "y": y1,
                            "width": image_width-20,
                            "height": y2 - y1,
                            "coordinates": [10, y1, image_width-10, y2]
                        })
                        current_y = y2
        
        # 再次排序
        regions.sort(key=lambda r: r["y"])
        
        print(f"最终检测到 {len(regions)} 个新闻区域")
        for i, region in enumerate(regions):
            x1, y1, x2, y2 = region["coordinates"]
            print(f" 区域 {i+1}: x={x1}, y={y1}, 宽={x2-x1}, 高={y2-y1}")
        
        # 转换为客户端期望的格式
        result_regions = []
        for region in regions:
            result_regions.append({
                "x": region["x"],
                "y": region["y"],
                "width": region["width"],
                "height": region["height"],
                "coordinates": region["coordinates"]
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


if __name__ == "__main__":
    # 测试分析
    image_path = "downloaded_images/ft_uk_2026-03-10.jpg"
    result = analyze_layout(image_path)
    
    print("\n=== 分析结果 ===")
    print(f"成功: {result['success']}")
    if result['success']:
        print(f"图像尺寸: {result['image_size']['width']}x{result['image_size']['height']}")
        print(f"区域数量: {result['regions_count']}")
        print("区域列表:")
        for i, region in enumerate(result['regions']):
            print(f"  区域 {i+1}: {region['coordinates']}")
    else:
        print(f"错误: {result['error']}")
