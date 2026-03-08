import requests
import os
from datetime import datetime

def download_wsj_front_page():
    """最小化的华尔街日报首页下载器"""
    
    print("华尔街日报首页下载器 - 最小化版本")
    print("=" * 50)
    
    # 使用用户提供的具体链接
    tweet_url = "https://x.com/WSJ/status/2030229522163859834"
    
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
    
    try:
        print("1. 访问推文页面...")
        
        # 尝试有代理连接
        try:
            response = requests.get(tweet_url, headers=headers, proxies=proxies, timeout=30)
            print(f"   代理连接状态码: {response.status_code}")
        except:
            # 如果代理失败，尝试无代理
            print("   代理连接失败，尝试无代理连接...")
            response = requests.get(tweet_url, headers=headers, timeout=30)
            print(f"   无代理连接状态码: {response.status_code}")
        
        if response.status_code != 200:
            print(f"   页面访问失败")
            return False
        
        print("   页面访问成功")
        
        # 查找图片URL - 使用正则表达式直接提取
        import re
        
        # 查找图片URL模式
        img_patterns = [
            r'https://pbs\.twimg\.com/media/[^"]+',
            r'src="([^"]*pbs\.twimg\.com[^"]*)"',
            r'data-src="([^"]*pbs\.twimg\.com[^"]*)"'
        ]
        
        image_urls = []
        for pattern in img_patterns:
            matches = re.findall(pattern, response.text)
            image_urls.extend(matches)
        
        # 去重
        image_urls = list(set(image_urls))
        
        print(f"   找到 {len(image_urls)} 个图片URL")
        
        if not image_urls:
            print("   未找到图片URL")
            return False
        
        # 显示找到的图片URL
        for i, url in enumerate(image_urls[:3]):
            print(f"   图片{i+1}: {url[:80]}...")
        
        # 选择第一个图片URL进行下载
        image_url = image_urls[0]
        
        # 确保URL完整
        if not image_url.startswith('http'):
            image_url = 'https:' + image_url
        
        print(f"\n2. 下载图片: {image_url[:100]}...")
        
        # 下载图片
        try:
            img_response = requests.get(image_url, headers=headers, proxies=proxies, timeout=30)
        except:
            # 如果代理失败，尝试无代理
            img_response = requests.get(image_url, headers=headers, timeout=30)
        
        if img_response.status_code != 200:
            print(f"   图片下载失败，状态码: {img_response.status_code}")
            return False
        
        # 保存图片
        today = datetime.now().strftime('%Y-%m-%d')
        filename = f"wsj_front_page_{today}.jpg"
        
        with open(filename, 'wb') as f:
            f.write(img_response.content)
        
        file_size = os.path.getsize(filename)
        
        print(f"\n🎉 下载成功!")
        print(f"   文件大小: {file_size} 字节")
        print(f"   保存位置: {os.path.abspath(filename)}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")
        return False

def alternative_download_method():
    """备选下载方法 - 直接使用已知的图片URL模式"""
    
    print("\n备选方法: 直接构造图片URL")
    print("-" * 50)
    
    # 基于用户提供的推文ID构造图片URL
    tweet_id = "2030229522163859834"
    
    # 常见的Twitter图片URL模式
    image_url_patterns = [
        f"https://pbs.twimg.com/media/F{tweet_id}?format=jpg&name=large",
        f"https://pbs.twimg.com/media/F{tweet_id}?format=jpg&name=orig",
        f"https://pbs.twimg.com/media/F{tweet_id}?format=jpg",
        f"https://pbs.twimg.com/media/G{tweet_id}?format=jpg&name=large",
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    for i, image_url in enumerate(image_url_patterns):
        print(f"尝试模式 {i+1}: {image_url}")
        
        try:
            response = requests.get(image_url, headers=headers, timeout=10)
            
            if response.status_code == 200 and len(response.content) > 1000:
                # 保存图片
                today = datetime.now().strftime('%Y-%m-%d')
                filename = f"wsj_direct_{today}.jpg"
                
                with open(filename, 'wb') as f:
                    f.write(response.content)
                
                file_size = os.path.getsize(filename)
                print(f"   ✓ 下载成功! 大小: {file_size} 字节")
                print(f"   文件: {filename}")
                return True
            else:
                print(f"   ✗ 无效响应")
                
        except Exception as e:
            print(f"   ✗ 错误: {e}")
    
    return False

if __name__ == "__main__":
    print("华尔街日报首页下载器 - 调试版本")
    print("=" * 60)
    
    # 方法1: 通过页面解析下载
    success = download_wsj_front_page()
    
    if not success:
        print("\n方法1失败，尝试备选方法...")
        # 方法2: 直接构造URL下载
        success = alternative_download_method()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 下载成功完成!")
    else:
        print("❌ 所有方法都失败了")
        print("\n可能的原因:")
        print("1. 网络连接问题")
        print("2. 代理设置不正确")
        print("3. 页面结构已改变")
        print("4. 需要登录或验证")