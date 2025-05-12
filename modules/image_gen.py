# modules/image_gen.py
# Tạo hình ảnh từ nội dung truyện sử dụng Leonardo.ai API
import os
import json
import logging
from PIL import Image, ImageDraw, ImageFont
from typing import List, Optional
from modules.story_segment import (
    StorySegmenter,
    LeonardoImageGenerator,
    process_story_for_images,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Default Leonardo.ai API key (thay bằng API key thật của bạn)
LEONARDO_API_KEY = "your-leonardo-api-key-here"


def generate_image_from_story(story, output_path, api_key=None, num_images=1):
    """
    Tạo hình ảnh từ nội dung truyện sử dụng Leonardo.ai API

    Args:
        story (str): Nội dung truyện
        output_path (str): Đường dẫn để lưu hình ảnh
        api_key (str, optional): Leonardo.ai API key. Nếu không cung cấp, sẽ sử dụng key mặc định
        num_images (int, optional): Số lượng hình ảnh cần tạo. Mặc định là 1

    Returns:
        str: Đường dẫn đến hình ảnh đã tạo
    """
    if api_key is None:
        api_key = LEONARDO_API_KEY

    if num_images <= 1:
        # Tạo một hình ảnh duy nhất
        return _generate_single_image(story, output_path, api_key)
    else:
        # Tạo nhiều hình ảnh từ các phân đoạn truyện
        output_dir = os.path.dirname(output_path)
        image_paths = _generate_multiple_images(story, num_images, output_dir, api_key)

        # Tạo một hình ảnh đại diện (hình đầu tiên được tạo)
        if image_paths and os.path.exists(image_paths[0]):
            representative_image = Image.open(image_paths[0])
            representative_image.save(output_path)
        else:
            # Tạo hình ảnh mặc định nếu không tạo được hình ảnh từ API
            _create_default_image(story, output_path)

        return output_path


def _generate_single_image(story, output_path, api_key):
    """
    Tạo một hình ảnh duy nhất từ nội dung truyện
    """
    try:
        print(f"DEBUG: Starting image generation for story: {story[:50]}...")

        # Tạo prompt từ nội dung truyện
        segmenter = StorySegmenter(story, 1)
        segmenter.segment_by_paragraphs()
        prompts = segmenter.generate_prompts()

        print(f"DEBUG: Generated prompts: {prompts}")

        if prompts and prompts[0]:
            # Tạo hình ảnh với Leonardo.ai
            generator = LeonardoImageGenerator(api_key)
            print(f"DEBUG: Using API key: {api_key[:5]}...")
            image_url = generator.generate_image(prompts[0])

            print(f"DEBUG: Image URL from Leonardo: {image_url}")

            if image_url:
                logger.info(f"Leonardo.ai returned image URL: {image_url}")

                # Ensure output directory exists
                os.makedirs(
                    os.path.dirname(os.path.abspath(output_path)), exist_ok=True
                )

                # Download the image
                success = generator.download_image(image_url, output_path)

                if (
                    success
                    and os.path.exists(output_path)
                    and os.path.getsize(output_path) > 0
                ):
                    logger.info(
                        f"Đã tạo hình ảnh thành công: {output_path} ({os.path.getsize(output_path)} bytes)"
                    )
                    return output_path
                else:
                    logger.error(
                        f"Image download failed or file is empty: {output_path}"
                    )

                    # Check if a previous valid image exists (for cases where the API worked but download failed)
                    if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                        logger.info(f"Using previously downloaded image: {output_path}")
                        return output_path

                    # Try to manually download the image with a different method
                    try:
                        logger.info(
                            f"Attempting alternative download method for {image_url}"
                        )
                        import urllib.request

                        urllib.request.urlretrieve(image_url, output_path)
                        if (
                            os.path.exists(output_path)
                            and os.path.getsize(output_path) > 0
                        ):
                            logger.info(
                                f"Alternative download successful: {output_path}"
                            )
                            return output_path
                    except Exception as e:
                        logger.error(f"Alternative download method failed: {str(e)}")

        # Nếu không thể tạo hoặc tải hình ảnh từ API, tạo hình ảnh mặc định
        logger.warning("Không thể tạo hình ảnh từ API, sử dụng hình ảnh mặc định.")
        return _create_default_image(story, output_path)

    except Exception as e:
        logger.error(f"Lỗi khi tạo hình ảnh: {str(e)}")
        import traceback

        logger.error(traceback.format_exc())
        return _create_default_image(story, output_path)


def _generate_multiple_images(story, num_images, output_dir, api_key):
    """
    Tạo nhiều hình ảnh từ các phân đoạn truyện
    """
    try:
        # Tạo thư mục segment_images nếu chưa tồn tại
        segments_dir = os.path.join(output_dir, "segment_images")
        os.makedirs(segments_dir, exist_ok=True)

        # Tạo các hình ảnh từ các phân đoạn truyện
        image_paths = process_story_for_images(story, num_images, segments_dir, api_key)

        # Lưu thông tin về các hình ảnh đã tạo
        info_path = os.path.join(output_dir, "segment_images.json")
        with open(info_path, "w", encoding="utf-8") as f:
            json.dump(
                {"num_images": num_images, "image_paths": image_paths},
                f,
                ensure_ascii=False,
                indent=2,
            )

        return image_paths

    except Exception as e:
        logger.error(f"Lỗi khi tạo nhiều hình ảnh: {str(e)}")
        return []


def _create_default_image(story, output_path):
    """
    Tạo hình ảnh mặc định khi không thể tạo từ API
    """
    try:
        img = Image.new("RGB", (1280, 720), color=(73, 109, 137))
        d = ImageDraw.Draw(img)

        # Sử dụng font mặc định vì không biết hệ thống có hỗ trợ font unicode hay không
        font = ImageFont.load_default()

        # Hiển thị một phần văn bản truyện
        preview = story[:200] + "..." if len(story) > 200 else story
        d.text(
            (20, 20), "Không thể tạo hình ảnh từ API", fill=(255, 255, 255), font=font
        )
        d.text((20, 50), preview, fill=(255, 255, 255), font=font)

        img.save(output_path)
        logger.info(f"Đã tạo hình ảnh mặc định: {output_path}")
        return output_path

    except Exception as e:
        logger.error(f"Lỗi khi tạo hình ảnh mặc định: {str(e)}")
        return output_path
