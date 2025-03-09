import streamlit as st
from datetime import datetime
import requests

# Dummy data structure
chats = {}

# Backend API endpoints
API_BASE_URL = "http://localhost:8000"  # Thay bằng địa chỉ backend thực tế
GET_CHATS_ENDPOINT = f"{API_BASE_URL}/chats"
POST_MESSAGE_ENDPOINT = f"{API_BASE_URL}/messages"
UPLOAD_FILE_ENDPOINT = f"{API_BASE_URL}/upload"
DELETE_FILE_ENDPOINT = f"{API_BASE_URL}/delete_file"

# Fetch danh sách cuộc trò chuyện từ backend
@st.cache_data(show_spinner=False)
def fetch_chats():
    try:
        response = requests.get(GET_CHATS_ENDPOINT)
        if response.status_code == 200:
            return response.json()
        else:
            st.error("Không lấy được danh sách cuộc trò chuyện")
            return {}
    except Exception as e:
        st.error(f"Lỗi khi fetch chats: {e}")
        return {}

# Gửi tin nhắn và nhận phản hồi bot
def send_message(chat_id, messages):
    try:
        payload = {"chat_id": chat_id, "messages": messages}
        response = requests.post(POST_MESSAGE_ENDPOINT, json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            st.error("Không gửi được tin nhắn")
            return None
    except Exception as e:
        st.error(f"Lỗi khi gửi tin nhắn: {e}")
        return None

# Upload file lên backend
def upload_file(chat_id, file):
    try:
        files = {"file": (file.name, file.getvalue())}
        data = {"chat_id": chat_id}
        response = requests.post(UPLOAD_FILE_ENDPOINT, files=files, data=data)
        if response.status_code == 200:
            return response.json()
        else:
            st.error("Không upload được file")
            return None
    except Exception as e:
        st.error(f"Lỗi khi upload file: {e}")
        return None

# Xoá file khỏi backend
def delete_file(chat_id, file_name):
    try:
        payload = {"chat_id": chat_id, "file_name": file_name}
        response = requests.post(DELETE_FILE_ENDPOINT, json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            st.error("Không xoá được file")
            return None
    except Exception as e:
        st.error(f"Lỗi khi xoá file: {e}")
        return None

# Load data từ backend
chats = fetch_chats()

# Sidebar: Danh sách cuộc trò chuyện
st.sidebar.title("Danh sách cuộc trò chuyện")
chat_names = list(chats.keys())
selected_chat = st.sidebar.radio("Chọn cuộc trò chuyện", chat_names)

# Tạo cuộc trò chuyện mới
new_chat_name = st.sidebar.text_input("Tên cuộc trò chuyện mới")
if st.sidebar.button("Tạo mới"):
    if new_chat_name and new_chat_name not in chats:
        chats[new_chat_name] = {"messages": [], "files": []}
        st.experimental_rerun()

# Nội dung chính: Cuộc trò chuyện
st.title("Chatbot")
if selected_chat:
    st.subheader(f"Cuộc trò chuyện: {selected_chat}")
    conversation = chats[selected_chat]

    # Hiển thị tin nhắn dạng 2 cột
    for msg in conversation["messages"]:
        col1, col2 = st.columns([1, 1])
        if msg["role"] == "bot":
            with col1:
                st.info(f'Bot ({msg["id"]}): {msg["text"]}')
        else:
            with col2:
                st.success(f'User ({msg["id"]}): {msg["text"]}')

    # Nhập tin nhắn mới
    user_input = st.text_input("Nhập tin nhắn:", "")
    if st.button("Gửi") and user_input:
        # Thêm tin nhắn user vào list
        next_id = conversation["messages"][-1]["id"] + 1 if conversation["messages"] else 1
        conversation["messages"].append({"role": "user", "text": user_input, "id": next_id})
        
        # Gửi toàn bộ đoạn chat lên backend
        response = send_message(selected_chat, conversation["messages"])

        # Nếu có phản hồi từ bot
        if response and "bot_reply" in response:
            next_id += 1
            conversation["messages"].append({"role": "bot", "text": response["bot_reply"], "id": next_id})
            st.experimental_rerun()

    # Upload file
    st.subheader("Files đã tải lên")
    uploaded_file = st.file_uploader("Tải lên tệp đính kèm", key=selected_chat)
    if uploaded_file is not None:
        upload_result = upload_file(selected_chat, uploaded_file)
        if upload_result:
            st.success(f"Đã tải lên: {uploaded_file.name}")
            st.experimental_rerun()

    # Hiển thị danh sách file đã tải lên
    for idx, file_name in enumerate(conversation["files"]):
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(file_name)
        with col2:
            if st.button("Xoá", key=f"delete_{idx}"):
                delete_result = delete_file(selected_chat, file_name)
                if delete_result:
                    st.success(f"Đã xoá file: {file_name}")
                    st.experimental_rerun()
