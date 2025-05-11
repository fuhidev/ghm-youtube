# modules/tts.py
# Chuyển văn bản thành giọng nói tiếng Việt và tính thời gian cho từng từ/câu
import edge_tts
import asyncio
import os
import re
import json
import tempfile
from pydub import AudioSegment

# Danh sách các giọng tiếng Việt có sẵn trên Edge TTS
VIETNAMESE_VOICES = ["vi-VN-HoaiMyNeural", "vi-VN-NamMinhNeural"]  # Nữ  # Nam

# Danh sách giọng tiếng Anh phổ biến
ENGLISH_VOICES = ["en-US-AriaNeural", "en-US-GuyNeural"]  # Nữ  # Nam


# Hàm lấy tất cả giọng nói có sẵn
async def get_available_voices():
    voices = await edge_tts.VoicesManager.create()
    all_voices = voices.voices
    return all_voices


# Hàm lọc giọng nói theo ngôn ngữ
def filter_voices_by_language(all_voices, language_code="vi-VN"):
    filtered_voices = []
    for voice in all_voices:
        if voice.get("Locale", "").startswith(language_code):
            name = voice.get("ShortName", "")
            gender = voice.get("Gender", "")
            filtered_voices.append(
                {"name": name, "gender": gender, "locale": voice.get("Locale", "")}
            )
    return filtered_voices


async def generate_speech_with_edge_tts(text, output_path, voice="vi-VN-HoaiMyNeural"):
    """Tạo speech với Edge TTS và trả về timing data"""
    communicate = edge_tts.Communicate(text, voice)

    # Tạo SubMaker để xử lý subtitles
    sub_maker = edge_tts.submaker.SubMaker()

    # Tạo file tạm để lưu timing data
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp_file:
        timing_file = tmp_file.name

    # Mở file để lưu audio
    with open(output_path, "wb") as audio_file:
        # Stream audio và metadata
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_file.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                sub_maker.feed(chunk)

    # Lưu subtitle data vào file tạm
    with open(timing_file, "w", encoding="utf-8") as f:
        f.write(sub_maker.get_srt())

    # Đọc timing data từ file tạm
    with open(timing_file, "r", encoding="utf-8") as f:
        timing_data = f.read()

    # Xóa file tạm
    os.unlink(timing_file)

    # Chuyển đổi format timing data sang định dạng giống với hàm cũ
    word_timings = convert_edge_tts_timing(timing_data, text)

    return word_timings


def convert_edge_tts_timing(timing_data, original_text):
    """Chuyển đổi timing data từ Edge TTS sang định dạng phù hợp với code hiện tại"""
    word_timings = []
    lines = timing_data.strip().split("\n")
    
    print(f"Số dòng timing data: {len(lines)}")
    if len(lines) > 0:
        print(f"Mẫu dòng đầu tiên: {lines[0]}")
    
    # Xử lý định dạng SRT: số thứ tự, thời gian, và nội dung
    index = 0
    while index < len(lines):
        # Tìm dòng chứa số thứ tự (index định dạng SRT)
        if lines[index].strip().isdigit():
            srt_index = int(lines[index].strip())
            
            # Dòng tiếp theo là timestamp
            if index + 1 < len(lines) and " --> " in lines[index + 1]:
                time_line = lines[index + 1]
                parts = time_line.split(" --> ")
                if len(parts) == 2:
                    start_time = parts[0].strip()
                    end_time = parts[1].strip()
                    
                    # Dòng tiếp theo là nội dung
                    if index + 2 < len(lines):
                        content = lines[index + 2].strip()
                        
                        # Chuyển đổi thời gian
                        start_seconds = time_to_seconds(start_time)
                        end_seconds = time_to_seconds(end_time)
                        
                        word_timings.append({
                            "word": content,
                            "start": start_seconds,
                            "end": end_seconds
                        })
                
                # Tìm dòng trống tiếp theo
                index += 3
                while index < len(lines) and lines[index].strip():
                    index += 1
                index += 1  # Vượt qua dòng trống
            else:
                index += 1
        else:
            index += 1
    
    print(f"Số lượng word_timings sau khi xử lý: {len(word_timings)}")
    if len(word_timings) > 0:
        print(f"Mẫu word_timing đầu tiên: {word_timings[0]}")
    
    return word_timings

    return word_timings


def time_to_seconds(time_str):
    """Chuyển đổi định dạng thời gian HH:MM:SS.mmm hoặc HH:MM:SS,mmm sang số giây"""
    try:
        h, m, s = time_str.split(":")
        # Xử lý cả dấu chấm và dấu phẩy trong định dạng thời gian
        if "." in s:
            s, ms = s.split(".")
        elif "," in s:
            s, ms = s.split(",")
        else:
            ms = "0"
        return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000
    except Exception as e:
        print(f"Lỗi chuyển đổi thời gian '{time_str}': {e}")
        return 0  # Trả về 0 trong trường hợp lỗi


def text_to_speech(text, output_path, lang="vi", timing_file=None, voice=None):
    """Hàm wrapper để gọi Edge TTS và duy trì API giống với gTTS"""
    # Luôn tạo event loop mới để tránh DeprecationWarning
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Chọn voice dựa trên ngôn ngữ nếu không được chỉ định
    if voice is None:
        if lang == "vi":
            voice = VIETNAMESE_VOICES[0]  # Voice nữ tiếng Việt mặc định
        else:
            voice = ENGLISH_VOICES[0]  # Voice nữ tiếng Anh mặc định

    # Gọi hàm async để tạo speech
    word_timings = loop.run_until_complete(
        generate_speech_with_edge_tts(text, output_path, voice)
    )

    # Lưu timing data vào file nếu được chỉ định
    if timing_file:
        with open(timing_file, "w", encoding="utf-8") as f:
            json.dump(word_timings, f, ensure_ascii=False, indent=2)

    return output_path, word_timings
