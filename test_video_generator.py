import unittest
import os
import json
import tempfile
from video_generator import VideoGenerator

class TestVideoGenerator(unittest.TestCase):
    def setUp(self):
        # 创建临时目录
        self.temp_dir = tempfile.mkdtemp()
        self.analysis_dir = os.path.join(self.temp_dir, 'analysis_results')
        os.makedirs(self.analysis_dir, exist_ok=True)
        
        # 模拟配置
        self.config = {
            'analysis_settings': {
                'analysis_directory': self.analysis_dir
            },
            'download_settings': {
                'save_directory': self.temp_dir
            }
        }
        
        # 模拟进度条和标签
        class MockWidget:
            def config(self, **kwargs):
                pass
        
        self.progress_label = MockWidget()
        self.progress_bar = MockWidget()
        
        # 创建VideoGenerator实例
        self.video_generator = VideoGenerator(
            self.config, 
            self.progress_label, 
            self.progress_bar
        )
    
    def tearDown(self):
        # 清理临时文件
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_silent_load_json(self):
        """测试静默加载JSON文件"""
        # 创建测试JSON文件
        test_json = {
            'news_blocks': [
                {
                    'title': '测试新闻1',
                    'content': '测试内容1',
                    'position': [10, 10, 100, 100]
                }
            ]
        }
        
        json_file = os.path.join(self.analysis_dir, 'test.json')
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(test_json, f, ensure_ascii=False)
        
        # 调用测试方法
        self.video_generator.silent_load_json('test.jpg')
        
        # 验证结果
        self.assertEqual(len(self.video_generator.video_data), 1)
        self.assertEqual(self.video_generator.video_data[0]['title'], '测试新闻1')
    
    def test_save_video_data(self):
        """测试保存视频数据"""
        # 添加测试数据
        self.video_generator.video_data = [
            {
                'id': 1,
                'title': '测试新闻1',
                'content': '测试内容1',
                'position': [10, 10, 100, 100]
            }
        ]
        
        # 模拟当前图片文件
        self.video_generator.current_image_file = os.path.join(self.temp_dir, 'test.jpg')
        
        # 创建原始JSON文件
        original_data = {
            'newspaper': '测试报纸',
            'date': '2026-03-11',
            'news_blocks': []
        }
        
        json_file = os.path.join(self.analysis_dir, 'test.json')
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(original_data, f, ensure_ascii=False)
        
        # 调用测试方法
        result = self.video_generator.save_video_data()
        
        # 验证结果
        self.assertTrue(result)
        
        # 读取保存后的文件
        with open(json_file, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        
        self.assertEqual(len(saved_data['news_blocks']), 1)
        self.assertEqual(saved_data['news_blocks'][0]['title'], '测试新闻1')
        self.assertEqual(saved_data['newspaper'], '测试报纸')  # 确保其他字段保留
    
    def test_load_json_file(self):
        """测试加载JSON文件"""
        # 创建测试JSON文件
        test_json = {
            'news_blocks': [
                {
                    'title': '测试新闻1',
                    'content': '测试内容1',
                    'position': [10, 10, 100, 100]
                },
                {
                    'title': '测试新闻2',
                    'content': '测试内容2',
                    'position': [110, 10, 200, 100]
                }
            ]
        }
        
        json_file = os.path.join(self.analysis_dir, 'test.json')
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(test_json, f, ensure_ascii=False)
        
        # 调用测试方法
        self.video_generator.load_json_file(json_file)
        
        # 验证结果
        self.assertEqual(len(self.video_generator.video_data), 2)
        self.assertEqual(self.video_generator.video_data[0]['title'], '测试新闻1')
        self.assertEqual(self.video_generator.video_data[1]['title'], '测试新闻2')
    
    def test_move_news_up(self):
        """测试向上移动新闻"""
        # 添加测试数据
        self.video_generator.video_data = [
            {'id': 1, 'title': '新闻1'},
            {'id': 2, 'title': '新闻2'},
            {'id': 3, 'title': '新闻3'}
        ]
        self.video_generator.current_news_index = 1  # 选中第二条新闻
        
        # 调用测试方法
        # 注意：这里会弹出消息框，我们需要模拟
        try:
            self.video_generator.move_news_up()
        except Exception:
            pass
        
        # 验证结果
        self.assertEqual(self.video_generator.video_data[0]['title'], '新闻2')
        self.assertEqual(self.video_generator.video_data[1]['title'], '新闻1')
        self.assertEqual(self.video_generator.current_news_index, 0)
    
    def test_move_news_down(self):
        """测试向下移动新闻"""
        # 添加测试数据
        self.video_generator.video_data = [
            {'id': 1, 'title': '新闻1'},
            {'id': 2, 'title': '新闻2'},
            {'id': 3, 'title': '新闻3'}
        ]
        self.video_generator.current_news_index = 0  # 选中第一条新闻
        
        # 调用测试方法
        try:
            self.video_generator.move_news_down()
        except Exception:
            pass
        
        # 验证结果
        self.assertEqual(self.video_generator.video_data[0]['title'], '新闻2')
        self.assertEqual(self.video_generator.video_data[1]['title'], '新闻1')
        self.assertEqual(self.video_generator.current_news_index, 1)
    
    def test_delete_news(self):
        """测试删除新闻"""
        # 添加测试数据
        self.video_generator.video_data = [
            {'id': 1, 'title': '新闻1'},
            {'id': 2, 'title': '新闻2'},
            {'id': 3, 'title': '新闻3'}
        ]
        self.video_generator.current_news_index = 1  # 选中第二条新闻
        
        # 调用测试方法
        try:
            self.video_generator.delete_news()
        except Exception:
            pass
        
        # 验证结果
        self.assertEqual(len(self.video_generator.video_data), 2)
        self.assertEqual(self.video_generator.video_data[0]['title'], '新闻1')
        self.assertEqual(self.video_generator.video_data[1]['title'], '新闻3')
        self.assertEqual(self.video_generator.current_news_index, -1)

if __name__ == '__main__':
    unittest.main()