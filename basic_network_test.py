import requests
import socket

def test_basic_network():
    print("=== 基本网络连接测试 ===\n")
    
    # 测试1: 检查网络连通性
    print("1. 测试网络连通性...")
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=5)
        print("   ✓ 网络连接正常")
    except:
        print("   ✗ 网络连接失败")
    
    # 测试2: 测试代理服务
    print("\n2. 测试代理服务...")
    proxy_host = "127.0.0.1"
    proxy_port = 1080
    
    try:
        # 检查代理端口是否开放
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((proxy_host, proxy_port))
        sock.close()
        
        if result == 0:
            print("   ✓ 代理端口 1080 已开放")
        else:
            print("   ✗ 代理端口 1080 未开放")
            print("   请确保代理服务正在运行")
    except Exception as e:
        print(f"   ✗ 代理测试错误: {e}")
    
    # 测试3: 测试HTTP请求
    print("\n3. 测试HTTP请求...")
    
    # 测试无代理
    print("   a) 无代理请求:")
    try:
        response = requests.get("http://httpbin.org/ip", timeout=10)
        print(f"     状态码: {response.status_code}")
        print(f"     IP地址: {response.json()['origin']}")
    except Exception as e:
        print(f"     失败: {e}")
    
    # 测试有代理
    print("   b) 有代理请求:")
    proxies = {
        'http': f'http://{proxy_host}:{proxy_port}',
        'https': f'http://{proxy_host}:{proxy_port}'
    }
    
    try:
        response = requests.get("http://httpbin.org/ip", proxies=proxies, timeout=10)
        print(f"     状态码: {response.status_code}")
        print(f"     代理IP: {response.json()['origin']}")
    except Exception as e:
        print(f"     失败: {e}")
        print("     请检查代理设置")

def test_x_access():
    print("\n=== 测试X网站访问 ===\n")
    
    proxy_host = "127.0.0.1"
    proxy_port = 1080
    proxies = {
        'http': f'http://{proxy_host}:{proxy_port}',
        'https': f'http://{proxy_host}:{proxy_port}'
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    urls = [
        "https://x.com/wsj",
        "https://x.com/WSJ/status/2030229522163859834"
    ]
    
    for url in urls:
        print(f"测试URL: {url}")
        
        # 测试无代理
        print("   无代理:")
        try:
            response = requests.get(url, headers=headers, timeout=10)
            print(f"     状态码: {response.status_code}")
            if response.status_code == 200:
                print("     页面访问成功")
                # 检查页面内容
                if "wsj" in response.text.lower() or "wall street journal" in response.text.lower():
                    print("     页面包含WSJ内容")
                if "pbs.twimg.com" in response.text:
                    print("     页面包含图片链接")
            else:
                print("     页面访问失败")
        except Exception as e:
            print(f"     错误: {e}")
        
        # 测试有代理
        print("   有代理:")
        try:
            response = requests.get(url, headers=headers, proxies=proxies, timeout=30)
            print(f"     状态码: {response.status_code}")
            if response.status_code == 200:
                print("     页面访问成功")
                # 检查页面内容
                if "wsj" in response.text.lower() or "wall street journal" in response.text.lower():
                    print("     页面包含WSJ内容")
                if "pbs.twimg.com" in response.text:
                    print("     页面包含图片链接")
                    
                    # 尝试提取图片URL
                    import re
                    img_urls = re.findall(r'https://pbs\.twimg\.com/media/[^"]+', response.text)
                    if img_urls:
                        print(f"     找到 {len(img_urls)} 个图片URL")
                        for i, img_url in enumerate(img_urls[:2]):
                            print(f"       图片{i+1}: {img_url[:80]}...")
            else:
                print("     页面访问失败")
        except Exception as e:
            print(f"     错误: {e}")
        
        print()

if __name__ == "__main__":
    print("华尔街日报下载器网络诊断工具")
    print("=" * 60)
    
    test_basic_network()
    test_x_access()
    
    print("\n诊断完成")
    print("=" * 60)
    print("\n建议:")
    print("1. 确保代理服务正在运行")
    print("2. 检查代理端口设置是否正确")
    print("3. 如果代理不可用，可能需要其他网络解决方案")