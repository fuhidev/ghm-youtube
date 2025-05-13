import os
import sys
import argparse
from modules.video_gen import (
    create_video,
    create_video_with_segments,
    normalize_path_for_ffmpeg,
)


def main():
    """
    Hàm test các chức năng của video_gen.py
    """
    parser = argparse.ArgumentParser(
        description="Test tạo video với hoặc không có phụ đề"
    )
    parser.add_argument(
        "--single", action="store_true", help="Test tạo video với 1 hình"
    )
    parser.add_argument(
        "--multiple", action="store_true", help="Test tạo video với nhiều hình"
    )
    parser.add_argument("--both", action="store_true", help="Test cả 2 phương pháp")
    parser.add_argument("--image", help="Đường dẫn đến hình ảnh (cho test single)")
    parser.add_argument(
        "--imagedir", help="Thư mục chứa nhiều hình ảnh (cho test multiple)"
    )
    parser.add_argument("--audio", help="Đường dẫn đến file audio")
    parser.add_argument("--subtitle", help="Đường dẫn đến file phụ đề")

    args = parser.parse_args()

    # Nếu không có tham số, mặc định test cả hai phương pháp
    if not (args.single or args.multiple or args.both):
        args.both = True

    # Chuẩn bị các đường dẫn mặc định nếu không được cung cấp
    output_dir = os.path.join(os.getcwd(), "output")
    os.makedirs(output_dir, exist_ok=True)

    # Kiểm tra và thiết lập các đường dẫn mặc định
    if not args.image:
        args.image = os.path.join(output_dir, "default_image.jpg")
        # Tạo một hình ảnh đơn giản nếu không tồn tại
        if not os.path.exists(args.image):
            try:
                from PIL import Image, ImageDraw

                img = Image.new("RGB", (800, 600), color=(73, 109, 137))
                d = ImageDraw.Draw(img)
                d.text((300, 300), "Test Image", fill=(255, 255, 0))
                img.save(args.image)
                print(f"Đã tạo file hình ảnh mặc định: {args.image}")
            except ImportError:
                print(
                    "Không thể import PIL để tạo hình ảnh. Vui lòng cài đặt với 'pip install Pillow'"
                )
                return

    if not args.imagedir:
        args.imagedir = output_dir
        # Tạo một vài hình ảnh nếu chưa có
        default_images = []
        for i in range(1, 4):
            img_path = os.path.join(output_dir, f"default_image_{i}.jpg")
            default_images.append(img_path)
            if not os.path.exists(img_path):
                try:
                    from PIL import Image, ImageDraw

                    img = Image.new("RGB", (800, 600), color=(73 + i * 30, 109, 137))
                    d = ImageDraw.Draw(img)
                    d.text((300, 300), f"Test Image {i}", fill=(255, 255, 0))
                    img.save(img_path)
                    print(f"Đã tạo file hình ảnh mặc định: {img_path}")
                except ImportError:
                    print("Không thể import PIL để tạo hình ảnh.")
                    return
    else:
        # Lấy danh sách tất cả file .jpg và .png trong thư mục
        default_images = [
            os.path.join(args.imagedir, f)
            for f in os.listdir(args.imagedir)
            if f.lower().endswith((".jpg", ".jpeg", ".png"))
        ]

    if not args.audio:
        args.audio = os.path.join(output_dir, "default_audio.mp3")
        # Tạo file audio mặc định nếu không tồn tại
        if not os.path.exists(args.audio):
            try:
                from scipy.io import wavfile
                import numpy as np

                # Tạo một đoạn âm thanh cơ bản (3 giây)
                sample_rate = 44100
                duration = 3  # seconds
                t = np.linspace(0, duration, int(sample_rate * duration))
                # Âm thanh sin wave 440Hz
                data = np.sin(2 * np.pi * 440 * t) * 32767
                wavfile.write(
                    args.audio.replace(".mp3", ".wav"),
                    sample_rate,
                    data.astype(np.int16),
                )
                print(
                    f"Đã tạo file audio mặc định: {args.audio.replace('.mp3', '.wav')}"
                )

                # Chuyển từ wav sang mp3 nếu có ffmpeg
                import subprocess

                try:
                    subprocess.run(
                        [
                            "ffmpeg",
                            "-y",
                            "-i",
                            args.audio.replace(".mp3", ".wav"),
                            args.audio,
                        ],
                        check=True,
                    )
                    print(f"Đã chuyển đổi sang MP3: {args.audio}")
                except:
                    print("Không thể chuyển đổi sang MP3. Sử dụng file WAV.")
                    args.audio = args.audio.replace(".mp3", ".wav")
            except ImportError:
                print(
                    "Không thể import scipy để tạo audio. Vui lòng cài đặt với 'pip install scipy'"
                )
                return

    if not args.subtitle:
        args.subtitle = os.path.join(output_dir, "subtitle.ass")
        # Tạo file phụ đề mặc định nếu không tồn tại
        if not os.path.exists(args.subtitle):
            with open(args.subtitle, "w", encoding="utf-8") as f:
                f.write(
                    """[Script Info]
ScriptType: v4.00+
PlayResX: 1280
PlayResY: 720
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,28,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2,0,2,10,10,10,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.00,0:00:03.00,Default,,0,0,0,,Đây là phụ đề mẫu dòng 1
Dialogue: 0,0:00:03.00,0:00:06.00,Default,,0,0,0,,Đây là phụ đề mẫu dòng 2
"""
                )
                print(f"Đã tạo file phụ đề mẫu: {args.subtitle}")

    # Thiết lập đường dẫn file đầu ra
    single_output = os.path.join(output_dir, "video_single.mp4")
    multi_output = os.path.join(output_dir, "video_multi.mp4")

    # Test với một hình ảnh
    if args.single or args.both:
        print("\n=== TEST TẠO VIDEO VỚI MỘT HÌNH ẢNH ===")
        print(f"Hình ảnh: {args.image}")
        print(f"Audio: {args.audio}")
        print(f"Phụ đề: {args.subtitle}")
        print(f"Output: {single_output}")

        try:
            result = create_video(args.image, args.audio, single_output, args.subtitle)
            if result:
                print(f"✅ Tạo video với 1 hình thành công: {result}")
                # Hiển thị thông tin đường dẫn phụ đề đã xử lý
                subtitle_path_escaped = normalize_path_for_ffmpeg(args.subtitle)
                print(f"Đường dẫn phụ đề sau khi xử lý: {subtitle_path_escaped}")
            else:
                print("❌ Tạo video với 1 hình thất bại!")
        except Exception as e:
            print(f"❌ Lỗi khi tạo video với 1 hình: {str(e)}")

    # Test với nhiều hình ảnh
    if args.multiple or args.both:
        print("\n=== TEST TẠO VIDEO VỚI NHIỀU HÌNH ẢNH ===")
        print(f"Hình ảnh: {default_images}")
        print(f"Audio: {args.audio}")
        print(f"Phụ đề: {args.subtitle}")
        print(f"Output: {multi_output}")

        try:
            result = create_video_with_segments(
                default_images, args.audio, multi_output, args.subtitle
            )
            if result:
                print(f"✅ Tạo video với nhiều hình thành công: {result}")
                # Hiển thị thông tin đường dẫn phụ đề đã xử lý
                subtitle_path_escaped = normalize_path_for_ffmpeg(args.subtitle)
                print(f"Đường dẫn phụ đề sau khi xử lý: {subtitle_path_escaped}")
            else:
                print("❌ Tạo video với nhiều hình thất bại!")
        except Exception as e:
            print(f"❌ Lỗi khi tạo video với nhiều hình: {str(e)}")


if __name__ == "__main__":
    main()
