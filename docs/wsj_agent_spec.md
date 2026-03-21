# 华尔街日报首页图片自动下载智能体规格说明

## 1. 概述

### 1.1 目标
自动从华尔街日报(WSJ)的Twitter账号下载每日报纸首页图片，用于后续的新闻内容分析和视频生成。

### 1.2 使用场景
- 每日新闻素材采集
- 自动化报纸头版归档
- 新闻视频制作素材获取

## 2. 需求规格

### 2.1 功能需求

| ID | 需求描述 | 优先级 |
|----|----------|--------|
| FR-001 | 自动打开华尔街日报Twitter页面 | 高 |
| FR-002 | 定位包含首页图片的特定帖子 | 高 |
| FR-003 | 提取帖子中的首页图片URL | 高 |
| FR-004 | 下载图片并保存到指定目录 | 高 |
| FR-005 | 支持共享Chrome浏览器实例 | 中 |
| FR-006 | 提供进度和状态反馈 | 中 |
| FR-007 | 支持滚动加载查找历史帖子 | 低 |

### 2.2 非功能需求

| ID | 需求描述 |
|----|----------|
| NFR-001 | 响应时间：页面加载等待5秒，确保内容完全渲染 |
| NFR-002 | 可靠性：支持滚动查找，最多滚动5次 |
| NFR-003 | 兼容性：支持Windows系统，Chrome浏览器 |
| NFR-004 | 可维护性：模块化设计，独立于主程序 |

## 3. 技术架构

### 3.1 技术栈

```
┌─────────────────────────────────────────┐
│           WSJAutomation                 │
│  (wsj_automation.py)                    │
├─────────────────────────────────────────┤
│  Playwright (sync_api)                  │
│  - chromium.connect_over_cdp()          │
│  - page.goto()                          │
│  - page.query_selector_all()            │
│  - context.request.get()                │
├─────────────────────────────────────────┤
│  Chrome Browser (Debug Mode)            │
│  - Port: 9222                           │
│  - CDP Protocol                         │
└─────────────────────────────────────────┘
```

### 3.2 核心组件

#### 3.2.1 WSJAutomation 类

```python
class WSJAutomation:
    def __init__(self, config, progress_callback, status_callback)
    def connect_to_chrome() -> bool
    def download_wsj_frontpage(save_dir) -> str | None
    def update_progress(message, progress)
    def update_status(message)
```

#### 3.2.2 依赖关系

```
main.py
    └── WSJAutomation
            ├── config (配置对象)
            ├── progress_callback (进度回调)
            └── status_callback (状态回调)
```

## 4. 业务流程

### 4.1 主流程图

```
┌──────────────┐
│   开始       │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ 连接Chrome   │ (CDP 9222端口)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ 导航到       │
│ x.com/wsj    │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ 等待页面加载 │ (5秒)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ 查找目标帖子 │ "look at the front page of The Wall Street"
└──────┬───────┘
       │
       ├── 找到 ──────────────┐
       │                      │
       ▼ 未找到               ▼
┌──────────────┐      ┌──────────────┐
│ 滚动页面     │      │ 提取图片URL  │
│ (最多5次)    │      └──────┬───────┘
└──────┬───────┘             │
       │                     ▼
       └─────────────►┌──────────────┐
                      │ 打开图片URL  │
                      └──────┬───────┘
                             │
                             ▼
                      ┌──────────────┐
                      │ 下载图片     │
                      │ (context.request)
                      └──────┬───────┘
                             │
                             ▼
                      ┌──────────────┐
                      │ 保存到本地   │
                      │ wsj_YYYYMMDD.jpg
                      └──────┬───────┘
                             │
                             ▼
                      ┌──────────────┐
                      │   结束       │
                      └──────────────┘
```

### 4.2 状态流转

| 状态 | 描述 | 进度 |
|------|------|------|
| 连接Chrome | 建立CDP连接 | 10% |
| 获取页面 | 获取浏览器context和page | 10% |
| 导航到WSJ | 跳转到Twitter页面 | 20% |
| 等待页面加载 | 等待内容渲染 | 40% |
| 查找帖子 | 搜索目标帖子 | 50% |
| 查找图片 | 提取图片URL | 60% |
| 打开图片页面 | 导航到图片URL | 70% |
| 下载图片 | 获取图片数据 | 80% |
| 保存完成 | 写入本地文件 | 90% |

## 5. 关键技术细节

### 5.1 Chrome调试模式连接

```python
# 启动Chrome调试模式命令
chrome.exe --remote-debugging-port=9222 --remote-allow-origins=* --user-data-dir="E:\temp_profile"

# Playwright连接
playwright = sync_playwright().start()
browser = playwright.chromium.connect_over_cdp('http://127.0.0.1:9222')
```

### 5.2 帖子定位策略

**目标文本**: `"look at the front page of The Wall Street"`

**选择器**: `article[data-testid="tweet"]`

**匹配逻辑**:
1. 获取所有帖子元素
2. 遍历检查文本内容
3. 不区分大小写匹配目标文本
4. 未找到则滚动页面继续查找

### 5.3 图片提取策略

**选择器**: `img`

**过滤条件**:
- URL包含 `media` 或 `pbs.twimg.com`
- 排除 `profile_images` (头像)
- 排除 `avatar` (头像)
- 排除 `profile` (头像)

### 5.4 图片下载策略

使用浏览器context的request API，共享登录session：

```python
context = browser.contexts[0]
api_request = context.request
response = api_request.get(img_src)
img_data = response.body()
```

### 5.5 文件命名规则

```python
filename = f"wsj_{datetime.now().strftime('%Y%m%d')}.jpg"
# 示例: wsj_20260321.jpg
```

## 6. 错误处理

### 6.1 异常场景

| 场景 | 处理方式 |
|------|----------|
| Chrome未启动 | 返回None，提示用户启动浏览器 |
| 页面加载超时 | 60秒超时，返回None |
| 未找到目标帖子 | 滚动5次后仍找不到，返回None |
| 图片下载失败 | 返回None，记录错误日志 |
| 网络异常 | 捕获异常，返回None |

### 6.2 资源清理

```python
finally:
    try:
        if self.playwright:
            self.playwright.stop()
    except:
        pass
```

## 7. 配置项

```json
{
  "download_settings": {
    "save_directory": "downloaded_images"
  }
}
```

## 8. 接口定义

### 8.1 初始化参数

| 参数 | 类型 | 描述 |
|------|------|------|
| config | dict | 配置对象 |
| progress_callback | Callable[[str, int], None] | 进度回调函数 |
| status_callback | Callable[[str], None] | 状态回调函数 |

### 8.2 返回值

| 类型 | 描述 |
|------|------|
| str | 成功时返回保存的文件路径 |
| None | 失败时返回None |

## 9. 使用示例

```python
from wsj_automation import WSJAutomation

# 创建实例
wsj = WSJAutomation(
    config={'download_settings': {'save_directory': 'downloaded_images'}},
    progress_callback=lambda msg, prog: print(f"[{prog}%] {msg}"),
    status_callback=lambda msg: print(f"状态: {msg}")
)

# 执行下载
result = wsj.download_wsj_frontpage()

if result:
    print(f"下载成功: {result}")
else:
    print("下载失败")
```

## 10. 限制与约束

1. **浏览器依赖**: 需要预先启动Chrome调试模式
2. **登录状态**: Twitter需要用户已登录（手动登录）
3. **网络要求**: 需要能够访问x.com
4. **帖子格式**: 依赖WSJ发布的帖子包含特定文本
5. **单线程**: 不支持并发下载

## 11. 未来优化方向

1. **自动登录**: 集成Twitter自动登录功能
2. **多账号支持**: 支持多个Twitter账号轮换
3. **历史归档**: 支持下载历史日期的首页
4. **错误重试**: 自动重试机制
5. **代理支持**: 支持通过代理访问

## 12. 版本历史

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| 1.0 | 2026-03-21 | 初始版本，支持基本下载功能 |
