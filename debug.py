"""
Debugging script for YouTube Tool.
Run this file to test and debug specific components.
"""

import os
import logging
import json
from modules.story_segment import LeonardoImageGenerator, StorySegmenter
from modules.deepseek import DeepSeek

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("debug.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def test_leonardo_api():
    """Test Leonardo.ai image generation"""
    api_key = input("Enter your Leonardo API key: ")

    # Test prompt
    prompt = "A beautiful landscape with mountains and a lake, digital art style"

    logger.info(f"Testing Leonardo.ai API with prompt: {prompt}")
    generator = LeonardoImageGenerator(api_key)

    # Generate image
    image_url = generator.generate_image(prompt)
    logger.info(f"Generated image URL: {image_url}")

    if image_url:
        # Download image
        output_path = "debug_image.png"
        success = generator.download_image(image_url, output_path)
        logger.info(f"Image download {'successful' if success else 'failed'}")

        if success:
            logger.info(f"Image saved to {os.path.abspath(output_path)}")

            # Check file details
            file_size = os.path.getsize(output_path)
            logger.info(f"File size: {file_size} bytes")

            if file_size == 0:
                logger.error("File is empty!")
    else:
        logger.error("Failed to generate image URL")


def test_deepseek_api():
    """Test DeepSeek API"""
    api_key = input(
        "Enter your DeepSeek API key (press Enter to use environment variable): "
    )
    if not api_key.strip():
        api_key = None

    client = DeepSeek(api_key)
    response = client.chat("Hello, can you help me debug my Python application?")
    logger.info(f"DeepSeek API response: {response[:100]}...")


def test_story_segmentation():
    """Test story segmentation and prompt generation"""
    story = """
    Ý thức của Vân Triệt dần tỉnh lại.
    
    Chuyện gì đây... Chẳng lẽ ta vẫn chưa chết? Rõ ràng ta đã rơi xuống Tuyệt Vân Nhai, sao có thể còn sống được!
    
    Vân Triệt cố gắng mở mắt, ánh sáng chói chang khiến anh khó chịu. Khi đôi mắt dần quen với ánh sáng, anh nhận ra mình đang nằm trong một căn phòng lạ, xung quanh là những thiết bị y tế hiện đại.
    """

    segmenter = StorySegmenter(story, 2)
    segments = segmenter.segment_by_paragraphs()

    logger.info(f"Created {len(segments)} segments")
    for i, segment in enumerate(segments):
        logger.info(f"Segment {i+1}: {segment}")

    prompts = segmenter.generate_prompts()
    for i, prompt in enumerate(prompts):
        logger.info(f"Prompt {i+1}: {prompt}")

    # Save to file for inspection
    with open("debug_segments.json", "w", encoding="utf-8") as f:
        json.dump(
            {"segments": segments, "prompts": prompts}, f, indent=2, ensure_ascii=False
        )

    logger.info("Saved debug information to debug_segments.json")


if __name__ == "__main__":
    print("YouTube Tool Debugging Utility")
    print("=============================")
    print("1. Test Leonardo.ai API")
    print("2. Test DeepSeek API")
    print("3. Test story segmentation")
    print("0. Exit")

    choice = input("Enter your choice: ")

    if choice == "1":
        test_leonardo_api()
    elif choice == "2":
        test_deepseek_api()
    elif choice == "3":
        test_story_segmentation()
    else:
        print("Exiting debug utility.")
