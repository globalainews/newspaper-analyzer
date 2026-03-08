import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime

def test_download():
    try:
        proxy_port = 1080
        proxies = {
            'http': f'http://127.0.0.1:{proxy_port}',
            'https': f'http://127.0.0.1:{proxy_port}'
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
        }
        
        url = "https://x.com/wsj"
        
        print("正在获取页面内容...")
        response = requests.get(url, headers=headers, proxies=proxies, timeout=30)
        
        if response.status_code != 200:
            print(f"无法访问页面，状态码: {response.status_code}")
            return False
        
        print("正在解析页面...")
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 查找图片
        img_tags = soup.find_all('img')
        print(f"找到 {len(img_tags)} 个图片标签")
        
        # 显示前10个图片的src和alt属性
        for i, img in enumerate(img_tags[:10]):
            src = img.get('src', '')
            alt = img.get('alt', '')
            print(f"图片 {i+1}: src={src[:100]}... alt={alt}")
        
        # 查找可能的图片链接
        possible_images = []
        for img in img_tags:
            src = img.get('src', '')
            if src and ('pbs.twimg.com' in src or 'twimg.com' in src):
                possible_images.append(src)
        
        print(f"\n找到 {len(possible_images)} 个可能的图片链接")
        
        if possible_images:
            # 尝试下载第一个图片
            image_url = possible_images[0]
            if not image_url.startswith('http'):
                image_url = 'https:' + image_url
            
            print(f"尝试下载图片: {image_url}")
            
            img_response = requests.get(image_url, headers=headers, proxies=proxies, timeout=30)
            
            if img_response.status_code == 200:
                print("图片下载成功!")
                
                # 保存图片
                today = datetime.now().strftime('%Y-%m-%d')
                filename = f"test_wsj_{today}.jpg"
                filepath = os.path.join(os.getcwd(), filename)
                
                with open(filepath, 'wb') as f:
                    f.write(img_response.content)
                
                print(f"图片已保存到: {filepath}")
                return True
            else:
                print(f"图片下载失败，状态码: {img_response.status_code}")
                return False
        else:
            print("未找到任何图片链接")
            return False
            
    except Exception as e:
        print(f"发生错误: {str(e)}")
        return False

if __name__ == "__main__":
    print("开始测试华尔街日报图片下载...")
    success = test_download()
    if success:
        print("测试成功!")
    else:
        print("测试失败!")
    print("测试完成")