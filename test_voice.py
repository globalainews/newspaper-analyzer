#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试音色文件加载和语音生成
"""

import os
import sys

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from voice_clone import get_cosyvoice_cloner


def main():
    """主函数"""
    print("=== 测试音色文件加载和语音生成 ===")
    
    try:
        # 获取语音克隆器实例
        cloner = get_cosyvoice_cloner()
        
        # 加载模型
        if not cloner.model_loaded:
            print("加载CosyVoice3模型...")
            if not cloner.load_model():
                print("模型加载失败")
                return False
        
        # 检查音色文件是否加载成功
        print(f"音色文件加载状态: {cloner.voice_loaded}")
        
        # 测试生成语音
        test_text = "今天的天气不错啊，这是一段测试文本。"
        test_output = "test_voice.wav"
        
        print(f"\n测试文本: {test_text}")
        print(f"输出文件: {test_output}")
        
        print("开始生成语音...")
        success = cloner.generate_voice(test_text, test_output, text_frontend=False)
        
        if success:
            print("\n✅ 语音生成成功!")
            print(f"文件位置: {test_output}")
        else:
            print("\n❌ 语音生成失败")
        
        return success
        
    except Exception as e:
        print(f"错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    main()
