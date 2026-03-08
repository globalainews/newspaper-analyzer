import requests
from bs4 import BeautifulSoup
import os
import time
from datetime import datetime
import json

class WSJDebugger:
    def __init__(self):
        self.proxy_host = "127.0.0.1"
        self.proxy_port = 1080
        self.proxies = {
            'http': f'http://{self.proxy_host}:{self.proxy_port}',
            'https': f'http://{self.proxy_host}:{self.proxy_port}'
        }
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
        }
        
        self.test_output_dir = "debug_output"
        if not os.path.exists(self.test_output_dir):
            os.makedirs(self.test_output_dir)
    
    def log_step(self, step, message, success=True):
        """记录调试步骤"""
        status = "✓" if success else "✗"
        print(f"{status} {step}: {message}")
    
    def save_debug_info(self, filename, content):
        """保存调试信息到文件"""
        filepath = os.path.join(self.test_output_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return filepath
    
    def test_proxy_connection(self):
        """测试代理连接"""
        print("\n=== 测试代理连接 ===")
        
        try:
            # 测试直接连接
            print("1. 测试直接连接（无代理）...")
            try:
                response = requests.get("https://httpbin.org/ip", timeout=10)
                self.log_step("直接连接", f"成功 - IP: {response.json()['origin']}")
            except Exception as e:
                self.log_step("直接连接", f"失败 - {str(e)}", False)
            
            # 测试代理连接
            print("2. 测试代理连接...")
            try:
                response = requests.get("https://httpbin.org/ip", proxies=self.proxies, timeout=10)
                proxy_ip = response.json()['origin']
                self.log_step("代理连接", f"成功 - 代理IP: {proxy_ip}")
                return True
            except Exception as e:
                self.log_step("代理连接", f"失败 - {str(e)}", False)
                return False
                
        except Exception as e:
            self.log_step("代理测试", f"整体失败 - {str(e)}", False)
            return False
    
    def test_wsj_page_access(self):
        """测试WSJ页面访问"""
        print("\n=== 测试WSJ页面访问 ===")
        
        urls_to_test = [
            "https://x.com/wsj",
            "https://x.com/WSJ/status/2030229522163859834"
        ]
        
        results = {}
        
        for url in urls_to_test:
            print(f"\n测试URL: {url}")
            
            try:
                response = requests.get(url, headers=self.headers, proxies=self.proxies, timeout=30)
                
                if response.status_code == 200:
                    self.log_step("页面访问", f"成功 - 状态码: {response.status_code}")
                    
                    # 保存页面内容用于分析
                    filename = f"page_{url.split('//')[1].replace('/', '_')}.html"
                    filepath = self.save_debug_info(filename, response.text)
                    self.log_step("页面保存", f"已保存到: {filepath}")
                    
                    # 分析页面内容
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # 检查页面标题
                    title = soup.find('title')
                    if title:
                        self.log_step("页面标题", title.text)
                    
                    # 检查是否有重定向或登录要求
                    if "重定向" in response.text or "login" in response.text.lower():
                        self.log_step("页面状态", "可能需要登录或重定向", False)
                    else:
                        self.log_step("页面状态", "页面内容正常")
                    
                    results[url] = {
                        'success': True,
                        'status_code': response.status_code,
                        'content_length': len(response.text),
                        'filepath': filepath
                    }
                    
                else:
                    self.log_step("页面访问", f"失败 - 状态码: {response.status_code}", False)
                    results[url] = {'success': False, 'status_code': response.status_code}
                    
            except Exception as e:
                self.log_step("页面访问", f"异常 - {str(e)}", False)
                results[url] = {'success': False, 'error': str(e)}
        
        return results
    
    def analyze_page_content(self, filepath):
        """分析页面内容，查找图片"""
        print(f"\n=== 分析页面内容: {filepath} ===")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # 查找所有图片标签
        img_tags = soup.find_all('img')
        self.log_step("图片标签", f"找到 {len(img_tags)} 个图片标签")
        
        # 分类图片
        twitter_images = []
        other_images = []
        
        for i, img in enumerate(img_tags):
            src = img.get('src', '')
            alt = img.get('alt', '')
            data_src = img.get('data-src', '')
            
            img_info = {
                'index': i,
                'src': src,
                'alt': alt,
                'data_src': data_src
            }
            
            if 'pbs.twimg.com' in src or 'twimg.com' in src:
                twitter_images.append(img_info)
            else:
                other_images.append(img_info)
        
        self.log_step("Twitter图片", f"找到 {len(twitter_images)} 个Twitter图片")
        self.log_step("其他图片", f"找到 {len(other_images)} 个其他图片")
        
        # 显示前5个Twitter图片
        print("\n前5个Twitter图片:")
        for img_info in twitter_images[:5]:
            print(f"  [{img_info['index']}] src: {img_info['src'][:100]}...")
            print(f"      alt: {img_info['alt']}")
            if img_info['data_src']:
                print(f"      data-src: {img_info['data_src'][:100]}...")
            print()
        
        # 查找推文链接
        links = soup.find_all('a', href=True)
        tweet_links = []
        
        for link in links:
            href = link.get('href', '')
            if '/status/' in href and ('/wsj' in href or '/WSJ' in href):
                tweet_links.append('https://x.com' + href)
        
        self.log_step("推文链接", f"找到 {len(tweet_links)} 个推文链接")
        
        # 显示推文链接
        for link in tweet_links[:3]:
            print(f"  推文: {link}")
        
        return {
            'twitter_images': twitter_images,
            'tweet_links': tweet_links
        }
    
    def test_image_download(self, image_urls):
        """测试图片下载"""
        print("\n=== 测试图片下载 ===")
        
        success_count = 0
        
        for i, img_info in enumerate(image_urls[:3]):  # 测试前3个图片
            print(f"\n测试图片 {i+1}:")
            
            try:
                image_url = img_info['src']
                if not image_url.startswith('http'):
                    image_url = 'https:' + image_url
                
                print(f"  图片URL: {image_url[:100]}...")
                
                # 下载图片
                response = requests.get(image_url, headers=self.headers, proxies=self.proxies, timeout=30)
                
                if response.status_code == 200:
                    # 保存图片
                    today = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
                    filename = f"test_image_{i+1}_{today}.jpg"
                    filepath = os.path.join(self.test_output_dir, filename)
                    
                    with open(filepath, 'wb') as f:
                        f.write(response.content)
                    
                    file_size = os.path.getsize(filepath)
                    self.log_step("图片下载", f"成功 - 大小: {file_size} 字节")
                    self.log_step("图片保存", f"已保存到: {filepath}")
                    
                    success_count += 1
                    
                else:
                    self.log_step("图片下载", f"失败 - 状态码: {response.status_code}", False)
                    
            except Exception as e:
                self.log_step("图片下载", f"异常 - {str(e)}", False)
        
        return success_count
    
    def run_comprehensive_test(self):
        """运行全面测试"""
        print("开始全面调试华尔街日报图片下载...")
        print("=" * 60)
        
        # 测试代理连接
        proxy_success = self.test_proxy_connection()
        
        if not proxy_success:
            print("\n⚠️  代理连接失败，请检查代理设置")
            return False
        
        # 测试页面访问
        page_results = self.test_wsj_page_access()
        
        successful_pages = [url for url, result in page_results.items() if result.get('success')]
        
        if not successful_pages:
            print("\n⚠️  所有页面访问失败，请检查网络连接")
            return False
        
        # 分析成功的页面
        for url in successful_pages:
            result = page_results[url]
            analysis = self.analyze_page_content(result['filepath'])
            
            # 测试图片下载
            if analysis['twitter_images']:
                success_count = self.test_image_download(analysis['twitter_images'])
                
                if success_count > 0:
                    print(f"\n🎉 成功下载 {success_count} 张图片!")
                    return True
                else:
                    print("\n⚠️  图片下载失败，可能需要调整图片URL处理逻辑")
            else:
                print("\n⚠️  页面中未找到Twitter图片")
        
        return False

def main():
    debugger = WSJDebugger()
    
    print("华尔街日报图片下载调试器")
    print("=" * 60)
    
    # 运行全面测试
    success = debugger.run_comprehensive_test()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 调试完成! 图片下载功能正常")
    else:
        print("⚠️  调试完成，但存在一些问题需要解决")
    
    print(f"\n调试输出文件保存在: {debugger.test_output_dir}")

if __name__ == "__main__":
    main()