# 🤖 AI Chatbot với Streamlit & Google Gemini API

Ứng dụng chatbot AI thông minh, giao diện trực quan tương tự ChatGPT, được xây dựng bằng **Python**, **Streamlit** và SDK chính thức mới nhất **`google-genai`**.

---

## ✨ Tính năng nổi bật

- **Giao diện trò chuyện tối giản, trực quan**: Tương tự ChatGPT, chỉ hiển thị tiêu đề và nội dung chat, không bị rối mắt bởi thanh bên.
- **Chọn mô hình ngay tại ô soạn tin**: Dropdown lựa chọn model AI (`gemini-3.5-flash`, `gemini-3.8-flash`,...) và nút xóa chat được tích hợp ngay phía trên thanh nhập tin nhắn.
- **Nhận biết thời gian thực**: Tự động cung cấp ngữ cảnh ngày, tháng, năm, thứ và giờ theo thời gian thực tại Việt Nam vào bot.
- **Tự động lưu API Key**: Tự động nhận diện và nạp API Key vĩnh viễn từ file cấu hình `.env` / `secrets.toml`.
- **Phản hồi thời gian thực (Streaming)**: Chữ xuất hiện mượt mà từng từ với `generate_content_stream` và `st.write_stream`.
- **Lưu lịch sử hội thoại**: Tự động lưu trữ ngữ cảnh trong `st.session_state`, AI ghi nhớ các tin nhắn trước trong phiên trò chuyện.
- **Xử lý lỗi thông minh**: Hiển thị thông báo chi tiết ngay trong giao diện chat nếu xảy ra sự cố API.
- **Giao diện 100% tiếng Việt**: Thân thiện, hiện đại và dễ sử dụng.

---

## 🔑 Hướng dẫn lấy Google Gemini API Key miễn phí

1. Truy cập vào trang quản lý khóa của Google AI Studio: [https://aistudio.google.com/apikey](https://aistudio.google.com/apikey).
2. Đăng nhập bằng tài khoản Google của bạn.
3. Nhấp vào nút **"Create API key"** (Tạo khóa API).
4. Chọn dự án Google Cloud có sẵn hoặc tạo dự án mới, sau đó nhấn **"Create API key in new project"**.
5. Sao chép chuỗi API key được tạo (bắt đầu bằng `AIzaSy...`).

---

## 🚀 Hướng dẫn cài đặt và khởi chạy

### 1. Chuẩn bị môi trường
Yêu cầu máy tính đã cài đặt Python 3.9 trở lên.

Mở Terminal hoặc PowerShell tại thư mục dự án `d:\chatbot`:

```bash
# (Khuyến nghị) Tạo và kích hoạt môi trường ảo
python -m venv venv

# Kích hoạt trên Windows:
.\venv\Scripts\activate

# Hoặc kích hoạt trên macOS/Linux:
source venv/bin/activate
```

### 2. Cài đặt các thư viện cần thiết

Cài đặt các gói phụ thuộc từ tệp `requirements.txt`:

```bash
pip install -r requirements.txt
```

### 3. Cấu hình API Key (Tùy chọn)

Bạn có thể cấu hình API Key thông qua biến môi trường để không cần nhập lại mỗi lần mở app:

**Trên Windows (PowerShell):**
```powershell
$env:GEMINI_API_KEY="AIzaSy_YOUR_API_KEY_HERE"
```

**Hoặc tạo file `.env`** nếu muốn cấu hình tự động.
*(Nếu không cấu hình biến môi trường, bạn có thể nhập trực tiếp API Key trên thanh bên trái của giao diện web).*

### 4. Chạy ứng dụng

Khởi chạy ứng dụng Streamlit:

```bash
streamlit run app.py
```

Sau khi chạy lệnh trên, trình duyệt web sẽ tự động mở địa chỉ:
👉 **`http://localhost:8501`**

---

## 📁 Cấu trúc thư mục

```text
chatbot/
├── app.py              # Mã nguồn chính của ứng dụng
├── requirements.txt    # Danh sách thư viện phụ thuộc (streamlit, google-genai)
└── README.md           # Tài liệu hướng dẫn sử dụng
```

---

## 🛠️ Hướng phát triển mở rộng (Extensions)

Mã nguồn được cấu trúc sạch sẽ và có chú thích chi tiết, bạn có thể dễ dàng mở rộng:
1. **Lưu lịch sử hội thoại**: Kết nối với SQLite hoặc PostgreSQL để lưu trữ vĩnh viễn các đoạn chat theo người dùng.
2. **Hỗ trợ đa phương tiện**: Nâng cấp cho phép người dùng tải lên hình ảnh hoặc tài liệu PDF để Gemini phân tích (Multimodal).
3. **Thêm Personas chuyên sâu**: Mở rộng danh sách vai trò cho bot (Chuyên gia tài chính, Luyện thi IELTS, Phỏng vấn tuyển dụng,...).
