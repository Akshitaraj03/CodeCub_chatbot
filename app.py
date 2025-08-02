import streamlit as st
from rag_chat import rag_query, create_vector_store, summarize_chat

# --- Session Setup ---
if "auth" not in st.session_state:
    st.session_state.auth = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- Branding Header with Theme Support ---
st.markdown(
    """
    <h1 style='text-align: center; color: var(--text-color); font-size: 48px; font-family: "Courier New", monospace;'>
        codecub
    </h1>
    """,
    unsafe_allow_html=True
)

# --- Auth Portal ---
def auth_portal():
    st.subheader("🔐 Login or Register")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    action = st.selectbox("Choose Action", ["Login", "Register"])

    if st.button("Submit"):
        if username and password:
            st.session_state.auth = True
            st.session_state.username = username
            st.success(f"{action} successful. Welcome, {username}!")
        else:
            st.error("Please enter both username and password.")

# --- Chat Page ---
def chat_page():
    st.sidebar.header("📄 Upload File")
    uploaded_file = st.sidebar.file_uploader("Choose a file", type=["pdf", "txt", "csv"])

    if uploaded_file:
        create_vector_store(uploaded_file)
        st.sidebar.success("✅ Knowledge base created.")

    st.sidebar.markdown("---")
    st.sidebar.button("🔁 New Chat", on_click=lambda: st.session_state.chat_history.clear())

    # Chat interface
    st.subheader(f"🤖 Chat with your Knowledge Base, {st.session_state.username}!")

    user_input = st.text_input("You:", key="input")

    if user_input:
        response = rag_query(user_input, chat_history=st.session_state.chat_history)
        st.session_state.chat_history.append(("You", user_input))
        st.session_state.chat_history.append(("Bot", response))

    for sender, message in st.session_state.chat_history:
        if sender == "You":
            st.markdown(f"**🧑‍💻 You:** {message}")
        else:
            st.markdown(f"**🤖 Bot:** {message}")

    st.sidebar.markdown("---")
    if st.sidebar.button("🧠 Summarize Chat"):
        summary = summarize_chat(st.session_state.chat_history)
        st.sidebar.markdown("### 💡 Summary")
        st.sidebar.info(summary)

# --- Entry Point ---
if st.session_state.auth:
    chat_page()
else:
    auth_portal()
