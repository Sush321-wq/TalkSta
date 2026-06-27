import streamlit as st
import requests
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""
if 'receiver' not in st.session_state:
    st.session_state.receiver = "durga" # Default fallback    

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
    if not st.session_state.logged_in:
        st.markdown("## 🔐 Login to TalkSta")
        tab1, tab2 = st.tabs(["Login", "Sign Up"])
        with tab1:
            user = st.text_input("Username", key="login_u")
            pwd = st.text_input("Password", type="password", key="login_p")
            if st.button("Login"):
                # Backend login check
                res = requests.post(f"https://talksta.onrender.com/login", json={"username": user, "password": pwd})
                if res.status_code == 200:
                    st.session_state.logged_in = True
                    st.session_state.username = user
                    st.rerun()
        with tab2:
            new_u = st.text_input("New Username", key="sign_u")
            new_email=st.text_input("Email",key="sign_email")
            new_p = st.text_input("New Password", type="password", key="sign_p")
            if st.button("Register"):
                res = requests.post(f"https://talksta.onrender.com/signup", json={"username": new_u, "email": new_email,"password": new_p})
                if res.status_code == 200:
                    st.success("✅ Account Created! Now go to Login tab")
                else:
                    st.error("res.text")    
    else:
        st.write(f"Logged in as: **{st.session_state.username}**")
        contact_list=requests.get("https://talksta.onrender.com/api/users").json().get("users",[])
        st.session_state.receiver = st.selectbox("Choose Someone to text:", [c for c in contact_list if c != st.session_state.username])
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()

# --- MAIN HEADER LAYOUT ---
col1, col2 = st.columns([3, 1])
with col1:
    st.markdown(f"<h1 class='main-header'>💬 TalkSta </h1>", unsafe_allow_html=True)
with col2:
    st.write("")
    st.markdown("<span class='status-tag'>● Server Connected</span>", unsafe_allow_html=True)

# --- MAIN HEADER LAYOUT ---
if st.session_state.logged_in:
    st.markdown(f"<div style='background-color: #1E1E24; border-left: 4px solid #4F46E5; padding: 10px; border-radius: 4px;'>Active Session: Logged in as <b>{st.session_state.username}</b> | Chatting with <b>{st.session_state.receiver}</b> <span style='color: #34D399;'>● Online</span></div>", unsafe_allow_html=True)
else:
    st.info("⚠️ Please log in from the sidebar to start chatting.")

st.write("---")

# --- ASYNCHRONOUS POLL LAYER (Real-Time Background Streaming) ---
@st.fragment(run_every=3)
def load_chat_stream():
    if not st.session_state.get("username"):
        return


    try:
        # Pull complete communication logs mapping transaction indices
        history_response = requests.get(
            "https://talksta.onrender.com/get_messages", 
            params={"sender": st.session_state.username, "receiver": st.session_state.receiver}
        )
        
        if history_response.status_code == 200:
            chat_history = history_response.json().get("messages", [])
            
            if not chat_history:
                st.info(f"This is the beginning of your chat history with {st.session_state.receiver}. Say hi! 👋")
            
            for msg in chat_history:
                if msg['sender_name'].lower() == st.session_state.username.lower():
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
    if not st.session_state.get("username"):
        st.error("⚠️ Please log in first to send messages!")
        st.stop()
    # Optimistic client UI update rendering instantaneous visual block
    with st.chat_message("user"):
        st.markdown(f"**You** <br> {user_message}", unsafe_allow_html=True)
        
    payload = {
        "sender": st.session_state.username,
        "receiver": st.session_state.receiver,
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