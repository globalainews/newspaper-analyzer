import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime

def simple_test():
    print("=== 简单测试华尔街日报图片下载 ===\n")
    
    # 代理设置
    proxy_host = "127.0.0.1"
    proxy_port = 1080
    proxies = {
        'http': f'http://{proxy_host}:{proxy_port}',
        'https': f'http://{proxy_host}:{proxy_port}'
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    # 测试URL - 使用用户提供的具体链接
    test_urls = [
        "https://x.com/wsj",
        "https://x.com/WSJ/status/2030229522163859834"
    ]
    
    for url in test_urls:
        print(f"测试URL: {url}")
        print("-" * 50)
        
        try:
            # 测试连接
            print("1. 测试连接...")
            response = requests.get(url, headers=headers, proxies=proxies, timeout=30)
            print(f"   状态码: {response.status_code}")
            
            if response.status_code != 200:
                print("   连接失败，跳过此URL")
                continue
            
            # 解析页面
            print("2. 解析页面...")
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 查找图片
            print("3. 查找图片...")
            img_tags = soup.find_all('img')
            print(f"   找到 {len(img_tags)} 个图片标签")
            
            # 查找Twitter图片
            twitter_images = []
            for img in img_tags:
                src = img.get('src', '')
                if 'pbs.twimg.com' in src or 'twimg.com' in src:
                    twitter_images.append(src)
            
            print(f"   找到 {len(twitter_images)} 个Twitter图片")
            
            # 显示前3个图片URL
            for i, img_url in enumerate(twitter_images[:3]):
                print(f"   图片{i+1}: {img_url[:100]}...")
            
            # 尝试下载第一个图片
            if twitter_images:
                print("4. 尝试下载图片...")
                image_url = twitter_images[0]
                
                if not image_url.startswith('http'):
                    image_url = 'https:' + image_url
                
                print(f"   下载URL: {image_url[:100]}...")
                
                img_response = requests.get(image_url, headers=headers, proxies=proxies, timeout=30)
                
                if img_response.status_code == 200:
                    # 保存图片
                    today = datetime.now().strftime('%Y-%m-%d')
                    filename = f"wsj_test_{today}.jpg"
                    
                    with open(filename, 'wb') as f:
                        f.write(img_response.content)
                    
                    file_size = os.path.getsize(filename)
                    print(f"   ✓ 下载成功! 文件大小: {file_size} 字节")
                    print(f"   文件已保存为: {filename}")
                    return True
                else:
                    print(f"   ✗ 下载失败，状态码: {img_response.status_code}")
            else:
                print("   ✗ 未找到可下载的图片")
                
        except requests.exceptions.ProxyError as e:
            print(f"   ✗ 代理错误: {str(e)}")
            print("   请检查代理服务是否正在运行")
            
        except requests.exceptions.ConnectTimeout as e:
            print(f"   ✗ 连接超时: {str(e)}")
            print("   请检查网络连接")
            
        except requests.exceptions.ConnectionError as e:
            print(f"   ✗ 连接错误: {str(e)}")
            print("   请检查网络连接")
            
        except Exception as e:
            print(f"   ✗ 其他错误: {str(e)}")
        
        print()
    
    return False

def test_without_proxy():
    """测试无代理连接"""
    print("\n=== 测试无代理连接 ===\n")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    url = "https://x.com/wsj"
    
    try:
        print("1. 测试直接连接...")
        response = requests.get(url, headers=headers, timeout=10)
        print(f"   状态码: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✓ 直接连接成功")
            
            # 检查页面内容
            if "Wall Street Journal" in response.text:
                print("   ✓ 页面包含华尔街日报内容")
            else:
                print("   ⚠️ 页面可能被重定向")
                
            # 检查图片链接
            if "pbs.twimg.com" in response.text:
                print("   ✓ 页面包含Twitter图片链接")
            else:
                print("   ⚠️ 页面未找到图片链接")
                
        else:
            print(f"   ✗ 直接连接失败")
            
    except Exception as e:
        print(f"   ✗ 直接连接错误: {str(e)}")

if __name__ == "__main__":
    print("华尔街日报图片下载测试程序")
    print("=" * 60)
    
    # 测试无代理连接
    test_without_proxy()
    
    # 测试代理连接
    success = simple_test()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 测试成功! 图片下载功能正常")
    else:
        print("⚠️  测试失败，请检查代理设置和网络连接")
    print("测试完成")