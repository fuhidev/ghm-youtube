# modules/video_gen.py
# Tạo video từ hình ảnh và audio
import ffmpeg
import os


def create_video(image_path, audio_path, output_path, subtitle_path=None):
    # Lấy độ dài audio
    probe = ffmpeg.probe(audio_path)
    duration = float(probe["format"]["duration"])

    # Tạo video từ ảnh tĩnh và audio
    input_image = ffmpeg.input(image_path, loop=1, t=duration)
    input_audio = ffmpeg.input(audio_path)

    temp_video = output_path + ".temp.mp4"

    # Tạo video cơ bản
    (
        ffmpeg.output(
            input_image,
            input_audio,
            temp_video,
            vcodec="libx264",
            acodec="aac",
            shortest=None,
            pix_fmt="yuv420p",
            r=24,
        ).run(overwrite_output=True)
    )  # Gắn phụ đề trực tiếp vào video (burned-in)
    if subtitle_path and os.path.exists(subtitle_path):
        video_with_subtitles = ffmpeg.input(temp_video)

        # Kiểm tra xem file phụ đề có dữ liệu không
        with open(subtitle_path, "r", encoding="utf-8") as f:
            subtitle_content = f.read()

        if not subtitle_content.strip():
            print(f"File phụ đề rỗng: {subtitle_path}")
            # Kiểm tra và xử lý nếu file đích đã tồn tại
            if os.path.exists(output_path):
                os.remove(output_path)
            os.rename(temp_video, output_path)
            return output_path

        # Sử dụng đường dẫn tuyệt đối cho Windows
        import pathlib

        subtitle_absolute_path = pathlib.Path(subtitle_path).absolute()

        # Escape đường dẫn phụ đề cho ffmpeg theo cách đảm bảo hoạt động trên Windows
        subtitle_path_escaped = (
            str(subtitle_absolute_path).replace("\\", "/").replace(":", "\\:")
        )

        # Sử dụng subtitles filter với các tùy chọn để phụ đề lớn, đậm, màu trắng viền xanh, ở giữa
        subtitle_options = f"force_style='Fontname=Arial,Fontsize=28,PrimaryColour=&HFFFFFF,OutlineColour=&H0000FF,BorderStyle=1,Outline=3,Shadow=0,Alignment=2,MarginV=35'"

        # In thông tin debug
        print(f"Subtitle path: {subtitle_path}")
        print(f"Subtitle path escaped: {subtitle_path_escaped}")
        print(f"Output path: {output_path}")

        try:
            # Kiểm tra và xóa file đích nếu đã tồn tại
            if os.path.exists(output_path):
                os.remove(output_path)

            # Sử dụng cả hai cách để thử gắn phụ đề
            try:
                # Cách 1: Sử dụng vf=subtitles trực tiếp
                (
                    ffmpeg.output(
                        video_with_subtitles,
                        output_path,
                        vf=f"subtitles='{subtitle_path_escaped}':{subtitle_options}",
                        vcodec="libx264",
                        acodec="copy",
                    ).run(overwrite_output=True)
                )
            except Exception as e1:
                print(f"Lỗi phương pháp 1: {str(e1)}")

                # Cách 2: Sử dụng options thông qua -vf flag
                import subprocess

                cmd = [
                    "ffmpeg",
                    "-y",
                    "-i",
                    temp_video,
                    "-vf",
                    f"subtitles='{subtitle_path_escaped}':{subtitle_options}",
                    "-c:v",
                    "libx264",
                    "-c:a",
                    "copy",
                    output_path,
                ]
                print(f"Lệnh ffmpeg: {' '.join(cmd)}")
                result = subprocess.run(cmd, capture_output=True, text=True)

                if result.returncode != 0:
                    print(f"Lỗi phương pháp 2: {result.stderr}")
                    raise Exception(result.stderr)

        except Exception as e:
            print(f"Lỗi khi gắn phụ đề: {str(e)}")
            # Fallback: sử dụng video không có phụ đề
            if os.path.exists(output_path):
                os.remove(output_path)
            os.rename(temp_video, output_path)
    else:
        # Nếu không có file phụ đề, đổi tên file tạm thành file đích
        if os.path.exists(output_path):
            os.remove(output_path)
        os.rename(temp_video, output_path)

        # Xóa file tạm
        try:
            os.remove(temp_video)
        except:
            pass
    return output_path
