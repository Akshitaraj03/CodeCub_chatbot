from PIL import Image
import streamlit as st
import json
import os
from rag_chat import rag_query, create_vector_store, summarize_chat
import openai

st.set_page_config(page_title="🧠 CodeCub", layout="wide")

# --- Custom CSS for original look + dark mode fix ---
st.markdown("""
    <style>
    body {
        background-color: #E6E6fa;
    }
    .block-container {
        padding-top: 2rem;
    }
    .stChatMessage {
        border-radius: 18px !important;
        padding: 1rem !important;
        margin-bottom: 0.5rem !important;
        font-size: 1.08rem !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }
    .stChatMessage.user {
        background: linear-gradient(90deg, #f9d29d 0%, #ffd6e0 100%);
        color: #333;
        align-self: flex-end;
    }
    .stChatMessage.assistant {
        background: linear-gradient(90deg, #b7eaff 0%, #e0c3fc 100%);
        color: #222;
        align-self: flex-start;
    }
    .stButton>button {
        border-radius: 12px;
        font-weight: 600;
        background: #f9d29d;
        color: #333;
        border: none;
        margin: 0.2rem 0.2rem 0.2rem 0;
    }
    .stButton>button:hover {
        background: #ffd6e0;
        color: #111;
    }
    .stDownloadButton>button {
        border-radius: 12px;
        font-weight: 600;
        background: #b7eaff;
        color: #333;
        border: none;
    }
    .stDownloadButton>button:hover {
        background: #e0c3fc;
        color: #111;
    }
    h1 span {
        color: var(--text-color);
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='font-size:2.6rem;'>🐾 <span>CodeCub</span></h1>", unsafe_allow_html=True)

logo = Image.open("logo.png")
st.sidebar.image(logo, width=120)

# Initialize session state
if "auth" not in st.session_state:
    st.session_state.auth = False
if "messages" not in st.session_state:
    st.session_state.messages = []

CREDENTIALS_FILE = "users.json"

def load_credentials():
    if os.path.exists(CREDENTIALS_FILE):
        with open(CREDENTIALS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_credentials(credentials):
    with open(CREDENTIALS_FILE, "w") as f:
        json.dump(credentials, f)

def auth_portal():
    st.subheader("🔐 Login or Register")
    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
        col1, col2 = st.columns([1, 1])
        with col1:
            username = st.text_input("User", key="login_user", max_chars=16)
        with col2:
            password = st.text_input("Pass", type="password", key="login_pass", max_chars=16)
        if st.button("Login"):
            users = load_credentials()
            if username and password and username in users and users[username] == password:
                st.session_state.auth = True
                st.session_state.username = username
                st.rerun()
            else:
                st.error("❌ Invalid credentials")

    with tab2:
        col1, col2 = st.columns([1, 1])
        with col1:
            new_user = st.text_input("User", key="reg_user", max_chars=16)
        with col2:
            new_pass = st.text_input("Pass", type="password", key="reg_pass", max_chars=16)
        if st.button("Register"):
            users = load_credentials()
            if new_user in users:
                st.warning("⚠️ Username already exists.")
            elif not new_user or not new_pass:
                st.warning("⚠️ Please enter both username and password.")
            else:
                users[new_user] = new_pass
                save_credentials(users)
                st.success("✅ Registration successful. Please login.")

def chat_page():
    st.sidebar.header(f"📂 Welcome {st.session_state.username}")
    files = st.sidebar.file_uploader("Upload PDF, TXT, CSV", type=["pdf", "txt", "csv"], accept_multiple_files=True)
    if st.sidebar.button("📌 Build Knowledge Base"):
        if files:
            with st.spinner("Building knowledge base..."):
                create_vector_store(files)
            st.sidebar.success("✅ Knowledge base updated.")
        else:
            st.sidebar.warning("⚠️ Please upload files.")

    st.subheader("💬 Ask a question")

    user_input = st.chat_input("Type your question here...")

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🆕 New Chat"):
            st.session_state.messages = []
            st.success("🔄 Chat cleared.")
    with col2:
        if st.button("📤 Export Chat"):
            if st.session_state.messages:
                chat_data = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])
                st.download_button("📥 Download Chat", data=chat_data, file_name="chat_history.txt")
            else:
                st.warning("⚠️ No chat to export.")
    with col3:
        if st.button("📝 Summarize Chat"):
            with st.spinner("Summarizing..."):
                summary = summarize_chat(st.session_state.messages)
            st.markdown("### 📌 Summary")
            st.info(summary)

    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.spinner("🤖 Generating answer..."):
            answer = rag_query(user_input)
        st.session_state.messages.append({"role": "bot", "content": answer})

    for msg in st.session_state.messages:
        with st.chat_message("user" if msg["role"] == "user" else "assistant"):
            st.markdown(msg["content"])

chat_page() if st.session_state.auth else auth_portal()
