#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成音色文件：从testCosyvoice.wav提取音色特征并保存为myVoice.pt
"""

import os
import sys
import torch
import torchaudio
import onnxruntime
import numpy as np
import whisper
import torchaudio.compliance.kaldi as kaldi

# 配置
COSYVOICE_ROOT_DIR = 'D:\\trea\\CosyVoice3'
MODEL_DIR = os.path.join(COSYVOICE_ROOT_DIR, 'pretrained_models/Fun-CosyVoice3-0.5B')
REFERENCE_AUDIO = os.path.join(COSYVOICE_ROOT_DIR, 'testCosyvoice.WAV')
OUTPUT_FILE = os.path.join(COSYVOICE_ROOT_DIR, 'myVoice.pt')

# 模型文件路径
CAMP_PLUS_MODEL = os.path.join(MODEL_DIR, 'campplus.onnx')
SPEECH_TOKENIZER_MODEL = os.path.join(MODEL_DIR, 'speech_tokenizer_v3.onnx')


def load_wav(wav_path, sr=16000):
    """加载音频文件"""
    audio, sample_rate = torchaudio.load(wav_path, backend='soundfile')
    if sample_rate != sr:
        audio = torchaudio.transforms.Resample(orig_freq=sample_rate, new_freq=sr)(audio)
    # 转换为单声道
    if audio.shape[0] > 1:
        audio = audio.mean(dim=0, keepdim=True)
    return audio


def extract_speech_feat(audio):
    """提取语音特征"""
    # 重采样到24000Hz
    audio_24k = torchaudio.transforms.Resample(orig_freq=16000, new_freq=24000)(audio)
    
    # 提取特征（这里使用简化的特征提取，实际应该使用模型的feat_extractor）
    # 注意：这里只是一个示例，实际需要使用与模型匹配的特征提取方法
    feat = torchaudio.compliance.kaldi.fbank(
        audio_24k,
        num_mel_bins=80,
        dither=0,
        sample_frequency=24000
    )
    feat = feat.unsqueeze(dim=0)
    feat_len = torch.tensor([feat.shape[1]], dtype=torch.int32)
    return feat, feat_len


def extract_speech_token(audio, tokenizer_session):
    """提取语音token"""
    if audio.shape[1] / 16000 > 30:
        print("警告: 音频长度超过30秒，可能会影响提取效果")
    
    feat = whisper.log_mel_spectrogram(audio, n_mels=128)
    speech_token = tokenizer_session.run(
        None, 
        {
            tokenizer_session.get_inputs()[0].name: feat.detach().cpu().numpy(),
            tokenizer_session.get_inputs()[1].name: np.array([feat.shape[2]], dtype=np.int32)
        }
    )[0].flatten().tolist()
    
    speech_token = torch.tensor([speech_token], dtype=torch.int32)
    speech_token_len = torch.tensor([speech_token.shape[1]], dtype=torch.int32)
    return speech_token, speech_token_len


def extract_spk_embedding(audio, embedding_session):
    """提取说话人嵌入"""
    feat = kaldi.fbank(
        audio,
        num_mel_bins=80,
        dither=0,
        sample_frequency=16000
    )
    feat = feat - feat.mean(dim=0, keepdim=True)
    embedding = embedding_session.run(
        None, 
        {embedding_session.get_inputs()[0].name: feat.unsqueeze(dim=0).cpu().numpy()}
    )[0].flatten().tolist()
    embedding = torch.tensor([embedding])
    return embedding


def main():
    """主函数"""
    print("=== 生成音色文件 ===")
    print(f"参考音频: {REFERENCE_AUDIO}")
    print(f"输出文件: {OUTPUT_FILE}")
    
    # 检查文件是否存在
    if not os.path.exists(REFERENCE_AUDIO):
        print(f"错误: 参考音频文件不存在: {REFERENCE_AUDIO}")
        return False
    
    if not os.path.exists(CAMP_PLUS_MODEL):
        print(f"错误: 模型文件不存在: {CAMP_PLUS_MODEL}")
        return False
    
    if not os.path.exists(SPEECH_TOKENIZER_MODEL):
        print(f"错误: 模型文件不存在: {SPEECH_TOKENIZER_MODEL}")
        return False
    
    try:
        # 加载音频
        print("加载音频文件...")
        audio = load_wav(REFERENCE_AUDIO, sr=16000)
        print(f"✓ 音频加载成功: {audio.shape}")
        
        # 初始化ONNX会话
        print("初始化模型...")
        
        # 初始化说话人嵌入模型
        option = onnxruntime.SessionOptions()
        option.graph_optimization_level = onnxruntime.GraphOptimizationLevel.ORT_ENABLE_ALL
        option.intra_op_num_threads = 1
        
        embedding_session = onnxruntime.InferenceSession(
            CAMP_PLUS_MODEL, 
            sess_options=option, 
            providers=["CPUExecutionProvider"]
        )
        
        # 初始化语音tokenizer模型
        tokenizer_session = onnxruntime.InferenceSession(
            SPEECH_TOKENIZER_MODEL, 
            sess_options=option, 
            providers=["CPUExecutionProvider"]
        )
        
        print("✓ 模型初始化成功")
        
        # 提取特征
        print("提取语音特征...")
        speech_feat, speech_feat_len = extract_speech_feat(audio)
        print(f"✓ 提取speech_feat: shape={speech_feat.shape}")
        
        print("提取语音token...")
        speech_token, speech_token_len = extract_speech_token(audio, tokenizer_session)
        print(f"✓ 提取speech_token: shape={speech_token.shape}")
        
        # 调整speech_feat和speech_token的长度，确保它们匹配
        # 参考frontend.py中的逻辑
        resample_rate = 24000  # CosyVoice3使用24000Hz
        if resample_rate == 24000:
            # force speech_feat % speech_token = 2
            token_len = min(int(speech_feat.shape[1] / 2), speech_token.shape[1])
            speech_feat = speech_feat[:, :2 * token_len]
            speech_feat_len = torch.tensor([2 * token_len], dtype=torch.int32)
            speech_token = speech_token[:, :token_len]
            speech_token_len = torch.tensor([token_len], dtype=torch.int32)
            print(f"✓ 调整后speech_feat: shape={speech_feat.shape}")
            print(f"✓ 调整后speech_token: shape={speech_token.shape}")
        
        print("提取说话人嵌入...")
        embedding = extract_spk_embedding(audio, embedding_session)
        print(f"✓ 提取embedding: shape={embedding.shape}")
        
        # 构建说话人信息字典
        speaker_info = {
            'prompt_text': torch.zeros(1, 0, dtype=torch.int32),  # 使用空张量而不是None
            'prompt_text_len': torch.tensor([0], dtype=torch.int32),  # 使用空张量长度
            'llm_prompt_speech_token': speech_token,
            'llm_prompt_speech_token_len': speech_token_len,
            'flow_prompt_speech_token': speech_token,
            'flow_prompt_speech_token_len': speech_token_len,
            'prompt_speech_feat': speech_feat,
            'prompt_speech_feat_len': speech_feat_len,
            'llm_embedding': embedding,
            'flow_embedding': embedding
        }
        
        # 确保输出目录存在
        output_dir = os.path.dirname(OUTPUT_FILE)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
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
    main()
