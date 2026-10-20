"""
Ứng dụng Chatbot AI đơn giản với Streamlit và Google Gemini API (google-genai SDK).
Hỗ trợ streaming phản hồi, quản lý lịch sử hội thoại, tuỳ biến vai trò (system prompt).
"""

import os
from datetime import datetime
import streamlit as st
from google import genai
from google.genai import types

def get_current_time_context() -> str:
    """Trả về ngữ cảnh ngày và thứ thời gian thực bằng tiếng Việt."""
    now = datetime.now()
    weekdays_vn = {
        0: "Thứ Hai",
        1: "Thứ Ba",
        2: "Thứ Tư",
        3: "Thứ Năm",
        4: "Thứ Sáu",
        5: "Thứ Bảy",
        6: "Chủ Nhật"
    }
    weekday_str = weekdays_vn[now.weekday()]
    date_str = now.strftime("%d/%m/%Y")
    time_str = now.strftime("%H:%M:%S")
    return (
        f"[THỜI GIAN THỰC TẠI VIỆT NAM]\n"
        f"- Thứ hiện tại: {weekday_str}\n"
        f"- Ngày tháng năm: {date_str} (Ngày {now.day}, Tháng {now.month}, Năm {now.year})\n"
        f"- Giờ hiện tại: {time_str}\n"
        f"Hãy luôn sử dụng thông tin thời gian thực này để trả lời chính xác khi người dùng hỏi về hôm nay là thứ mấy, ngày mấy, tháng mấy, năm mấy hoặc mấy giờ."
    )


# -----------------------------------------------------------------------------
# 1. Cấu hình trang Streamlit
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Gemini AI Chatbot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Thêm một chút CSS tùy chỉnh để giao diện hiện đại và gọn gàng hơn
st.markdown("""
<style>
    .chat-header {
        font-size: 1.8rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        display: flex;
        align-items: center;
        gap: 0.6rem;
    }
    .badge {
        background: linear-gradient(135deg, #4285F4, #9B51E0);
        color: white;
        padding: 0.2rem 0.6rem;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .stChatMessage {
        border-radius: 12px;
        margin-bottom: 0.5rem;
    }
    .welcome-card {
        padding: 1.5rem;
        border-radius: 12px;
        background-color: rgba(66, 133, 244, 0.08);
        border: 1px dashed rgba(66, 133, 244, 0.3);
        margin-bottom: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. Khởi tạo Session State (lưu lịch sử chat)
# -----------------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# -----------------------------------------------------------------------------
# 3. Nạp API Key & Thiết lập mặc định
# -----------------------------------------------------------------------------
api_key = ""
try:
    if "GEMINI_API_KEY" in st.secrets:
        api_key = str(st.secrets["GEMINI_API_KEY"])
except Exception:
    pass

if not api_key:
    api_key = os.environ.get("GEMINI_API_KEY", "")

if not api_key and os.path.exists(".env"):
    try:
        with open(".env", "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("GEMINI_API_KEY="):
                    api_key = line.strip().split("=", 1)[1].strip().strip('"').strip("'")
                    break
    except Exception:
        pass

# System prompt mặc định
system_prompt = "Bạn là một trợ lý AI thông minh, nhiệt tình và hữu ích. Hãy trả lời ngắn gọn, chính xác bằng tiếng Việt."

# -----------------------------------------------------------------------------
# 4. Giao diện Chat chính
# -----------------------------------------------------------------------------
st.markdown('<div class="chat-header"><span>🤖 Trợ lý AI</span></div>', unsafe_allow_html=True)

# Hiển thị lời chào khi chưa có tin nhắn nào
if not st.session_state.messages:
    with st.container():
        st.markdown("""
        <div class="welcome-card">
            <h4>👋 Xin chào! Tôi có thể giúp gì cho bạn hôm nay?</h4>
        </div>
        """, unsafe_allow_html=True)

# Hiển thị lại toàn bộ lịch sử trò chuyện đã lưu trong session_state
for message in st.session_state.messages:
    role = message["role"]
    content = message["content"]
    with st.chat_message(role):
        st.markdown(content)

# -----------------------------------------------------------------------------
# 5. Khu vực soạn tin nhắn & Chọn Model ở cuối trang
# -----------------------------------------------------------------------------
with st.bottom:
    col_model, col_clear, _ = st.columns([2.5, 1.2, 4])
    with col_model:
        selected_model = st.selectbox(
            "Chọn mô hình AI:",
            options=[
                "gemini-3.5-flash",
                "gemini-3.5-flash-lite",
                "gemini-3.8-flash",
                "gemini-3.7-flash"
            ],
            index=0,
            label_visibility="collapsed",
            help="Chọn mô hình AI để trò chuyện"
        )
    with col_clear:
        if st.button("🗑️ Xóa chat", help="Xóa sạch lịch sử hội thoại"):
            st.session_state.messages = []
            st.rerun()

    user_input = st.chat_input("Nhập tin nhắn của bạn tại đây...")


if user_input:
    # 5.1 Kiểm tra API Key
    if not api_key:
        st.warning("⚠️ Vui lòng nhập **Google Gemini API Key** ở thanh bên trái (Sidebar) để bắt đầu trò chuyện!")
        st.stop()

    # 5.2 Lưu và hiển thị ngay tin nhắn của người dùng
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # 5.3 Chuẩn bị ngữ cảnh hội thoại cho Gemini API
    # Chuyển đổi định dạng lịch sử từ session_state sang cấu trúc Content của google-genai
    gemini_contents = []
    for msg in st.session_state.messages:
        # Trong Gemini API: vai trò người dùng là 'user', bot là 'model'
        gemini_role = "user" if msg["role"] == "user" else "model"
        gemini_contents.append(
            types.Content(
                role=gemini_role,
                parts=[types.Part.from_text(text=msg["content"])]
            )
        )

    # 5.4 Tạo phản hồi của AI với giao diện Streaming
    with st.chat_message("assistant"):
        full_response = ""
        try:
            # Khởi tạo client Gemini với giới hạn thời gian phản hồi (timeout 20s)
            client = genai.Client(
                api_key=api_key,
                http_options=types.HttpOptions(timeout=20000)
            )

            # Tự động kết hợp System Prompt tuỳ biến và ngữ cảnh ngày/thứ thời gian thực
            time_context = get_current_time_context()
            final_system_instruction = (
                f"{system_prompt.strip()}\n\n{time_context}"
                if system_prompt.strip()
                else time_context
            )

            # Cấu hình system prompt và tắt AFC thừa để tăng tốc
            config = types.GenerateContentConfig(
                system_instruction=final_system_instruction,
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True)
            )

            # Gọi API theo cơ chế streaming kèm thông báo chờ
            with st.spinner("🤖 Đang suy nghĩ..."):
                response_stream = client.models.generate_content_stream(
                    model=selected_model,
                    contents=gemini_contents,
                    config=config
                )

            # Generator để truyền vào st.write_stream nhằm hiển thị chữ mượt mà
            def stream_generator():
                for chunk in response_stream:
                    if chunk.text:
                        yield chunk.text

            # Streamlit render phản hồi từng chữ
            full_response = st.write_stream(stream_generator())

            # Lưu phản hồi hoàn chỉnh của trợ lý vào session_state
            st.session_state.messages.append({"role": "assistant", "content": full_response})

        except Exception as e:
            error_str = str(e)
            
            # Xử lý các loại lỗi phổ biến và đưa ra hướng dẫn cụ thể
            if "timeout" in error_str.lower() or "deadline" in error_str.lower() or "504" in error_str:
                st.error(
                    f"⏳ **Mô hình `{selected_model}` phản hồi quá lâu (Timeout / Quá tải).**\n\n"
                    f"👉 Hãy chuyển sang mô hình nhanh và ổn định nhất: **`gemini-3.5-flash`** ở thanh bên trái (Sidebar)."
                )
            elif "503" in error_str or "high demand" in error_str.lower() or "unavailable" in error_str.lower():
                st.error(
                    f"⚠️ **Mô hình `{selected_model}` đang bị quá tải từ phía Google (Lỗi 503 - High Demand).**\n\n"
                    f"👉 Hãy chuyển sang mô hình **`gemini-3.5-flash`** ở thanh bên trái (Sidebar) — mô hình này đang hoạt động rất tốt."
                )
            elif "404" in error_str or "not_found" in error_str.lower() or "no longer available" in error_str.lower():
                st.error(
                    f"⚠️ **Mô hình `{selected_model}` không còn khả dụng hoặc đã dừng hỗ trợ.**\n\n"
                    f"👉 Vui lòng chuyển sang **`gemini-3.5-flash`** ở thanh bên trái (Sidebar)."
                )
            elif "400" in error_str or "api_key_invalid" in error_str.lower() or "api key not valid" in error_str.lower():
                st.error("❌ **API Key không hợp lệ!** Vui lòng kiểm tra lại Google Gemini API Key trong Sidebar.")
            elif "429" in error_str or "quota" in error_str.lower() or "resource_exhausted" in error_str.lower():
                st.error("⏳ **Đã vượt quá giới hạn lượt gọi (Rate Limit / Quota).** Vui lòng đợi khoảng 1 phút rồi thử lại.")
            else:
                st.error(f"❌ **Đã xảy ra lỗi khi gọi Gemini API:**\n\n`{error_str}`")

            # Nếu lỗi, xóa câu hỏi vừa gửi khỏi session_state để không làm hỏng ngữ cảnh hội thoại
            if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
                st.session_state.messages.pop()

