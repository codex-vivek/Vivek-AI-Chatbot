import streamlit as st
from google import genai
from google.genai import types

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Vivek AI Chatbot",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS ---
st.markdown("""
<style>
    /* Add a modern font and styling */
    .stApp {
        font-family: 'Inter', sans-serif;
    }
    .title-container {
        display: flex;
        align-items: center;
        gap: 15px;
        margin-bottom: 20px;
    }
    .title-text {
        font-size: 2.5rem;
        font-weight: 800;
        background: -webkit-linear-gradient(45deg, #FF6B6B, #4ECDC4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
</style>
""", unsafe_allow_html=True)

import os
import base64

def get_base64_img(file_path):
    with open(file_path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

# Try to load the image if it exists
img_html = "🤖" # Default bot icon
if os.path.exists("vivek.jpg"):
    img_b64 = get_base64_img("vivek.jpg")
    img_html = f'<img src="data:image/jpeg;base64,{img_b64}" style="width: 55px; height: 55px; border-radius: 50%; object-fit: cover; border: 2px solid #4ECDC4;">'
elif os.path.exists("vivek.png"):
    img_b64 = get_base64_img("vivek.png")
    img_html = f'<img src="data:image/png;base64,{img_b64}" style="width: 55px; height: 55px; border-radius: 50%; object-fit: cover; border: 2px solid #4ECDC4;">'

# --- HEADER ---
st.markdown(
    f'''
    <div class="title-container">
        {img_html}
        <h1 class="title-text">Vivek AI Chatbot</h1>
    </div>
    <p style="font-size: 1.1rem; color: #a1a1aa; margin-bottom: 2rem;">
        Welcome to Vivek AI! Experience real-time interactive conversations powered by the latest Google AI.
    </p>
    ''',
    unsafe_allow_html=True
)

# --- SIDEBAR & API KEY SETUP ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/8624/8624102.png", width=100) # Simple bot icon
    st.header("⚙️ Configuration")
    
    # Using password input for API key
    api_key = st.text_input("Enter your Google Gemini API Key:", type="password", help="You can get this from Google AI Studio").strip()
    
    st.markdown("---")
    st.markdown("### 💡 Key Features")
    st.markdown("✅ Clean and user-friendly interface")
    st.markdown("✅ Real-time question answering")
    st.markdown("✅ Integrated with Gemini 1.5 Flash")
    st.markdown("✅ Fast and interactive AI responses")
    
    st.markdown("---")
    st.markdown("Made with ❤️ using Streamlit & Python")

# --- INITIALIZE SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state["messages"] = []

if "chat_session" not in st.session_state:
    st.session_state["chat_session"] = None

# --- DISPLAY CHAT HISTORY ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- HANDLE USER INPUT ---
prompt = st.chat_input("Ask Vivek AI a question...")

if prompt:
    # 1. Stop if no API key
    if not api_key:
        st.warning("⚠️ Please enter your **Gemini API Key** in the sidebar to start chatting with Vivek AI.")
        st.stop()
        
    # 2. Add user message to state and display
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 3. Configure Gemini and generate response
    try:
        # Streamlit works statically via reruns, so preserving a TCP-based Client object 
        # breaks between re-runs. We reconstruct the connection cleanly every time.
        client = genai.Client(api_key=api_key)
        
        # Build strict history representation strictly from session state (excluding the current prompt)
        history_list = []
        for msg in st.session_state.messages[:-1]:
            role = "user" if msg["role"] == "user" else "model"
            history_list.append(
                types.Content(role=role, parts=[types.Part.from_text(text=msg["content"])])
            )
            
        chat_session = client.chats.create(
            model="gemini-2.5-flash",
            config=types.GenerateContentConfig(
                system_instruction="You are Vivek AI, a helpful, friendly, and highly intelligent AI assistant created for this project. Answer queries in a helpful and engaging way."
            ),
            history=history_list
        )
        
        with st.chat_message("assistant"):
            response_placeholder = st.empty()
            full_response = ""
            
            import time
            max_retries = 3
            success = False
            
            # Stream the response with automatic retries for server overloads
            with st.spinner("Vivek AI is thinking..."):
                for attempt in range(max_retries):
                    try:
                        response = chat_session.send_message_stream(prompt)
                        for chunk in response:
                            if chunk.text:
                                full_response += chunk.text
                                response_placeholder.markdown(full_response + "▌")
                        
                        success = True
                        break # Break out of the retry loop if successful
                    except Exception as e:
                        if "503" in str(e) and attempt < max_retries - 1:
                            # Server is overloaded, wait 3 seconds before retrying silently
                            time.sleep(3)
                            continue
                        else:
                            # If it's a different error or we ran out of retries, raise it to be caught by the outer try-except
                            raise e
                            
                if success:
                    # Finally, display the complete response without the cursor
                    response_placeholder.markdown(full_response)
                
        # 4. Add assistant response to state
        if success:
            st.session_state.messages.append({"role": "assistant", "content": full_response})

    except Exception as e:
        error_message = f"An error occurred: {str(e)}"
        st.error(error_message)
        # If API key is invalid, this will catch it
        if "API_KEY_INVALID" in str(e):
            st.error("It looks like your API key is invalid. Please check the sidebar and try again.")
