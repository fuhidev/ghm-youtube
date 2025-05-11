import sys
import os
import datetime
import asyncio
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QPushButton,
    QLabel,
    QTextEdit,
    QFileDialog,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QDateTimeEdit,
    QMessageBox,
    QComboBox,
    QGroupBox,
)
from modules.tts import text_to_speech
from modules.image_gen import generate_image_from_story
from modules.video_gen import create_video
from modules.subtitle import create_subtitle
from modules.scheduler import schedule_task


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GHM-Youtube")
        self.setGeometry(100, 100, 800, 600)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Story input group
        story_group = QGroupBox("Nội dung truyện")
        story_layout = QVBoxLayout()

        # Input type selection
        input_type_layout = QHBoxLayout()
        self.input_direct_btn = QPushButton("Nhập trực tiếp", self)
        self.input_direct_btn.setCheckable(True)
        self.input_direct_btn.setChecked(True)
        self.input_file_btn = QPushButton("Chọn file txt", self)
        self.input_file_btn.setCheckable(True)

        input_type_layout.addWidget(self.input_direct_btn)
        input_type_layout.addWidget(self.input_file_btn)
        story_layout.addLayout(input_type_layout)

        # File selection area
        self.file_selection_layout = QHBoxLayout()
        self.file_path_label = QLabel("Chưa chọn file...", self)
        self.browse_file_btn = QPushButton("Chọn file", self)
        self.file_selection_layout.addWidget(self.file_path_label, 1)
        self.file_selection_layout.addWidget(self.browse_file_btn, 0)
        story_layout.addLayout(self.file_selection_layout)

        # Story input area
        self.story_input = QTextEdit(self)
        self.story_input.setPlaceholderText("Nhập truyện (tối đa 7000 ký tự)...")
        self.story_input.setText(
            "Mấy bông tuyết rơi lên bệ cửa sổ quán rượu ven đường - nơi trú chân duy nhất trong mười dặm giữa cơn bão tuyết."
        )
        story_layout.addWidget(self.story_input)

        # Set up story group
        story_group.setLayout(story_layout)
        layout.addWidget(story_group)

        # Voice selection group
        voice_group = QGroupBox("Lựa chọn giọng đọc")
        voice_layout = QVBoxLayout()

        # Ngôn ngữ
        lang_layout = QHBoxLayout()
        lang_label = QLabel("Ngôn ngữ:", self)
        self.lang_combobox = QComboBox(self)
        self.lang_combobox.addItem("Tiếng Việt", "vi")
        self.lang_combobox.addItem("Tiếng Anh", "en")
        lang_layout.addWidget(lang_label)
        lang_layout.addWidget(self.lang_combobox)
        voice_layout.addLayout(lang_layout)

        # Giọng đọc
        voice_layout_row = QHBoxLayout()
        voice_label = QLabel("Giọng đọc:", self)
        self.voice_combobox = QComboBox(self)

        # Thêm các giọng tiếng Việt mặc định
        self.voice_combobox.addItem("Nữ - Hoài My (vi-VN)", "vi-VN-HoaiMyNeural")
        self.voice_combobox.addItem("Nam - Nam Minh (vi-VN)", "vi-VN-NamMinhNeural")

        voice_layout_row.addWidget(voice_label)
        voice_layout_row.addWidget(self.voice_combobox)
        voice_layout.addLayout(voice_layout_row)

        # Nút cập nhật danh sách giọng
        self.refresh_voices_btn = QPushButton("Cập nhật danh sách giọng đọc", self)
        voice_layout.addWidget(self.refresh_voices_btn)

        voice_group.setLayout(voice_layout)
        layout.addWidget(voice_group)

        # Generate buttons
        self.generate_btn = QPushButton("Tạo Video", self)
        self.schedule_btn = QPushButton("Đặt lịch tạo Video", self)
        self.datetime_edit = QDateTimeEdit(self)
        self.datetime_edit.setCalendarPopup(True)
        self.status_label = QLabel("Trạng thái: Chờ nhập truyện", self)

        layout.addWidget(self.generate_btn)
        layout.addWidget(self.schedule_btn)
        layout.addWidget(self.datetime_edit)
        layout.addWidget(self.status_label)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # Connect signals
        self.generate_btn.clicked.connect(self.handle_generate)
        self.schedule_btn.clicked.connect(self.handle_schedule)
        self.refresh_voices_btn.clicked.connect(self.update_voice_list)
        self.lang_combobox.currentIndexChanged.connect(self.update_voice_list)

    def handle_generate(self):
        story = self.story_input.toPlainText().strip()
        if not story:
            self.status_label.setText("Vui lòng nhập truyện!")
            return
        self.status_label.setText("Đang xử lý...")
        self.generate_all(story)

    def handle_schedule(self):
        story = self.story_input.toPlainText().strip()
        if not story:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập truyện!")
            return
        run_time = self.datetime_edit.dateTime().toPyDateTime()
        if run_time < datetime.datetime.now():
            QMessageBox.warning(self, "Lỗi", "Thời gian phải ở tương lai!")
            return
        schedule_task(self.generate_all, run_time, story)
        QMessageBox.information(
            self, "Đặt lịch", f"Đã đặt lịch tạo video lúc {run_time}"
        )

    def update_voice_list(self):
        # Lưu lại voice ID đã chọn (nếu có)
        current_voice = self.voice_combobox.currentData()

        # Xóa danh sách hiện tại
        self.voice_combobox.clear()

        # Chọn danh sách giọng dựa trên ngôn ngữ
        lang_code = self.lang_combobox.currentData()

        if lang_code == "vi":
            # Thêm các giọng tiếng Việt
            self.voice_combobox.addItem("Nữ - Hoài My (vi-VN)", "vi-VN-HoaiMyNeural")
            self.voice_combobox.addItem("Nam - Nam Minh (vi-VN)", "vi-VN-NamMinhNeural")
        else:
            # Thêm các giọng tiếng Anh
            self.voice_combobox.addItem("Nữ - Aria (en-US)", "en-US-AriaNeural")
            self.voice_combobox.addItem("Nam - Guy (en-US)", "en-US-GuyNeural")
            self.voice_combobox.addItem("Nữ - Jenny (en-US)", "en-US-JennyNeural")
            self.voice_combobox.addItem("Nam - Jason (en-US)", "en-US-JasonNeural")

        # Khôi phục lại lựa chọn cũ nếu có trong danh sách mới
        if current_voice:
            index = self.voice_combobox.findData(current_voice)
            if index >= 0:
                self.voice_combobox.setCurrentIndex(index)

            # Nếu muốn tải đầy đủ danh sách giọng từ Edge TTS (có thể mất thời gian)        if self.sender() == self.refresh_voices_btn:
            self.status_label.setText("Đang tải danh sách giọng từ Edge TTS...")
            QApplication.processEvents()
            try:
                # Luôn tạo event loop mới để tránh DeprecationWarning
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                # Lấy danh sách giọng từ Edge TTS
                from modules.tts import get_available_voices, filter_voices_by_language

                all_voices = loop.run_until_complete(get_available_voices())

                # Xóa danh sách hiện tại
                self.voice_combobox.clear()

                # Lọc theo ngôn ngữ
                lang_prefix = "vi-VN" if lang_code == "vi" else "en"
                filtered_voices = filter_voices_by_language(all_voices, lang_prefix)

                # Thêm vào combo box
                for voice in filtered_voices:
                    gender = "Nữ" if voice["gender"] == "Female" else "Nam"
                    name = voice["name"]
                    locale = voice["locale"]
                    display_text = f"{gender} - {name} ({locale})"
                    self.voice_combobox.addItem(display_text, name)

                self.status_label.setText(
                    f"Đã tải {len(filtered_voices)} giọng {lang_prefix}"
                )
            except Exception as e:
                self.status_label.setText(f"Lỗi khi tải danh sách giọng: {str(e)}")
                # Khôi phục lại danh sách mặc định
                self.update_voice_list()

    def generate_all(self, story):
        base = "output"
        os.makedirs(base, exist_ok=True)
        audio_path = os.path.join(base, "audio.mp3")
        img_path = os.path.join(base, "image.png")
        video_path = os.path.join(base, "video.mp4")
        sub_path = os.path.join(base, "subtitle.ass")
        timing_path = os.path.join(base, "timings.json")

        # Lấy giọng đọc được chọn
        selected_voice = self.voice_combobox.currentData()
        selected_lang = self.lang_combobox.currentData()

        # 1. TTS (với ước tính thời gian)
        self.status_label.setText(
            f"Đang tạo giọng nói ({selected_voice}) và tính thời gian..."
        )
        QApplication.processEvents()
        audio_path, word_timings = text_to_speech(
            story,
            audio_path,
            lang=selected_lang,
            timing_file=timing_path,
            voice=selected_voice,
        )

        # 2. Image
        self.status_label.setText("Đang tạo hình ảnh...")
        QApplication.processEvents()
        generate_image_from_story(story, img_path)

        # 3. Subtitle (với dữ liệu timing)
        self.status_label.setText("Đang tạo phụ đề đồng bộ với audio...")
        QApplication.processEvents()
        create_subtitle(story, sub_path, word_timings=word_timings)

        # 4. Video với phụ đề
        self.status_label.setText("Đang tạo video và gắn phụ đề...")
        QApplication.processEvents()
        create_video(img_path, audio_path, video_path, sub_path)

        self.status_label.setText(f"Đã tạo video: {video_path}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
