# modules/image_gen.py
# Tạo hình ảnh từ nội dung truyện (placeholder: tạo ảnh nền đơn giản)
from PIL import Image, ImageDraw, ImageFont

def generate_image_from_story(story, output_path):
    img = Image.new('RGB', (1280, 720), color=(73, 109, 137))
    d = ImageDraw.Draw(img)
    font = ImageFont.load_default()
    d.text((10,10), story[:200] + '...', fill=(255,255,255), font=font)
    img.save(output_path)
    return output_path
