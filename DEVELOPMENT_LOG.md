# 项目开发记录

> 本文档汇总了 newspaper-analyzer 项目的关键开发过程和技术细节

## 项目概述

`newspaper-analyzer` 是一个报纸头版视频生成工具，支持：
- 自动下载金融时报、华尔街日报等报纸头版
- 使用 Gemini AI 分析报纸内容，提取新闻标题和位置
- 使用 CosyVoice3 进行语音克隆
- 生成剪映(Jianying Pro)草稿视频

---

## 一、主要功能模块

### 1. 报纸下载模块
- `download_ft_cover.py` - 金融时报头版下载
- `wsj_downloader.py` - 华尔街日报下载
- 支持定时任务自动更新

### 2. 图像分析模块
- `analyzer.py` - 使用 Gemini API 分析报纸图片
- `layoutlmv3_service.py` - OCR 文字识别
- 输出：新闻标题、内容、位置坐标

### 3. 语音克隆模块
- `voice_clone.py` - CosyVoice3 零样本语音克隆
- 支持 reference_audio 进行音色克隆
- 可配置 seed、speed、instruct 参数

### 4. 视频生成模块
- `video_generator/` - 视频生成核心目录
  - `jianying_draft.py` - 生成剪映草稿 JSON
  - `timing_sync.py` - 音视频时序同步
  - `ui_helpers.py` - UI 辅助函数
  - `data_management.py` - 数据保存加载
  - `video_creation.py` - 视频创建逻辑

---

## 二、关键配置 (config.json)

```json
{
  "cosyvoice": {
    "model_dir": "pretrained_models/Fun-CosyVoice3-0.5B",
    "reference_audio": "testCosyvoice.WAV",
    "speed": 1,
    "seed": 42,
    "test_instruct": "You are a helpful assistant...",
    "test_text": "停火协议首日即摇摇欲坠..."
  },
  "jianying_settings": {
    "drafts_directory": "E:\\剪映5.9\\JianyingPro Drafts"
  },
  "video_settings": {
    "width": 1500,
    "height": 3200
  }
}
```

---

## 三、时序同步逻辑 (timing_sync.py)

### 3.1 入口函数
`process_jianying_draft_timing()` - 处理剪映草稿时序

### 3.2 处理流程

| 步骤 | 功能 | 说明 |
|------|------|------|
| 1 | sync_audio_durations | 读取 textReading/*.wav 实际时长，更新到 materials |
| 2 | sync_tts_and_subtitles | 核心同步逻辑 |

### 3.3 同步TTS和字幕的详细步骤

```
1. 收集 text_to_audio 音频片段，按原始开始时间排序
2. 重新计算时序：第1条保持原位，后续 = 前一条结束 + 0.8秒间隔
3. 更新音频 track segment 的 start 和 duration
4. 更新字幕 track segment 的 start 和 duration (duration = 音频时长 + 0.4秒)
5. 更新贴纸 track segment 的 start 和 duration (duration = 音频时长 + 0.4秒)
6. 处理"最后位置"素材：放在最后字幕结束 + 0.4秒处
7. 处理贴纸位置：与新闻矩形框左下角对齐
8. 处理 photo 素材(P1.jpg, P2.jpg...)：
   - P1.jpg: 保持原开始位置
   - P2+: 开始位置减少 0.4秒，避免空白
9. 处理翻页sound素材：与对应P.jpg按名称排序一一对齐，只对齐开始位置
10. 处理视频素材：对齐到 TTS 音频之后
11. 对齐背景音乐、文本等素材时长到视频总时长
12. 更新总时长文本显示("XX秒")
```

### 3.4 时序示意图

```
[音频1]--0.8s--[音频2]--0.8s--[音频3]--0.4s--[最后位置]--[视频素材...]
  ↑字幕1(+0.4s)    ↑字幕2(+0.4s)    ↑字幕3(+0.4s)
  ↑贴纸1(+0.4s)    ↑贴纸2(+0.4s)    ↑贴纸3(+0.4s)
  ↑P1.jpg          ↑P2.jpg(-0.4s)   ↑P3.jpg(-0.4s)
  ↑翻页1           ↑翻页2           ↑翻页3
```

---

## 四、数据流

### 4.1 JSON 文件结构

剪映草稿 `draft_content.json` 结构：
```json
{
  "canvas_config": {"width": 1620, "height": 2700},
  "duration": 33766666,
  "materials": {
    "audios": [...],      // 音频素材(含 text_to_audio 和 sound)
    "videos": [...],      // 视频素材(P.jpg等)
    "texts": [...],       // 字幕素材
    "stickers": [...],    // 贴纸素材
    "images": [...]        // 图片素材
  },
  "tracks": [
    {"type": "audio", "segments": [...]},
    {"type": "text", "segments": [...]},
    {"type": "video", "segments": [...]}
  ]
}
```

### 4.2 Segment 结构

```json
{
  "material_id": "xxx",
  "target_timerange": {
    "start": 9466666,      // 微秒
    "duration": 7900000
  },
  "source_timerange": {
    "start": 0,
    "duration": 7900000
  }
}
```

---

## 五、问题与修复记录

### 5.1 总时长计算错误(3小时视频)
- **原因**: 使用 material duration 而非 track segment duration
- **修复**: 改用 `last_position_track_duration` 基于 track segments 计算

### 5.2 剪映草稿语音与测试音色不一致
- **原因**: 文本含特殊引号，参数不一致
- **修复**: 添加文本清理，标准化 reference_audio、instruct、speed、seed 参数

### 5.3 source_timerange 与 target_timerange duration 不一致
- **原因**: 只更新了 target_timerange
- **修复**: 同步更新 source_timerange.duration

### 5.4 P2及以后图片有空白间隙
- **原因**: 后续图片开始位置未调整
- **修复**: P2+ 开始位置减少 0.4秒 (400000微秒)

### 5.5 新闻编辑后数据未保存
- **原因**: current_image_file 未正确设置
- **修复**: 增强保存逻辑，查找最新 JSON 文件作为备选

### 5.6 翻页素材未对齐
- **原因**: 翻页名称只有"翻页"无数字后缀，无法按名称匹配
- **修复**: 按名称排序后与 P.jpg 一一对应，只对齐开始位置

---

## 六、UI 布局

### 6.1 视频生成标签页布局

```
+-------------------------------------------------------------------+
|  [📊生成数据] [💾保存数据] [🔊加载模型] [🎵测试音色]  |  新闻编辑区域  |  预览区域  |
|  [🎬剪映草稿]  [⏱️同步时序]  [📷截图]              |               |           |
|  [📐完美矩形]  [🎬生成视频]                       |               |           |
+-------------------------------------------------------------------+
```

- 按钮区域：屏幕左侧，垂直排列
- 新闻编辑区：左侧面板，可编辑标题和内容
- 预览区：右侧，显示报纸图片和新闻位置

---

## 七、常用 Git 命令

```bash
# 提交代码
git add <files>
git commit -m "提交信息"
git push

# 拉取代码
git pull

# 丢弃本地修改
git checkout -- <file>
```

---

## 八、测试与调试

### 8.1 调试翻页对齐
```python
# 查看翻页和photos的对应关系
import json
d = json.load(open('draft_content.json','r',encoding='utf-8'))
# ...调试代码
```

### 8.2 查看 materials 结构
```python
print(list(d.get('materials',{}).keys()))
```

---

## 九、文件清单

| 文件路径 | 功能说明 |
|---------|---------|
| `main.py` | 主程序，UI 入口 |
| `config.json` | 配置文件 |
| `voice_clone.py` | 语音克隆模块 |
| `video_generator/jianying_draft.py` | 剪映草稿生成 |
| `video_generator/timing_sync.py` | 时序同步 |
| `video_generator/ui_helpers.py` | UI 辅助函数 |
| `video_generator/data_management.py` | 数据管理 |
| `video_generator/video_creation.py` | 视频创建 |

---

## 十、最近更新 (2026-05-06)

1. **翻页素材对齐**：翻页sound素材与P.jpg按顺序对齐开始位置
2. **字幕/贴纸时长**：增加0.4秒与JPG结束位置一致
3. **测试文本配置化**：test_text 移至 config.json
4. **按钮布局优化**：移至屏幕左侧，垂直排列
5. **新闻编辑区**：文本框宽度限制为60字符

---

*本文档由 AI 自动生成，最后更新于 2026-05-06*
