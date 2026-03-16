# 报纸头版下载与分析工具

一个用于下载报纸头版图片、使用 AI 进行分析并生成视频的桌面应用程序。

## 功能特性

- **图片下载**: 从 kiosko.net 下载华尔街日报(WSJ)和金融时报(FT)头版图片
- **AI 分析**: 使用 Google Gemini 2.5 Flash 模型分析报纸内容
- **结果保存**: 自动保存分析结果，支持重复加载
- **图片导出**: 支持导出图片到指定目录
- **代理支持**: 支持通过代理服务器访问 API
- **新闻块标识**: 自动识别并标识报纸头版新闻块位置
- **视频生成**: 自动生成带配音和字幕的新闻视频
- **剪映草稿**: 自动生成剪映(CapCut)草稿文件，支持直接导入编辑

## 环境要求

- Python 3.8+
- Windows 系统
- 剪映专业版 5.9+（用于视频草稿导入）

## 安装依赖

```bash
pip install requests Pillow
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
  },
  "jianying_settings": {
    "drafts_directory": "F:/剪映5.9/JianyingPro Drafts"
  },
  "video_settings": {
    "output_directory": "generated_videos"
  }
}
```

## 目录结构

```
project/
├── main.py                          # 主程序
├── run.py                           # 命令行启动文件 (Python)
├── run.bat                          # Windows批处理启动文件 (Windows双击运行)
├── config.json                      # 配置文件
├── analyzer.py                      # AI分析模块
├── downloader.py                    # 图片下载模块
├── layoutlm_analyzer.py             # LayoutLM分析模块
├── news_image_exporter.py           # 图片导出模块
├── utils.py                         # 工具函数模块
├── video_generator.py               # 视频生成模块（旧版，已弃用）
├── video_generator/                 # 视频生成模块（新版，模块化重构）
│   ├── __init__.py                  # 包初始化
│   ├── base.py                      # 基础类
│   ├── data_management.py           # 数据管理
│   ├── ui_helpers.py                # UI辅助函数
│   ├── video_creation.py            # 视频创建
│   ├── jianying_draft.py            # 剪映草稿处理
│   ├── timing_sync.py               # 时间同步
│   ├── main.py                      # 主类
│   └── draft_content.json           # 剪映草稿模板
├── downloaded_images/               # 下载的图片
├── analysis_results/                # 分析结果
├── generated_videos/                # 生成的视频
└── README.md
```

## 使用方法

### 基本使用流程

1. 修改 `config.json` 中的 API Key 和代理设置
2. 运行程序: 
   - Windows: 双击 `run.bat`
   - 或使用命令行: `python run.py`
   - 或直接运行: `python main.py`
3. 点击"下载华尔街日报"或"下载金融时报"按钮下载图片
4. 选择图片后点击"分析图片"进行分析
5. 分析结果自动保存，下次点击图片时自动加载
6. 新闻块位置会自动标识在图片预览上

### 视频生成功能

1. 选择已分析的报纸图片
2. 点击"生成视频"按钮
3. 程序会自动：
   - 生成TTS音频（新闻播报配音）
   - 生成字幕文件
   - 创建剪映草稿文件
   - 自动对齐视频素材时间轴
4. 打开剪映专业版，导入生成的草稿即可继续编辑

### 视频素材对齐说明

程序会自动对齐以下素材的结束时间：
- 早间播报背景配乐
- 新闻标题文本
- 金融时报图片
- 更多内容提示视频

所有素材的结束时间会自动对齐到视频结束点，确保视频播放时各元素同步结束。

## 运行

### 方式一：Windows 批处理（推荐）
双击 `run.bat` 即可启动

### 方式二：Python 脚本
```bash
python run.py
```

### 方式三：直接运行主程序
```bash
python main.py
```

程序启动后默认全屏显示，包含左右布局：
- 左侧：图片列表
- 中间：图片预览（带新闻块标识）
- 右侧：分析结果

## 剪映草稿配置

在 `config.json` 中配置剪映草稿目录：

```json
{
  "jianying_settings": {
    "drafts_directory": "F:/剪映5.9/JianyingPro Drafts"
  }
}
```

根据你的剪映安装路径修改 `drafts_directory`。

## 注意事项

1. 首次使用前请确保已配置正确的 Gemini API Key
2. 如果使用代理，请在配置文件中设置代理地址和端口
3. 剪映草稿目录需要根据实际安装路径配置
4. 生成的视频草稿需要在剪映中进一步编辑和导出

## 更新日志

### 2026-03-16
- 模块化重构视频生成代码
- 添加统一的素材时间对齐功能
- 修复金融时报图片对齐逻辑
- 优化剪映草稿生成流程
