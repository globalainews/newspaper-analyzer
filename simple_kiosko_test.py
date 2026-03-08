import requests
import os
from datetime import datetime

def test_single_download():
    """测试单个图片下载"""
    
    print("kiosko.net 图片下载简单测试")
    print("=" * 50)
    
    # 使用用户提供的示例URL
    test_urls = [
        ("华尔街日报", "https://img.kiosko.net/2026/03/06/us/wsj.750.jpg"),
        ("金融时报", "https://img.kiosko.net/2026/03/06/uk/ft_uk.750.jpg")
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://en.kiosko.net/'
    }
    
    success_count = 0
    
    for name, url in test_urls:
        print(f"\n测试 {name}:")
        print(f"URL: {url}")
        
        try:
            # 下载图片
            response = requests.get(url, headers=headers, timeout=30)
            
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                # 检查图片内容
                content_length = len(response.content)
                print(f"图片大小: {content_length} 字节")
                
                if content_length > 1000:
                    # 保存图片
                    filename = f"test_{name}_{datetime.now().strftime('%H%M%S')}.jpg"
                    
                    with open(filename, 'wb') as f:
                        f.write(response.content)
                    
                    file_size = os.path.getsize(filename)
                    print(f"✓ 下载成功! 文件: {filename} ({file_size} 字节)")
                    success_count += 1
                else:
                    print("⚠️ 图片内容过小")
            else:
                print("✗ 下载失败")
                
        except Exception as e:
            print(f"✗ 错误: {str(e)}")
    
    print("\n" + "=" * 50)
    print(f"测试结果: {success_count}/{len(test_urls)} 成功")
    
    return success_count == len(test_urls)

def test_url_pattern():
    """测试URL模式"""
    
    print("\nURL模式测试")
    print("-" * 40)
    
    # 今天的日期
    today = datetime.now().strftime('%Y/%m/%d')
    
    # 生成今天的URL
    wsj_url = f"https://img.kiosko.net/{today}/us/wsj.750.jpg"
    ft_url = f"https://img.kiosko.net/{today}/uk/ft_uk.750.jpg"
    
    print(f"今日日期: {today}")
    print(f"华尔街日报URL: {wsj_url}")
    print(f"金融时报URL: {ft_url}")
    
    # 测试连接
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    for name, url in [("WSJ", wsj_url), ("FT", ft_url)]:
        try:
            response = requests.head(url, headers=headers, timeout=10)
            print(f"{name}: 状态码 {response.status_code}")
        except:
            print(f"{name}: 连接失败")

if __name__ == "__main__":
    print("kiosko.net 图片下载功能验证")
    
    # 测试URL模式
    test_url_pattern()
    
    # 测试具体下载
    success = test_single_download()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 所有测试通过!")
        print("\n可以运行 kiosko_downloader.py 使用图形界面程序")
    else:
        print("⚠️ 部分测试失败")
        print("\n建议:")
        print("1. 检查网络连接")
        print("2. 确认图片URL是否有效")
        print("3. 可能需要使用代理")
    
    print("\n测试完成")