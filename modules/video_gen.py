# modules/video_gen.py
# Tạo video từ hình ảnh và audio
import ffmpeg
import os

def create_video(image_path, audio_path, output_path, subtitle_path=None):
    # Lấy độ dài audio
    probe = ffmpeg.probe(audio_path)
    duration = float(probe['format']['duration'])
    
    # Tạo video từ ảnh tĩnh và audio
    input_image = ffmpeg.input(image_path, loop=1, t=duration)
    input_audio = ffmpeg.input(audio_path)
    
    temp_video = output_path + ".temp.mp4"
    
    # Tạo video cơ bản
    (
        ffmpeg
        .output(input_image, input_audio, temp_video, vcodec='libx264', acodec='aac', shortest=None, pix_fmt='yuv420p', r=24)
        .run(overwrite_output=True)
    )
    
    # Gắn phụ đề trực tiếp vào video (burned-in)
    if subtitle_path and os.path.exists(subtitle_path):
        video_with_subtitles = ffmpeg.input(temp_video)        # Escape đường dẫn phụ đề để ffmpeg có thể xử lý đúng trên Windows
        subtitle_path_escaped = subtitle_path.replace('\\', '\\\\').replace(':', '\\:')
        
        # Sử dụng subtitles filter với các tùy chọn để phụ đề lớn, đậm, màu trắng viền xanh, ở giữa
        subtitle_options = f"force_style='Fontname=Arial,Fontsize=48,PrimaryColour=&HFFFFFF,OutlineColour=&H0000FF,BorderStyle=1,Outline=3,Shadow=0,Alignment=8,MarginV=35'"
        
        # In thông tin debug
        print(f"Subtitle path: {subtitle_path_escaped}")
        print(f"Output path: {output_path}")
        
        try:
            (
                ffmpeg
                .output(
                    video_with_subtitles, 
                    output_path,
                    vf=f"subtitles='{subtitle_path_escaped}':{subtitle_options}",
                    vcodec='libx264', 
                    acodec='copy'
                )
                .run(overwrite_output=True)
            )
        except Exception as e:
            print(f"Error applying subtitles: {str(e)}")
            # Fallback: sử dụng video không có phụ đề
            os.rename(temp_video, output_path)
        
        # Xóa file tạm
        try:
            os.remove(temp_video)
        except:
            pass
    else:
        # Nếu không có file phụ đề, đổi tên file tạm thành file đích
        os.rename(temp_video, output_path)
    return output_path
