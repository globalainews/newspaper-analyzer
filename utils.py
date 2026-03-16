import os
import json
import shutil


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


def refresh_image_list(download_dir):
    """刷新图片列表"""
    image_files = []
    if os.path.exists(download_dir):
        image_files = [f for f in os.listdir(download_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        image_files = sorted(image_files)
    return image_files