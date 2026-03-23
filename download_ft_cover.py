#!/usr/bin/env python3
"""
自动下载金融时报头版图片
访问 https://x.com/FT，找到包含 "front page of the Financial Times" 的推文
优先选择带有 "international edition" 的推文下载
"""

import os
import sys
import time
import re
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from browser_manager import browser_manager

def download_ft_cover():
    """下载金融时报头版图片"""
    print("=== 自动下载金融时报头版图片 ===")

    # 确保输出目录存在
    output_dir = r"E:\中文听见\报纸头版"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    try:
        # 启动浏览器
        print("\n1. 启动浏览器...")
        success = browser_manager.start_chrome()
        if not success:
            print("❌ 启动浏览器失败")
            return False

        # 获取页面
        print("\n2. 创建新页面...")
        page = browser_manager.new_page()
        if not page:
            print("❌ 创建页面失败")
            return False

        # 打开 FT 账号页面
        print("\n3. 打开 x.com/FT 页面...")
        page.goto("https://x.com/FT", timeout=60000)
        time.sleep(5)

        print("\n4. 等待页面加载完成...")
        time.sleep(3)

        print("\n5. 从上到下查找金融时报头版推文...")

        articles = page.query_selector_all('article')
        print(f"   找到 {len(articles)} 条推文")

        ft_cover_tweets = []

        for i, article in enumerate(articles):
            try:
                text_content = article.inner_text()
                text_lower = text_content.lower()

                if "front page" in text_lower and "financial times" in text_lower:
                    print(f"\n   ✅ 推文 {i+1} 包含 front page 内容!")

                    has_international = "international edition" in text_lower
                    if has_international:
                        print(f"   ✅ 包含 'international edition'")

                    link = article.query_selector('a[href*="/status/"]')
                    if link:
                        href = link.get_attribute('href')
                        if href and '/photo/' not in href:
                            full_url = f"https://x.com{href}" if href.startswith('/') else href
                            print(f"   推文链接: {full_url}")

                            ft_cover_tweets.append({
                                'url': full_url,
                                'text': text_content,
                                'has_international': has_international
                            })

            except Exception as e:
                print(f"   处理推文 {i+1} 时出错: {e}")
                continue

        print(f"\n6. 共找到 {len(ft_cover_tweets)} 个金融时报头版推文")

        if not ft_cover_tweets:
            print("\n   未找到front page推文，扩大搜索范围...")
            for i, article in enumerate(articles):
                try:
                    link = article.query_selector('a[href*="/status/"]')
                    if link:
                        href = link.get_attribute('href')
                        if href and '/photo/' not in href:
                            full_url = f"https://x.com{href}" if href.startswith('/') else href
                            text_content = article.inner_text()
                            print(f"   推文 {i+1}: {full_url}")

                            ft_cover_tweets.append({
                                'url': full_url,
                                'text': text_content,
                                'has_international': False
                            })
                except:
                    continue

        target_tweet = None
        for tweet in ft_cover_tweets:
            if tweet['has_international']:
                target_tweet = tweet
                print(f"\n   选择 'international edition' 推文: {target_tweet['url']}")
                break

        if not target_tweet and ft_cover_tweets:
            target_tweet = ft_cover_tweets[0]
            print(f"\n   选择推文: {target_tweet['url']}")

        if target_tweet:
            print(f"\n7. 进入推文详情页获取图片...")
            date_str = datetime.now().strftime("%Y-%m-%d")

            try:
                detail_page = browser_manager.new_page()
                detail_page.set_viewport_size({"width": 1200, "height": 1600})
                detail_page.goto(target_tweet['url'], timeout=60000)
                time.sleep(5)

                print(f"   页面加载完成，截取图片...")

                # 查找页面中的图片元素
                images = detail_page.query_selector_all('img[src*="pbs.twimg.com/media/"]')
                print(f"   找到 {len(images)} 个图片元素")

                for idx, img in enumerate(images):
                    img_src = img.get_attribute('src') or ''
                    if 'format=jpg' in img_src and 'name=small' in img_src:
                        print(f"\n   找到小图URL: {img_src}")

                        # 尝试点击图片打开全屏查看大图
                        try:
                            print(f"   尝试点击图片打开全屏...")
                            img.click()
                            time.sleep(3)

                            # 查找全屏图片
                            time.sleep(2)

                            # 截取整个页面
                            temp_file = os.path.join(output_dir, f"temp_ft_{date_str}.png")
                            detail_page.screenshot(path=temp_file, full_page=False)

                            if os.path.exists(temp_file):
                                file_size = os.path.getsize(temp_file)
                                print(f"   截图保存: {temp_file}, 大小: {file_size / 1024:.2f} KB")

                                if file_size > 50000:
                                    # 移动到目标位置
                                    filename = f"金融时报_{date_str}.jpg"
                                    filepath = os.path.join(output_dir, filename)

                                    # 读取PNG并转换为JPG
                                    try:
                                        from PIL import Image
                                        img = Image.open(temp_file)
                                        rgb_img = img.convert('RGB')
                                        rgb_img.save(filepath, 'JPEG', quality=95)
                                        os.remove(temp_file)
                                        print(f"   ✅ 保存成功: {filepath}")
                                        detail_page.close()
                                        print("\n✅ 下载完成！")
                                        return True
                                    except ImportError:
                                        import shutil
                                        shutil.move(temp_file, filepath)
                                        print(f"   ✅ 保存成功: {filepath}")
                                        detail_page.close()
                                        print("\n✅ 下载完成！")
                                        return True

                            # 按ESC关闭全屏
                            detail_page.keyboard.press("Escape")
                            time.sleep(1)

                        except Exception as e:
                            print(f"   点击图片失败: {e}")

                # 如果无法点击全屏，直接截图整页
                print("\n   直接截取推文详情页...")
                temp_file = os.path.join(output_dir, f"temp_ft_{date_str}.png")
                detail_page.screenshot(path=temp_file, full_page=False)

                if os.path.exists(temp_file):
                    file_size = os.path.getsize(temp_file)
                    print(f"   截图保存: {temp_file}, 大小: {file_size / 1024:.2f} KB")

                    if file_size > 50000:
                        filename = f"金融时报_{date_str}.jpg"
                        filepath = os.path.join(output_dir, filename)

                        try:
                            from PIL import Image
                            img = Image.open(temp_file)
                            rgb_img = img.convert('RGB')
                            rgb_img.save(filepath, 'JPEG', quality=95)
                            os.remove(temp_file)
                            print(f"   ✅ 保存成功: {filepath}")
                            detail_page.close()
                            print("\n✅ 下载完成！")
                            return True
                        except ImportError:
                            import shutil
                            shutil.move(temp_file, filepath)
                            print(f"   ✅ 保存成功: {filepath}")
                            detail_page.close()
                            print("\n✅ 下载完成！")
                            return True

                detail_page.close()

            except Exception as e:
                print(f"   下载失败: {e}")

        print("\n⚠️ 未找到金融时报头版图片")
        print("\n提示: 请手动访问以下网址下载:")
        print("https://x.com/FT")
        return False

    except Exception as e:
        print(f"\n❌ 下载失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        print("\n关闭浏览器...")
        browser_manager.close()

if __name__ == '__main__':
    success = download_ft_cover()
    sys.exit(0 if success else 1)
