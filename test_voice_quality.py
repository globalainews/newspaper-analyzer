#!/usr/bin/env python3
"""
测试语音克隆质量参数
"""

import os
import sys

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from voice_clone import VoiceCloner

def test_voice_quality():
    """测试语音克隆质量参数"""
    print("=" * 60)
    print("语音克隆质量测试")
    print("=" * 60)
    
    # 简单的测试文本
    test_text = "这是一个测试音频，用于测试语音克隆的质量参数。"
    
    # 输出目录
    output_dir = os.path.join(os.path.dirname(__file__), 'test_quality')
    os.makedirs(output_dir, exist_ok=True)
    
    # 测试不同的text_frontend设置
    test_cases = [
        {'name': 'text_frontend=True', 'text_frontend': True},
        {'name': 'text_frontend=False', 'text_frontend': False}
    ]
    
    for test_case in test_cases:
        print(f"\n测试: {test_case['name']}")
        print("-" * 40)
        
        # 创建语音克隆器
        cloner = VoiceCloner()
        
        # 输出文件路径
        output_file = os.path.join(output_dir, f"test_{test_case['name'].replace(' ', '_')}.wav")
        
        # 生成语音
        print(f"生成语音...")
        success = cloner.generate_voice(
            test_text, 
            output_file, 
            text_frontend=test_case['text_frontend']
        )
        
        if success:
            print(f"✅ 成功生成: {output_file}")
        else:
            print(f"❌ 生成失败")
    
    print("\n" + "=" * 60)
    print("测试完成! 请比较生成的音频文件质量")
    print(f"输出目录: {output_dir}")
    print("=" * 60)

if __name__ == '__main__':
    test_voice_quality()