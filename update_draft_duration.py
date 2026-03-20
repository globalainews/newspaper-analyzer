import json
import os

# 草稿文件路径
draft_file = 'd:\\trea\\newspaper-analyzer\\video_generator\\draft_content.json'

# 读取草稿文件
with open(draft_file, 'r', encoding='utf-8') as f:
    draft_data = json.load(f)

# 找到id为4F5AEA3A-6BDF-4933-8DE1-EC31E979E97F的文本片段
texts = draft_data.get('materials', {}).get('texts', [])
for text in texts:
    if text.get('id') == '4F5AEA3A-6BDF-4933-8DE1-EC31E979E97F':
        # 替换内容
        text['content'] = '{"styles": [{"fill": {"content": {"render_type": "solid", "solid": {"alpha": 1.0, "color": [1.0, 1.0, 1.0]}}}, "font": {"id": "", "path": "E:/剪映5.9/JianyingPro/5.9.0.11611/Resources/Font/SystemFont/zh-hans.ttf"}, "range": [0, 4], "size": 15, "useLetterColor": true}], "text": "12秒"}'
        print(f"✓ 找到并更新文本片段: {text['id']}")
        break
else:
    print("✗ 未找到指定ID的文本片段")

# 计算total_duration（这里使用所有音频的总时长）
audios = draft_data.get('materials', {}).get('audios', [])
total_duration = 0
for audio in audios:
    # 只计算text_to_audio类型的音频
    if audio.get('type') == 'text_to_audio':
        total_duration += audio.get('duration', 0)

print(f"✓ 计算总时长: {total_duration} 微秒")

# 替换最上层的duration值
draft_data['duration'] = total_duration
print(f"✓ 更新最上层duration为: {total_duration}")

# 保存修改后的文件
with open(draft_file, 'w', encoding='utf-8') as f:
    json.dump(draft_data, f, ensure_ascii=False, indent=2)

print("\n✅ 任务完成！")
print(f"修改文件: {draft_file}")
print(f"更新的总时长: {total_duration} 微秒")