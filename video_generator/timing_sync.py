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
        print("=" * 60)
        print("开始同步语音文件时长...")
        print("=" * 60)
        
        text_reading_dir = os.path.join(draft_dir, 'textReading')
        print(f"[调试] textReading目录: {text_reading_dir}")
        print(f"[调试] 目录是否存在: {os.path.exists(text_reading_dir)}")
        
        # 检查textReading目录是否存在
        if not os.path.exists(text_reading_dir):
            print(f"[警告] textReading目录不存在: {text_reading_dir}")
            return draft_content
        
        # 查找所有audio*.wav文件
        audio_files = []
        for filename in os.listdir(text_reading_dir):
            if filename.startswith('audio') and filename.endswith('.wav'):
                audio_files.append(filename)
        
        audio_files.sort()  # 按文件名排序
        
        if not audio_files:
            print(f"[警告] textReading目录下没有找到audio*.wav文件")
            print(f"[调试] 目录内容: {os.listdir(text_reading_dir)}")
            return draft_content
        
        print(f"[步骤1] 找到 {len(audio_files)} 个语音文件:")
        
        # 获取每个语音文件的时长
        audio_durations = {}
        
        # 尝试使用soundfile读取
        try:
            import soundfile as sf
            use_soundfile = True
            print("[调试] 使用soundfile读取音频时长")
        except ImportError:
            use_soundfile = False
            print("[调试] soundfile不可用，尝试使用wave")
        
        for audio_file in audio_files:
            audio_path = os.path.join(text_reading_dir, audio_file)
            try:
                if use_soundfile:
                    # 使用soundfile读取
                    info = sf.info(audio_path)
                    duration_seconds = info.duration
                else:
                    # 使用wave读取
                    import wave
                    with wave.open(audio_path, 'rb') as wf:
                        frames = wf.getnframes()
                        rate = wf.getframerate()
                        duration_seconds = frames / float(rate)
                
                # 转换为微秒（项目使用微秒作为时间单位）
                duration_us = int(duration_seconds * 1000000)
                audio_durations[audio_file] = {
                    'seconds': duration_seconds,
                    'microseconds': duration_us
                }
                print(f"  {audio_file}: {duration_seconds:.2f}秒 ({duration_us}微秒)")
            except Exception as e:
                print(f"  [错误] 读取 {audio_file} 失败: {str(e)}")
        
        # 更新draft_content中的audios素材
        materials = draft_content.get('materials', {})
        audios = materials.get('audios', [])
        
        print(f"\n[步骤2] 匹配并更新audios素材...")
        
        updated_count = 0
        for audio in audios:
            audio_type = audio.get('type', '')
            audio_name = audio.get('name', '')
            audio_path = audio.get('path', '')
            
            if audio_type != 'text_to_audio':
                continue
            
            matched_file = None
            for audio_file in audio_durations:
                base_name = audio_file.replace('.wav', '')
                if base_name in audio_path:
                    matched_file = audio_file
                    break
            
            if matched_file:
                old_duration = audio.get('duration', 0)
                new_duration = audio_durations[matched_file]['microseconds']
                duration_sec = audio_durations[matched_file]['seconds']
                
                audio['duration'] = new_duration
                
                print(f"  [更新] {audio_name}: {old_duration/1e6:.2f}秒 → {duration_sec:.2f}秒")
                updated_count += 1
        
        print(f"\n共更新 {updated_count} 个音频素材的duration")

        print(f"\n[步骤3] 同步segments中的source_timerange与target_timerange...")
        tracks = draft_content.get('tracks', [])

        for track in tracks:
            segments = track.get('segments', [])
            for segment in segments:
                material_id = segment.get('material_id')
                target_timerange = segment.get('target_timerange', {})
                source_timerange = segment.get('source_timerange')

                # 确保source_timerange是字典
                if source_timerange is None:
                    source_timerange = {}
                    segment['source_timerange'] = source_timerange

                target_duration = target_timerange.get('duration', 0)
                source_duration = source_timerange.get('duration', 0)

                if target_duration != source_duration and target_duration > 0:
                    old_source_duration = source_duration
                    source_timerange['duration'] = target_duration
                    print(f"  [同步] material_id={material_id}: source_timerange.duration {old_source_duration} → {target_duration}")

        print(f"\nsegments中的source_timerange同步完成")
        print("=" * 60)
        print("语音文件时长同步完成")
        print("=" * 60)

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
        
        print("=" * 60)
        print("开始同步TTS音频和字幕时序...")
        print("=" * 60)
        
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
                        print(f"[信息] 图片原始尺寸: {orig_image_width}x{orig_image_height}")
                except Exception as e:
                    print(f"[警告] 无法读取图片尺寸: {e}")
            
            # 获取materials中的audios
            materials = data.get('materials', {})
            audios = materials.get('audios', [])
            print(f"[步骤1] 从materials中获取到 {len(audios)} 个音频素材")
            
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
                    print(f"  [TTS-{len(tts_audios)}] ID={tts_info['id']}, resource_id={tts_info['resource_id']}, text_id={tts_info['text_id']}, duration={tts_info['duration']}")
            
            if not tts_audios:
                print("[错误] 未找到text_to_audio类型的音频素材")
                return data
            
            print(f"[步骤2] 找到 {len(tts_audios)} 个TTS音频素材")
            
            # 获取tracks
            tracks = data.get('tracks', [])
            print(f"[步骤3] 获取到 {len(tracks)} 个轨道")
            
            # 查找所有文本轨道(type: "text")、所有音频轨道(type: "audio")和所有贴纸轨道(type: "sticker")
            text_tracks = []
            audio_tracks = []
            sticker_tracks = []
            
            for idx, track in enumerate(tracks):
                track_type = track.get('type')
                seg_count = len(track.get('segments', []))
                print(f"  [轨道-{idx+1}] type={track_type}, segments={seg_count}")
                if track_type == 'text':
                    text_tracks.append(track)
                elif track_type == 'audio':
                    audio_tracks.append(track)
                elif track_type == 'sticker':
                    sticker_tracks.append(track)
            
            if not text_tracks:
                print("[错误] 未找到文本轨道(type: text)")
                return data
            print(f"[步骤4] 找到 {len(text_tracks)} 个文本轨道")
            
            if not audio_tracks:
                print("[错误] 未找到音频轨道(type: audio)")
                return data
            print(f"[步骤5] 找到 {len(audio_tracks)} 个音频轨道")
            
            print(f"[步骤6] 找到 {len(sticker_tracks)} 个贴纸轨道")
            
            # 获取所有文本片段（从所有文本轨道中）
            text_segments = []
            print(f"[步骤6] 从所有文本轨道中获取文本片段:")
            for track_idx, track in enumerate(text_tracks):
                track_segments = track.get('segments', [])
                print(f"  [文本轨道-{track_idx+1}] 包含 {len(track_segments)} 个片段")
                for seg_idx, seg in enumerate(track_segments):
                    seg_id = seg.get('id')
                    print(f"    [片段-{seg_idx+1}] id={seg_id}")
                text_segments.extend(track_segments)
            print(f"  总计获取到 {len(text_segments)} 个文本片段")
            
            # 建立text_id到文本片段的映射（包含原始顺序）
            text_segment_map = {}
            print(f"[步骤7] 建立text_id到文本片段的映射（包含原始顺序）:")
            print(f"  TTS音频的text_id列表: {[tts.get('text_id') for tts in tts_audios]}")
            for idx, segment in enumerate(text_segments):
                seg_id = segment.get('id')
                timerange = segment.get('target_timerange', {})
                start = timerange.get('start', 0)
                duration = timerange.get('duration', 0)
                text_to_audio_ids = segment.get('text_to_audio_ids', [])
                material_id = segment.get('material_id')
                # 输出文本片段的所有关键字段
                print(f"  [文本-{idx+1}] id={seg_id}, start={start}, duration={duration}, text_to_audio_ids={text_to_audio_ids}, material_id={material_id}")
                if seg_id:
                    text_segment_map[seg_id] = {
                        'segment': segment,
                        'original_order': idx  # 记录原始顺序
                    }
            print(f"  共建立 {len(text_segment_map)} 个文本片段映射")
            print(f"  文本映射中的id列表: {list(text_segment_map.keys())}")
            
            # 获取所有音频片段（从所有音频轨道中）
            audio_segments = []
            for track in audio_tracks:
                audio_segments.extend(track.get('segments', []))
            print(f"[步骤8] 从所有音频轨道中获取到 {len(audio_segments)} 个音频片段")
            
            # 获取所有贴纸片段（从所有贴纸轨道中）
            sticker_segments = []
            for track in sticker_tracks:
                sticker_segments.extend(track.get('segments', []))
            print(f"[步骤9] 从所有贴纸轨道中获取到 {len(sticker_segments)} 个贴纸片段")
            
            # 收集所有text_to_audio类型的音频片段（不管属于哪个track）
            print(f"[步骤8.5] 收集并排序text_to_audio类型的音频片段:")
            text_to_audio_segments = []
            tts_ids = [tts.get('id') for tts in tts_audios]
            print(f"  TTS音频ID列表: {tts_ids}")
            
            for idx, segment in enumerate(audio_segments):
                material_id = segment.get('material_id')
                if material_id and material_id in tts_ids:
                    timerange = segment.get('target_timerange', {})
                    start = timerange.get('start', 0)
                    duration = timerange.get('duration', 0)
                    text_to_audio_segments.append({
                        'segment': segment,
                        'start': start,
                        'duration': duration,
                        'material_id': material_id
                    })
                    print(f"  [TTS音频片段-{len(text_to_audio_segments)}] material_id={material_id}, start={start}, duration={duration}")
            
            # 按开始时间排序
            text_to_audio_segments.sort(key=lambda x: x['start'])
            print(f"  排序后的text_to_audio音频片段顺序:")
            for idx, item in enumerate(text_to_audio_segments):
                print(f"  [排序-{idx+1}] material_id={item['material_id']}, start={item['start']}, duration={item['duration']}")
            print(f"  共 {len(text_to_audio_segments)} 个text_to_audio音频片段")
            
            # 建立material_id到音频片段的映射（一个material_id可能对应多个片段）
            audio_segment_map = {}
            print(f"[步骤9] 建立material_id到音频片段的映射:")
            print(f"  TTS音频的resource_id列表: {[tts.get('resource_id') for tts in tts_audios]}")
            for idx, segment in enumerate(audio_segments):
                material_id = segment.get('material_id')
                timerange = segment.get('target_timerange', {})
                start = timerange.get('start', 0)
                duration = timerange.get('duration', 0)
                # 输出音频片段的所有关键字段
                print(f"  [音频-{idx+1}] material_id={material_id}, start={start}, duration={duration}")
                if material_id:
                    # 使用列表存储，因为一个material_id可能对应多个片段
                    if material_id not in audio_segment_map:
                        audio_segment_map[material_id] = []
                    audio_segment_map[material_id].append(segment)
            print(f"  共建立 {len(audio_segment_map)} 个material_id映射")
            print(f"  音频映射中的material_id列表: {list(audio_segment_map.keys())}")
            
            # 按时间顺序排序贴纸片段（用于与文本片段对应）
            print(f"[步骤12] 按时间顺序排序贴纸片段:")
            sorted_sticker_segments = []
            for idx, segment in enumerate(sticker_segments):
                material_id = segment.get('material_id')
                timerange = segment.get('target_timerange', {})
                start = timerange.get('start', 0)
                duration = timerange.get('duration', 0)
                # 输出贴纸片段的所有关键字段
                print(f"  [贴纸-{idx+1}] material_id={material_id}, start={start}, duration={duration}")
                sorted_sticker_segments.append({
                    'segment': segment,
                    'start': start
                })
            
            # 按start时间排序
            sorted_sticker_segments.sort(key=lambda x: x['start'])
            print(f"  排序后的贴纸片段顺序:")
            for idx, item in enumerate(sorted_sticker_segments):
                segment = item['segment']
                material_id = segment.get('material_id')
                start = item['start']
                print(f"  [排序-{idx+1}] material_id={material_id}, start={start}")
            print(f"  共找到 {len(sorted_sticker_segments)} 个贴纸片段")
                
                # 建立material_id到贴纸片段的映射（一个material_id可能对应多个片段）
            sticker_segment_map = {}
            print(f"  建立material_id到贴纸片段的映射:")
            for item in sorted_sticker_segments:
                segment = item['segment']
                material_id = segment.get('material_id')
                if material_id:
                    if material_id not in sticker_segment_map:
                        sticker_segment_map[material_id] = []
                    sticker_segment_map[material_id].append(segment)
            print(f"  共建立 {len(sticker_segment_map)} 个material_id映射")
            print(f"  贴纸映射中的material_id列表: {list(sticker_segment_map.keys())}")
            
            # 按text_to_audio音频片段的开始时间排序
            print(f"[步骤10] 按text_to_audio音频片段的开始时间排序:")
            
            # 建立tts_id到原始开始时间的映射
            tts_id_to_original_start = {}
            for item in text_to_audio_segments:
                material_id = item.get('material_id')
                start = item.get('start', 0)
                tts_id_to_original_start[material_id] = start
            
            # 为TTS音频添加原始开始时间
            tts_with_order = []
            for idx, tts in enumerate(tts_audios):
                tts_id = tts.get('id')
                original_start = tts_id_to_original_start.get(tts_id, 0)
                tts_with_order.append({
                    **tts,
                    'original_start': original_start
                })
                print(f"  [TTS-{idx+1}] id={tts_id}, original_start={original_start}")

            # 按原始开始时间排序
            tts_with_order.sort(key=lambda x: x['original_start'])
            print(f"[步骤11] 排序后的TTS音频顺序:")
            for idx, tts in enumerate(tts_with_order):
                print(f"  [排序-{idx+1}] id={tts['id']}, text_id={tts['text_id']}, original_start={tts['original_start']}")
            
            # 重新计算TTS音频的时序
            # 间隔: 0.8秒 = 800,000微秒
            gap_us = 800000  # 微秒
            current_time = 0
            
            print(f"[步骤12] 重新计算TTS音频时序 (间隔={gap_us}微秒=0.8秒):")
            
            # 存储新的时间信息
            new_timing = []
            for idx, tts in enumerate(tts_with_order):
                duration = tts.get('duration', 0)
                new_timing.append({
                    'id': tts.get('id'),
                    'resource_id': tts.get('resource_id'),
                    'text_id': tts.get('text_id'),
                    'new_start': current_time,
                    'new_duration': duration
                })
                print(f"  [计算-{idx+1}] id={tts.get('id')}, new_start={current_time}, duration={duration}")
                # 下一个音频的起始时间 = 当前起始时间 + 当前时长 + 间隔
                current_time += duration + gap_us
            
            print(f"[步骤13] 共重新排布 {len(new_timing)} 个TTS音频片段")
            
            # 计算视频素材的起始和结束时间
            video_start_time = current_time  # 最后一个音频结束后+0.8秒
            print(f"[步骤17] 计算视频素材时间: start={video_start_time}")
            print(f"  最后一个音频的结束时间: {current_time - gap_us} (不包含0.8秒间隔)")
            print(f"  视频素材开始时间: {video_start_time} (包含0.8秒间隔)")
            
            # 更新音频轨道中的TTS片段（按照排序后的text_to_audio音频片段顺序）
            print(f"[步骤14] 更新音频轨道中的TTS片段:")
            print(f"  音频映射中的material_id列表: {list(audio_segment_map.keys())}")
            print(f"  使用TTS音频的id进行匹配")
            update_count = 0
            
            # 建立tts_id到timing的映射
            tts_id_to_timing = {}
            for timing in new_timing:
                tts_id = timing.get('id')
                if tts_id:
                    tts_id_to_timing[tts_id] = timing
            
            # 按照排序后的text_to_audio音频片段顺序进行处理
            for idx, item in enumerate(text_to_audio_segments):
                segment = item['segment']
                material_id = segment.get('material_id')
                
                # 检查这个音频片段是否是TTS音频
                if material_id and material_id in tts_id_to_timing:
                    timing = tts_id_to_timing[material_id]
                    old_start = segment.get('target_timerange', {}).get('start', 0)
                    old_duration = segment.get('target_timerange', {}).get('duration', 0)
                    
                    # 更新target_timerange
                    if 'target_timerange' not in segment:
                        segment['target_timerange'] = {}
                    segment['target_timerange']['start'] = timing.get('new_start', 0)
                    segment['target_timerange']['duration'] = timing.get('new_duration', 0)
                    
                    update_count += 1
                    print(f"  [音频更新-{update_count}] material_id={material_id}")
                    print(f"    旧: start={old_start}, duration={old_duration}")
                    print(f"    新: start={timing.get('new_start')}, duration={timing.get('new_duration')}")
                
            print(f"  共更新 {update_count} 个音频片段")
            
            # 更新文本轨道中的字幕片段
            print(f"[步骤15] 更新文本轨道中的字幕片段:")
            print(f"  文本映射中的id列表: {list(text_segment_map.keys())}")
            print(f"  使用TTS音频的text_id匹配文本片段的material_id")
            
            # 建立material_id到文本片段的映射
            material_to_text_map = {}
            for seg_id, seg_info in text_segment_map.items():
                seg = seg_info.get('segment', {})
                material_id = seg.get('material_id')
                if material_id:
                    material_to_text_map[material_id] = seg
            print(f"  建立material_id到文本片段的映射: {list(material_to_text_map.keys())}")
            
            # 存储文本片段的位置信息，用于贴纸定位
            text_position_map = {}
            update_count = 0
            for idx, timing in enumerate(new_timing):
                # 使用TTS音频的text_id（不是id）来匹配文本片段的material_id
                text_id = timing.get('text_id')
                print(f"  [处理-{idx+1}] 查找text_id={text_id}（匹配文本片段的material_id）")
                if text_id and text_id in material_to_text_map:
                    text_seg = material_to_text_map[text_id]
                    old_start = text_seg.get('target_timerange', {}).get('start', 0)
                    old_duration = text_seg.get('target_timerange', {}).get('duration', 0)
                    old_material_id = text_seg.get('material_id')
                    # 更新target_timerange
                    if 'target_timerange' not in text_seg:
                        text_seg['target_timerange'] = {}
                    text_seg['target_timerange']['start'] = timing.get('new_start', 0)
                    text_seg['target_timerange']['duration'] = timing.get('new_duration', 0)
                    
                    # 确保material_id和text_to_audio_ids与TTS音频素材的id一致
                    tts_id = timing.get('id')
                    if 'text_to_audio_ids' not in text_seg:
                        text_seg['text_to_audio_ids'] = []
                    if tts_id not in text_seg['text_to_audio_ids']:
                        text_seg['text_to_audio_ids'].append(tts_id)
                    
                    # 存储文本片段的位置信息
                    position = text_seg.get('position', {})
                    size = text_seg.get('size', {})
                    text_position_map[idx] = {
                        'position': position,
                        'size': size
                    }
                    print(f"  文本片段位置: position={position}, size={size}")
                    
                    update_count += 1
                    print(f"  [字幕更新-{update_count}] text_id={text_id}")
                    print(f"    旧: start={old_start}, duration={old_duration}, material_id={old_material_id}")
                    print(f"    新: start={timing.get('new_start')}, duration={timing.get('new_duration')}, material_id={tts_id}")
                else:
                    print(f"  [字幕跳过-{idx+1}] text_id={text_id} 未在material_id映射中找到")
                    print(f"    可用的material_id: {list(material_to_text_map.keys())}")
            print(f"  共更新 {update_count} 个字幕片段")
            
            # 收集所有贴纸片段并按时间排序
            all_sticker_segments = []
            for track in sticker_tracks:
                for seg in track.get('segments', []):
                    timerange = seg.get('target_timerange', {})
                    start = timerange.get('start', 0)
                    all_sticker_segments.append({
                        'segment': seg,
                        'start': start
                    })
            
            # 按开始时间排序
            sorted_sticker_segments = sorted(all_sticker_segments, key=lambda x: x['start'])
            print(f"[步骤16] 收集并排序贴纸片段: 共 {len(sorted_sticker_segments)} 个")
            
            # 更新贴纸轨道中的贴纸片段（与文本片段对齐，按时间顺序对应）
            print(f"[步骤19] 更新贴纸轨道中的贴纸片段:")
            print(f"  按时间顺序与TTS音频对应，并定位到新闻矩形框左下角")
            
            update_count = 0
            for idx, timing in enumerate(new_timing):
                if idx < len(sorted_sticker_segments):
                    # 按顺序对应：第1个TTS音频对应第1个贴纸片段，以此类推
                    sticker_item = sorted_sticker_segments[idx]
                    sticker_seg = sticker_item['segment']
                    material_id = sticker_seg.get('material_id')
                    old_start = sticker_seg.get('target_timerange', {}).get('start', 0)
                    old_duration = sticker_seg.get('target_timerange', {}).get('duration', 0)
                    
                    # 更新target_timerange，与对应TTS音频保持一致
                    if 'target_timerange' not in sticker_seg:
                        sticker_seg['target_timerange'] = {}
                    sticker_seg['target_timerange']['start'] = timing.get('new_start', 0)
                    sticker_seg['target_timerange']['duration'] = timing.get('new_duration', 0)
                    
                    # 使用transform方式定位贴纸到对应新闻矩形框的中心
                    if news_data and idx < len(news_data):
                        news = news_data[idx]
                        # 新闻位置格式: [x1, y1, x2, y2]
                        position = news.get('position', [0, 0, 0, 0])
                        if len(position) == 4:
                            x1, y1, x2, y2 = position
                            # 计算新闻矩形框中心点
                            news_center_x = (x1 + x2) / 2
                            news_center_y = (y1 + y2) / 2
                            
                            # 获取报纸类型和配置
                            newspaper_type = self._detect_newspaper_type(news)
                            video_width, video_height = self._get_video_dimensions()
                            paper_config = self._get_newspaper_config(newspaper_type)
                            
                            # 计算贴纸在视频中的transform位置（比例值）
                            transform_x, transform_y = self._calculate_sticker_transform(
                                news_center_x, news_center_y,
                                paper_config, video_width, video_height,
                                orig_image_width, orig_image_height
                            )
                            
                            # 更新贴纸的transform
                            if 'clip' not in sticker_seg:
                                sticker_seg['clip'] = {}
                            if 'transform' not in sticker_seg['clip']:
                                sticker_seg['clip']['transform'] = {}
                            
                            sticker_seg['clip']['transform']['x'] = transform_x
                            sticker_seg['clip']['transform']['y'] = transform_y
                            
                            print(f"  贴纸transform定位: x={transform_x:.6f}, y={transform_y:.6f}")
                            print(f"  新闻中心点: ({news_center_x}, {news_center_y})")
                            print(f"  新闻位置: {position}")
                            print(f"  报纸类型: {newspaper_type}")
                    
                    update_count += 1
                    print(f"  [贴纸更新-{update_count}] 顺序对应 TTS-{idx+1} -> 贴纸-{idx+1}")
                    print(f"    贴纸material_id={material_id}")
                    print(f"    旧: start={old_start}, duration={old_duration}")
                    print(f"    新: start={timing.get('new_start')}, duration={timing.get('new_duration')}")
                else:
                    print(f"  [贴纸跳过-{idx+1}] 没有更多贴纸片段可用")
            print(f"  共更新 {update_count} 个贴纸片段")
            
            # 处理视频素材
            print("=" * 60)
            print("开始处理视频素材...")
            print("=" * 60)
            
            # 1. 找到 local_material_id 为 "adfc1f13-688a-4cce-8472-3b31aa079b30" 的素材
            video_material_local_id = "adfc1f13-688a-4cce-8472-3b31aa079b30"
            target_video_id = "E42351AB-2F8B-4159-9C19-7CD524DD53C8"
            
            # 查找视频素材的duration和id
            video_duration = 0
            video_material_id = None
            materials = data.get('materials', {})
            videos = materials.get('videos', [])
            print(f"[步骤20] 查找视频素材: local_material_id={video_material_local_id}")
            for video in videos:
                if video.get('local_material_id') == video_material_local_id:
                    video_duration = video.get('duration', 0)
                    video_material_id = video.get('id')
                    print(f"  找到视频素材，id={video_material_id}, duration={video_duration}")
                    break
            
            if video_duration > 0 and video_material_id:
                # 2. 计算视频素材的结束时间
                video_end_time = video_start_time + video_duration
                print(f"[步骤21] 视频素材时间: start={video_start_time}, duration={video_duration}, end={video_end_time}")
                
                # 3. 查找并更新"更多内容在评论区.mp4"视频素材的时间
                # 金融时报0318.jpg将在后面的统一对齐代码中处理
                print(f"[步骤22] 查找并更新'更多内容在评论区.mp4'视频素材片段")
                print(f"[步骤23] 查找并更新视频素材片段")
                video_material_updated = False
                
                # 检查所有类型的轨道，不仅仅是视频轨道
                for track_idx, track in enumerate(data.get('tracks', [])):
                    track_type = track.get('type')
                    segments = track.get('segments', [])
                    print(f"  轨道 {track_idx+1} (类型: {track_type}) 包含 {len(segments)} 个片段")
                    
                    for seg_idx, segment in enumerate(segments):
                        seg_id = segment.get('id')
                        seg_material_id = segment.get('material_id')
                        seg_material_name = segment.get('material_name', '')
                        seg_timerange = segment.get('target_timerange', {})
                        seg_start = seg_timerange.get('start', 0)
                        seg_duration = seg_timerange.get('duration', 0)
                        print(f"    片段 {seg_idx+1}: id={seg_id}, material_id={seg_material_id}, material_name={seg_material_name}, start={seg_start}, duration={seg_duration}")
                        
                        # 尝试多种匹配方式
                        if seg_material_id == video_material_id:
                            old_start = seg_start
                            old_duration = seg_duration
                            old_end = old_start + old_duration
                            new_end = video_start_time + video_duration
                            
                            if 'target_timerange' not in segment:
                                segment['target_timerange'] = {}
                            segment['target_timerange']['start'] = video_start_time
                            segment['target_timerange']['duration'] = video_duration
                            
                            print(f"  [视频素材更新] material_id={video_material_id}")
                            print(f"    旧位置: start={old_start}, duration={old_duration}, end={old_end}")
                            print(f"    新位置: start={video_start_time}, duration={video_duration}, end={new_end}")
                            print(f"    计算的开始时间: {video_start_time}")
                            print(f"    计算的结束时间: {new_end}")
                            print(f"    轨道类型: {track_type}")
                            print(f"    素材名称: {seg_material_name}")
                            video_material_updated = True
                            break
                    if video_material_updated:
                        break
                
                if not video_material_updated:
                    print(f"[警告] 未找到视频素材片段: material_id={video_material_id}")
                    print("  尝试查找所有轨道中的所有片段...")
                    for track_idx, track in enumerate(data.get('tracks', [])):
                        track_type = track.get('type')
                        segments = track.get('segments', [])
                        print(f"  轨道 {track_idx+1} (类型: {track_type}):")
                        for segment in segments:
                            print(f"    片段: id={segment.get('id')}, material_id={segment.get('material_id')}")
                    
                    # 检查materials中的videos
                    print("  检查materials中的videos...")
                    materials = data.get('materials', {})
                    videos = materials.get('videos', [])
                    print(f"  找到 {len(videos)} 个视频素材:")
                    for idx, video in enumerate(videos):
                        print(f"    视频 {idx+1}: local_material_id={video.get('local_material_id')}, id={video.get('id')}")
                else:
                    # 两个视频素材都已更新，输出同步确认信息
                    print("=" * 60)
                    print("[视频对齐确认]")
                    print(f"  视频素材1 (更多内容在评论区.mp4):")
                    print(f"    material_id: {video_material_id}")
                    print(f"    开始时间: {video_start_time}")
                    print(f"    结束时间: {video_end_time}")
                    print(f"  视频素材2 (金融时报0318.jpg):")
                    print(f"    material_id: {target_video_id}")
                    print(f"    结束时间对齐到: {video_end_time}")
                    print(f"  ✓ 两个视频素材的结束时间已对齐")
                    print("=" * 60)
                    
                    # 对齐其他素材的结束时间（开始时间不变，调整duration）
                    print("=" * 60)
                    print("开始对齐其他素材的结束时间...")
                    print("=" * 60)
                    
                    # 定义需要对齐的素材列表
                    materials_to_align = [
                        {"type": "audio", "id": "6D967A4F-3E5F-4cf4-8B8D-BE2B17D3A3F8", "name": "早间播报 背景配乐"},
                        {"type": "audio", "id": "4C5380AE-3F65-488f-B887-C977206F83E8", "name": "时尚商务节奏 企业"},
                        {"type": "text", "id": "4F5AEA3A-6BDF-4933-8DE1-EC31E979E97F", "name": "文本1"},
                        {"type": "text", "id": "7453700C-DD8B-44d8-91DA-05690591DCA9", "name": "文本2"},
                        {"type": "text", "id": "F2A47FCE-BA46-402b-8EC2-FFA641BA706C", "name": "文本3"},
                        {"type": "video", "id": "E42351AB-2F8B-4159-9C19-7CD524DD53C8", "name": "金融时报0318.jpg"}
                    ]
                    
                    for material_info in materials_to_align:
                        material_id = material_info["id"]
                        material_name = material_info["name"]
                        material_type = material_info["type"]
                        
                        print(f"[对齐] {material_name} (material_id: {material_id}, type: {material_type})")
                        
                        # 在所有轨道中查找引用该素材的片段
                        found = False
                        processed_segments = 0
                        
                        for track_idx, track in enumerate(data.get('tracks', [])):
                            track_type = track.get('type', 'unknown')
                            segments = track.get('segments', [])
                            print(f"  检查轨道 {track_idx} (类型: {track_type})，包含 {len(segments)} 个片段")
                            
                            for seg_idx, segment in enumerate(segments):
                                seg_material_id = segment.get('material_id')
                                print(f"    片段 {seg_idx}: material_id={seg_material_id}")
                                
                                if seg_material_id == material_id:
                                    # 找到片段，调整duration使结束时间对齐
                                    old_start = segment.get('target_timerange', {}).get('start', 0)
                                    old_duration = segment.get('target_timerange', {}).get('duration', 0)
                                    old_end = old_start + old_duration
                                    
                                    # 计算新的duration：保持开始时间不变，结束时间对齐到video_end_time
                                    new_duration = video_end_time - old_start
                                    new_end = old_start + new_duration
                                    
                                    if 'target_timerange' not in segment:
                                        segment['target_timerange'] = {}
                                    segment['target_timerange']['duration'] = new_duration
                                    
                                    # 对于音频素材，同时调整source_timerange的duration，使其与target_timerange一致
                                    if material_type == 'audio':
                                        print(f"    处理音频素材，调整source_timerange")
                                        if 'source_timerange' not in segment:
                                            segment['source_timerange'] = {}
                                        # 保持source_timerange的start不变，只调整duration
                                        segment['source_timerange']['duration'] = new_duration
                                        print(f"    同步 source_timerange: duration={new_duration}")
                                    
                                    print(f"  [更新] {material_name}")
                                    print(f"    旧位置: start={old_start}, duration={old_duration}, end={old_end}")
                                    print(f"    新位置: start={old_start}, duration={new_duration}, end={new_end}")
                                    print(f"    目标结束时间: {video_end_time}")
                                    print(f"    时间同步: {abs(new_end - video_end_time) < 1000} (误差小于1ms)")
                                    found = True
                                    processed_segments += 1
                                    # 不要break，继续处理其他可能的segment
                            # 不要break，继续检查其他track
                        
                        if found:
                            print(f"  [完成] 处理了 {processed_segments} 个片段")
                        else:
                            print(f"  [警告] 未找到素材片段: {material_name} (material_id: {material_id})")
                    
                    print("=" * 60)
                    print("所有素材结束时间对齐完成")
                    print("=" * 60)
            else:
                if not video_material_id:
                    print(f"[错误] 未找到视频素材: local_material_id={video_material_local_id}")
                else:
                    print(f"[错误] 视频素材duration为0: local_material_id={video_material_local_id}")
            
            print("=" * 60)
            print("TTS音频、字幕、贴纸和视频素材时序同步完成")
            print("=" * 60)
            
            # 补充：处理时间长度显示
            print("[补充] 处理时间长度显示:")
            
            # 1. 找到id为7453700C-DD8B-44d8-91DA-05690591DCA9的文本片段
            target_text_id = "7453700C-DD8B-44d8-91DA-05690591DCA9"
            display_text_id = "4F5AEA3A-6BDF-4933-8DE1-EC31E979E97F"
            
            # 查找所有文本轨道中的片段
            total_duration = 0
            for track in text_tracks:
                for segment in track.get('segments', []):
                    material_id = segment.get('material_id')
                    if material_id == target_text_id:
                        # 获取时间长度（微秒）
                        timerange = segment.get('target_timerange', {})
                        duration_us = timerange.get('duration', 0)
                        # 转换为秒并取整数
                        total_duration = int(duration_us / 1000000)
                        print(f"  找到目标文本片段，时长: {duration_us}微秒 = {total_duration}秒")
                        break
                if total_duration > 0:
                    break
            
            # 2. 找到id为4F5AEA3A-6BDF-4933-8DE1-EC31E979E97F的文本片段并替换内容
            if total_duration > 0:
                # 查找materials中的texts
                if 'materials' in data and 'texts' in data['materials']:
                    for text_item in data['materials']['texts']:
                        text_id = text_item.get('id')
                        if text_id == display_text_id:
                            # 替换content中的text
                            content_str = text_item.get('content', '')
                            if content_str:
                                try:
                                    content_obj = json.loads(content_str)
                                    old_text = content_obj.get('text', '')
                                    new_text = f"{total_duration}秒"
                                    print(f"  替换前显示文本: {old_text}")
                                    content_obj['text'] = new_text
                                    text_item['content'] = json.dumps(content_obj, ensure_ascii=False)
                                    print(f"  替换后显示文本: {new_text}")
                                except json.JSONDecodeError:
                                    # 如果解析失败，直接替换整个content
                                    old_text = content_str
                                    new_text = f"{total_duration}秒"
                                    print(f"  替换前显示content: {old_text[:50]}...")
                                    text_item['content'] = new_text
                                    print(f"  替换后显示content: {new_text}")
                            else:
                                new_text = f"{total_duration}秒"
                                text_item['content'] = new_text
                                print(f"  显示content为空，设置为: {new_text}")
                            break
            
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