import streamlit as st
import requests
from datetime import datetime

# ========================
# Cấu hình Backend API URL
# ========================
API_URL = "http://localhost:8000/api"

# ========================
# Hàm gọi API
# ========================

def get_chats():
    res = requests.get(f"{API_URL}/chats")
    return res.json()

def create_chat(name):
    res = requests.post(f"{API_URL}/chats", json={"name": name})
    return res.json()

def get_chat(chat_id):
    res = requests.get(f"{API_URL}/chats/{chat_id}")
    return res.json()

def send_message(chat_id, messages):
    res = requests.post(f"{API_URL}/messages", json={
        "chat_id": chat_id,
        "messages": messages
    })
    return res.json()

def upload_file(chat_id, file):
    files = {"file": (file.name, file.getvalue())}
    data = {"chat_id": chat_id}
    res = requests.post(f"{API_URL}/upload", data=data, files=files)
    return res.json()

def delete_file(chat_id, file_id):
    res = requests.delete(f"{API_URL}/files/{file_id}", json={"chat_id": chat_id})
    return res.json()

# ========================
# Layout Streamlit
# ========================
st.set_page_config(layout="wide")

st.title("💬 Simple Chatbot")

# Lấy query param chat_id từ URL
query_params = st.query_params
current_chat_id = query_params.get("chat_id", "")

# ========================
# Sidebar - Danh sách cuộc trò chuyện
# ========================
with st.sidebar:
    st.header("📂 Các đoạn chat")
    
    chats = get_chats()
    
    for chat in chats:
        btn_label = f"📝 {chat['name']}"
        if st.button(btn_label, key=chat['id']):
            st.query_params["chat_id"] = chat['id']
            st.session_state['current_messages'] = []
            st.rerun()

    st.markdown("---")
    
    with st.form("create_chat_form"):
        new_chat_name = st.text_input("Tạo đoạn chat mới")
        submitted = st.form_submit_button("Tạo mới")
        
        if submitted and new_chat_name:
            chat = create_chat(new_chat_name)
            st.query_params["chat_id"] = chat['id']
            st.session_state['current_messages'] = []
            st.rerun()

# ========================
# Cột giữa - Nội dung chat
# ========================
if not current_chat_id:
    st.info("👉 Vui lòng chọn hoặc tạo đoạn chat!")
    st.stop()

chat_data = get_chat(current_chat_id)

# Giao diện upload file
st.subheader(f"Đoạn chat: {chat_data['name']}")
uploaded_file = st.file_uploader("📤 Upload file cho đoạn chat này", type=None)

if uploaded_file:
    res = upload_file(current_chat_id, uploaded_file)
    st.success(f"Đã upload: {res['file_name']}")
    st.rerun()

# Hiển thị file đã upload
st.markdown("### 📎 File đã upload")
for f in chat_data["files"]:
    col1, col2 = st.columns([6, 1])
    with col1:
        st.write(f"{f['file_name']} ({f['created_at']})")
    with col2:
        if st.button("❌", key=f"delete_{f['id']}"):
            delete_file(current_chat_id, f['id'])
            st.rerun()

st.markdown("---")

# Hiển thị các tin nhắn
st.markdown("### 💬 Tin nhắn")

if "current_messages" not in st.session_state:
    st.session_state['current_messages'] = chat_data['messages']

for message in st.session_state['current_messages']:
    align = "flex-start" if message['role'] == 'ai' else "flex-end"
    bg_color = "#f1f1f1" if message['role'] == 'ai' else "#dcf8c6"
    
    st.markdown(
        f"""
        <div style='display: flex; justify-content: {align}; margin-bottom: 5px;'>
            <div style='background-color: {bg_color}; padding: 10px 15px; border-radius: 10px; max-width: 60%;'>
                <small><b>{message['role'].upper()}</b> | {message['id']}</small><br/>
                {message['content']}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

# ========================
# Nhập tin nhắn mới
# ========================
with st.form("send_message_form", clear_on_submit=True):
    user_message = st.text_area("✏️ Nhập tin nhắn")
    send_btn = st.form_submit_button("Gửi")

    if send_btn and user_message:
        user_msg = {
            "chat_id": current_chat_id,
            "role": "user",
            "content": user_message
        }
        messages = st.session_state['current_messages'] + [user_msg]

        # Gửi toàn bộ đoạn hội thoại
        res = send_message(current_chat_id, messages)

        # Cập nhật session state messages
        bot_reply = {
            "chat_id": current_chat_id,
            "role": "ai",
            "content": res.get('bot_reply', '')
        }

        st.session_state['current_messages'] = messages + [bot_reply]
        st.rerun()
