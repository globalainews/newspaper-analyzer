# 图片处理辅助模块
# 用于截图后的图片增强处理

from PIL import Image, ImageEnhance

def expand_to_ratio(image, target_ratio=(3, 4), bg_color=(255, 255, 255)):
    """
    将图片扩展到指定宽高比例
    保持原图内容居中，使用指定背景色填充扩展区域
    
    Args:
        image: PIL.Image 对象
        target_ratio: 目标宽高比例，默认 (3, 4) 表示宽:高 = 3:4
        bg_color: 背景填充颜色，默认白色
    
    Returns:
        PIL.Image: 扩展后的图片
    """
    # 确保图片为RGB模式
    if image.mode == 'RGBA':
        image = image.convert('RGB')
    elif image.mode != 'RGB':
        image = image.convert('RGB')
    
    w, h = image.size
    target_w_ratio, target_h_ratio = target_ratio
    
    # 计算目标尺寸，保持比例
    current_ratio = w / h
    target_ratio_value = target_w_ratio / target_h_ratio
    
    if current_ratio > target_ratio_value:
        # 当前图片宽度比例较大，需要扩展高度
        new_h = int(w * target_h_ratio / target_w_ratio)
        new_w = w
    else:
        # 当前图片高度比例较大，需要扩展宽度
        new_w = int(h * target_w_ratio / target_h_ratio)
        new_h = h
    
    # 创建新画布
    new_image = Image.new('RGB', (new_w, new_h), bg_color)
    
    # 将原图放在顶部右对齐粘贴
    x_offset = new_w - w  # 右对齐
    y_offset = 0  # 顶部对齐
    new_image.paste(image, (x_offset, y_offset))
    
    return new_image

def enhance_text_clarity(image, sharpness_factor=1.5, contrast_factor=1.2):
    """
    增强图片文字清晰度
    通过锐化和对比度增强提高文字可读性
    
    Args:
        image: PIL.Image 对象
        sharpness_factor: 锐化系数，默认1.5（>1增强锐化）
        contrast_factor: 对比度系数，默认1.2（>1增强对比）
    
    Returns:
        PIL.Image: 增强后的图片
    """
    # 确保图片为RGB模式
    if image.mode == 'RGBA':
        image = image.convert('RGB')
    elif image.mode != 'RGB':
        image = image.convert('RGB')
    
    # 锐化增强 - 增强边缘清晰度
    sharpness_enhancer = ImageEnhance.Sharpness(image)
    image = sharpness_enhancer.enhance(sharpness_factor)
    
    # 对比度增强 - 提高文字与背景对比
    contrast_enhancer = ImageEnhance.Contrast(image)
    image = contrast_enhancer.enhance(contrast_factor)
    
    return image

def process_screenshot(image, target_ratio=(3, 4), sharpness=1.5, contrast=1.2):
    """
    组合处理截图图片
    1. 扩展到目标宽高比例
    2. 增强文字清晰度
    
    Args:
        image: PIL.Image 对象
        target_ratio: 目标宽高比例
        sharpness: 锐化系数
        contrast: 对比度系数
    
    Returns:
        PIL.Image: 处理后的图片
    """
    print(f"[DEBUG] process_screenshot 输入: {image.size}, mode={image.mode}")
    
    # 先扩展比例
    image = expand_to_ratio(image, target_ratio)
    print(f"[DEBUG] expand_to_ratio 输出: {image.size}, mode={image.mode}")
    
    # 再增强清晰度
    image = enhance_text_clarity(image, sharpness, contrast)
    print(f"[DEBUG] enhance_text_clarity 输出: {image.size}, mode={image.mode}")
    
    print(f"[DEBUG] process_screenshot 最终输出: {image.size}")
    return image