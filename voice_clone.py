#!/usr/bin/env python3
"""
语音克隆模块 - 使用CosyVoice3生成语音
"""

import os
import sys
import json

# CosyVoice3项目根目录
COSYVOICE_ROOT_DIR = r"D:\trea\CosyVoice3"

# 添加CosyVoice3目录到Python路径
cosyvoice_dir = COSYVOICE_ROOT_DIR
if os.path.exists(cosyvoice_dir):
    sys.path.insert(0, cosyvoice_dir)
    sys.path.insert(0, os.path.join(cosyvoice_dir, 'third_party', 'Matcha-TTS'))


class ProgressBar:
    """简单的进度条"""
    
    def __init__(self, total, prefix='进度', width=50):
        self.total = total
        self.prefix = prefix
        self.width = width
        self.current = 0
    
    def update(self, current=None, message=''):
        if current is not None:
            self.current = current
        else:
            self.current += 1
        
        percent = self.current / self.total
        filled = int(self.width * percent)
        bar = '█' * filled + '░' * (self.width - filled)
        
        print(f'\r{self.prefix}: |{bar}| {self.current}/{self.total} ({percent*100:.1f}%) {message}', end='', flush=True)
        
        if self.current >= self.total:
            print()
    
    def finish(self, message=''):
        self.current = self.total
        self.update(message=message)

class VoiceCloner:
    """语音克隆器"""
    
    def __init__(self, config=None, progress_callback=None):
        """初始化语音克隆器
        
        Args:
            config: 配置字典
            progress_callback: 进度回调函数，格式为 callback(current, total, message)
        """
        self.config = config or {}
        self.cosyvoice = None
        self.sample_rate = 22050
        self.model_loaded = False
        self.progress_callback = progress_callback
        
        # 从配置获取参数
        cosyvoice_config = self.config.get('cosyvoice', {})
        
        # 处理模型目录路径（可能是相对路径或绝对路径）
        model_dir_config = cosyvoice_config.get('model_dir', '')
        if model_dir_config:
            if os.path.isabs(model_dir_config):
                # 已经是绝对路径
                self.model_dir = model_dir_config
            else:
                # 相对路径，基于CosyVoice3根目录
                self.model_dir = os.path.join(COSYVOICE_ROOT_DIR, model_dir_config)
        else:
            # 默认路径
            self.model_dir = os.path.join(COSYVOICE_ROOT_DIR, 'pretrained_models/Fun-CosyVoice3-0.5B')
        
        # 处理参考音频路径
        ref_audio_config = cosyvoice_config.get('reference_audio', '')
        if ref_audio_config:
            if os.path.isabs(ref_audio_config):
                self.reference_audio = ref_audio_config
            else:
                self.reference_audio = os.path.join(COSYVOICE_ROOT_DIR, ref_audio_config)
        else:
            self.reference_audio = os.path.join(COSYVOICE_ROOT_DIR, 'testCosyvoice.WAV')
        
        # 处理音色文件路径
        voice_file_config = cosyvoice_config.get('voice_file', '')
        if voice_file_config:
            if os.path.isabs(voice_file_config):
                self.voice_file = voice_file_config
            else:
                self.voice_file = os.path.join(COSYVOICE_ROOT_DIR, voice_file_config)
        else:
            self.voice_file = os.path.join(COSYVOICE_ROOT_DIR, 'myVoice.pt')
        
        self.speed = cosyvoice_config.get('speed', 1.3)
        self.instruct = cosyvoice_config.get('test_instruct', 'You are a helpful assistant.<|endofprompt|>')
        self.seed = cosyvoice_config.get('seed', 888)
        self.voice_loaded = False  # 音色文件加载状态
    
    def _report_progress(self, current, total, message=''):
        """报告进度"""
        if self.progress_callback:
            self.progress_callback(current, total, message)
        else:
            # 默认使用进度条
            if not hasattr(self, '_progress_bar'):
                self._progress_bar = ProgressBar(total)
            self._progress_bar.update(current, message)
    
    def load_model(self):
        """加载CosyVoice3模型"""
        if self.model_loaded:
            return True
        
        try:
            print("正在加载CosyVoice3模型...")
            
            # 检查模型目录
            if not os.path.exists(self.model_dir):
                print(f"错误: 模型目录不存在: {self.model_dir}")
                return False
            
            # 导入CosyVoice模块
            from cosyvoice.cli.cosyvoice import AutoModel
            import torchaudio
            
            # 加载模型
            self.cosyvoice = AutoModel(model_dir=self.model_dir)
            self.sample_rate = self.cosyvoice.sample_rate
            self.model_loaded = True
            
            # 设置随机种子以保持生成风格一致（只设置一次）
            import torch
            torch.manual_seed(self.seed)
            torch.cuda.manual_seed_all(self.seed)  # 如果使用GPU
            
            print(f"模型加载成功! 采样率: {self.sample_rate}, 语速: {self.speed}, 随机种子: {self.seed}")

            # 尝试加载音色文件
            self.load_voice_file()

            # 预热模型（运行一次推理以稳定模型状态）
            print("正在预热模型...")
            try:
                warmup_text = "今天天气不错"
                import tempfile
                warmup_output = os.path.join(tempfile.gettempdir(), "_cosyvoice_warmup.wav")
                self.generate_voice(warmup_text, warmup_output, silent=True, text_frontend=False)
                print("模型预热完成")
            except Exception as e:
                print(f"模型预热时出现警告: {e}")
            
            # 移除模型加载完成对话窗
            # try:
            #     import tkinter as tk
            #     from tkinter import messagebox
            #     
            #     # 创建一个临时的tk根窗口
            #     root = tk.Tk()
            #     root.withdraw()  # 隐藏主窗口
            #     
            #     # 显示信息框
            #     messagebox.showinfo("模型加载", "CosyVoice3模型加载完成\n点击OK开始生成音频")
            #     
            #     root.destroy()
            # except Exception as e:
            #     # 如果tkinter有问题，继续执行
            #     print(f"显示对话窗失败: {e}")
            
            return True
            
        except ImportError as e:
            print(f"错误: 缺少依赖包: {e}")
            print("请运行: pip install -r requirements.txt")
            return False
        except Exception as e:
            print(f"加载模型失败: {str(e)}")
            return False
    
    def load_voice_file(self):
        """
        加载音色文件（myVoice.pt）
        
        Returns:
            bool: 是否成功
        """
        if not self.model_loaded:
            return False
        
        try:
            if os.path.exists(self.voice_file):
                print(f"正在加载音色文件: {self.voice_file}")
                import torch
                voice_info = torch.load(self.voice_file, map_location=self.cosyvoice.frontend.device)
                
                # 确保所有必要的字段都存在且不是None
                # 对于prompt_text和prompt_text_len，使用包含<|endofprompt|>的张量
                if voice_info.get('prompt_text') is None or voice_info['prompt_text'].numel() == 0:
                    # 生成包含<|endofprompt|>的prompt_text
                    endofprompt_text = 'You are a helpful assistant.<|endofprompt|>'
                    prompt_text_token, _ = self.cosyvoice.frontend._extract_text_token(endofprompt_text)
                    voice_info['prompt_text'] = prompt_text_token
                    voice_info['prompt_text_len'] = torch.tensor([prompt_text_token.shape[1]], dtype=torch.int32).to(self.cosyvoice.frontend.device)
                
                # 确保其他必要字段存在
                required_fields = ['llm_prompt_speech_token', 'llm_prompt_speech_token_len', 
                                 'flow_prompt_speech_token', 'flow_prompt_speech_token_len', 
                                 'prompt_speech_feat', 'prompt_speech_feat_len', 
                                 'llm_embedding', 'flow_embedding']
                for field in required_fields:
                    if field not in voice_info or voice_info[field] is None:
                        print(f"警告: 音色文件缺少字段: {field}")
                        self.voice_loaded = False
                        return False
                
                # 将音色信息添加到spk2info中
                spk_id = 'my_voice'
                self.cosyvoice.frontend.spk2info[spk_id] = voice_info
                self.voice_loaded = True
                print("✅ 音色文件加载成功!")
                return True
            else:
                print(f"警告: 音色文件不存在: {self.voice_file}")
                print("将使用参考音频进行零样本克隆")
                self.voice_loaded = False
                return False
        except Exception as e:
            print(f"加载音色文件失败: {str(e)}")
            self.voice_loaded = False
            return False

    def generate_voice(self, text, output_file, reference_audio=None, speed=None, silent=False, text_frontend=False, zero_shot_spk_id='', instruct=None):
        """
        生成单个语音文件
        
        Args:
            text: 要合成的文本
            output_file: 输出文件路径
            reference_audio: 参考音频文件路径（可选，默认使用配置中的）
            speed: 语速（可选，默认使用配置中的）
            silent: 是否静默模式（不打印日志）
            text_frontend: 是否使用文本前端处理（默认False，避免前端分开）
            zero_shot_spk_id: 零样本说话人ID（可选）
            instruct: 微调指令文本（可选，默认使用配置中的）
        
        Returns:
            bool: 是否成功
        """
        if not self.model_loaded:
            if not self.load_model():
                return False
        
        try:
            import torch
            import torchaudio

            # 使用传入的参数或默认值
            ref_audio = reference_audio or self.reference_audio
            voice_speed = speed or self.speed

            # 检查参考音频文件
            if not os.path.exists(ref_audio):
                if not silent:
                    print(f"错误: 参考音频文件不存在: {ref_audio}")
                return False

            if not silent:
                print(f"正在生成语音: '{text[:50]}...'")
                print(f"  语速参数: {voice_speed}")
                print(f"  随机种子: {self.seed}")

            # 每次生成前重置随机种子，确保风格一致性
            import torch
            import numpy as np
            torch.manual_seed(self.seed)
            torch.cuda.manual_seed_all(self.seed)
            try:
                np.random.seed(self.seed)
            except Exception:
                pass

            # 直接处理整个文本，不进行分割
            from cosyvoice.cli.frontend import CosyVoiceFrontEnd
            
            # 前端处理
            tts_text = text
            import re
            tts_text = re.sub(r'[""'']', '', tts_text)
            if text_frontend:
                # 直接调用frontend的text_normalize但不分割
                normalized_text = self.cosyvoice.frontend.text_normalize(tts_text, split=False, text_frontend=text_frontend)
            else:
                # 即使不使用前端处理，也确保文本是字符串格式
                normalized_text = str(tts_text)

            # 检查文本长度
            if len(normalized_text) > 1000:
                if not silent:
                    print(f"警告: 文本长度较长 ({len(normalized_text)} 字符)，可能会影响生成质量")
            
            # 生成语音
            # 确定使用的instruct文本
            use_instruct = instruct if instruct is not None else self.instruct

            all_speech = []

            # 准备模型输入
            if self.voice_loaded:
                # 使用加载的音色文件
                model_input = self.cosyvoice.frontend.frontend_instruct2(
                    normalized_text,
                    use_instruct,
                    ref_audio,  # 虽然使用音色文件，但仍需要参考音频路径（可能是模型要求）
                    self.cosyvoice.sample_rate,
                    zero_shot_spk_id='my_voice'  # 使用加载的音色
                )
            else:
                # 使用参考音频进行零样本克隆
                model_input = self.cosyvoice.frontend.frontend_instruct2(
                    normalized_text,
                    use_instruct,
                    ref_audio,
                    self.cosyvoice.sample_rate,
                    zero_shot_spk_id=zero_shot_spk_id
                )
            
            # 检查模型输入
            if not silent:
                text_token = model_input.get('text', None)
                if text_token is not None:
                    print(f"文本编码长度: {text_token.shape[1]}  tokens")
            
            # 生成语音
            for model_output in self.cosyvoice.model.tts(**model_input, stream=False, speed=voice_speed):
                speech = model_output['tts_speech']
                all_speech.append(speech)
                if not silent:
                    print(f"生成语音片段: {speech.shape[1]}  samples")
            
            # 合并语音片段（如果有的话）
            if all_speech:
                merged_speech = torch.cat(all_speech, dim=1)
                
                if not silent:
                    print(f"合并后语音长度: {merged_speech.shape[1]}  samples")
                    print(f"预计时长: {merged_speech.shape[1] / self.sample_rate:.2f} 秒")
                
                # 确保输出目录存在
                output_dir = os.path.dirname(output_file)
                if output_dir and not os.path.exists(output_dir):
                    os.makedirs(output_dir)
                
                # 保存音频文件
                torchaudio.save(output_file, merged_speech, self.sample_rate)
                total_duration = merged_speech.shape[1] / self.sample_rate
                
                if not silent:
                    print(f"语音已保存到: {output_file}")
                    print(f"总时长: {total_duration:.2f} 秒")
                return True
            else:
                if not silent:
                    print("错误: 未生成语音")
                return False
                
        except Exception as e:
            if not silent:
                print(f"生成语音失败: {str(e)}")
                import traceback
                traceback.print_exc()
            return False
    
    def generate_voices_for_news(self, news_list, output_dir, reference_audio=None, speed=None, text_frontend=False, instruct=None):
        """
        为新闻列表批量生成语音
        
        Args:
            news_list: 新闻列表，每个元素是包含'content'字段的字典
            output_dir: 输出目录（textReading目录）
            reference_audio: 参考音频文件路径（可选）
            speed: 语速（可选）
            text_frontend: 是否使用文本前端处理（默认False，避免前端分开）
            instruct: 微调指令文本（可选）
        
        Returns:
            list: 生成的音频文件列表
        """
        if not self.model_loaded:
            if not self.load_model():
                return []
        
        generated_files = []
        
        # 确保输出目录存在
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"创建输出目录: {output_dir}")
        
        total_news = len(news_list)
        print(f"\n开始批量生成语音，共 {total_news} 条新闻...")
        print("=" * 60)
        
        # 初始化进度
        self._report_progress(0, total_news + 1, "准备生成测试音频...")
        
        # 添加测试音频
        print("[测试] 生成测试音频...")
        test_output_file = os.path.join(output_dir, "test_audio.wav")
        test_content = "今天的天气不错啊"
        
        # 生成测试音频（暂时关闭静默模式以查看错误信息）
        test_success = self.generate_voice(test_content, test_output_file, reference_audio, speed, silent=False, text_frontend=text_frontend, instruct=instruct)
        
        if test_success:
            print("[测试] 测试音频生成成功: test_audio.wav")
        else:
            print("[测试] 测试音频生成失败")
        
        # 测试音频完成，更新进度
        self._report_progress(1, total_news + 1, "测试音频生成完成")
        
        # 为每条新闻生成语音
        for i, news in enumerate(news_list):
            content = news.get('content', '')
            audio_filename = f"audio{i+1:02d}.wav"
            
            if not content:
                self._report_progress(i + 2, total_news + 1, f'{audio_filename} - 跳过(内容为空)')
                continue
            
            output_file = os.path.join(output_dir, audio_filename)
            
            # 更新进度
            self._report_progress(i + 2, total_news + 1, f'正在生成 {audio_filename} (speed={self.speed}, seed={self.seed})...')
            
            # 生成语音（静默模式，避免干扰进度条）
            success = self.generate_voice(content, output_file, reference_audio, speed, silent=True, text_frontend=text_frontend, instruct=instruct)
            
            if success:
                generated_files.append({
                    'index': i + 1,
                    'filename': audio_filename,
                    'path': output_file,
                    'content': content
                })
                # 更新进度条显示完成状态
                self._report_progress(i + 2, total_news + 1, f'{audio_filename} ✓')
            else:
                self._report_progress(i + 2, total_news + 1, f'{audio_filename} ✗ 失败')
        
        print("\n" + "=" * 60)
        print(f"批量语音生成完成! 成功: {len(generated_files)}/{total_news}")

        return generated_files


    def generate_voice_file(self, reference_audio, output_file):
        """
        从参考音频生成音色文件（.pt）
        
        Args:
            reference_audio: 参考音频文件路径
            output_file: 输出音色文件路径（.pt）
        
        Returns:
            bool: 是否成功
        """
        if not self.model_loaded:
            if not self.load_model():
                return False
        
        try:
            import torch
            
            # 检查参考音频文件
            if not os.path.exists(reference_audio):
                print(f"错误: 参考音频文件不存在: {reference_audio}")
                return False
            
            print(f"正在从参考音频生成音色文件: {reference_audio}")
            
            # 提取语音特征
            speech_feat, speech_feat_len = self.cosyvoice.frontend._extract_speech_feat(reference_audio)
            print(f"✓ 提取speech_feat: shape={speech_feat.shape}")
            
            # 提取语音token
            speech_token, speech_token_len = self.cosyvoice.frontend._extract_speech_token(reference_audio)
            print(f"✓ 提取speech_token: shape={speech_token.shape}")
            
            # 提取说话人嵌入
            embedding = self.cosyvoice.frontend._extract_spk_embedding(reference_audio)
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
            
            # 确保输出目录存在
            output_dir = os.path.dirname(output_file)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            # 保存为pt文件
            print(f"保存音色文件到: {output_file}")
            torch.save(speaker_info, output_file)
            print("✅ 音色文件生成成功!")
            
            return True
            
        except Exception as e:
            print(f"生成音色文件失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False


# 全局VoiceCloner实例
_cosyvoice_cloner = None

def get_cosyvoice_cloner(config=None, progress_callback=None):
    """获取或创建全局VoiceCloner实例"""
    global _cosyvoice_cloner
    if _cosyvoice_cloner is None:
        _cosyvoice_cloner = VoiceCloner(config, progress_callback)
    return _cosyvoice_cloner


def clone_voices_for_draft(draft_dir, news_list, config=None, reference_audio=None, progress_callback=None, text_frontend=False, instruct=None):
    """
    为剪映草稿生成语音文件
    
    Args:
        draft_dir: 剪映草稿目录
        news_list: 新闻列表
        config: 配置字典（可选）
        reference_audio: 参考音频文件路径（可选）
        progress_callback: 进度回调函数（可选）
        text_frontend: 是否使用文本前端处理（默认False，避免前端分开）
        instruct: 微调指令文本（可选）
    
    Returns:
        list: 生成的音频文件列表
    """
    # 检查草稿目录
    if not os.path.exists(draft_dir):
        print(f"错误: 草稿目录不存在: {draft_dir}")
        return []
    
    # 检查textReading目录
    text_reading_dir = os.path.join(draft_dir, 'textReading')
    if not os.path.exists(text_reading_dir):
        os.makedirs(text_reading_dir)
        print(f"创建textReading目录: {text_reading_dir}")

    # 获取全局语音克隆器实例
    cloner = get_cosyvoice_cloner(config, progress_callback)

    # 更新参考音频（如果指定了，需要转换为绝对路径）
    if reference_audio:
        if os.path.isabs(reference_audio):
            cloner.reference_audio = reference_audio
        else:
            cloner.reference_audio = os.path.join(COSYVOICE_ROOT_DIR, reference_audio)

    # 如果没有指定参考音频，使用默认路径
    if not cloner.reference_audio:
        default_ref = os.path.join(COSYVOICE_ROOT_DIR, 'testCosyvoice.WAV')
        if os.path.exists(default_ref):
            cloner.reference_audio = default_ref
        else:
            print(f"错误: 找不到参考音频文件: {default_ref}")
            return []

    # 生成语音
    return cloner.generate_voices_for_news(news_list, text_reading_dir, speed=cloner.speed, text_frontend=text_frontend, instruct=instruct)


if __name__ == '__main__':
    # 测试代码
    print("=== 语音克隆模块测试 ===")
    print(f"CosyVoice3根目录: {COSYVOICE_ROOT_DIR}")
    
    # 测试配置
    test_config = {
        'cosyvoice': {
            'model_dir': os.path.join(COSYVOICE_ROOT_DIR, 'pretrained_models/Fun-CosyVoice3-0.5B'),
            'reference_audio': os.path.join(COSYVOICE_ROOT_DIR, 'testCosyvoice.WAV'),
            'speed': 1.3
        }
    }
    
    # 创建克隆器
    cloner = VoiceCloner(test_config)
    
    # 测试生成单个语音
    test_text = "这是一段测试文本，用于验证语音克隆功能。"
    test_output = "test_output.wav"
    
    print(f"\n测试文本: {test_text}")
    print(f"输出文件: {test_output}")
    
    # 注意：需要先加载模型才能生成语音
    # success = cloner.generate_voice(test_text, test_output)
    # if success:
    #     print("测试成功!")
    # else:
    #     print("测试失败!")
