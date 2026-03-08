import requests
import os
import re
from datetime import datetime

def simple_download():
    """最简单的下载方法 - 绕过复杂逻辑"""
    
    print("最简单的华尔街日报图片下载器")
    print("=" * 60)
    
    # 直接使用用户提供的推文链接
    tweet_url = "https://x.com/WSJ/status/2030229522163859834"
    
    # 简单的headers
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        print("1. 获取页面内容...")
        
        # 直接请求，不设置代理
        response = requests.get(tweet_url, headers=headers, timeout=30)
        
        print(f"   状态码: {response.status_code}")
        print(f"   内容长度: {len(response.text)} 字节")
        
        if response.status_code != 200:
            print("   页面访问失败")
            return False
        
        # 检查页面内容
        if "Wall Street Journal" in response.text:
            print("   ✓ 页面包含华尔街日报内容")
        else:
            print("   ⚠️ 页面内容可能已改变")
        
        # 使用正则表达式查找图片URL
        print("\n2. 查找图片URL...")
        
        # 多种图片URL模式
        patterns = [
            r'https://pbs\.twimg\.com/media/[A-Za-z0-9_-]+\.(jpg|png|jpeg)[^"]*',
            r'src="([^"]*pbs\.twimg\.com/media/[^"]*)"',
            r'data-src="([^"]*pbs\.twimg\.com/media/[^"]*)"'
        ]
        
        all_urls = []
        for pattern in patterns:
            matches = re.findall(pattern, response.text)
            if matches:
                # 处理不同类型的匹配结果
                if isinstance(matches[0], tuple):
                    matches = [m[0] if isinstance(m, tuple) else m for m in matches]
                all_urls.extend(matches)
        
        # 去重
        image_urls = list(set(all_urls))
        
        print(f"   找到 {len(image_urls)} 个图片URL")
        
        if not image_urls:
            print("   未找到图片URL，尝试备选方法...")
            return alternative_method()
        
        # 显示找到的URL
        for i, url in enumerate(image_urls):
            print(f"   URL{i+1}: {url[:80]}...")
        
        # 选择第一个URL下载
        image_url = image_urls[0]
        
        # 确保URL完整
        if not image_url.startswith('http'):
            image_url = 'https:' + image_url
        
        print(f"\n3. 下载图片: {image_url[:100]}...")
        
        # 下载图片
        img_response = requests.get(image_url, headers=headers, timeout=30)
        
        print(f"   图片状态码: {img_response.status_code}")
        
        if img_response.status_code != 200:
            print("   图片下载失败")
            return False
        
        # 检查图片内容
        content_length = len(img_response.content)
        print(f"   图片大小: {content_length} 字节")
        
        if content_length < 1000:
            print("   图片内容过小，可能不是有效图片")
            return False
        
        # 保存图片
        today = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        filename = f"wsj_front_page_{today}.jpg"
        
        with open(filename, 'wb') as f:
            f.write(img_response.content)
        
        file_size = os.path.getsize(filename)
        
        print(f"\n🎉 下载成功!")
        print(f"   文件大小: {file_size} 字节")
        print(f"   文件路径: {os.path.abspath(filename)}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")
        return False

def alternative_method():
    """备选方法 - 直接构造URL"""
    
    print("\n备选方法: 直接构造图片URL")
    print("-" * 50)
    
    # 基于常见的Twitter图片URL模式
    base_urls = [
        "https://pbs.twimg.com/media/GgABCDEFG?format=jpg&name=large",
        "https://pbs.twimg.com/media/F123456789?format=jpg&name=orig",
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    # 这里无法直接构造有效URL，需要实际页面内容
    print("   需要实际页面内容来构造有效URL")
    return False

def test_network():
    """测试网络连接"""
    
    print("网络连接测试")
    print("-" * 50)
    
    try:
        # 测试基本网络连接
        response = requests.get("https://httpbin.org/ip", timeout=10)
        print(f"   网络连接: ✓ (IP: {response.json()['origin']})")
        
        # 测试X网站可访问性
        response = requests.get("https://x.com", timeout=10)
        print(f"   X网站访问: ✓ (状态码: {response.status_code})")
        
        return True
        
    except Exception as e:
        print(f"   网络测试失败: {e}")
        return False

if __name__ == "__main__":
    print("华尔街日报图片下载器 - 最终调试版本")
    print("=" * 60)
    
    # 测试网络连接
    network_ok = test_network()
    
    if network_ok:
        print("\n网络连接正常，开始下载...")
        success = simple_download()
    else:
        print("\n网络连接失败，无法继续")
        success = False
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 程序执行成功!")
        print("\n下一步:")
        print("1. 检查下载的图片文件")
        print("2. 如果图片有效，可以运行主程序")
        print("3. 如果仍有问题，可能需要调整网络设置")
    else:
        print("❌ 程序执行失败")
        print("\n可能的原因:")
        print("1. 网络连接问题")
        print("2. 页面结构已改变")
        print("3. 需要代理或VPN")
        print("4. 网站访问限制")
    
    print("\n调试完成")