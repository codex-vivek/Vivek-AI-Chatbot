import streamlit as st
import requests
import json
import time
from dotenv import load_dotenv
from duckduckgo_search import DDGS

# Load environment variables from .env file if it exists
load_dotenv()

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
    
    # Priority 1: Load from environment variables (including .env file via load_dotenv)
    # Priority 2: Load from Streamlit secrets
    api_key = os.getenv("SARVAM_API_KEY") 
    
    if not api_key:
        try:
            api_key = st.secrets["SARVAM_API_KEY"]
        except Exception:
            api_key = ""
            
    if not api_key or api_key == "YOUR_API_KEY_HERE":
        st.error("⚠️ **API key missing!** Please add your `SARVAM_API_KEY` to the `.streamlit/secrets.toml` file or a `.env` file to start chatting.")
        st.stop()


    
    st.markdown("---")
    st.markdown("### 💡 Key Features")
    st.markdown("✅ Clean and user-friendly interface")
    st.markdown("✅ Real-time question answering")
    st.markdown("✅ Integrated with Sarvam AI")
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
    # 1. Double check API key
    if not api_key or api_key == "YOUR_API_KEY_HERE":
        st.warning("⚠️ **API key not configured.** Please add it to your secrets or environment variables.")
        st.stop()

        
    # 2. Search for latest info if needed (Simple keyword check)
    search_keywords = ["latest", "recent", "today", "now", "news", "current", "kaun hai", "kiske", "who is", "match", "score"]
    search_context = ""
    
    if any(keyword in prompt.lower() for keyword in search_keywords):
        with st.status("🔍 Searching the internet for latest updates...") as status:
            try:
                with DDGS() as ddgs:
                    results = list(ddgs.text(prompt, max_results=5))
                    if results:
                        search_context = "\n\nLATEST SEARCH CONTEXT FROM INTERNET:\n"
                        for i, r in enumerate(results):
                            search_context += f"- {r['body']}\n"
                status.update(label="✅ Search complete!", state="complete")
            except Exception as e:
                status.update(label="⚠️ Search failed, using base knowledge.", state="error")

    # 3. Add user message to state and display
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 4. Configure Sarvam API and generate response
    try:
        # Build strict history representation from session state
        # Include search context in the last message's part for grounding
        history_list = [{"role": "system", "content": "You are Vivek AI, a helpful, friendly assistant. Use the provided search context if available to answer questions accurately. If no search context is provided or useful, use your own knowledge."}]
        
        for msg in st.session_state.messages[:-1]:
            history_list.append({"role": msg["role"], "content": msg["content"]})
            
        # Add the current prompt with search context
        final_prompt_content = prompt
        if search_context:
            final_prompt_content = f"Question: {prompt}\n{search_context}\nPlease answer based on this context if it's relevant."
            
        history_list.append({"role": "user", "content": final_prompt_content})

            
        with st.chat_message("assistant"):
            response_placeholder = st.empty()
            full_response = ""
            
            with st.spinner("Vivek AI is thinking..."):
                url = "https://api.sarvam.ai/v1/chat/completions"
                headers = {
                    "Content-Type": "application/json",
                    "api-subscription-key": api_key
                }
                data = {
                    "model": "sarvam-30b",  # or whichever sarvam model you're using, like sarvam-105B or sarvam-2b-v0.5
                    "messages": history_list,
                    "stream": True,
                    "temperature": 0.7
                }
                
                response = requests.post(url, headers=headers, json=data, stream=True)
                
                if response.status_code == 200:
                    for line in response.iter_lines():
                        if line:
                            decoded_line = line.decode('utf-8')
                            if decoded_line.startswith('data: ') and decoded_line != 'data: [DONE]':
                                try:
                                    chunk = json.loads(decoded_line[6:])
                                    if 'choices' in chunk and len(chunk['choices']) > 0:
                                        content = chunk['choices'][0].get('delta', {}).get('content', '')
                                        if content:
                                            full_response += content
                                            response_placeholder.markdown(full_response + "▌")
                                except json.JSONDecodeError:
                                    pass
                    # Finally, display the complete response without the cursor
                    response_placeholder.markdown(full_response)
                    # 4. Add assistant response to state
                    st.session_state.messages.append({"role": "assistant", "content": full_response})
                else:
                    error_msg = response.text
                    if response.status_code == 401:
                        st.error("❌ It looks like your API key is invalid. Please check the sidebar and try again.")
                    elif response.status_code == 429:
                        st.warning("⏳ **API Limit Reached!** \n\nAapki limit cross ho gayi hai. Please wait before sending another message!")
                    else:
                        st.error(f"An error occurred: {error_msg}")

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
