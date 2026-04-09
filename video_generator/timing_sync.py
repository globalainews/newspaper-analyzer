# Timing synchronization module
# 时序同步模块

import copy
import json
import os
import datetime

class TimingSynchronizer:
    def __init__(self, config, progress_label_widget=None, progress_bar_widget=None, root=None):
        self.config = config
        self.progress_label_widget = progress_label_widget
        self.progress_bar_widget = progress_bar_widget
        self.root = root
    
    def sync_audio_durations(self, draft_dir, draft_content):
        """
        同步语音文件时长到草稿素材
        
        功能:
        1. 查看textReading目录下的audio*.wav文件
        2. 获取每个语音文件的实际时长
        3. 更新draft_content.json中audios素材的duration
        
        Args:
            draft_dir: 剪映草稿目录路径
            draft_content: 剪映草稿JSON数据
            
        Returns:
            修改后的draft_content
        """
        print("开始同步语音文件时长...")

        text_reading_dir = os.path.join(draft_dir, 'textReading')

        if not os.path.exists(text_reading_dir):
            print(f"[警告] textReading目录不存在")
            return draft_content

        audio_files = []
        for filename in os.listdir(text_reading_dir):
            if filename.startswith('audio') and filename.endswith('.wav'):
                audio_files.append(filename)

        audio_files.sort()

        if not audio_files:
            print(f"[警告] 没有找到audio*.wav文件")
            return draft_content

        audio_durations = {}

        try:
            import soundfile as sf
            use_soundfile = True
        except ImportError:
            use_soundfile = False

        for audio_file in audio_files:
            audio_path = os.path.join(text_reading_dir, audio_file)
            try:
                if use_soundfile:
                    info = sf.info(audio_path)
                    duration_seconds = info.duration
                else:
                    import wave
                    with wave.open(audio_path, 'rb') as wf:
                        frames = wf.getnframes()
                        rate = wf.getframerate()
                        duration_seconds = frames / float(rate)

                duration_us = int(duration_seconds * 1000000)
                audio_durations[audio_file] = {
                    'seconds': duration_seconds,
                    'microseconds': duration_us
                }
            except Exception as e:
                print(f"[错误] 读取 {audio_file} 失败: {str(e)}")
        
        # 更新draft_content中的audios素材和segments
        materials = draft_content.get('materials', {})
        audios = materials.get('audios', [])
        tracks = draft_content.get('tracks', [])

        for audio in audios:
            audio_type = audio.get('type', '')
            audio_name = audio.get('name', '')
            audio_path = audio.get('path', '')
            audio_id = audio.get('id', '')
            
            if audio_type != 'text_to_audio':
                continue
            
            matched_file = None
            for audio_file in audio_durations:
                base_name = audio_file.replace('.wav', '')
                if base_name in audio_path:
                    matched_file = audio_file
                    break
            
            if matched_file:
                audio['duration'] = audio_durations[matched_file]['microseconds']

                for track in tracks:
                    segments = track.get('segments', [])
                    for segment in segments:
                        material_id = segment.get('material_id')
                        if material_id == audio_id:
                            target_timerange = segment.get('target_timerange', {})
                            target_timerange['duration'] = audio_durations[matched_file]['microseconds']

                            source_timerange = segment.get('source_timerange')
                            if source_timerange is None:
                                source_timerange = {}
                                segment['source_timerange'] = source_timerange
                            source_timerange['duration'] = audio_durations[matched_file]['microseconds']

        return draft_content

    def sync_tts_and_subtitles(self, draft_content, news_data=None):
        """
        同步TTS音频和字幕的时序
        
        功能:
        1. 重新排布TTS音频片段的时序，每个音频之间保持0.8秒间隔
        2. 同步调整字幕片段的起止时间和时长，使其与TTS音频对齐
        3. 将贴纸定位到对应新闻矩形框的左下角
        
        Args:
            draft_content: 剪映草稿JSON数据
            news_data: 新闻数据列表，包含新闻的位置信息
            
        Returns:
            修改后的draft_content
        """
        import copy

        print("开始同步TTS音频和字幕时序...")
        
        # 深拷贝，避免修改原始数据
        data = copy.deepcopy(draft_content)
        
        try:
            # 获取当前图片的原始尺寸
            orig_image_width = 1600  # 默认值
            orig_image_height = 3200  # 默认值
            if hasattr(self, 'current_image_file') and self.current_image_file:
                try:
                    from PIL import Image
                    with Image.open(self.current_image_file) as img:
                        orig_image_width, orig_image_height = img.size
                except Exception:
                    pass
            
            # 获取materials中的audios
            materials = data.get('materials', {})
            audios = materials.get('audios', [])

            # 查找所有type为"text_to_audio"的TTS音频素材
            tts_audios = []
            for idx, audio in enumerate(audios):
                audio_type = audio.get('type')
                if audio_type == 'text_to_audio':
                    tts_info = {
                        'id': audio.get('id'),
                        'resource_id': audio.get('resource_id'),
                        'duration': audio.get('duration', 0),
                        'text_id': audio.get('text_id')
                    }
                    tts_audios.append(tts_info)

            if not tts_audios:
                print("[错误] 未找到TTS音频素材")
                return data

            # 获取tracks
            tracks = data.get('tracks', [])

            # 查找所有文本轨道、音频轨道和贴纸轨道
            text_tracks = []
            audio_tracks = []
            sticker_tracks = []

            for idx, track in enumerate(tracks):
                track_type = track.get('type')
                if track_type == 'text':
                    text_tracks.append(track)
                elif track_type == 'audio':
                    audio_tracks.append(track)
                elif track_type == 'sticker':
                    sticker_tracks.append(track)

            if not text_tracks or not audio_tracks:
                print("[错误] 未找到必要的轨道")
                return data

            # 获取所有文本片段
            text_segments = []
            for track in text_tracks:
                text_segments.extend(track.get('segments', []))
            
            # 建立text_id到文本片段的映射
            text_segment_map = {}
            for idx, segment in enumerate(text_segments):
                seg_id = segment.get('id')
                if seg_id:
                    text_segment_map[seg_id] = {
                        'segment': segment,
                        'original_order': idx
                    }

            # 获取所有音频片段和贴纸片段
            audio_segments = []
            for track in audio_tracks:
                audio_segments.extend(track.get('segments', []))

            sticker_segments = []
            for track in sticker_tracks:
                sticker_segments.extend(track.get('segments', []))

            # 收集text_to_audio类型的音频片段
            text_to_audio_segments = []
            tts_ids = [tts.get('id') for tts in tts_audios]

            for segment in audio_segments:
                material_id = segment.get('material_id')
                if material_id and material_id in tts_ids:
                    timerange = segment.get('target_timerange', {})
                    text_to_audio_segments.append({
                        'segment': segment,
                        'start': timerange.get('start', 0),
                        'duration': timerange.get('duration', 0),
                        'material_id': material_id
                    })

            # 按开始时间排序
            text_to_audio_segments.sort(key=lambda x: x['start'])

            # 建立material_id到音频片段的映射
            audio_segment_map = {}
            for segment in audio_segments:
                material_id = segment.get('material_id')
                if material_id:
                    if material_id not in audio_segment_map:
                        audio_segment_map[material_id] = []
                    audio_segment_map[material_id].append(segment)

            # 按时间顺序排序贴纸片段
            sorted_sticker_segments = []
            for segment in sticker_segments:
                timerange = segment.get('target_timerange', {})
                sorted_sticker_segments.append({
                    'segment': segment,
                    'start': timerange.get('start', 0)
                })

            # 按start时间排序
            sorted_sticker_segments.sort(key=lambda x: x['start'])

            # 建立material_id到贴纸片段的映射
            sticker_segment_map = {}
            for item in sorted_sticker_segments:
                segment = item['segment']
                material_id = segment.get('material_id')
                if material_id:
                    if material_id not in sticker_segment_map:
                        sticker_segment_map[material_id] = []
                    sticker_segment_map[material_id].append(segment)
            
            # 建立tts_id到原始开始时间的映射
            tts_id_to_original_start = {}
            for item in text_to_audio_segments:
                material_id = item.get('material_id')
                start = item.get('start', 0)
                tts_id_to_original_start[material_id] = start

            # 为TTS音频添加原始开始时间
            tts_with_order = []
            for tts in tts_audios:
                tts_id = tts.get('id')
                original_start = tts_id_to_original_start.get(tts_id, 0)
                tts_with_order.append({
                    **tts,
                    'original_start': original_start
                })

            # 按原始开始时间排序
            tts_with_order.sort(key=lambda x: x['original_start'])

            # 重新计算TTS音频的时序
            gap_us = 800000  # 0.8秒间隔

            # 获取第一条音频的原始起始时间作为基准
            base_start = tts_with_order[0].get('original_start', 0) if tts_with_order else 0
            current_time = base_start

            # 存储新的时间信息
            new_timing = []
            for tts in tts_with_order:
                duration = tts.get('duration', 0)
                new_timing.append({
                    'id': tts.get('id'),
                    'resource_id': tts.get('resource_id'),
                    'text_id': tts.get('text_id'),
                    'new_start': current_time,
                    'new_duration': duration
                })
                current_time += duration + gap_us

            # 计算视频素材的起始和结束时间
            video_start_time = current_time
            total_video_duration = current_time - base_start

            # 更新音频轨道中的TTS片段
            update_count = 0

            # 建立tts_id到timing的映射
            tts_id_to_timing = {}
            for timing in new_timing:
                tts_id = timing.get('id')
                if tts_id:
                    tts_id_to_timing[tts_id] = timing
            
            # 按照排序后的text_to_audio音频片段顺序进行处理
            for item in text_to_audio_segments:
                segment = item['segment']
                material_id = segment.get('material_id')

                if material_id and material_id in tts_id_to_timing:
                    timing = tts_id_to_timing[material_id]

                    if 'target_timerange' not in segment:
                        segment['target_timerange'] = {}
                    segment['target_timerange']['start'] = timing.get('new_start', 0)
                    segment['target_timerange']['duration'] = timing.get('new_duration', 0)

                    # 同步更新source_timerange的duration
                    if 'source_timerange' not in segment:
                        segment['source_timerange'] = {}
                    segment['source_timerange']['duration'] = timing.get('new_duration', 0)

                    update_count += 1

            # 更新文本轨道中的字幕片段
            material_to_text_map = {}
            for seg_id, seg_info in text_segment_map.items():
                seg = seg_info.get('segment', {})
                material_id = seg.get('material_id')
                if material_id:
                    material_to_text_map[material_id] = seg

            text_position_map = {}
            update_count = 0
            for idx, timing in enumerate(new_timing):
                text_id = timing.get('text_id')
                if text_id and text_id in material_to_text_map:
                    text_seg = material_to_text_map[text_id]

                    if 'target_timerange' not in text_seg:
                        text_seg['target_timerange'] = {}
                    text_seg['target_timerange']['start'] = timing.get('new_start', 0)
                    text_seg['target_timerange']['duration'] = timing.get('new_duration', 0)

                    tts_id = timing.get('id')
                    if 'text_to_audio_ids' not in text_seg:
                        text_seg['text_to_audio_ids'] = []
                    if tts_id not in text_seg['text_to_audio_ids']:
                        text_seg['text_to_audio_ids'].append(tts_id)

                    position = text_seg.get('position', {})
                    size = text_seg.get('size', {})
                    text_position_map[idx] = {
                        'position': position,
                        'size': size
                    }

                    update_count += 1
            
            # 计算最后一个字幕的结束时间 + 0.4 秒
            last_subtitle_end = 0
            for timing in new_timing:
                subtitle_end = timing.get('new_start', 0) + timing.get('new_duration', 0)
                if subtitle_end > last_subtitle_end:
                    last_subtitle_end = subtitle_end
            gap_04s = 400000
            last_position_start = last_subtitle_end + gap_04s

            materials = data.get('materials', {})
            last_position_ids = []
            for material_type in ['videos', 'audios', 'texts', 'stickers', 'images', 'effects']:
                type_list = materials.get(material_type, [])
                for item in type_list:
                    if item.get('local_id') == '最后位置' or item.get('name') == '最后位置':
                        last_position_ids.append(item.get('id'))

            tracks = data.get('tracks', [])
            for track_idx, track in enumerate(tracks):
                segments = track.get('segments', [])
                for seg_idx, segment in enumerate(segments):
                    material_id = segment.get('material_id', '')
                    if material_id in last_position_ids:
                        segment_duration = segment.get('target_timerange', {}).get('duration', 0)
                        old_start = segment.get('target_timerange', {}).get('start', 0)
                        segment['target_timerange']['start'] = last_position_start
                        print(f"[已更新] 轨道{track_idx} 片段{seg_idx}: start {old_start} → {last_position_start}, segment_duration={segment_duration}")
                        total_video_duration = last_position_start + segment_duration

            # 收集所有贴纸片段并按时间排序
            all_sticker_segments = []
            for track in sticker_tracks:
                for seg in track.get('segments', []):
                    timerange = seg.get('target_timerange', {})
                    all_sticker_segments.append({
                        'segment': seg,
                        'start': timerange.get('start', 0)
                    })

            stickers_materials = materials.get('stickers', [])
            material_id_to_name = {}
            for sticker in stickers_materials:
                material_id_to_name[sticker.get('id', '')] = sticker.get('name', '')

            sorted_sticker_segments = sorted(all_sticker_segments, key=lambda x: x['start'])

            update_count = 0
            for idx, timing in enumerate(new_timing):
                found_matching_sticker = False
                for si in range(len(sorted_sticker_segments)):
                    sticker_item = sorted_sticker_segments[si]
                    sticker_seg = sticker_item['segment']
                    material_id = sticker_seg.get('material_id', '')
                    sticker_name = material_id_to_name.get(material_id, '')

                    if sticker_name != "春日晴天-卡通太阳遮挡":
                        continue

                    found_matching_sticker = True

                    if 'target_timerange' not in sticker_seg:
                        sticker_seg['target_timerange'] = {}
                    sticker_seg['target_timerange']['start'] = timing.get('new_start', 0)
                    sticker_seg['target_timerange']['duration'] = timing.get('new_duration', 0)

                    if news_data and idx < len(news_data):
                        news = news_data[idx]
                        position = news.get('position', [0, 0, 0, 0])
                        if len(position) == 4:
                            x1, y1, x2, y2 = position
                            news_center_x = (x1 + x2) / 2
                            news_center_y = (y1 + y2) / 2

                            newspaper_type = self._detect_newspaper_type(news)
                            video_width, video_height = self._get_video_dimensions()
                            paper_config = self._get_newspaper_config(newspaper_type)

                            transform_x, transform_y = self._calculate_sticker_transform(
                                news_center_x, news_center_y,
                                paper_config, video_width, video_height,
                                orig_image_width, orig_image_height
                            )

                            if 'clip' not in sticker_seg:
                                sticker_seg['clip'] = {}
                            if 'transform' not in sticker_seg['clip']:
                                sticker_seg['clip']['transform'] = {}

                            sticker_seg['clip']['transform']['x'] = transform_x
                            sticker_seg['clip']['transform']['y'] = transform_y

                    update_count += 1
                    sorted_sticker_segments.pop(si)
                    break

            # 处理 photo 素材（P1.jpg, P2.jpg 等）的位置
            photos_to_align = []
            videos_list = materials.get('videos', [])
            for video in videos_list:
                material_name = video.get('material_name', '')
                if material_name and material_name.startswith('P') and material_name.endswith('.jpg'):
                    import re
                    if re.match(r'^P\d+\.jpg$', material_name):
                        photos_to_align.append({
                            'id': video.get('id'),
                            'material_name': material_name,
                            'item': video,
                        })

            photos_to_align.sort(key=lambda x: x['material_name'])

            # 计算每个 photo 的位置
            gap_04s = 400000
            if photos_to_align and new_timing:
                for idx_photo, photo_info in enumerate(photos_to_align):
                    photo_id = photo_info['id']
                    photo_item = photo_info['item']

                    if idx_photo < len(new_timing):
                        timing = new_timing[idx_photo]
                        audio_start = timing.get('new_start', 0)
                        audio_end = audio_start + timing.get('new_duration', 0)
                        new_end = audio_end + gap_04s

                        for track in data.get('tracks', []):
                            for segment in track.get('segments', []):
                                if segment.get('material_id') == photo_id:
                                    old_seg_start = segment.get('target_timerange', {}).get('start', 0)
                                    old_seg_duration = segment.get('target_timerange', {}).get('duration', 0)

                                    if idx_photo == 0:
                                        new_start = old_seg_start
                                        new_duration = new_end - old_seg_start
                                        segment['target_timerange']['start'] = new_start
                                        segment['target_timerange']['duration'] = new_duration
                                    else:
                                        # P2及以后的图片，开始位置减少0.4秒，避免空白
                                        new_start = audio_start - gap_04s
                                        new_duration = new_end - new_start
                                        segment['target_timerange']['start'] = new_start
                                        segment['target_timerange']['duration'] = new_duration

                                    photo_item['duration'] = new_duration
                                    break

            # 处理视频素材
            video_material_local_id = "adfc1f13-688a-4cce-8472-3b31aa079b30"
            target_video_id = "E42351AB-2F8B-4159-9C19-7CD524DD53C8"

            video_duration = 0
            video_material_id = None
            videos = materials.get('videos', [])
            for video in videos:
                if video.get('local_material_id') == video_material_local_id:
                    video_duration = video.get('duration', 0)
                    video_material_id = video.get('id')
                    break

            if video_duration > 0 and video_material_id:
                video_end_time = video_start_time + video_duration
                video_material_updated = False

                for track_idx, track in enumerate(data.get('tracks', [])):
                    segments = track.get('segments', [])
                    for segment in segments:
                        seg_material_id = segment.get('material_id')
                        if seg_material_id == video_material_id:
                            segment['target_timerange']['start'] = video_start_time
                            segment['target_timerange']['duration'] = video_duration
                            video_material_updated = True
                            break
                    if video_material_updated:
                        break
                
                if not video_material_updated:
                    print(f"[警告] 未找到视频素材片段: material_id={video_material_id}")
                else:
                    materials_to_align = [
                        {"type": "audio", "id": "0375B918-9C67-4dad-A791-E8DF540B04A4", "name": "新品发布"},
                        {"type": "audio", "id": "4C5380AE-3F65-488f-B887-C977206F83E8", "name": "时尚商务节奏 企业"},
                        {"type": "text", "id": "4F5AEA3A-6BDF-4933-8DE1-EC31E979E97F", "name": "文本1"},
                        {"type": "text", "id": "7453700C-DD8B-44d8-91DA-05690591DCA9", "name": "文本2"},
                        {"type": "text", "id": "F2A47FCE-BA46-402b-8EC2-FFA641BA706C", "name": "文本3"},
                        {"type": "video", "id": "E42351AB-2F8B-4159-9C19-7CD524DD53C8", "name": "金融时报0318.jpg"}
                    ]

                    for material_info in materials_to_align:
                        material_id = material_info["id"]
                        material_type = material_info["type"]

                        for track in data.get('tracks', []):
                            segments = track.get('segments', [])
                            for segment in segments:
                                seg_material_id = segment.get('material_id')
                                if seg_material_id == material_id:
                                    old_start = segment.get('target_timerange', {}).get('start', 0)
                                    new_duration = video_end_time - old_start

                                    segment['target_timerange']['duration'] = new_duration

                                    if material_type == 'audio':
                                        if 'source_timerange' not in segment:
                                            segment['source_timerange'] = {}
                                        segment['source_timerange']['duration'] = new_duration
                                    break
            else:
                if not video_material_id:
                    print(f"[错误] 未找到视频素材: local_material_id={video_material_local_id}")
                elif video_duration == 0:
                    print(f"[错误] 视频素材duration为0")

            # 计算最终视频总时长
            last_position_track_duration = 0
            for track in data.get('tracks', []):
                for segment in track.get('segments', []):
                    if segment.get('material_id') in last_position_ids:
                        seg_duration = segment.get('target_timerange', {}).get('duration', 0)
                        seg_start = segment.get('target_timerange', {}).get('start', 0)
                        seg_end = seg_start + seg_duration
                        if seg_end > last_position_track_duration:
                            last_position_track_duration = seg_duration

            if last_position_ids and last_position_track_duration > 0:
                final_total_duration = last_subtitle_end + gap_04s + last_position_track_duration
            else:
                final_total_duration = last_subtitle_end + gap_04s + 2000000

            data['duration'] = final_total_duration

            # 更新指定ID的素材duration为视频总时长
            global_track_ids = [
                "4F5AEA3A-6BDF-4933-8DE1-EC31E979E97F",
                "7453700C-DD8B-44d8-91DA-05690591DCA9",
                "6D615812-D534-4a33-8A98-282CF7D86ED7",
                "C8069C58-C619-4b7f-9D11-62526E90AB21"
            ]

            audios_list = materials.get('audios', [])
            for audio_item in audios_list:
                if audio_item.get('type') == 'music':
                    music_id = audio_item.get('id')
                    if music_id:                                                                                                            
                        global_track_ids.append(music_id)

            matched_materials = []

            for item_id in global_track_ids:                                                                    
                for material_type in ['videos', 'audios', 'texts', 'stickers', 'images', 'effects']:
                    type_list = materials.get(material_type, [])
                    for item in type_list:
                        if item.get('id') == item_id:
                            item['duration'] = final_total_duration
                            matched_materials.append(item_id)
                            break
                    if item_id in matched_materials:
                        break

            if not matched_materials:
                print(f"未找到指定ID的素材")
            else:
                for track in data.get('tracks', []):
                    segments = track.get('segments', [])
                    for segment in segments:
                        material_id = segment.get('material_id')
                        if material_id in matched_materials:
                            segment['target_timerange']['duration'] = final_total_duration
                            source_timerange = segment.get('source_timerange')
                            if source_timerange is not None:
                                source_timerange['duration'] = final_total_duration

            # 处理时间长度显示
            display_text_id = "4F5AEA3A-6BDF-4933-8DE1-EC31E979E97F"
            total_seconds = int(final_total_duration / 1000000)

            if 'materials' in data and 'texts' in data['materials']:
                for text_item in data['materials']['texts']:
                    text_id = text_item.get('id')
                    if text_id == display_text_id:
                        content_str = text_item.get('content', '')
                        if content_str:
                            try:
                                content_obj = json.loads(content_str)
                                new_text = f"{total_seconds}秒"
                                content_obj['text'] = new_text
                                text_item['content'] = json.dumps(content_obj, ensure_ascii=False)
                            except json.JSONDecodeError:
                                text_item['content'] = f"{total_seconds}秒"
                        else:
                            text_item['content'] = f"{total_seconds}秒"
                        break

            print(f"处理完成，总时长: {total_seconds}秒")
            return data
            
        except Exception as e:
            print(f"同步TTS和字幕时序失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return draft_content
    
    def process_jianying_draft_timing(self):
        """处理剪映草稿时序"""
        try:
            if not self.current_image_file:
                self.show_warning("警告", "请先选择一张报纸图片")
                return
            
            # 检查是否有新闻数据
            if not self.video_data:
                self.show_warning("警告", "没有新闻数据，请先生成或加载视频数据")
                return
            
            # 获取图片名称（不含扩展名）
            image_filename = os.path.basename(self.current_image_file)
            base_name = os.path.splitext(image_filename)[0]
            
            # 获取当前日期
            today = datetime.datetime.now()
            date_str = today.strftime("%Y%m%d")
            
            # 生成草稿目录名称（图片名+日期）
            draft_name = f"{base_name}_{date_str}"
            
            # 生成草稿目录路径
            draft_dir = os.path.join(self.jianying_drafts_dir, draft_name)
            
            # 检查目录是否存在
            if not os.path.exists(draft_dir):
                self.show_warning("警告", f"剪映草稿目录不存在: {draft_dir}")
                return
            
            # 读取draft_content.json文件
            draft_content_file = os.path.join(draft_dir, "draft_content.json")
            if not os.path.exists(draft_content_file):
                self.show_warning("警告", f"draft_content.json文件不存在: {draft_content_file}")
                return
            
            # 读取JSON文件
            with open(draft_content_file, 'r', encoding='utf-8') as f:
                draft_content = json.load(f)
            
            # 步骤1: 同步语音文件时长（从textReading目录读取实际语音文件时长）
            draft_content = self.sync_audio_durations(draft_dir, draft_content)
            
            # 步骤2: 同步TTS和字幕时序
            updated_content = self.sync_tts_and_subtitles(draft_content, self.video_data)
            
            # 保存更新后的JSON文件
            with open(draft_content_file, 'w', encoding='utf-8') as f:
                json.dump(updated_content, f, ensure_ascii=False, indent=2)
            
            print(f"剪映草稿时序处理完成: {draft_content_file}")
            self.show_info("成功", f"剪映草稿时序处理完成!\n\n目录: {draft_dir}")
            
        except Exception as e:
            print(f"处理剪映草稿时序失败: {str(e)}")
            self.show_error("错误", f"处理剪映草稿时序失败: {str(e)}")
    
    def _detect_newspaper_type(self, news):
        """检测报纸类型"""
        # 从新闻标题或内容中检测报纸类型
        title = news.get('title', '')
        content = news.get('content', '')
        
        # 检查关键词
        if '金融时报' in title or '金融时报' in content:
            return '金融时报'
        elif '华尔街日报' in title or '华尔街日报' in content:
            return '华尔街日报'
        
        # 默认返回金融时报
        return '金融时报'
    
    def _get_video_dimensions(self):
        """获取视频尺寸"""
        # 从配置中获取视频尺寸
        if hasattr(self, 'config') and self.config:
            video_settings = self.config.get('video_settings', {})
            width = video_settings.get('width', 1500)
            height = video_settings.get('height', 3200)
            return width, height
        # 默认值
        return 1500, 3200
    
    def _get_newspaper_config(self, newspaper_type):
        """获取报纸配置"""
        if hasattr(self, 'config') and self.config:
            newspaper_position = self.config.get('newspaper_position', {})
            config = newspaper_position.get(newspaper_type, {})
            if config:
                return config
        
        # 默认配置
        return {
            'x': 100,
            'y': 200,
            'width': 1300,
            'height': 2800
        }
    
    def _calculate_sticker_transform(self, news_center_x, news_center_y, paper_config, video_width, video_height, orig_image_width=1600, orig_image_height=3200):
        """
        计算贴纸在视频中的transform位置（比例值）
        
        参数:
            news_center_x: 新闻在报纸图片中的中心点x坐标
            news_center_y: 新闻在报纸图片中的中心点y坐标
            paper_config: 报纸在视频中的配置 {x, y, width, height}
            video_width: 视频宽度
            video_height: 视频高度
            orig_image_width: 报纸图片原始宽度
            orig_image_height: 报纸图片原始高度
            
        返回:
            transform_x, transform_y: 相对于视频尺寸的比例值
        """
        # 报纸在视频中的位置和尺寸
        paper_x = paper_config.get('x', 100)
        paper_y = paper_config.get('y', 200)
        paper_width = paper_config.get('width', 1300)
        paper_height = paper_config.get('height', 2800)
        
        # 使用传入的图片原始尺寸
        orig_paper_width = orig_image_width
        orig_paper_height = orig_image_height
        
        # 计算新闻中心点在报纸图片中的比例位置
        news_ratio_x = news_center_x / orig_paper_width
        news_ratio_y = news_center_y / orig_paper_height
        
        # 计算新闻中心点在视频中的实际像素位置
        video_pixel_x = paper_x + news_ratio_x * paper_width
        video_pixel_y = paper_y + news_ratio_y * paper_height
        
        # 转换为比例值（相对于视频尺寸，左下角为-1,-1，右上角为1,1，中间为0,0）
        # 计算相对于视频中心的位置
        center_x = video_width / 2
        center_y = video_height / 2
        
        # 计算偏移量（相对于中心）
        offset_x = video_pixel_x - center_x
        offset_y = video_pixel_y - center_y
        
        # 转换为-1到1的范围
        transform_x = (offset_x / center_x)
        transform_y = (offset_y / center_y)
        
        # 注意：y轴方向通常是相反的，需要反转
        transform_y = -transform_y
        
        return transform_x, transform_y