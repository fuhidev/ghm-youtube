# prompt_generator.py
# Script để tạo prompt cho Leonardo.ai từ nội dung truyện

import os
import json
import math
import re
import textwrap
from typing import List, Dict


def divide_story_into_segments(story_text: str, num_segments: int) -> List[str]:
    """
    Chia truyện thành các phân đoạn có kích thước tương đương nhau

    Args:
        story_text (str): Nội dung truyện
        num_segments (int): Số lượng phân đoạn cần tạo

    Returns:
        List[str]: Danh sách các phân đoạn
    """
    # Loại bỏ khoảng trắng thừa
    story_text = story_text.strip()

    # Chia truyện thành các đoạn văn
    paragraphs = re.split(r"\n\s*\n", story_text)
    paragraphs = [p.strip() for p in paragraphs if p.strip()]

    if len(paragraphs) <= num_segments:
        # Nếu số đoạn văn ít hơn số phân đoạn cần tạo
        segments = paragraphs
        # Điền thêm các phân đoạn trống
        segments.extend([""] * (num_segments - len(paragraphs)))
    else:
        # Tính số đoạn văn cho mỗi phân đoạn
        paragraphs_per_segment = math.ceil(len(paragraphs) / num_segments)

        # Nhóm các đoạn văn thành các phân đoạn
        segments = []
        for i in range(0, len(paragraphs), paragraphs_per_segment):
            segment_paragraphs = paragraphs[i : i + paragraphs_per_segment]
            segments.append("\n\n".join(segment_paragraphs))

        # Nếu có nhiều phân đoạn hơn cần thiết, gộp các phân đoạn cuối
        if len(segments) > num_segments:
            last_segments = segments[num_segments - 1 :]
            segments = segments[: num_segments - 1]
            segments.append("\n\n".join(last_segments))

    return segments


def extract_scene_description(text: str) -> str:
    """
    Trích xuất mô tả cảnh từ một đoạn văn bản

    Args:
        text (str): Đoạn văn bản cần trích xuất

    Returns:
        str: Mô tả cảnh
    """
    # Loại bỏ đối thoại (văn bản trong dấu ngoặc kép)
    clean_text = re.sub(r'"[^"]*"', "", text)

    # Trích xuất các câu mô tả cảnh, đối tượng, nhân vật
    descriptive_lines = []
    visual_keywords = [
        "nhìn",
        "thấy",
        "mặc",
        "ánh",
        "màu",
        "hiện ra",
        "xuất hiện",
        "kinh ngạc",
        "phát hiện",
        "cảnh",
        "đôi mắt",
        "gương mặt",
        "khuôn mặt",
        "trang phục",
        "bầu trời",
        "mặt trời",
        "mặt trăng",
        "phong cảnh",
        "bóng",
        "sáng",
        "tối",
        "ánh sáng",
        "dáng vẻ",
        "vẻ",
        "trang",
        "tóc",
        "đầu",
        "mình",
        "thân",
        "tay",
        "chân",
    ]

    for line in clean_text.split("\n"):
        if any(keyword in line.lower() for keyword in visual_keywords):
            descriptive_lines.append(line)

    # Nếu không tìm thấy dòng mô tả, sử dụng 2-3 câu đầu tiên
    if not descriptive_lines:
        sentences = re.split(r"[.!?]\s+", clean_text)
        descriptive_lines = sentences[: min(3, len(sentences))]

    # Kết hợp các dòng mô tả
    description = " ".join(descriptive_lines)

    # Giới hạn độ dài mô tả
    description = textwrap.shorten(description, width=250, placeholder="...")

    return description


def generate_image_prompt(segment_text: str) -> str:
    """
    Tạo prompt cho Leonardo.ai từ một phân đoạn truyện

    Args:
        segment_text (str): Nội dung phân đoạn truyện

    Returns:
        str: Prompt cho Leonardo.ai
    """
    if not segment_text or not segment_text.strip():
        return ""

    # Trích xuất mô tả cảnh
    scene_description = extract_scene_description(segment_text)

    # Thêm hướng dẫn phong cách
    style_instruction = (
        "High-quality fantasy illustration, realistic 8k, "
        "detailed scene, natural lighting, cinematic composition, "
        "chinese wuxia style, anime, anime inspired, fantasy artwork"
    )

    negative_prompt = (
        "low quality, blurry, distorted faces, bad anatomy, "
        "extra limbs, text, watermark, signature, low resolution"
    )

    # Tạo prompt hoàn chỉnh
    prompt = f"{scene_description} {style_instruction}"

    return prompt


def create_prompts_from_story(
    story_text: str, num_segments: int, output_file: str = None
) -> Dict:
    """
    Tạo các prompt cho Leonardo.ai từ nội dung truyện

    Args:
        story_text (str): Nội dung truyện
        num_segments (int): Số lượng phân đoạn/prompt cần tạo
        output_file (str, optional): Đường dẫn file để lưu kết quả (JSON)

    Returns:
        Dict: Dictionary chứa các phân đoạn và prompt
    """
    # Chia truyện thành các phân đoạn
    segments = divide_story_into_segments(story_text, num_segments)

    # Tạo prompt cho mỗi phân đoạn
    prompts = []
    for segment in segments:
        prompt = generate_image_prompt(segment)
        prompts.append(prompt)

    # Tạo kết quả
    result = {"num_segments": num_segments, "segments": []}

    for i, (segment, prompt) in enumerate(zip(segments, prompts)):
        result["segments"].append(
            {"segment_id": i + 1, "text": segment, "prompt": prompt}
        )

    # Lưu kết quả vào file nếu có yêu cầu
    if output_file:
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

    return result


if __name__ == "__main__":
    # Ví dụ sử dụng
    sample_story = """
    Ý thức của Vân Triệt dần tỉnh lại.

    Chuyện gì đây... Chẳng lẽ ta vẫn chưa chết? Rõ ràng ta đã rơi xuống Tuyệt Vân Nhai, sao có thể còn sống được!
    
    Vân Triệt bỗng mở to mắt, ngồi bật dậy, kinh ngạc phát hiện mình đang nằm trên một chiếc giường lớn mềm mại, phía trên giường buông rèm đỏ rực, tạo nên không khí vui tươi.
    """

    result = create_prompts_from_story(sample_story, 3, "prompts.json")

    for i, segment in enumerate(result["segments"]):
        print(f"Phân đoạn {i+1}:")
        print(
            segment["text"][:100] + "..."
            if len(segment["text"]) > 100
            else segment["text"]
        )
        print(f"Prompt: {segment['prompt']}")
        print("-" * 50)
