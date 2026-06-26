import streamlit as st
import requests

# 1. UI Layout Configuration and Presentation Layer Styling
st.set_page_config(page_title="Talksta Premium", page_icon="⚡", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #111216; color: #FFFFFF; }
    .main-header { font-size: 2.6rem; font-weight: 700; color: #4F46E5; margin-bottom: 0px; }
    .status-tag { background-color: #064E3B; color: #34D399; padding: 4px 14px; border-radius: 12px; font-size: 0.85rem; display: inline-block; font-weight: bold; }
    </style>
""", unsafe_allow_html=True) # Permitting HTML injection for custom theme definitions

# --- SIDEBAR: PROFILE & DYNAMIC CONTACT SELECTION ---
with st.sidebar:
    st.markdown("<h2 style='color: #4F46E5;'>⚡ Talksta Settings</h2>", unsafe_allow_html=True)
    st.write("Configure your identity securely.")
    
    username = st.text_input("🔑 Active Username", value="sush").strip()
    email = st.text_input("📧 Email Address", value="sush@gmail.com").strip()
    
    st.write("---")
    st.markdown("<h3>🎯 Contact List </h3>", unsafe_allow_html=True)
    
    #Fetch authenticated active directory accounts for dynamic drop-down indexing
    contact_list = []
    try:
        users_res = requests.get("https://talksta.onrender.com/api/users")
        if users_res.status_code == 200:
            contact_list = users_res.json().get("users", [])
    except requests.exceptions.ConnectionError:
        pass  # Default gracefully to empty array state if communication handshakes fail
        
    # Exclude self-identity reference from selectable recipient query array
    filtered_contacts = [c for c in contact_list if c.lower() != username.lower()]
    
    #Fallback simulation instance array when operational directory is void
    if not filtered_contacts:
        filtered_contacts = ["durga"]
        
    receiver = st.selectbox("Choose Someone to text:", filtered_contacts)

# --- MAIN HEADER LAYOUT ---
col1, col2 = st.columns([3, 1])
with col1:
    st.markdown(f"<h1 class='main-header'>💬 TalkSta </h1>", unsafe_allow_html=True)
with col2:
    st.write("")
    st.markdown("<span class='status-tag'>● Server Connected</span>", unsafe_allow_html=True)

st.markdown(f"<div style='background-color: #1E1E24; border-left: 4px solid #4F46E5; padding: 10px; border-radius: 4px;'>Active Session: Logged in as <b>{username}</b> | Chatting with <b>{receiver}</b> <span style='color: #34D399;'>● Online</span></div>", unsafe_allow_html=True)
st.write("---")

# --- ASYNCHRONOUS POLL LAYER (Real-Time Background Streaming) ---
@st.fragment(run_every=3)
def load_chat_stream():
    try:
        # Pull complete communication logs mapping transaction indices
        history_response = requests.get(
            "https://talksta.onrender.com/get_messages", 
            params={"sender": username, "receiver": receiver}
        )
        
        if history_response.status_code == 200:
            chat_history = history_response.json().get("messages", [])
            
            if not chat_history:
                st.info(f"This is the beginning of your chat history with {receiver}. Say hi! 👋")
            
            for msg in chat_history:
                if msg['sender_name'].lower() == username.lower():
                    with st.chat_message("user"):
                        st.markdown(f"**You** <br> {msg['message_text']}", unsafe_allow_html=True)
                else:
                    with st.chat_message("assistant", avatar="✨"):
                        st.markdown(f"**{msg['sender_name']}** <br> {msg['message_text']}", unsafe_allow_html=True)
        else:
            st.info("No older conversation history found between these users.")
            
    except requests.exceptions.ConnectionError:
        st.error("🔌 Network Error: Cannot fetch history. Is your backend running on Port 8000?")

# Invoke asynchronous background rendering engine process
st.subheader("💬 Conversation History")
load_chat_stream()


# --- CHAT INPUT & MESSAGE SEND LOGIC ---
user_message = st.chat_input("Write a private message...")

if user_message:
    # Optimistic client UI update rendering instantaneous visual block
    with st.chat_message("user"):
        st.markdown(f"**You** <br> {user_message}", unsafe_allow_html=True)
        
    payload = {
        "sender": username,
        "receiver": receiver,
        "message": user_message
    }
    
    try:
        response = requests.post("https://talksta.onrender.com/send_message", json=payload)
        if response.status_code == 200:
            st.rerun() #Enforce structural tree reload to reset client view state
        else:
            st.error(f"Backend error: {response.text}")
    except requests.exceptions.ConnectionError:
        st.error("Failed to transmit message payload. Verify your Uvicorn server.")