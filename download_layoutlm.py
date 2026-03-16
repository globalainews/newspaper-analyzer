from transformers import AutoProcessor, AutoModelForDocumentQuestionAnswering
import os
import json
import os

# 加载配置文件
def load_config(config_file='config.json'):
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except Exception as e:
        print(f"加载配置文件失败: {e}")
        return {}

# 模型名称
model_name = "microsoft/layoutlmv3-large-chinese"

# 加载配置
config = load_config()

# 设置代理
proxy_config = config.get('gemini', {}).get('proxy', {})
proxy_host = proxy_config.get('host', '127.0.0.1')
proxy_port = proxy_config.get('port', 1080)

# 设置环境变量
os.environ['HTTP_PROXY'] = f'http://{proxy_host}:{proxy_port}'
os.environ['HTTPS_PROXY'] = f'http://{proxy_host}:{proxy_port}'

print(f"使用代理: http://{proxy_host}:{proxy_port}")

# 下载目录（使用transformers默认缓存目录）
cache_dir = os.path.expanduser("~/.cache/huggingface/hub")
print(f"模型将下载到: {cache_dir}")

print("开始下载 LayoutLMv3-large-chinese 模型...")
print("这可能需要一些时间，取决于网络速度...")

# 下载处理器
print("\n1. 下载处理器 (processor)...")
try:
    processor = AutoProcessor.from_pretrained(model_name, cache_dir=cache_dir)
    print("✅ 处理器下载成功")
except Exception as e:
    print(f"❌ 处理器下载失败: {e}")

# 下载模型
print("\n2. 下载模型 (model)...")
try:
    model = AutoModelForDocumentQuestionAnswering.from_pretrained(model_name, cache_dir=cache_dir)
    print("✅ 模型下载成功")
except Exception as e:
    print(f"❌ 模型下载失败: {e}")

print("\n下载完成！")
print(f"模型已保存到本地缓存目录: {cache_dir}")
print("下次运行程序时，系统将直接使用本地模型，无需再次下载")
