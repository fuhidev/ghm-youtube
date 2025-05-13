# modules/video_gen.py
# Tạo video từ hình ảnh và audio
import ffmpeg
import os
import json
import logging
from typing import List, Optional
from pydub import AudioSegment
import math

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def normalize_path_for_ffmpeg(path):
    """
    Chuẩn hóa đường dẫn để sử dụng với ffmpeg trên Windows.
    Đảm bảo đường dẫn luôn là tuyệt đối, sử dụng dấu / thay vì \,
    và xử lý các ký tự đặc biệt.

    Args:
        path (str): Đường dẫn cần chuẩn hóa

    Returns:
        str: Đường dẫn đã chuẩn hóa
    """
    import pathlib

    # Chuyển đổi thành đường dẫn tuyệt đối
    abs_path = str(pathlib.Path(path).absolute())
    # Thay thế dấu \ bằng /
    normalized_path = abs_path.replace("\\", "/")
    return normalized_path


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
        subtitle_path_escaped = normalize_path_for_ffmpeg(subtitle_path)

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


def create_video_with_segments(
    image_paths: List[str], audio_path: str, output_path: str, subtitle_path=None
):
    """
    Tạo video từ nhiều hình ảnh và audio, với mỗi hình ảnh hiển thị trong một phần của audio

    Args:
        image_paths (List[str]): Danh sách đường dẫn đến các hình ảnh
        audio_path (str): Đường dẫn đến file audio
        output_path (str): Đường dẫn để lưu video đầu ra
        subtitle_path (str, optional): Đường dẫn đến file phụ đề

    Returns:
        str: Đường dẫn đến video đã tạo
    """
    # Lọc bỏ các đường dẫn hình ảnh không tồn tại
    valid_image_paths = [path for path in image_paths if path and os.path.exists(path)]

    if not valid_image_paths:
        logger.error("Không có hình ảnh hợp lệ để tạo video")
        # Nếu không có hình ảnh hợp lệ, sử dụng hàm tạo video từ một hình ảnh
        if len(image_paths) > 0 and os.path.exists(image_paths[0]):
            return create_video(image_paths[0], audio_path, output_path, subtitle_path)
        return None

    # Lấy độ dài audio
    probe = ffmpeg.probe(audio_path)
    total_duration = float(probe["format"]["duration"])

    # Tính thời gian cho mỗi hình ảnh
    segment_duration = total_duration / len(valid_image_paths)

    # Tạo file danh sách hình ảnh cho ffmpeg
    concat_file_path = os.path.join(os.path.dirname(output_path), "concat_list.txt")

    with open(concat_file_path, "w", encoding="utf-8") as f:
        for img_path in valid_image_paths:
            # Lấy đường dẫn tuyệt đối
            img_path_escaped = normalize_path_for_ffmpeg(img_path)
            f.write(f"file '{img_path_escaped}'\n")
            f.write(f"duration {segment_duration}\n")

        # Thêm hình ảnh cuối cùng một lần nữa với duration 0 để tránh lỗi        img_path_escaped = normalize_path_for_ffmpeg(valid_image_paths[-1])
        f.write(f"file '{img_path_escaped}'\n")

    # Tạo video từ danh sách hình ảnh (không có audio)
    temp_video_no_audio = output_path + ".temp_no_audio.mp4"

    try:
        # Log thông tin về concat_file_path để debug
        logger.info(f"Sử dụng concat file: {concat_file_path}")
        with open(concat_file_path, "r", encoding="utf-8") as f:
            content = f.read()
            logger.info(
                f"Nội dung concat file: {content}"
            )  # Thay vì dùng python-ffmpeg, dùng subprocess để có thể kiểm soát chính xác cách truyền đường dẫn
        import subprocess

        try:
            # Thêm '@' vào trước đường dẫn để tránh các vấn đề với ký tự đặc biệt trên Windows
            abs_concat_path = os.path.abspath(concat_file_path)
            logger.info(f"Đường dẫn concat file tuyệt đối: {abs_concat_path}")

            # Sử dụng ffmpeg trực tiếp qua subprocess
            cmd = [
                "ffmpeg",
                "-y",
                "-safe",
                "0",
                "-f",
                "concat",
                "-i",
                abs_concat_path,
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-r",
                "24",
                temp_video_no_audio,
            ]
            logger.info(f"Chạy lệnh ffmpeg: {' '.join(cmd)}")

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                logger.error(f"Lỗi ffmpeg: {result.stderr}")
                raise Exception(result.stderr)
            else:
                logger.info("Tạo video không có audio thành công")
        except Exception as subprocess_error:
            logger.error(f"Lỗi khi chạy ffmpeg: {str(subprocess_error)}")
            raise  # Thêm audio vào video sử dụng subprocess
        temp_video = output_path + ".temp.mp4"
        try:
            import subprocess

            cmd_audio = [
                "ffmpeg",
                "-y",
                "-i",
                temp_video_no_audio,
                "-i",
                audio_path,
                "-c:v",
                "copy",
                "-c:a",
                "aac",
                "-shortest",
                temp_video,
            ]
            logger.info(f"Chạy lệnh thêm audio: {' '.join(cmd_audio)}")

            result_audio = subprocess.run(cmd_audio, capture_output=True, text=True)

            if result_audio.returncode != 0:
                logger.error(f"Lỗi khi thêm audio: {result_audio.stderr}")
                raise Exception(result_audio.stderr)
            else:
                logger.info("Thêm audio vào video thành công")
        except Exception as audio_error:
            logger.error(f"Lỗi khi thêm audio: {str(audio_error)}")
            raise

        # Tiếp tục với phần xử lý phụ đề như trong hàm create_video
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
            # Không có phụ đề, sử dụng video đã có
            if os.path.exists(output_path):
                os.remove(output_path)
            os.rename(temp_video, output_path)

        # Dọn dẹp file tạm
        for file_path in [temp_video, temp_video_no_audio, concat_file_path]:
            try:
                if file_path and os.path.exists(file_path):
                    os.remove(file_path)
                    logger.info(f"Đã xóa file tạm: {file_path}")
            except Exception as cleanup_error:
                logger.warning(
                    f"Không thể xóa file tạm {file_path}: {str(cleanup_error)}"
                )

        logger.info(f"Đã tạo video từ {len(valid_image_paths)} hình ảnh: {output_path}")
        return output_path

    except Exception as e:
        logger.error(f"Lỗi khi tạo video từ nhiều hình ảnh: {str(e)}")

        # Nếu có lỗi, thử tạo video từ hình ảnh đầu tiên
        if valid_image_paths:
            logger.info("Thử tạo video với hình ảnh đầu tiên...")
            return create_video(
                valid_image_paths[0], audio_path, output_path, subtitle_path
            )
        return None


def get_audio_duration(audio_path):
    """
    Lấy độ dài của file audio

    Args:
        audio_path (str): Đường dẫn đến file audio

    Returns:
        float: Độ dài của file audio (đơn vị: giây)
    """
    try:
        probe = ffmpeg.probe(audio_path)
        return float(probe["format"]["duration"])
    except Exception:
        # Nếu ffprobe không hoạt động, thử với pydub
        try:
            audio = AudioSegment.from_file(audio_path)
            return len(audio) / 1000.0  # Chuyển từ mili giây sang giây
        except Exception as e:
            logger.error(f"Không thể lấy độ dài audio: {str(e)}")
            return 0
