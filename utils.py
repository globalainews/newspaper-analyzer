import os
import json
import shutil
import datetime


def load_config(config_file='config.json'):
    """加载配置文件"""
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        prompt_file = config.get('analysis_prompt_file', 'prompt.txt')
        if os.path.exists(prompt_file):
            try:
                with open(prompt_file, 'r', encoding='utf-8') as f:
                    config['analysis_prompt'] = f.read()
            except Exception as e:
                print(f"警告：无法加载提示词文件 {prompt_file}: {e}")
                config['analysis_prompt'] = "请分析这张报纸首页图片。"
        else:
            config['analysis_prompt'] = "请分析这张报纸首页图片。"
            
        return config
    except FileNotFoundError:
        default_config = {
            "gemini": {
                "api_key": "YOUR_GEMINI_API_KEY_HERE",
                "model": "gemini-2.5-flash",
                "proxy": {
                    "host": "127.0.0.1",
                    "port": 1080
                }
            },
            "analysis_prompt_file": "prompt.txt",
            "download_settings": {
                "save_directory": "downloaded_images",
                "image_quality": "750"
            },
            "export_settings": {
                "export_directory": "E:\\中文听见\\报纸头版"
            },
            "analysis_settings": {
                "analysis_directory": "analysis_results"
            }
        }
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, ensure_ascii=False, indent=2)
        return default_config


def export_image(source_filepath, export_dir, filename):
    """导出图片到指定目录"""
    try:
        if not os.path.exists(source_filepath):
            return False, f"源文件不存在: {source_filepath}"
        
        if not os.path.exists(export_dir):
            os.makedirs(export_dir, exist_ok=True)
        
        base_name = os.path.splitext(filename)[0]
        
        if 'wsj' in base_name.lower():
            export_filename = "华尔街日报.jpg"
        elif 'ft' in base_name.lower() or 'ft_uk' in base_name.lower():
            export_filename = "金融时报.jpg"
        else:
            export_filename = filename
        
        export_filepath = os.path.join(export_dir, export_filename)
        
        shutil.copy2(source_filepath, export_filepath)
        
        return True, f"图片已导出到:\n{export_filepath}"
        
    except Exception as e:
        return False, f"导出图片时出错:\n{str(e)}"


def refresh_image_list(download_dir, sort_by='date'):
    """刷新图片列表
    Args:
        download_dir: 下载目录
        sort_by: 排序方式 'date' 按日期, 'name' 按文件名
    Returns:
        排序后的图片文件列表（倒序）
    """
    # 从下载目录查找今天最新的报纸文件并复制到项目目录
    copy_todays_newspaper()
    
    image_files = []
    if os.path.exists(download_dir):
        image_files = [f for f in os.listdir(download_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        if sort_by == 'date':
            # 按修改日期倒序
            image_files = sorted(image_files, key=lambda f: os.path.getmtime(os.path.join(download_dir, f)), reverse=True)
        else:
            # 按文件名倒序
            image_files = sorted(image_files, key=lambda f: f.lower(), reverse=True)
    return image_files


def copy_todays_newspaper():
    """从下载目录查找今天最新的报纸文件并复制到项目的downloaded_images目录"""
    import shutil
    
    # 下载目录
    downloads_dir = r'F:\Administrator\Downloads'
    # 目标目录
    project_dir = os.path.dirname(os.path.abspath(__file__))
    target_dir = os.path.join(project_dir, 'downloaded_images')
    
    # 确保目标目录存在
    os.makedirs(target_dir, exist_ok=True)
    
    if not os.path.exists(downloads_dir):
        print(f"[DEBUG] 下载目录不存在: {downloads_dir}")
        return
    
    # 获取今天日期（YYYYMMDD格式）
    today = datetime.datetime.now().strftime('%Y%m%d')
    
    # 查找今天的报纸文件（WSJ/FT开头 + 今天日期 + 支持jpg/png）
    today_files = []
    for f in os.listdir(downloads_dir):
        lower_name = f.lower()
        if lower_name.endswith('.jpg') or lower_name.endswith('.jpeg') or lower_name.endswith('.png'):
            upper_name = f.upper()
            if (upper_name.startswith('WSJ') or upper_name.startswith('FT')) and today in upper_name:
                today_files.append(f)
    
    if not today_files:
        print(f"[DEBUG] 未找到今天({today})的报纸文件")
        return
    
    # 按修改时间排序，取最新的
    today_files = sorted(today_files, key=lambda f: os.path.getmtime(os.path.join(downloads_dir, f)), reverse=True)
    latest_file = today_files[0]
    source_path = os.path.join(downloads_dir, latest_file)
    target_path = os.path.join(target_dir, latest_file)
    
    # 检查是否需要复制
    if os.path.exists(target_path):
        source_mtime = os.path.getmtime(source_path)
        target_mtime = os.path.getmtime(target_path)
        if source_mtime <= target_mtime:
            print(f"[DEBUG] 目标文件已是最新版本，无需复制: {latest_file}")
            return
    
    # 复制文件
    try:
        shutil.copy2(source_path, target_path)
        print(f"[DEBUG] 已复制报纸文件: {latest_file} -> {target_dir}")
    except Exception as e:
        print(f"[ERROR] 复制文件失败: {str(e)}")