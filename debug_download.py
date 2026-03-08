import requests
import sys

def debug_connection():
    print("=== 调试网络连接 ===")
    
    proxy_port = 1080
    proxies = {
        'http': f'http://127.0.0.1:{proxy_port}',
        'https': f'http://127.0.0.1:{proxy_port}'
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    url = "https://x.com/wsj"
    
    print(f"目标URL: {url}")
    print(f"代理设置: {proxies}")
    
    try:
        print("\n1. 测试直接连接（无代理）...")
        response = requests.get(url, headers=headers, timeout=10)
        print(f"   状态码: {response.status_code}")
        print(f"   响应大小: {len(response.text)} 字节")
    except Exception as e:
        print(f"   直接连接失败: {str(e)}")
    
    try:
        print("\n2. 测试代理连接...")
        response = requests.get(url, headers=headers, proxies=proxies, timeout=30)
        print(f"   状态码: {response.status_code}")
        print(f"   响应大小: {len(response.text)} 字节")
        
        if response.status_code == 200:
            print("   连接成功!")
            
            # 检查页面内容
            if "Wall Street Journal" in response.text:
                print("   页面包含华尔街日报相关内容")
            else:
                print("   页面可能被重定向或需要登录")
                
            # 检查是否有图片链接
            if "pbs.twimg.com" in response.text:
                print("   页面包含Twitter图片链接")
            else:
                print("   页面未找到图片链接")
                
        else:
            print(f"   连接失败，状态码: {response.status_code}")
            
    except requests.exceptions.ProxyError as e:
        print(f"   代理连接失败: {str(e)}")
        print("   请检查代理服务是否正在运行")
        
    except requests.exceptions.ConnectTimeout as e:
        print(f"   连接超时: {str(e)}")
        print("   请检查网络连接和代理设置")
        
    except requests.exceptions.ConnectionError as e:
        print(f"   连接错误: {str(e)}")
        print("   请检查网络连接")
        
    except Exception as e:
        print(f"   其他错误: {str(e)}")

if __name__ == "__main__":
    debug_connection()
    print("\n调试完成")