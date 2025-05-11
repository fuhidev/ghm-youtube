# modules/subtitle.py
# Tạo phụ đề và gắn vào video
import pysubs2
import os
import json
import math


def create_subtitle(
    text,
    output_path,
    font="Arial",
    color="&H00FFFFFF",
    outline_color="&H0000FF00",
    outline=2,
    words_per_line=4,
    duration_per_line=2.5,
    word_timings=None,
):
    subs = pysubs2.SSAFile()

    # Xử lý tiếng Việt: tách từ và câu
    words = text.replace("\n", " ").split()

    if word_timings:
        # Nếu có timing data, sử dụng để tạo phụ đề chính xác
        create_timed_subtitles(subs, word_timings, words_per_line, color, output_path)
    else:
        # Không có timing data, sử dụng phương pháp ước lượng đều
        lines = [
            " ".join(words[i : i + words_per_line])
            for i in range(0, len(words), words_per_line)
        ]
        start = 0
        for line in lines:
            end = (
                start + duration_per_line
            )  # Sử dụng style đặc biệt cho định dạng karaoke
            formatted_line = (
                "{\\an2}{\\fs48}{\\b1}{\\c&HFFFFFF&}{\\3c&H00AAFF&}{\\3a&H00&}{\\4a&HFF&}"
                + line
            )
            event = pysubs2.SSAEvent(
                start=int(start * 1000), end=int(end * 1000), text=formatted_line
            )
            subs.events.append(event)
            start = end


def create_timed_subtitles(subs, word_timings, words_per_line, color, output_path):
    """Tạo phụ đề dựa trên thời gian từng từ"""

    current_words = []
    line_start = 0

    # Kiểm tra xem word_timings có dữ liệu không
    if not word_timings or len(word_timings) == 0:
        print("Không có dữ liệu timing cho phụ đề")
        return

    # In ra một số dữ liệu timing để debug
    print(f"Số lượng word_timings: {len(word_timings)}")
    print(f"Sample word timing: {word_timings[0] if word_timings else 'None'}")

    for i, word_timing in enumerate(word_timings):
        if "word" not in word_timing:
            print(f"Thiếu trường 'word' trong word_timing: {word_timing}")
            continue

        current_words.append(word_timing["word"])

        # Khi đủ số từ cho một dòng hoặc là từ cuối cùng
        if len(current_words) == words_per_line or i == len(word_timings) - 1:
            line_text = " ".join(current_words)

            if "end" not in word_timing:
                print(f"Thiếu trường 'end' trong word_timing: {word_timing}")
                continue

            line_end = word_timing[
                "end"
            ]  # Format text với style đặc biệt (giống karaoke) - canh giữa dưới
            formatted_line = (
                "{\\an2}{\\fs28}{\\b1}{\\c&HFFFFFF&}{\\3c&H00AAFF&}{\\3a&H00&}{\\4a&HFF&}"
                + line_text
            )

            event = pysubs2.SSAEvent(
                start=int(line_start * 1000),  # Chuyển sang ms
                end=int(line_end * 1000),  # Chuyển sang ms
                text=formatted_line,
            )
            subs.events.append(event)

            # Reset cho dòng tiếp theo
            current_words = []
            line_start = line_end

    # Tạo style đặc biệt theo kiểu karaoke
    style = pysubs2.SSAStyle()
    style.fontname = "Arial"  # Font dễ đọc, hỗ trợ Unicode
    style.fontsize = 28  # Kích thước lớn
    style.bold = True  # Chữ đậm
    style.outline = 2  # Độ dày viền
    style.shadow = 0  # Không bóng
    style.primarycolor = (
        color  # Màu chữ trắng    style.outlinecolor = "&H00AAFF&"  # Màu viền xanh
    )
    style.alignment = 2  # 2 = giữa dưới
    subs.styles["Default"] = style
    subs.save(output_path)
    return output_path
