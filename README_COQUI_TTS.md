# Chuyển từ Edge TTS sang Coqui TTS

## Giới thiệu
Phần mềm YouTube Tool hiện sử dụng Coqui TTS thay vì Edge TTS cho việc tổng hợp giọng nói. Điều này mang lại nhiều lợi ích:

1. **Hoạt động ngoại tuyến**: Coqui TTS hoạt động hoàn toàn trên máy của bạn, không cần kết nối internet sau khi đã tải mô hình
2. **Kiểm soát nhiều hơn**: Cho phép điều chỉnh và tinh chỉnh nhiều thông số của giọng đọc
3. **Mã nguồn mở**: Đây là giải pháp mã nguồn mở hoàn toàn, không phụ thuộc vào dịch vụ của bên thứ ba

## Cài đặt
Để sử dụng Coqui TTS, bạn cần cài đặt các thư viện bổ sung. Chạy lệnh sau:

```bash
pip install -r requirements.txt
```

Điều này sẽ cài đặt:
- TTS (Coqui TTS)
- PyTorch
- Các phụ thuộc cần thiết khác

## Sử dụng lần đầu
Khi sử dụng lần đầu, Coqui TTS sẽ tự động tải xuống các mô hình giọng nói cần thiết. Quá trình này có thể mất một ít thời gian, tùy thuộc vào tốc độ internet của bạn. Các mô hình mặc định:

- Tiếng Việt: `tts_models/vi/vivos/vits`
- Tiếng Anh: `tts_models/en/ljspeech/tacotron2-DDC`

## Chọn mô hình giọng đọc
1. Trong giao diện chính, bạn có thể chọn giữa các mô hình có sẵn trong combobox "Giọng đọc"
2. Để tải thêm các mô hình khác, nhấn nút "Cập nhật danh sách giọng đọc"

## Tối ưu hóa hiệu suất
Coqui TTS có thể sử dụng GPU để tăng tốc quá trình tổng hợp giọng nói:

1. **Sử dụng GPU**: Nếu máy tính của bạn có GPU hỗ trợ CUDA, Coqui TTS sẽ tự động sử dụng GPU
2. **Tinh chỉnh hiệu suất**: Cho máy tính yếu hơn, bạn có thể giảm kích thước mô hình bằng cách chọn mô hình đơn giản hơn

## Xử lý lỗi thông thường
1. **ModuleNotFoundError: No module named 'TTS'**: Đảm bảo bạn đã cài đặt Coqui TTS bằng `pip install TTS`
2. **Lỗi tải mô hình**: Kiểm tra kết nối internet khi tải mô hình lần đầu
3. **Lỗi CUDA**: Nếu gặp lỗi liên quan đến CUDA, hãy đảm bảo bạn đã cài đặt đúng phiên bản PyTorch phù hợp với phiên bản CUDA

## Thông tin thời lượng video
Phiên bản mới hiện hiển thị thông tin chi tiết về thời lượng video và audio sau khi tạo. Các thông tin này giúp bạn kiểm tra xem video có được tạo đúng độ dài so với audio gốc hay không.

## Liên hệ hỗ trợ
Nếu bạn gặp bất kỳ vấn đề nào khi sử dụng Coqui TTS, vui lòng liên hệ với đội phát triển để được hỗ trợ.
