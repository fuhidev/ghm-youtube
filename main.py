import sys
import os
import datetime
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QPushButton,
    QLabel,
    QTextEdit,
    QFileDialog,
    QVBoxLayout,
    QWidget,
    QDateTimeEdit,
    QMessageBox,
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
        self.story_input = QTextEdit(self)
        self.story_input.setPlaceholderText("Nhập truyện (tối đa 7000 ký tự)...")
        self.story_input.setText(
            "Mấy bông tuyết rơi lên bệ cửa sổ quán rượu ven đường - nơi trú chân duy nhất trong mười dặm giữa cơn bão tuyết."
        )
        self.generate_btn = QPushButton("Tạo Video", self)
        self.schedule_btn = QPushButton("Đặt lịch tạo Video", self)
        self.datetime_edit = QDateTimeEdit(self)
        self.datetime_edit.setCalendarPopup(True)
        self.status_label = QLabel("Trạng thái: Chờ nhập truyện", self)
        layout.addWidget(self.story_input)
        layout.addWidget(self.generate_btn)
        layout.addWidget(self.schedule_btn)
        layout.addWidget(self.datetime_edit)
        layout.addWidget(self.status_label)
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
        self.generate_btn.clicked.connect(self.handle_generate)
        self.schedule_btn.clicked.connect(self.handle_schedule)

    def handle_generate(self):
        story = self.story_input.toPlainText().strip()
        if not story:
            self.status_label.setText("Vui lòng nhập truyện!")
            return
        self.status_label.setText("Đang xử lý...")
        self.generate_all(story)    def handle_schedule(self):
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

    def generate_all(self, story):
        base = "output"
        os.makedirs(base, exist_ok=True)
        audio_path = os.path.join(base, "audio.mp3")
        img_path = os.path.join(base, "image.png")
        video_path = os.path.join(base, "video.mp4")
        sub_path = os.path.join(base, "subtitle.ass")
        timing_path = os.path.join(base, "timings.json")

        # 1. TTS (với ước tính thời gian)
        self.status_label.setText("Đang tạo giọng nói và tính thời gian...")
        QApplication.processEvents()
        audio_path, word_timings = text_to_speech(
            story, audio_path, timing_file=timing_path
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
