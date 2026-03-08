# 测试新虚拟环境的脚本
import sys
print("Python版本:", sys.version)
print("Python路径:", sys.executable)

# 测试tkinter
try:
    import tkinter
    print("✓ tkinter导入成功")
except ImportError as e:
    print("✗ tkinter导入失败:", e)

# 测试requests
try:
    import requests
    print("✓ requests导入成功")
except ImportError as e:
    print("✗ requests导入失败:", e)

# 测试PIL
try:
    from PIL import Image
    print("✓ PIL导入成功")
except ImportError as e:
    print("✗ PIL导入失败:", e)

# 测试google.generativeai
try:
    import google.generativeai
    print("✓ google.generativeai导入成功")
except ImportError as e:
    print("✗ google.generativeai导入失败:", e)

print("\n环境测试完成")