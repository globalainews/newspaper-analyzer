#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成音色文件：从testCosyvoice.wav提取音色特征并保存为myVoice.pt
"""

import os
import sys

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from voice_clone import get_cosyvoice_cloner

# 配置
COSYVOICE_ROOT_DIR = 'D:\\trea\\CosyVoice3'
REFERENCE_AUDIO = os.path.join(COSYVOICE_ROOT_DIR, 'testCosyvoice.WAV')
OUTPUT_FILE = os.path.join(COSYVOICE_ROOT_DIR, 'myVoice.pt')


def main():
    """主函数"""
    print("=== 生成音色文件 ===")
    print(f"参考音频: {REFERENCE_AUDIO}")
    print(f"输出文件: {OUTPUT_FILE}")
    
    # 检查文件是否存在
    if not os.path.exists(REFERENCE_AUDIO):
        print(f"错误: 参考音频文件不存在: {REFERENCE_AUDIO}")
        return False
    
    try:
        # 获取语音克隆器实例
        cloner = get_cosyvoice_cloner()
        
        # 加载模型
        if not cloner.model_loaded:
            print("加载CosyVoice3模型...")
            if not cloner.load_model():
                print("模型加载失败")
                return False
        
        # 生成音色文件
        success = cloner.generate_voice_file(REFERENCE_AUDIO, OUTPUT_FILE)
        
        if success:
            print("\n✅ 音色文件生成成功!")
            print(f"文件位置: {OUTPUT_FILE}")
        else:
            print("\n❌ 音色文件生成失败")
        
        return success
        
    except Exception as e:
        print(f"错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    main()
