#!/usr/bin/env python3
"""
测试语音克隆功能
从JSON文件读取新闻数据，生成克隆语音
"""

import os
import sys
import json

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from voice_clone import VoiceCloner, clone_voices_for_draft


def load_news_from_json(json_file):
    """从JSON文件加载新闻数据"""
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 提取新闻内容
    news_list = []
    
    # 处理 news_blocks 数组
    if 'news_blocks' in data:
        for block in data['news_blocks']:
            news_list.append({
                'title': block.get('title', ''),
                'content': block.get('content', '')
            })
    
    # 处理 main_content_area
    if 'intro' in data:
        news_list.insert(0, {
            'title': '导语',
            'content': data['intro']
        })
    
    return news_list


def test_voice_clone(json_file, output_dir=None):
    """测试语音克隆功能
    
    Args:
        json_file: JSON文件路径
        output_dir: 输出目录（可选）
    
    Returns:
        bool: 是否成功
    """
    print("=" * 60)
    print("语音克隆测试程序")
    print("=" * 60)
    
    # 检查JSON文件
    if not os.path.exists(json_file):
        print(f"错误: JSON文件不存在: {json_file}")
        return False
    
    # 加载新闻数据
    print(f"\n加载新闻数据: {json_file}")
    try:
        news_list = load_news_from_json(json_file)
        print(f"成功加载 {len(news_list)} 条新闻")
        
        # 显示新闻内容
        print("\n新闻列表:")
        for i, news in enumerate(news_list):
            title = news.get('title', '')
            content = news.get('content', '')
            print(f"  [{i+1}] {title}")
            print(f"      {content[:50]}..." if len(content) > 50 else f"      {content}")
        
    except Exception as e:
        print(f"错误: 加载JSON失败: {str(e)}")
        return False
    
    # 加载配置
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    else:
        print("警告: config.json不存在，使用默认配置")
        config = {}
    
    # 创建输出目录
    if not output_dir:
        base_name = os.path.splitext(os.path.basename(json_file))[0]
        output_dir = os.path.join(os.path.dirname(__file__), 'output', base_name)
    
    os.makedirs(output_dir, exist_ok=True)
    print(f"\n输出目录: {output_dir}")
    
    # 创建语音克隆器
    print("\n初始化语音克隆器...")
    cloner = VoiceCloner(config)
    
    print(f"模型目录: {cloner.model_dir}")
    print(f"参考音频: {cloner.reference_audio}")
    print(f"语速: {cloner.speed}")
    
    # 检查参考音频
    if not os.path.exists(cloner.reference_audio):
        print(f"\n错误: 参考音频文件不存在: {cloner.reference_audio}")
        # 尝试在CosyVoice3目录下查找
        from voice_clone import COSYVOICE_ROOT_DIR
        alt_ref = os.path.join(COSYVOICE_ROOT_DIR, 'testCosyvoice.WAV')
        if os.path.exists(alt_ref):
            print(f"使用备用参考音频: {alt_ref}")
            cloner.reference_audio = alt_ref
        else:
            print("错误: 无法找到参考音频文件")
            return False
    
    # 生成语音
    print("\n" + "=" * 60)
    print("开始生成语音...")
    print("=" * 60)
    
    generated_files = cloner.generate_voices_for_news(news_list, output_dir)
    
    if generated_files:
        print(f"\n✅ 成功生成 {len(generated_files)} 个语音文件:")
        for gf in generated_files:
            print(f"   - {gf['filename']}")
        return True
    else:
        print("\n❌ 没有生成任何语音文件")
        return False


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='语音克隆测试程序')
    parser.add_argument('json_file', nargs='?', default='analysis_results/ft_2026-3-19.json', 
                        help='JSON文件路径 (默认: analysis_results/ft_2026-3-19.json)')
    parser.add_argument('-o', '--output', type=str, default=None,
                        help='输出目录 (可选)')
    
    args = parser.parse_args()
    
    # 获取JSON文件路径
    json_file = args.json_file
    if not os.path.isabs(json_file):
        json_file = os.path.join(os.path.dirname(__file__), json_file)
    
    # 运行测试
    success = test_voice_clone(json_file, args.output)
    
    if success:
        print("\n" + "=" * 60)
        print("🎉 测试完成!")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ 测试失败")
        print("=" * 60)
        sys.exit(1)


if __name__ == '__main__':
    main()
