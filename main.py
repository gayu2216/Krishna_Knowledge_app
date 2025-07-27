# main.py - Main application entry point
import streamlit as st
import base64

# If you have quiz and chatbot as separate modules, import them like this:
from custom_pages import quiz, chatbot  # <--- make sure they're not in "pages/" folder

# ------------------ Streamlit Config ------------------
st.set_page_config(
    page_title="Krishna Knowledge App", 
    page_icon="🦜",
    layout="wide"
)

def get_base64_of_bin_file(bin_file):
    try:
        with open(bin_file, 'rb') as f:
            return base64.b64encode(f.read()).decode()
    except:
        return ""

# Background image setup
try:
    img_base64 = get_base64_of_bin_file('/Users/gayathriutla/Desktop/Projects/krishna_game/Local-RAG-with-Ollama/image.jpg')
    has_image = True
except:
    img_base64 = ""
    has_image = False

# ------------------ Page CSS ------------------
def apply_styling():
    custom_style = f"""
    <style>
    /* Remove Streamlit default padding and margins */
    .block-container {{
        padding-top: 0rem;
        padding-bottom: 0rem;
        margin-top: 0rem;
    }}

    /* Hide header, footer, and toolbar */
    header {{ visibility: hidden !important; height: 0 !important; }}
    footer {{ visibility: hidden !important; height: 0 !important; }}
    .stDeployButton {{ display: none !important; }}
    
    /* Hide the main menu button (hamburger menu) */
    #MainMenu {{ visibility: hidden !important; }}
    
    /* Hide the Streamlit watermark */
    .stApp > header {{ display: none !important; }}
    
    /* Remove top white space */
    .stApp {{
        margin-top: -80px;
    }}
    
    /* Alternative method to hide header completely */
    div[data-testid="stToolbar"] {{ visibility: hidden !important; height: 0 !important; }}
    div[data-testid="stDecoration"] {{ visibility: hidden !important; height: 0 !important; }}
    div[data-testid="stStatusWidget"] {{ visibility: hidden !important; height: 0 !important; }}

    /* Hide top page navigation */
    section[data-testid="stSidebarNav"] {{ display: none; }}

    /* Make sidebar scrollable */
    [data-testid="stSidebar"] > div:first-child {{
        overflow-y: auto;
        max-height: 100vh;
    }}

    /* Background image */
    .stApp::before {{
        content: "";
        background-image: url("data:image/png;base64,{img_base64}");
        background-size: cover;
        background-position: center;
        position: fixed;
        top: 0; left: 0;
        width: 100%; height: 100%;
        opacity: 0.3;
        z-index: 0;
    }}

    .main-content {{
        position: relative;
        z-index: 1;
        background-color: rgba(255, 255, 255, 0.9);
        padding: 20px;
        border-radius: 15px;
        margin: 20px;
    }}

    /* Custom button styling */
    .nav-button {{
        width: 100%;
        margin-bottom: 10px;
        padding: 10px;
        border-radius: 10px;
        border: none;
        font-size: 16px;
        font-weight: bold;
        cursor: pointer;
        transition: all 0.3s ease;
    }}
    .nav-button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }}

    /* Additional fixes for white space */
    .main .block-container {{
        max-width: 100%;
        padding-top: 1rem;
    }}
    
    /* Force remove any remaining header elements */
    [data-testid="stHeader"] {{ display: none !important; }}
    </style>
    """
    st.markdown(custom_style, unsafe_allow_html=True)

apply_styling()

# ------------------ Session State ------------------
if 'current_page' not in st.session_state:
    st.session_state.current_page = "🎯 Quiz"

# ------------------ Sidebar Navigation ------------------
st.sidebar.title("🕉️ Navigation")
page = st.sidebar.selectbox(
    "Choose a page:",
    ["🎯 Quiz", "💬 Chat with AI"]
)

# ------------------ Page Routing ------------------
if page == "🎯 Quiz":
    quiz.show_quiz_page()
elif page == "💬 Chat with AI":
    chatbot.show_chatbot_page()