# modules/tts.py
# Chuyển văn bản thành giọng nói tiếng Việt và tính thời gian cho từng từ/câu
from gtts import gTTS
import os
import re
import math
import json

def estimate_word_durations(text, total_duration):
    """Ước tính thời gian cho từng từ dựa trên tổng thời gian audio"""
    # Tách văn bản thành các từ
    words = re.findall(r'\S+', text)
    total_chars = sum(len(word) for word in words)
    
    # Tính thời gian cho mỗi từ dựa trên số ký tự
    timings = []
    current_time = 0
    
    # Ước tính thời gian cho mỗi từ dựa trên số ký tự và tốc độ đọc trung bình
    avg_time_per_char = total_duration / total_chars if total_chars > 0 else 0.1
    
    for word in words:
        # Thêm 1 để tính cả khoảng trắng
        word_duration = len(word) * avg_time_per_char
        # Thêm khoảng dừng nhỏ sau mỗi từ
        pause = 0.05  
        
        # Thời gian bắt đầu và kết thúc của từ này
        start_time = current_time
        end_time = current_time + word_duration
        
        timings.append({
            'word': word,
            'start': start_time,
            'end': end_time
        })
        
        current_time = end_time + pause
    
    # Điều chỉnh lại tổng thời gian nếu cần
    if timings and current_time > total_duration:
        scale_factor = total_duration / current_time
        for timing in timings:
            timing['start'] *= scale_factor
            timing['end'] *= scale_factor
    
    return timings

def text_to_speech(text, output_path, lang='vi', timing_file=None):
    tts = gTTS(text=text, lang=lang)
    tts.save(output_path)
    
    # Ước lượng thời gian phát âm
    import subprocess
    import json
    from pydub import AudioSegment
    
    try:
        # Đo độ dài audio đã tạo
        audio = AudioSegment.from_mp3(output_path)
        duration_sec = len(audio) / 1000.0
        
        # Tính thời gian cho từng từ
        word_timings = estimate_word_durations(text, duration_sec)
        
        # Lưu thời gian vào file JSON (nếu được chỉ định)
        if timing_file:
            with open(timing_file, 'w', encoding='utf-8') as f:
                json.dump(word_timings, f, ensure_ascii=False, indent=2)
                
        return output_path, word_timings
    except Exception as e:
        print(f"Warning: Could not estimate word timings: {e}")
        return output_path, []
