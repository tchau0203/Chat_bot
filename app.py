"""
Ứng dụng Chatbot AI phong cách Google Gemini với Streamlit và Google GenAI SDK.
Giao diện thanh chat bo tròn dạng Pill Bar với Popover chọn mô hình AI & Cấp độ tư duy.
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
        f"Hãy luôn sử dụng thông tin thời gian thực này để trả lời chính xác khi người dùng hỏi về thời gian."
    )


# -----------------------------------------------------------------------------
# 1. Cấu hình trang Streamlit
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Chat Bot",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# -----------------------------------------------------------------------------
# 2. Nạp API Key & Danh sách Mô hình trực tiếp từ API hiện có
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

# Danh sách dự phòng chuẩn nếu không thể kết nối API lấy danh sách
FALLBACK_MODELS = [
    {
        "id": "gemini-3.8-flash",
        "name": "Gemini 3.8 Flash",
        "badge": "3.8-flash",
        "desc": "Mô hình Flash mới nhất, thông minh và nhanh chóng",
        "api_model": "gemini-3.8-flash"
    },
    {
        "id": "gemini-3.5-flash-lite",
        "name": "Gemini 3.5 Flash Lite",
        "badge": "3.5-flash-lite",
        "desc": "Phản hồi siêu tốc, tối ưu tài nguyên",
        "api_model": "gemini-3.5-flash-lite"
    },
    {
        "id": "gemini-3.5-flash",
        "name": "Gemini 3.5 Flash",
        "badge": "3.5-flash",
        "desc": "Cân bằng tốc độ và độ chính xác cao",
        "api_model": "gemini-3.5-flash"
    },
    {
        "id": "gemini-3.1-pro-preview",
        "name": "Gemini 3.1 Pro Preview",
        "badge": "3.1-pro",
        "desc": "Suy luận logic và giải quyết vấn đề phức tạp",
        "api_model": "gemini-3.1-pro-preview"
    }
]

@st.cache_data(show_spinner=False, ttl=1800)
def get_available_api_models(key: str):
    """Lấy danh sách các mô hình khả dụng thực tế trực tiếp từ Gemini API hiện có."""
    if not key:
        return []
    try:
        client = genai.Client(api_key=key)
        exclude_keywords = [
            "tts", "image", "banana", "robotics", "computer-use",
            "clip", "transcribe", "live", "embedding", "aqa", "customtools", "2.5"
        ]
        api_models = []
        for m in client.models.list():
            methods = getattr(m, 'supported_actions', None) or getattr(m, 'supported_generation_methods', [])
            model_id = m.name.replace("models/", "")
            
            # Chỉ lấy các model Gemini phục vụ sinh nội dung văn bản / trò chuyện
            if model_id.startswith("gemini-") and "generateContent" in methods:
                if any(kw in model_id.lower() for kw in exclude_keywords):
                    continue
                display_name = getattr(m, "display_name", model_id) or model_id
                
                badge = model_id.replace("gemini-", "")
                if len(badge) > 14:
                    badge = badge[:12] + ".."
                
                desc = getattr(m, "description", "") or "Mô hình Google Gemini"
                if len(desc) > 55:
                    desc = desc[:52] + "..."
                
                api_models.append({
                    "id": model_id,
                    "name": display_name,
                    "badge": badge,
                    "desc": desc,
                    "api_model": model_id
                })
        
        # Sắp xếp ưu tiên các model Flash phổ biến và mới nhất lên đầu
        priority_order = [
            "gemini-3.8-flash",
            "gemini-3.5-flash",
            "gemini-3.5-flash-lite",
            "gemini-3.7-flash",
            "gemini-3.6-flash",
            "gemini-3.1-flash-lite",
            "gemini-3.1-pro-preview",
            "gemini-4-argon",
            "gemini-flash-latest",
            "gemini-flash-lite-latest",
            "gemini-pro-latest"
        ]
        def sort_key(item):
            try:
                return priority_order.index(item["id"])
            except ValueError:
                return 999
                
        api_models.sort(key=sort_key)
        return api_models
    except Exception:
        return []

# Nạp danh sách model từ API
AVAILABLE_MODELS = get_available_api_models(api_key) or FALLBACK_MODELS
valid_model_ids = [m["id"] for m in AVAILABLE_MODELS]

# Khởi tạo trạng thái phiên làm việc
if "selected_model_id" not in st.session_state or st.session_state.selected_model_id not in valid_model_ids:
    default_id = "gemini-3.8-flash" if "gemini-3.8-flash" in valid_model_ids else valid_model_ids[0]
    st.session_state.selected_model_id = default_id

if "thinking_level" not in st.session_state:
    st.session_state.thinking_level = "Tự động"

if "messages" not in st.session_state:
    st.session_state.messages = []

# Model đang được chọn
active_model = next((m for m in AVAILABLE_MODELS if m["id"] == st.session_state.selected_model_id), AVAILABLE_MODELS[0])

# -----------------------------------------------------------------------------
# 3. CSS Tinh chỉnh Giao diện Chuẩn phong cách Google Gemini
# -----------------------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500;600;700&family=Inter:wght@400;500;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Google Sans', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Ẩn header mặc định và viền thừa */
    header[data-testid="stHeader"] {
        background-color: transparent !important;
    }

    .stApp {
        background: radial-gradient(circle at 50% 0%, #f2f6fc 0%, #ffffff 75%) !important;
    }

    /* Container tin nhắn chính */
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 7rem !important;
        max-width: 860px !important;
    }

    /* Header Gemini */
    .gemini-title {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 1.6rem;
        font-weight: 600;
        color: #1f1f1f;
        margin-bottom: 1rem;
    }
    .gemini-sparkle {
        background: linear-gradient(135deg, #1a73e8, #9334e8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 1.7rem;
    }

    /* Lời chào mở đầu */
    .gemini-hero {
        padding: 3rem 1.5rem 1.5rem 1.5rem;
        text-align: center;
    }
    .gemini-hero h2 {
        font-size: 2.2rem;
        font-weight: 500;
        background: linear-gradient(90deg, #4285F4, #9B51E0, #D96570);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .gemini-hero p {
        color: #5f6368;
        font-size: 1.05rem;
    }

    /* Chat message bubble */
    .stChatMessage {
        border-radius: 18px !important;
        margin-bottom: 0.8rem !important;
        padding: 1rem 1.2rem !important;
        background-color: #ffffff !important;
        box-shadow: 0 1px 4px rgba(0,0,0,0.03) !important;
    }

    /* Khu vực đáy trang stBottom */
    [data-testid="stBottom"] {
        background-color: transparent !important;
        padding-bottom: 20px !important;
    }
    [data-testid="stBottom"] > div {
        max-width: 860px !important;
        margin: 0 auto !important;
        background-color: transparent !important;
    }

    /* Gợi ý Pills phía trên thanh chat */
    .gemini-pills-row {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 10px;
        padding-left: 10px;
        flex-wrap: wrap;
    }
    .gemini-pill-tag {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: #ffffff;
        border: 1px solid #e0e4ea;
        border-radius: 20px;
        padding: 6px 14px;
        font-size: 0.88rem;
        color: #444746;
        cursor: pointer;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        transition: all 0.2s ease;
    }
    .gemini-pill-tag:hover {
        background: #f0f4f9;
        border-color: #c2d7f2;
        color: #1a73e8;
    }

    /* Khung thanh nhập liệu hợp nhất phong cách Gemini */
    div[data-testid="stHorizontalBlock"]:has([data-testid="stChatInput"]) {
        background: #ffffff !important;
        border-radius: 34px !important;
        border: 1px solid #dfe3eb !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.07), 0 1px 3px rgba(0, 0, 0, 0.03) !important;
        padding: 4px 12px 4px 8px !important;
        display: flex !important;
        align-items: center !important;
        gap: 4px !important;
        transition: all 0.25s ease !important;
    }

    div[data-testid="stHorizontalBlock"]:has([data-testid="stChatInput"]):focus-within {
        border-color: #a8c7fa !important;
        box-shadow: 0 6px 26px rgba(66, 133, 244, 0.15), 0 1px 4px rgba(66, 133, 244, 0.06) !important;
    }

    /* Làm trong suốt viền stChatInput bên trong thanh pill */
    div[data-testid="stHorizontalBlock"] div[data-testid="stChatInput"] {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding: 0 !important;
        margin: 0 !important;
    }

    div[data-testid="stHorizontalBlock"] div[data-testid="stChatInput"] > div {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding: 0 !important;
    }

    div[data-testid="stHorizontalBlock"] textarea[data-testid="stChatInputTextArea"] {
        background: transparent !important;
        border: none !important;
        font-size: 1.02rem !important;
        color: #1f1f1f !important;
        box-shadow: none !important;
        padding: 8px 4px !important;
        line-height: 1.4 !important;
    }

    div[data-testid="stHorizontalBlock"] textarea[data-testid="stChatInputTextArea"]::placeholder {
        color: #5f6368 !important;
        font-size: 1.02rem !important;
    }

    /* Nút dấu cộng (+) và nút micro (🎙️) */
    div[data-testid="stHorizontalBlock"] [data-testid="column"]:nth-child(1) [data-testid="stPopover"] > button,
    div[data-testid="stHorizontalBlock"] [data-testid="column"]:nth-child(4) button {
        border: none !important;
        background: transparent !important;
        color: #444746 !important;
        font-size: 1.25rem !important;
        border-radius: 50% !important;
        width: 38px !important;
        height: 38px !important;
        padding: 0 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        box-shadow: none !important;
        transition: background-color 0.15s ease !important;
    }

    div[data-testid="stHorizontalBlock"] [data-testid="column"]:nth-child(1) [data-testid="stPopover"] > button:hover,
    div[data-testid="stHorizontalBlock"] [data-testid="column"]:nth-child(4) button:hover {
        background: #f0f4f9 !important;
        color: #1f1f1f !important;
    }

    /* Nút chọn mô hình (Flash ⌃) chuẩn Gemini */
    div[data-testid="stHorizontalBlock"] [data-testid="column"]:nth-child(3) [data-testid="stPopover"] > button {
        background: #e9eef6 !important;
        color: #1f1f1f !important;
        border-radius: 20px !important;
        font-size: 0.92rem !important;
        font-weight: 500 !important;
        padding: 6px 14px !important;
        border: none !important;
        display: inline-flex !important;
        align-items: center !important;
        gap: 6px !important;
        box-shadow: none !important;
        white-space: nowrap !important;
        transition: background 0.2s ease !important;
    }

    div[data-testid="stHorizontalBlock"] [data-testid="column"]:nth-child(3) [data-testid="stPopover"] > button:hover {
        background: #dde5f2 !important;
    }

    /* Card Dropdown Menu (stPopoverBody) giống hệt ảnh chụp */
    [data-testid="stPopoverBody"] {
        border-radius: 20px !important;
        box-shadow: 0 10px 36px rgba(0, 0, 0, 0.13), 0 2px 8px rgba(0, 0, 0, 0.05) !important;
        border: 1px solid rgba(0, 0, 0, 0.08) !important;
        background: #ffffff !important;
        padding: 12px 10px !important;
        width: 320px !important;
        max-width: 90vw !important;
        max-height: 480px !important;
        overflow-y: auto !important;
    }

    /* Các item mô hình trong popup */
    .model-item-btn {
        width: 100%;
        text-align: left;
        background: transparent;
        border: 1.5px solid transparent;
        border-radius: 14px;
        padding: 10px 14px;
        cursor: pointer;
        transition: all 0.15s ease;
        margin-bottom: 4px;
        display: flex;
        flex-direction: column;
    }
    .model-item-btn:hover {
        background: #f2f5f9;
    }
    .model-item-btn.active {
        border-color: #1f1f1f;
        background: #ffffff;
    }
    .model-name {
        font-size: 0.98rem;
        font-weight: 600;
        color: #1f1f1f;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .model-desc {
        font-size: 0.82rem;
        color: #5f6368;
        margin-top: 2px;
        margin-left: 22px;
    }
    .model-desc-noicon {
        font-size: 0.82rem;
        color: #5f6368;
        margin-top: 2px;
    }

    /* Nút chọn mô hình dùng st.button bên trong popover */
    [data-testid="stPopoverBody"] button[kind="secondary"],
    [data-testid="stPopoverBody"] button[kind="primary"] {
        text-align: left !important;
        justify-content: flex-start !important;
        border-radius: 14px !important;
        padding: 8px 12px !important;
        margin-bottom: 4px !important;
        font-size: 0.95rem !important;
        font-weight: 500 !important;
        transition: all 0.15s ease !important;
        border: 1.5px solid transparent !important;
    }

    [data-testid="stPopoverBody"] button[kind="secondary"] {
        background: transparent !important;
        color: #1f1f1f !important;
    }

    [data-testid="stPopoverBody"] button[kind="secondary"]:hover {
        background: #f2f5f9 !important;
    }

    /* Viền đen bo góc khi được chọn (giống mục 3.5 Flash-Lite / 3.8 Flash trong ảnh) */
    [data-testid="stPopoverBody"] button[kind="primary"] {
        background: #ffffff !important;
        border: 1.5px solid #1f1f1f !important;
        color: #1f1f1f !important;
    }

    /* Đường kẻ ngăn cách */
    .menu-divider {
        border: none;
        border-top: 1px solid #ebeef2;
        margin: 8px 0;
    }

    /* Dòng Cấp độ tư duy */
    .thinking-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 8px 12px;
        font-size: 0.92rem;
        font-weight: 500;
        color: #1f1f1f;
        border-radius: 12px;
        cursor: pointer;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 4. Cấu hình Hệ thống
# -----------------------------------------------------------------------------
system_prompt = "Bạn là trợ lý AI thông minh, nhiệt tình và am hiểu. Hãy trả lời ngắn gọn, chính xác bằng tiếng Việt chuẩn."

# -----------------------------------------------------------------------------
# 5. Giao diện Chat chính
# -----------------------------------------------------------------------------
st.markdown("""
<div class="gemini-title">
    <span class="gemini-sparkle">✦</span>
    <span>Chat Bot</span>
</div>
""", unsafe_allow_html=True)

# Lời chào khi chưa có tin nhắn
if not st.session_state.messages:
    st.markdown("""
    <div class="gemini-hero">
        <h2>Xin chào bạn!</h2>
        <p>Hôm nay tôi có thể hỗ trợ gì cho bạn?</p>
    </div>
    """, unsafe_allow_html=True)

# Hiển thị lịch sử chat
for message in st.session_state.messages:
    role = message["role"]
    content = message["content"]
    with st.chat_message(role):
        st.markdown(content)

# -----------------------------------------------------------------------------
# 6. Thanh Chat Bar Chuẩn Gemini (Fixed Bottom)
# -----------------------------------------------------------------------------
with st.bottom:
    # 6.1 Gợi ý nhanh dạng Pills
    st.markdown("""
    <div class="gemini-pills-row">
        <span class="gemini-pill-tag">💬 Cuộc trò chuyện</span>
        <span class="gemini-pill-tag">💡 Lên ý tưởng</span>
        <span class="gemini-pill-tag">📝 Tóm tắt</span>
        <span class="gemini-pill-tag">⚡ Viết code</span>
    </div>
    """, unsafe_allow_html=True)

    # 6.2 Thanh Chat Hợp nhất (Plus + Input + Model Pill + Mic)
    col_plus, col_input, col_model, col_mic = st.columns([0.4, 7.3, 1.5, 0.4], vertical_alignment="center")

    with col_plus:
        with st.popover("＋", help="Thêm tệp hoặc tùy chọn"):
            st.markdown("##### Tiện ích")
            if st.button("🗑️ Xóa cuộc trò chuyện", use_container_width=True):
                st.session_state.messages = []
                st.rerun()
            if st.button("🔄 Đặt lại mô hình", use_container_width=True):
                default_id = "gemini-3.8-flash" if "gemini-3.8-flash" in valid_model_ids else valid_model_ids[0]
                st.session_state.selected_model_id = default_id
                st.rerun()

    with col_input:
        user_input = st.chat_input("Hỏi Chat Bot...")

    with col_model:
        # Nút hiển thị mô hình hiện tại: e.g. "3.8-flash ⌃"
        with st.popover(f"{active_model['badge']} ⌃"):
            for m in AVAILABLE_MODELS:
                is_selected = (m["id"] == st.session_state.selected_model_id)
                check_symbol = "✓ " if is_selected else ""
                btn_text = f"{check_symbol}{m['name']}\n{m['desc']}"
                if st.button(
                    btn_text,
                    key=f"model_btn_{m['id']}",
                    use_container_width=True,
                    type="primary" if is_selected else "secondary"
                ):
                    st.session_state.selected_model_id = m["id"]
                    st.rerun()

            st.markdown("<hr class='menu-divider'>", unsafe_allow_html=True)

            # Mục Cấp độ tư duy
            with st.expander("🧠 Cấp độ tư duy ▸", expanded=False):
                thinking_choice = st.radio(
                    "Cấp độ suy luận",
                    options=["Tự động (Khuyên dùng)", "Nhanh", "Sâu (Reasoning)"],
                    index=0,
                    label_visibility="collapsed"
                )
                st.session_state.thinking_level = thinking_choice

    with col_mic:
        st.button("🎙️", help="Nhập liệu bằng giọng nói (Voice input)", key="gemini_mic_btn")

# -----------------------------------------------------------------------------
# 7. Xử lý gửi tin nhắn & Gọi Gemini API
# -----------------------------------------------------------------------------
if user_input:
    if not api_key:
        st.warning("⚠️ Không tìm thấy Google Gemini API Key! Vui lòng cấu hình `GEMINI_API_KEY` trong file `.streamlit/secrets.toml` hoặc `.env`.")
        st.stop()

    # Thêm câu hỏi vào hội thoại
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Chuẩn bị nội dung hội thoại
    gemini_contents = []
    for msg in st.session_state.messages:
        role_label = "user" if msg["role"] == "user" else "model"
        gemini_contents.append(
            types.Content(
                role=role_label,
                parts=[types.Part.from_text(text=msg["content"])]
            )
        )

    # Hiển thị phản hồi với streaming
    with st.chat_message("assistant"):
        try:
            client = genai.Client(
                api_key=api_key,
                http_options=types.HttpOptions(timeout=25000)
            )

            time_context = get_current_time_context()
            final_system_instruction = f"{system_prompt.strip()}\n\n{time_context}"

            config = types.GenerateContentConfig(
                system_instruction=final_system_instruction,
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True)
            )

            with st.spinner("✨ Chat Bot đang suy nghĩ..."):
                response_stream = client.models.generate_content_stream(
                    model=active_model["api_model"],
                    contents=gemini_contents,
                    config=config
                )

            def stream_generator():
                for chunk in response_stream:
                    if chunk.text:
                        yield chunk.text

            full_response = st.write_stream(stream_generator())
            st.session_state.messages.append({"role": "assistant", "content": full_response})

        except Exception as e:
            error_str = str(e)
            st.error(f"❌ **Lỗi khi phản hồi:** {error_str}")
            if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
                st.session_state.messages.pop()
