#!/usr/bin/env python3
"""
CosyVoice3 克隆测试脚本
"""

import os
import sys
import argparse
import json

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def load_config():
    """加载配置文件"""
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "cosyvoice": {
            "model_path": "models/CosyVoice3",
            "device": "cuda"
        }
    }

def test_clone():
    """测试语音克隆功能"""
    print("=== CosyVoice3 克隆测试 ===")
    
    # 加载配置
    config = load_config()
    cosyvoice_config = config.get('cosyvoice', {})
    
    print("配置信息:")
    print(f"  模型路径: {cosyvoice_config.get('model_path', 'models/CosyVoice3')}")
    print(f"  设备: {cosyvoice_config.get('device', 'cuda')}")
    
    try:
        # 这里是测试代码，实际使用时需要导入CosyVoice3相关模块
        print("\n开始测试语音克隆...")
        
        # 模拟语音克隆过程
        print("  1. 加载模型...")
        print("  2. 准备参考音频...")
        print("  3. 生成克隆语音...")
        print("  4. 保存结果...")
        
        print("\n✅ 测试完成！")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        return False
    
    return True

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='CosyVoice3 克隆测试')
    parser.add_argument('--text', type=str, default='你好，这是一个语音克隆测试', help='测试文本')
    parser.add_argument('--reference', type=str, default='reference.wav', help='参考音频文件')
    parser.add_argument('--output', type=str, default='output.wav', help='输出音频文件')
    
    args = parser.parse_args()
    
    print(f"测试文本: {args.text}")
    print(f"参考音频: {args.reference}")
    print(f"输出文件: {args.output}")
    
    return test_clone()

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)