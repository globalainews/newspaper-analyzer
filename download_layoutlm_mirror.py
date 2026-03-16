from huggingface_hub import snapshot_download
import os

# 模型名称
model_name = "microsoft/layoutlmv3-large"

# 下载目录（使用transformers默认缓存目录）
cache_dir = os.path.expanduser("~/.cache/huggingface/hub")
print(f"模型将下载到: {cache_dir}")

# 设置国内镜像
env_vars = os.environ.copy()
env_vars['HF_ENDPOINT'] = 'https://hf-mirror.com'

print("开始下载 LayoutLMv3-large 模型...")
print("这可能需要一些时间，取决于网络速度...")

# 下载模型
try:
    # 使用国内镜像下载
    print("使用国内镜像 https://hf-mirror.com 下载模型...")
    snapshot_download(
        repo_id=model_name,
        cache_dir=cache_dir,
        force_download=True,
        ignore_patterns=["*.bin"]  # 只下载配置文件，不下载权重文件
    )
    print("✅ 模型下载成功")
except Exception as e:
    print(f"❌ 模型下载失败: {e}")

print("\n下载完成！")
print(f"模型已保存到本地缓存目录: {cache_dir}")
print("下次运行程序时，系统将直接使用本地模型，无需再次下载")
