# modules/tts.py
# Chuyển văn bản thành giọng nói tiếng Việt và tính thời gian cho từng từ/câu
import os
import re
import json
import logging
import tempfile
from typing import List, Dict, Tuple, Optional
import torch
from TTS.api import TTS
import numpy as np
from pydub import AudioSegment

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Danh sách các mô hình tiếng Việt mặc định
VIETNAMESE_MODELS = ["tts_models/vi/vivos/vits"]

# Danh sách các mô hình tiếng Anh mặc định
ENGLISH_MODELS = [
    "tts_models/en/ljspeech/tacotron2-DDC",
    "tts_models/en/ljspeech/glow-tts",
]


class CoquiTTSWrapper:
    """Wrapper cho Coqui TTS để dễ dàng sử dụng"""

    def __init__(self):
        """Khởi tạo Coqui TTS wrapper"""
        logger.info("Khởi tạo Coqui TTS wrapper")
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Sử dụng thiết bị: {self.device}")

        # Khởi tạo TTS với mô hình mặc định (sẽ tự động tải nếu chưa có)
        self.tts = None
        self.current_model = None

    def load_model(self, model_name):
        """Tải mô hình TTS"""
        try:
            logger.info(f"Đang tải mô hình Coqui TTS: {model_name}")
            self.tts = TTS(model_name=model_name).to(self.device)
            self.current_model = model_name
            return True
        except Exception as e:
            logger.error(f"Lỗi khi tải mô hình Coqui TTS: {str(e)}")
            return False

    def get_available_models(self):
        """Lấy danh sách các mô hình Coqui TTS có sẵn"""
        try:
            # Trả về danh sách mô hình đã được định nghĩa sẵn để tránh vòng lặp vô hạn
            return SUPPORTED_MODELS
        except Exception as e:
            logger.error(f"Lỗi khi lấy danh sách mô hình: {str(e)}")
            return []

    def get_model_speakers(self):
        """Lấy danh sách các giọng nói cho mô hình hiện tại, nếu có"""
        if not self.tts:
            logger.error("Mô hình TTS chưa được tải")
            return []

        try:
            return self.tts.speakers
        except AttributeError:
            return []

    def synthesize(
        self, text: str, output_path: str, speaker: str = None, speed: float = 1.0
    ) -> Tuple[str, List[Dict]]:
        """
        Tổng hợp giọng nói từ văn bản và lưu vào file

        Args:
            text (str): Văn bản cần tổng hợp
            output_path (str): Đường dẫn để lưu file audio
            speaker (str, optional): Tên giọng nói cho mô hình multi-speaker
            speed (float, optional): Tốc độ nói (1.0 là bình thường)

        Returns:
            Tuple[str, List[Dict]]: Đường dẫn đến file audio và dữ liệu timing
        """
        if not self.tts:
            logger.error("Mô hình TTS chưa được tải")
            return output_path, []

        try:
            # Tạo thư mục nếu chưa tồn tại
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

            # Xử lý văn bản: chia thành các câu để tổng hợp tốt hơn
            sentences = self._split_into_sentences(text)

            # Tạo file tạm cho audio trung gian
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                temp_path = tmp_file.name

            # Xử lý từng câu và thu thập dữ liệu timing
            word_timings = []
            current_offset = 0

            # Tạo audio kết hợp
            combined_audio = None

            for i, sentence in enumerate(sentences):
                if not sentence.strip():
                    continue

                logger.info(
                    f"Đang tổng hợp câu {i+1}/{len(sentences)}: {sentence[:30]}..."
                )

                # Tổng hợp giọng nói cho câu
                speaker_args = {}
                if speaker and speaker in self.get_model_speakers():
                    speaker_args = {"speaker": speaker}

                wav = self.tts.tts(text=sentence, **speaker_args)

                # Chuyển đổi thành AudioSegment
                with tempfile.NamedTemporaryFile(
                    suffix=".wav", delete=False
                ) as sentence_file:
                    sentence_path = sentence_file.name
                self.tts.save_wav(wav, sentence_path)
                sentence_audio = AudioSegment.from_wav(sentence_path)

                # Điều chỉnh tốc độ nếu cần
                if speed != 1.0:
                    sentence_audio = self._adjust_speed(sentence_audio, speed)

                # Kết hợp với audio trước đó
                if combined_audio is None:
                    combined_audio = sentence_audio
                else:
                    combined_audio += sentence_audio

                # Ước tính thời gian cho từng từ trong câu
                sentence_duration = (
                    len(sentence_audio) / 1000.0
                )  # Chuyển từ ms sang giây
                sentence_timings = self._estimate_word_timings(
                    sentence, current_offset, sentence_duration
                )
                word_timings.extend(sentence_timings)

                # Cập nhật offset cho câu tiếp theo
                current_offset += sentence_duration

                # Xóa file tạm của câu
                os.unlink(sentence_path)

            # Lưu audio kết hợp
            if combined_audio:
                output_format = os.path.splitext(output_path)[1][1:].lower()
                if output_format == "mp3":
                    combined_audio.export(output_path, format="mp3")
                else:
                    combined_audio.export(output_path, format="wav")
            else:
                logger.error("Không có audio được tạo ra")

            # Xóa file tạm
            os.unlink(temp_path)

            return output_path, word_timings

        except Exception as e:
            logger.error(f"Lỗi trong quá trình tổng hợp giọng nói: {str(e)}")
            import traceback

            logger.error(traceback.format_exc())
            return output_path, []

    def _split_into_sentences(self, text: str) -> List[str]:
        """Chia văn bản thành các câu để tổng hợp tốt hơn"""
        # Chia câu đơn giản theo dấu câu
        sentences = re.split(r"(?<=[.!?])\s+", text)
        return sentences

    def _estimate_word_timings(
        self, sentence: str, start_time: float, duration: float
    ) -> List[Dict]:
        """
        Ước tính thời gian cho từng từ trong một câu

        Đây là một ước tính đơn giản phân bổ các từ đều nhau trong thời gian của câu.
        Để có timing chính xác hơn, cần sử dụng forced aligner.
        """
        words = sentence.split()
        if not words:
            return []

        # Phân bổ các từ đều đều trong thời lượng
        word_duration = duration / len(words)

        timings = []
        for i, word in enumerate(words):
            word_start = start_time + (i * word_duration)
            word_end = word_start + word_duration

            timings.append({"word": word, "start": word_start, "end": word_end})

        return timings

    def _adjust_speed(self, audio: AudioSegment, speed: float) -> AudioSegment:
        """Điều chỉnh tốc độ của một đoạn audio"""
        # Đây là cách đơn giản sử dụng pydub's speed change
        # Lưu ý: Cách này cũng thay đổi pitch, để có kết quả tốt hơn có thể sử dụng librosa
        sound_with_altered_frame_rate = audio._spawn(
            audio.raw_data, overrides={"frame_rate": int(audio.frame_rate * speed)}
        )
        return sound_with_altered_frame_rate.set_frame_rate(audio.frame_rate)


def get_available_voices():
    """
    Lấy tất cả các giọng nói/mô hình có sẵn trong Coqui TTS
    Tương thích với hàm liệt kê giọng nói của Edge TTS
    """
    # Danh sách mô hình cố định để tránh việc khởi tạo nhiều instance TTS
    # Coqui TTS có thể gây ra vòng lặp vô hạn khi tự gọi lại TTS().list_models()
    predefined_models = [
        # Tiếng Việt
        "tts_models/vi/vivos/vits",
        # Tiếng Anh
        "tts_models/en/ljspeech/tacotron2-DDC",
        "tts_models/en/ljspeech/glow-tts",
        "tts_models/en/ljspeech/speedy-speech",
        "tts_models/en/ljspeech/tacotron2-DDC_ph",
        "tts_models/en/ljspeech/fast_pitch",
        "tts_models/en/ljspeech/overflow",
        "tts_models/en/vctk/vits",
        "tts_models/en/vctk/fast_pitch",
        "tts_models/en/sam/tacotron-DDC",
        # Tiếng Tây Ban Nha
        "tts_models/es/mai/tacotron2-DDC",
        # Tiếng Pháp
        "tts_models/fr/mai/tacotron2-DDC",
        # Tiếng Đức
        "tts_models/de/thorsten/tacotron2-DDC",
        # Tiếng Hà Lan
        "tts_models/nl/mai/tacotron2-DDC",
        # Tiếng Ý
        "tts_models/it/mai/glow-tts",
        # Tiếng Nhật
        "tts_models/ja/kokoro/tacotron2-DDC",
    ]

    # Format các mô hình để phù hợp với format của Edge TTS
    formatted_models = []
    for model in predefined_models:
        # Trích xuất mã ngôn ngữ từ tên mô hình
        if "/vi/" in model:
            lang = "vi-VN"
        elif "/en/" in model:
            lang = "en-US"
        elif "/es/" in model:
            lang = "es-ES"
        elif "/fr/" in model:
            lang = "fr-FR"
        elif "/de/" in model:
            lang = "de-DE"
        elif "/nl/" in model:
            lang = "nl-NL"
        elif "/it/" in model:
            lang = "it-IT"
        elif "/ja/" in model:
            lang = "ja-JP"
        else:
            # Cố gắng trích xuất ngôn ngữ từ chuỗi mô hình
            lang_match = re.search(r"/([a-z]{2})/", model)
            lang = (
                f"{lang_match.group(1)}-{lang_match.group(1).upper()}"
                if lang_match
                else "unknown"
            )

        formatted_models.append(
            {
                "Name": model,
                "ShortName": model,
                "Gender": "Unknown",  # Coqui không chỉ định giới tính
                "Locale": lang,
            }
        )

    return formatted_models


def is_model_available(model_name):
    """
    Kiểm tra xem mô hình có sẵn trong danh sách mô hình định nghĩa sẵn không

    Args:
        model_name (str): Tên mô hình cần kiểm tra

    Returns:
        bool: True nếu mô hình có trong danh sách, False nếu không
    """
    available_models = [voice["Name"] for voice in get_available_voices()]
    return model_name in available_models


def filter_voices_by_language(all_voices, language_code="vi-VN"):
    """Lọc giọng nói theo mã ngôn ngữ"""
    filtered_voices = []
    language_prefix = language_code.split("-")[0]  # Trích xuất 'vi' từ 'vi-VN'

    for voice in all_voices:
        voice_lang = voice.get("Locale", "")
        if voice_lang.startswith(language_code) or f"/{language_prefix}/" in voice.get(
            "Name", ""
        ):
            filtered_voices.append(
                {
                    "name": voice.get("ShortName", ""),
                    "gender": voice.get("Gender", "Unknown"),
                    "locale": voice.get("Locale", ""),
                }
            )

    return filtered_voices


def text_to_speech(
    text, output_path, lang="vi", timing_file=None, voice=None, rate="+0%"
):
    """
    Tạo giọng nói từ văn bản sử dụng Coqui TTS với API tương thích với hệ thống hiện tại

    Args:
        text (str): Văn bản cần tổng hợp thành giọng nói
        output_path (str): Đường dẫn để lưu file audio
        lang (str): Mã ngôn ngữ ('vi' cho tiếng Việt, 'en' cho tiếng Anh)
        timing_file (str, optional): Đường dẫn để lưu dữ liệu timing
        voice (str, optional): Tên giọng nói/mô hình
        rate (str, optional): Tốc độ đọc theo định dạng "+0%", "+10%", "-5%", v.v.

    Returns:
        Tuple[str, List[Dict]]: Đường dẫn đến file audio và dữ liệu timing
    """
    # Chuyển đổi chuỗi rate thành số thực (ví dụ: "+7%" thành 1.07, "-5%" thành 0.95)
    speed = 1.0
    if rate.startswith("+"):
        speed = 1.0 + float(rate.strip("+%")) / 100
    elif rate.startswith("-"):
        speed = 1.0 - float(rate.strip("-%")) / 100

    # Khởi tạo và tải mô hình TTS
    tts_wrapper = CoquiTTSWrapper()

    # Chọn mô hình dựa trên ngôn ngữ và giọng được chỉ định
    selected_model = None  # Nếu đã có mô hình được chỉ định, kiểm tra và sử dụng nó
    if voice and voice.startswith("tts_models/"):
        # Kiểm tra xem mô hình có nằm trong danh sách được hỗ trợ không
        if is_model_available(voice):
            selected_model = voice
        else:
            logger.warning(
                f"Mô hình {voice} không có trong danh sách hỗ trợ, sử dụng mô hình mặc định"
            )
            # Sử dụng mô hình mặc định dựa trên ngôn ngữ
            if lang == "vi":
                selected_model = VIETNAMESE_MODELS[0]
            else:
                selected_model = ENGLISH_MODELS[0]
    else:
        # Nếu không, chọn mô hình mặc định dựa trên ngôn ngữ
        if lang == "vi":
            selected_model = VIETNAMESE_MODELS[0]
        else:
            selected_model = ENGLISH_MODELS[0]

    logger.info(f"Đang sử dụng mô hình: {selected_model}")
    success = tts_wrapper.load_model(selected_model)

    if not success:
        logger.error(
            "Không thể khởi tạo Coqui TTS, vui lòng kiểm tra xem mô hình có sẵn không"
        )
        return output_path, []

    # Tổng hợp giọng nói
    # Đối với mô hình đa giọng, chúng ta có thể truyền tham số speaker,
    # nhưng hiện tại chúng ta chỉ sử dụng mô hình đơn giọng nên bỏ qua
    output_path, word_timings = tts_wrapper.synthesize(
        text=text,
        output_path=output_path,
        speaker=None,  # Coqui TTS mô hình đơn giọng không cần tham số này
        speed=speed,
    )

    # Lưu dữ liệu timing nếu được yêu cầu
    if timing_file and word_timings:
        with open(timing_file, "w", encoding="utf-8") as f:
            json.dump(word_timings, f, ensure_ascii=False, indent=2)

    return output_path, word_timings


if __name__ == "__main__":
    # Thử nghiệm Coqui TTS
    print("Đang thử nghiệm Coqui TTS...")
    test_text = "Xin chào, đây là bài kiểm tra Coqui TTS. Tôi đang nói tiếng Việt."
    output_path = "test_coqui.mp3"

    result_path, timings = text_to_speech(test_text, output_path)
    print(f"Audio đã lưu tại: {result_path}")
    print(f"Đã tạo {len(timings)} timing từ")
