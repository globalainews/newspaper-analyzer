#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试时间同步功能
"""

import json
import os
from video_generator.timing_sync import TimingSynchronizer

# 加载draft_content.json
with open('video_generator/draft_content.json', 'r', encoding='utf-8') as f:
    draft_content = json.load(f)

# 创建TimingSynchronizer实例
config = {}
timing_sync = TimingSynchronizer(config)

# 运行同步
sync_result = timing_sync.sync_tts_and_subtitles(draft_content)

# 保存结果
with open('draft_content_sync.json', 'w', encoding='utf-8') as f:
    json.dump(sync_result, f, ensure_ascii=False, indent=2)

print("\n测试完成，结果已保存到 draft_content_sync.json")