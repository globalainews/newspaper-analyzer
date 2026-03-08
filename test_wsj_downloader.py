import unittest
import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime

class TestWSJDownloader(unittest.TestCase):
    
    def setUp(self):
        self.proxy_port = 1080
        self.proxies = {
            'http': f'http://127.0.0.1:{self.proxy_port}',
            'https': f'http://127.0.0.1:{self.proxy_port}'
        }
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
        }
        
        self.url = "https://x.com/wsj"
        self.test_output_dir = "test_output"
        
        # 创建测试输出目录
        if not os.path.exists(self.test_output_dir):
            os.makedirs(self.test_output_dir)
    
    def test_connection(self):
        """测试网络连接和代理设置"""
        print("\n=== 测试网络连接 ===")
        try:
            response = requests.get(self.url, headers=self.headers, proxies=self.proxies, timeout=30)
            self.assertEqual(response.status_code, 200, "页面访问失败")
            print("✓ 网络连接测试通过")
            return True
        except Exception as e:
            print(f"✗ 网络连接测试失败: {str(e)}")
            print("请检查代理设置和网络连接")
            return False
    
    def test_page_parsing(self):
        """测试页面解析和图片查找"""
        print("\n=== 测试页面解析 ===")
        try:
            response = requests.get(self.url, headers=self.headers, proxies=self.proxies, timeout=30)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 查找图片标签
            img_tags = soup.find_all('img')
            print(f"找到 {len(img_tags)} 个图片标签")
            
            # 查找可能的图片链接
            possible_images = []
            for img in img_tags:
                src = img.get('src', '')
                alt = img.get('alt', '')
                if src and ('pbs.twimg.com' in src or 'twimg.com' in src):
                    possible_images.append({'src': src, 'alt': alt})
            
            print(f"找到 {len(possible_images)} 个可能的图片链接")
            
            # 显示前5个可能的图片
            for i, img_info in enumerate(possible_images[:5]):
                print(f"图片 {i+1}: {img_info['src'][:80]}... alt: {img_info['alt']}")
            
            self.assertGreater(len(possible_images), 0, "未找到任何图片链接")
            print("✓ 页面解析测试通过")
            return possible_images
            
        except Exception as e:
            print(f"✗ 页面解析测试失败: {str(e)}")
            return None
    
    def test_image_download(self):
        """测试图片下载功能"""
        print("\n=== 测试图片下载 ===")
        
        # 先获取图片链接
        possible_images = self.test_page_parsing()
        if not possible_images:
            print("✗ 无法获取图片链接，跳过下载测试")
            return False
        
        try:
            # 尝试下载第一个图片
            image_info = possible_images[0]
            image_url = image_info['src']
            
            if not image_url.startswith('http'):
                image_url = 'https:' + image_url
            
            print(f"尝试下载图片: {image_url[:100]}...")
            
            img_response = requests.get(image_url, headers=self.headers, proxies=self.proxies, timeout=30)
            
            self.assertEqual(img_response.status_code, 200, "图片下载失败")
            
            # 检查图片内容
            self.assertGreater(len(img_response.content), 0, "下载的图片为空")
            
            # 保存测试图片
            today = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            filename = f"test_wsj_{today}.jpg"
            filepath = os.path.join(self.test_output_dir, filename)
            
            with open(filepath, 'wb') as f:
                f.write(img_response.content)
            
            # 验证文件是否创建成功
            self.assertTrue(os.path.exists(filepath), "图片文件保存失败")
            file_size = os.path.getsize(filepath)
            self.assertGreater(file_size, 0, "保存的图片文件为空")
            
            print(f"✓ 图片下载测试通过")
            print(f"图片已保存到: {filepath}")
            print(f"文件大小: {file_size} 字节")
            return True
            
        except Exception as e:
            print(f"✗ 图片下载测试失败: {str(e)}")
            return False
    
    def test_find_image_url_method(self):
        """测试图片URL查找方法（模拟主程序中的方法）"""
        print("\n=== 测试图片URL查找方法 ===")
        
        try:
            response = requests.get(self.url, headers=self.headers, proxies=self.proxies, timeout=30)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            image_url = self.find_image_url(soup)
            
            if image_url:
                print(f"✓ 找到图片URL: {image_url[:100]}...")
                return image_url
            else:
                print("✗ 未找到图片URL")
                return None
                
        except Exception as e:
            print(f"✗ 图片URL查找测试失败: {str(e)}")
            return None
    
    def find_image_url(self, soup):
        """从主程序复制的图片查找方法"""
        image_url = None
        
        img_tags = soup.find_all('img')
        
        # 策略1: 查找包含特定关键词的图片
        for img in img_tags:
            src = img.get('src', '')
            alt = img.get('alt', '').lower()
            
            if any(keyword in alt for keyword in ['wall street journal', 'front page', 'wsj', 'today\'s front page', 'today front page']):
                image_url = src
                break
        
        # 策略2: 查找推文中的媒体图片
        if not image_url:
            for img in img_tags:
                src = img.get('src', '')
                if 'pbs.twimg.com/media' in src:
                    if 'name=' in src and 'large' in src:
                        image_url = src
                        break
                    elif image_url is None:
                        image_url = src
        
        # 策略3: 查找推文卡片中的图片
        if not image_url:
            for img in img_tags:
                src = img.get('src', '')
                if 'pbs.twimg.com' in src and ('profile' not in src):
                    if 'small' in src:
                        image_url = src.replace('small', 'large')
                    elif 'medium' in src:
                        image_url = src.replace('medium', 'large')
                    else:
                        image_url = src
                    break
        
        # 策略4: 查找data-src属性中的图片
        if not image_url:
            for img in img_tags:
                data_src = img.get('data-src', '')
                if data_src and 'pbs.twimg.com' in data_src:
                    image_url = data_src
                    break
        
        # 策略5: 查找所有可能的图片链接
        if not image_url:
            possible_images = []
            for img in img_tags:
                src = img.get('src', '')
                if src and ('pbs.twimg.com' in src or 'twimg.com' in src):
                    possible_images.append(src)
            
            if possible_images:
                image_url = possible_images[0]
                for img_src in possible_images:
                    if 'large' in img_src or 'orig' in img_src:
                        image_url = img_src
                        break
        
        return image_url

def run_all_tests():
    """运行所有测试"""
    print("开始运行华尔街日报下载器测试...")
    print("=" * 50)
    
    tester = TestWSJDownloader()
    tester.setUp()
    
    results = {
        'connection': tester.test_connection(),
        'parsing': bool(tester.test_page_parsing()),
        'download': tester.test_image_download(),
        'url_finding': bool(tester.test_find_image_url_method())
    }
    
    print("\n" + "=" * 50)
    print("测试结果汇总:")
    print("=" * 50)
    
    for test_name, result in results.items():
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{test_name}: {status}")
    
    passed_count = sum(results.values())
    total_count = len(results)
    
    print(f"\n总测试数: {total_count}")
    print(f"通过数: {passed_count}")
    print(f"失败数: {total_count - passed_count}")
    
    if passed_count == total_count:
        print("\n🎉 所有测试通过!")
    else:
        print("\n⚠️  部分测试失败，请检查代理设置和网络连接")
    
    return passed_count == total_count

if __name__ == "__main__":
    # 运行所有测试
    success = run_all_tests()
    
    # 退出码
    exit(0 if success else 1)