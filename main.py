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
    QLineEdit,
    QCheckBox,
)
from modules.tts import text_to_speech
from modules.image_gen import generate_image_from_story
from modules.video_gen import create_video
from modules.subtitle import create_subtitle
from modules.scheduler import schedule_task
from modules.translate import translate_chinese_to_vietnamese


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GHM-Youtube")
        self.setGeometry(100, 100, 800, 600)
        self.api_key = "sk-b24c10868fa54902b565be1001666bfe"  # Default API key
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

        # Translation options
        translate_layout = QHBoxLayout()
        self.translate_checkbox = QCheckBox("Dịch từ tiếng Trung sang tiếng Việt", self)
        translate_layout.addWidget(self.translate_checkbox)
        story_layout.addLayout(translate_layout)

        # API key input for Deepseek
        api_key_layout = QHBoxLayout()
        api_key_label = QLabel("Deepseek API Key:", self)
        self.api_key_input = QLineEdit(self)
        self.api_key_input.setText(self.api_key)
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.textChanged.connect(self.update_api_key)
        api_key_layout.addWidget(api_key_label)
        api_key_layout.addWidget(self.api_key_input)
        story_layout.addLayout(api_key_layout)

        # Leonardo AI Key input
        leonardo_key_layout = QHBoxLayout()
        leonardo_key_label = QLabel("Leonardo AI Key:", self)
        self.leonardo_key_input = QLineEdit(self)
        self.leonardo_key_input.setPlaceholderText(
            "Nhập Leonardo.ai API key để tạo hình"
        )
        self.leonardo_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        leonardo_key_layout.addWidget(leonardo_key_label)
        leonardo_key_layout.addWidget(self.leonardo_key_input)
        story_layout.addLayout(leonardo_key_layout)

        # Image options
        image_options_layout = QHBoxLayout()
        image_count_label = QLabel("Số lượng hình ảnh:", self)
        self.image_count_combobox = QComboBox(self)
        for i in range(1, 11):  # 1 đến 10 hình
            self.image_count_combobox.addItem(f"{i} hình", i)
        image_options_layout.addWidget(image_count_label)
        image_options_layout.addWidget(self.image_count_combobox)
        story_layout.addLayout(image_options_layout)

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
        # self.schedule_btn = QPushButton("Đặt lịch tạo Video", self)
        # self.datetime_edit = QDateTimeEdit(self)
        # self.datetime_edit.setCalendarPopup(True)
        self.status_label = QLabel("Trạng thái: Chờ nhập truyện", self)

        layout.addWidget(self.generate_btn)
        # layout.addWidget(self.schedule_btn)
        # layout.addWidget(self.datetime_edit)
        layout.addWidget(self.status_label)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # Connect signals
        self.generate_btn.clicked.connect(self.handle_generate)
        # self.schedule_btn.clicked.connect(self.handle_schedule)
        self.refresh_voices_btn.clicked.connect(self.update_voice_list)
        self.lang_combobox.currentIndexChanged.connect(self.update_voice_list)

        # Connect input type signals
        self.input_direct_btn.clicked.connect(self.toggle_input_mode)
        self.input_file_btn.clicked.connect(self.toggle_input_mode)
        self.browse_file_btn.clicked.connect(self.browse_story_file)

        # Initialize UI state
        self.current_file_path = ""
        self.update_input_mode(direct=True)  # Initialize with direct input mode

    def toggle_input_mode(self):
        # If the sender is input_file_btn or it's already checked, switch to file mode
        if self.sender() == self.input_file_btn:
            self.update_input_mode(direct=False)
        # If the sender is input_direct_btn or it's already checked, switch to direct mode
        elif self.sender() == self.input_direct_btn:
            self.update_input_mode(direct=True)

    def update_input_mode(self, direct=True):
        # Update button states
        self.input_direct_btn.setChecked(direct)
        self.input_file_btn.setChecked(not direct)

        # Update UI elements based on mode
        self.file_path_label.setVisible(not direct)
        self.browse_file_btn.setVisible(not direct)

        # Update text field properties
        if direct:
            self.story_input.setReadOnly(False)
            self.story_input.setStyleSheet("")
        else:
            self.story_input.setReadOnly(True)
            if self.current_file_path:
                self.load_story_from_file(self.current_file_path)

    def browse_story_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Chọn file truyện", "", "Text Files (*.txt);;All Files (*)"
        )
        if file_path:
            self.current_file_path = file_path
            self.file_path_label.setText(os.path.basename(file_path))
            self.load_story_from_file(file_path)
            # Ensure we're in file mode after browsing
            self.update_input_mode(direct=False)

    def load_story_from_file(self, file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read()
                self.story_input.setText(content)
                self.status_label.setText(
                    f"Đã tải truyện từ file: {os.path.basename(file_path)}"
                )
        except Exception as e:
            self.status_label.setText(f"Lỗi khi đọc file: {str(e)}")
            QMessageBox.warning(self, "Lỗi đọc file", f"Không thể đọc file: {str(e)}")

    def handle_generate(self):
        story = self.story_input.toPlainText().strip()
        if not story:
            self.status_label.setText("Vui lòng nhập truyện hoặc chọn file!")
            return

        # Removed duplicate translation here as it's handled in generate_all
        self.status_label.setText("Đang xử lý...")
        self.generate_all(story)

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
            self.voice_combobox.addItem(
                "Nam - Jason (en-US)", "en-US-JasonNeural"
            )  # Khôi phục lại lựa chọn cũ nếu có trong danh sách mới
        if current_voice:
            index = self.voice_combobox.findData(current_voice)
            if index >= 0:
                self.voice_combobox.setCurrentIndex(index)

        # Nếu muốn tải đầy đủ danh sách giọng từ Edge TTS (có thể mất thời gian)
        if self.sender() == self.refresh_voices_btn:
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

        # Get Leonardo AI API key
        leonardo_api_key = self.leonardo_key_input.text().strip()

        # Check if translation is needed
        if self.translate_checkbox.isChecked():
            self.status_label.setText("Đang dịch từ tiếng Trung sang tiếng Việt...")
            QApplication.processEvents()
            try:
                # Save the original Chinese story
                original_story = story
                chinese_path = os.path.join(base, "original_chinese.txt")
                with open(chinese_path, "w", encoding="utf-8") as f:
                    f.write(original_story)

                # Translate the story
                story = translate_chinese_to_vietnamese(original_story, self.api_key)

                # Save the translated story
                vietnamese_path = os.path.join(base, "translated_vietnamese.txt")
                with open(vietnamese_path, "w", encoding="utf-8") as f:
                    f.write(story)

                self.status_label.setText("Đã dịch xong tiếng Trung sang tiếng Việt")
                QApplication.processEvents()

            except Exception as e:
                self.status_label.setText(f"Lỗi khi dịch: {str(e)}")
                QMessageBox.critical(
                    self, "Lỗi dịch thuật", f"Không thể dịch văn bản: {str(e)}"
                )
                return

        # Lấy giọng đọc được chọn
        selected_voice = self.voice_combobox.currentData()
        selected_lang = self.lang_combobox.currentData()

        # Ensure Vietnamese language is selected for translated content
        if self.translate_checkbox.isChecked():
            selected_lang = "vi"
            # Find a Vietnamese voice if current voice is not Vietnamese
            if not selected_voice.startswith("vi-"):
                # Set to default Vietnamese voice
                for i in range(self.voice_combobox.count()):
                    if self.voice_combobox.itemData(i).startswith("vi-"):
                        self.voice_combobox.setCurrentIndex(i)
                        selected_voice = self.voice_combobox.currentData()
                        break

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

        # 2. Image(s)
        self.status_label.setText("Đang tạo hình ảnh...")
        QApplication.processEvents()

        # Số lượng hình ảnh được chọn
        image_count = self.image_count_combobox.currentData()

        if image_count <= 1:
            # Tạo một hình duy nhất
            generate_image_from_story(story, img_path, leonardo_api_key or self.api_key)

            # 3. Subtitle (với dữ liệu timing)
            self.status_label.setText("Đang tạo phụ đề đồng bộ với audio...")
            QApplication.processEvents()
            create_subtitle(story, sub_path, word_timings=word_timings)

            # 4. Video với phụ đề
            self.status_label.setText("Đang tạo video và gắn phụ đề...")
            QApplication.processEvents()
            from modules.video_gen import create_video

            create_video(img_path, audio_path, video_path, sub_path)
        else:
            # Tạo nhiều hình ảnh
            self.status_label.setText(
                f"Đang tạo {image_count} hình ảnh cho các phân đoạn truyện..."
            )
            QApplication.processEvents()

            # Tạo nhiều hình ảnh
            segments_dir = os.path.join(base, "segment_images")
            os.makedirs(segments_dir, exist_ok=True)

            try:
                # Import các module cần thiết
                from modules.story_segment import process_story_for_images
                from modules.video_gen import (
                    create_video_with_segments,
                    get_audio_duration,
                )

                # Phân đoạn truyện và tạo hình ảnh
                image_paths = process_story_for_images(
                    story, image_count, segments_dir, leonardo_api_key or self.api_key
                )

                # 3. Subtitle (với dữ liệu timing)
                self.status_label.setText("Đang tạo phụ đề đồng bộ với audio...")
                QApplication.processEvents()
                create_subtitle(story, sub_path, word_timings=word_timings)

                # 4. Video với phụ đề từ nhiều hình ảnh
                self.status_label.setText(
                    f"Đang tạo video từ {len(image_paths)} hình ảnh và gắn phụ đề..."
                )
                QApplication.processEvents()

                create_video_with_segments(
                    image_paths, audio_path, video_path, sub_path
                )
            except Exception as e:
                self.status_label.setText(f"Lỗi khi tạo video từ nhiều hình: {str(e)}")
                QMessageBox.warning(
                    self,
                    "Lỗi tạo video",
                    f"Không thể tạo video từ nhiều hình: {str(e)}",
                )

                # Thử lại với một hình duy nhất
                self.status_label.setText("Thử tạo video với một hình đơn...")
                QApplication.processEvents()
                generate_image_from_story(
                    story, img_path, leonardo_api_key or self.api_key
                )

                from modules.video_gen import create_video

                create_video(img_path, audio_path, video_path, sub_path)

        self.status_label.setText(f"Đã tạo video: {video_path}")

    def update_api_key(self):
        """Update the API key when the input changes"""
        self.api_key = self.api_key_input.text().strip()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
