# 报纸头版下载与分析工具

一个用于下载报纸头版图片并使用 AI 进行分析的桌面应用程序。

## 功能特性

- **图片下载**: 从 kiosko.net 下载华尔街日报(WSJ)和金融时报(FT)头版图片
- **AI 分析**: 使用 Google Gemini 2.5 Flash 模型分析报纸内容
- **结果保存**: 自动保存分析结果，支持重复加载
- **图片导出**: 支持导出图片到指定目录
- **代理支持**: 支持通过代理服务器访问 API

## 环境要求

- Python 3.8+
- Windows 系统

## 安装依赖

```bash
pip install requests Pillow google-api-python-client
```

## 配置文件 (config.json)

```json
{
  "gemini": {
    "api_key": "YOUR_API_KEY",
    "model": "gemini-2.5-flash",
    "proxy": {
      "host": "127.0.0.1",
      "port": 1080
    }
  },
  "analysis_prompt": "分析报纸头版的提示词...",
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
```

## 目录结构

```
project/
├── main.py                 # 主程序
├── config.json            # 配置文件
├── downloaded_images/     # 下载的图片
├── analysis_results/      # 分析结果
└── README.md
```

## 使用方法

1. 修改 `config.json` 中的 API Key 和代理设置
2. 运行程序: `python main.py`
3. 点击"下载华尔街日报"或"下载金融时报"按钮下载图片
4. 选择图片后点击"分析图片"进行分析
5. 分析结果自动保存，下次点击图片时自动加载

## 运行

```bash
python main.py
```

程序启动后默认全屏显示，包含左右布局：
- 左侧：图片列表
- 中间：图片预览
- 右侧：分析结果
