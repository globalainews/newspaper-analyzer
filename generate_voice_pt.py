#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成音色文件：从testCosyvoice.wav提取音色特征并保存为myVoice.pt
"""

import os
import sys
import torch

# 添加CosyVoice3目录到Python路径
COSYVOICE_ROOT_DIR = 'D:\\trea\\CosyVoice3'
sys.path.insert(0, COSYVOICE_ROOT_DIR)

from cosyvoice.cli.cosyvoice import AutoModel
from cosyvoice.utils.file_utils import load_wav

# 配置
COSYVOICE_ROOT_DIR = 'D:\\trea\\CosyVoice3'
MODEL_DIR = os.path.join(COSYVOICE_ROOT_DIR, 'pretrained_models/Fun-CosyVoice3-0.5B')
REFERENCE_AUDIO = os.path.join(COSYVOICE_ROOT_DIR, 'testCosyvoice.WAV')
OUTPUT_FILE = os.path.join(COSYVOICE_ROOT_DIR, 'myVoice.pt')


def extract_speaker_info():
    """提取说话人信息并保存为pt文件"""
    print("=== 生成音色文件 ===")
    print(f"模型目录: {MODEL_DIR}")
    print(f"参考音频: {REFERENCE_AUDIO}")
    print(f"输出文件: {OUTPUT_FILE}")
    
    # 检查文件是否存在
    if not os.path.exists(REFERENCE_AUDIO):
        print(f"错误: 参考音频文件不存在: {REFERENCE_AUDIO}")
        return False
    
    if not os.path.exists(MODEL_DIR):
        print(f"错误: 模型目录不存在: {MODEL_DIR}")
        return False
    
    try:
        # 加载模型
        print("加载CosyVoice3模型...")
        cosyvoice = AutoModel(model_dir=MODEL_DIR)
        print("模型加载成功!")
        
        # 提取说话人特征
        print("提取说话人特征...")
        
        # 提取语音特征
        speech_feat, speech_feat_len = cosyvoice.frontend._extract_speech_feat(REFERENCE_AUDIO)
        print(f"✓ 提取speech_feat: shape={speech_feat.shape}")
        
        # 提取语音token
        speech_token, speech_token_len = cosyvoice.frontend._extract_speech_token(REFERENCE_AUDIO)
        print(f"✓ 提取speech_token: shape={speech_token.shape}")
        
        # 提取说话人嵌入
        embedding = cosyvoice.frontend._extract_spk_embedding(REFERENCE_AUDIO)
        print(f"✓ 提取embedding: shape={embedding.shape}")
        
        # 构建说话人信息字典
        speaker_info = {
            'prompt_text': None,  # 不需要prompt文本
            'prompt_text_len': None,
            'llm_prompt_speech_token': speech_token,
            'llm_prompt_speech_token_len': speech_token_len,
            'flow_prompt_speech_token': speech_token,
            'flow_prompt_speech_token_len': speech_token_len,
            'prompt_speech_feat': speech_feat,
            'prompt_speech_feat_len': speech_feat_len,
            'llm_embedding': embedding,
            'flow_embedding': embedding
        }
        
        # 保存为pt文件
        print(f"保存音色文件到: {OUTPUT_FILE}")
        torch.save(speaker_info, OUTPUT_FILE)
        print("✅ 音色文件生成成功!")
        
        return True
        
    except Exception as e:
        print(f"错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    extract_speaker_info()
