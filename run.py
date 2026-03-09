#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
报纸头版下载与分析工具 - 命令行启动文件
"""

import sys
import os

# 添加当前目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# 导入主程序
from main import NewspaperApp
import tkinter as tk

def main():
    """启动GUI主函数"""
    print("=" * 60)
    print("  报纸头版下载与分析工具")
    print("=" * 60)
    print()
    print("正在启动图形界面...")
    print("按 Ctrl+C 退出")
    print()
    
    try:
        root = tk.Tk()
        app = NewspaperApp(root)
        root.mainloop()
    except KeyboardInterrupt:
        print("\n程序已退出")
    except Exception as e:
        print(f"\n启动失败: {e}")
        input("按回车键退出...")

if __name__ == "__main__":
    main()
