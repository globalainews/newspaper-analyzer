import requests
import os
from datetime import datetime, timedelta

def test_kiosko_download():
    """测试kiosko.net图片下载功能"""
    
    print("kiosko.net 图片下载测试")
    print("=" * 60)
    
    # 报纸配置
    newspapers = {
        'wsj': {
            'name': '华尔街日报',
            'country': 'us',
            'code': 'wsj',
            'url_pattern': 'https://img.kiosko.net/{date}/{country}/{code}.750.jpg'
        },
        'ft': {
            'name': '金融时报',
            'country': 'uk',
            'code': 'ft_uk',
            'url_pattern': 'https://img.kiosko.net/{date}/{country}/{code}.750.jpg'
        }
    }
    
    # 测试日期
    test_dates = [
        datetime.now().strftime('%Y/%m/%d'),  # 今日
        (datetime.now() - timedelta(days=1)).strftime('%Y/%m/%d'),  # 昨日
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://en.kiosko.net/'
    }
    
    success_count = 0
    total_tests = 0
    
    for newspaper_code, paper in newspapers.items():
        print(f"\n测试 {paper['name']}:")
        print("-" * 40)
        
        for date_str in test_dates:
            total_tests += 1
            
            # 构造URL
            url = paper['url_pattern'].format(
                date=date_str.replace('/', '/'),
                country=paper['country'],
                code=paper['code']
            )
            
            print(f"  日期: {date_str}")
            print(f"  URL: {url}")
            
            try:
                # 测试连接
                response = requests.get(url, headers=headers, timeout=30)
                
                if response.status_code == 200:
                    # 检查内容类型和大小
                    content_type = response.headers.get('content-type', '')
                    content_length = len(response.content)
                    
                    print(f"   状态码: {response.status_code}")
                    print(f"   内容类型: {content_type}")
                    print(f"   内容大小: {content_length} 字节")
                    
                    if content_length > 1000 and 'image' in content_type:
                        # 保存测试文件
                        date_part = date_str.replace('/', '-')
                        filename = f"test_{paper['code']}_{date_part}.jpg"
                        
                        with open(filename, 'wb') as f:
                            f.write(response.content)
                        
                        file_size = os.path.getsize(filename)
                        print(f"   ✓ 下载成功! 文件: {filename} ({file_size} 字节)")
                        success_count += 1
                    else:
                        print(f"   ⚠️ 响应内容可能不是有效图片")
                        
                elif response.status_code == 404:
                    print(f"   ⚠️ 图片不存在 (404)")
                else:
                    print(f"   ✗ 请求失败，状态码: {response.status_code}")
                    
            except requests.exceptions.Timeout:
                print(f"   ✗ 请求超时")
            except requests.exceptions.ConnectionError:
                print(f"   ✗ 连接错误")
            except Exception as e:
                print(f"   ✗ 错误: {str(e)}")
            
            print()
    
    print("=" * 60)
    print(f"测试完成: {success_count}/{total_tests} 成功")
    
    return success_count > 0

def test_website_access():
    """测试网站可访问性"""
    
    print("\n网站可访问性测试")
    print("-" * 40)
    
    test_urls = [
        ("kiosko.net 主页", "https://en.kiosko.net/"),
        ("图片服务器", "https://img.kiosko.net/")
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    for name, url in test_urls:
        try:
            response = requests.get(url, headers=headers, timeout=10)
            print(f"{name}: ✓ (状态码: {response.status_code})")
        except Exception as e:
            print(f"{name}: ✗ ({str(e)})")

def generate_sample_urls():
    """生成示例URL"""
    
    print("\n示例图片URL")
    print("-" * 40)
    
    today = datetime.now().strftime('%Y/%m/%d')
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y/%m/%d')
    
    newspapers = {
        '华尔街日报 (WSJ)': f'https://img.kiosko.net/{today}/us/wsj.750.jpg',
        '金融时报 (FT)': f'https://img.kiosko.net/{today}/uk/ft_uk.750.jpg'
    }
    
    for name, url in newspapers.items():
        print(f"{name}:")
        print(f"  {url}")
        print()

if __name__ == "__main__":
    print("kiosko.net 新闻图片下载器 - 功能测试")
    print("=" * 60)
    
    # 显示示例URL
    generate_sample_urls()
    
    # 测试网站访问
    test_website_access()
    
    # 测试下载功能
    success = test_kiosko_download()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 测试成功! 图片下载功能正常")
        print("\n下一步:")
        print("1. 运行 kiosko_downloader.py 使用图形界面")
        print("2. 选择要下载的报纸和日期")
        print("3. 点击下载按钮获取图片")
    else:
        print("⚠️  测试发现一些问题")
        print("\n可能的原因:")
        print("1. 网络连接问题")
        print("2. 图片URL格式可能已改变")
        print("3. 特定日期的图片可能不存在")
    
    print("\n测试完成")