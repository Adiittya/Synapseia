import streamlit as st

# Page config
st.set_page_config(page_title="Reddit Answers", layout="wide", initial_sidebar_state="collapsed")

# Custom CSS for dark theme and styling
st.markdown("""
<style>
    /* Dark background */
    .stApp {
        background-color: #0f0f0f;
    }
    
    /* Remove padding */
    .main .block-container {
        padding-top: 3rem;
        padding-bottom: 3rem;
        max-width: 100%;
    }
    
    /* Header styling */
    .main-header {
        text-align: center;
        padding: 2rem 1rem 3rem 1rem;
        margin-bottom: 2rem;
    }
    
    .title {
        font-size: 4.5rem;
        font-weight: 800;
        margin-bottom: 1.5rem;
        line-height: 1.1;
    }
    
    .reddit {
        color: #ff4500;
    }
    
    .answers {
        color: #ff6b35;
    }
    
    .subtitle {
        font-size: 1.4rem;
        color: #d1d5db;
        line-height: 1.6;
        max-width: 900px;
        margin: 0 auto;
    }
    
    /* Scrolling container */
    .scroll-container {
        overflow-x: hidden;
        white-space: nowrap;
        margin-bottom: 1rem;
        padding: 0.5rem 0;
        position: relative;
    }
    
    /* Blur effect on edges */
    .scroll-container::before,
    .scroll-container::after {
        content: '';
        position: absolute;
        top: 0;
        bottom: 0;
        width: 150px;
        pointer-events: none;
        z-index: 10;
    }
    
    .scroll-container::before {
        left: 0;
        background: linear-gradient(to right, #0f0f0f 0%, transparent 100%);
    }
    
    .scroll-container::after {
        right: 0;
        background: linear-gradient(to left, #0f0f0f 0%, transparent 100%);
    }
    
    .scroll-row {
        display: inline-flex;
        animation: scroll 60s linear infinite;
        gap: 0.75rem;
    }
    
    .scroll-row-reverse {
        display: inline-flex;
        animation: scroll-reverse 65s linear infinite;
        gap: 0.75rem;
    }
    
    @keyframes scroll {
        0% {
            transform: translateX(0);
        }
        100% {
            transform: translateX(-50%);
        }
    }
    
    @keyframes scroll-reverse {
        0% {
            transform: translateX(-50%);
        }
        100% {
            transform: translateX(0);
        }
    }
    
    .scroll-row:hover, .scroll-row-reverse:hover {
        animation-play-state: paused;
    }
    
    /* Topic button styling */
    .topic-btn {
        display: inline-block;
        background-color: #1a1a1a;
        color: #e5e5e5;
        border: 1px solid #2a2a2a;
        border-radius: 9999px;
        padding: 0.65rem 1.5rem;
        font-size: 0.95rem;
        cursor: pointer;
        transition: all 0.3s ease;
        white-space: nowrap;
        user-select: none;
    }
    
    .topic-btn:hover {
        background-color: #2a2a2a;
        border-color: #3a3a3a;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(255, 69, 0, 0.2);
    }
    
    /* Hide default streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {visibility: hidden;}
    
    /* Learn more link */
    .learn-more {
        text-align: center;
        margin-top: 4rem;
        padding: 2rem;
    }
    
    .learn-more-link {
        color: #9ca3af;
        text-decoration: none;
        font-size: 1.05rem;
        transition: color 0.3s;
    }
    
    .learn-more-link:hover {
        color: #e5e5e5;
    }
    
    /* Remove streamlit branding */
    .css-1v0mbdj {
        display: none;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <div class="title">
        <span class="reddit">reddit</span> <span class="answers">answers</span>
    </div>
    <div class="subtitle">
        Got a question? Ask it and get answers, perspectives, and recommendations from all of Reddit
    </div>
</div>
""", unsafe_allow_html=True)

# Topics data - expanded for infinite scroll
topics_row1 = [
    ("🎧", "best wireless ear buds"),
    ("💸", "biggest investment mistakes"),
    ("🧠", "ADHD study tips"),
    ("💻", "best gaming laptop"),
    ("🎭", "anime similar to demon slayer"),
    ("💼", "should I change jobs"),
    ("🎵", "obscure pop songs from the 90s"),
    ("🎮", "best arkham game"),
]

topics_row2 = [
    ("🐱", "how to tell if a cut is infected"),
    ("🍊", "top vitamin c serums"),
    ("🎨", "learn to draw digitally"),
    ("📺", "best adult animated series"),
    ("📺", "best selling sunset drama"),
    ("⌚", "garmin vs apple watch"),
    ("🥽", "VR headset recommendations"),
]

topics_row3 = [
    ("💬", "how to ask someone out without being weird"),
    ("😰", "how to deal with anxiety"),
    ("🏫", "teaching middle school vs high school"),
    ("🏋️", "best home workout routine"),
    ("📚", "learn coding from scratch"),
    ("☕", "coffee vs tea benefits"),
    ("🎸", "beginner guitar songs"),
]

# Create infinite scrolling rows
def create_scroll_row(topics, reverse=False):
    row_class = "scroll-row-reverse" if reverse else "scroll-row"
    buttons_html = ""
    
    # Duplicate topics for seamless infinite scroll
    all_topics = topics * 3
    
    for emoji, text in all_topics:
        buttons_html += f'<div class="topic-btn">{emoji} {text}</div>'
    
    return f'<div class="{row_class}">{buttons_html}</div>'

# Row 1 - scroll left
st.markdown(f"""
<div class="scroll-container">
    {create_scroll_row(topics_row1, reverse=False)}
</div>
""", unsafe_allow_html=True)

# Row 2 - scroll right
st.markdown(f"""
<div class="scroll-container">
    {create_scroll_row(topics_row2, reverse=True)}
</div>
""", unsafe_allow_html=True)

# Row 3 - scroll left
st.markdown(f"""
<div class="scroll-container">
    {create_scroll_row(topics_row3, reverse=False)}
</div>
""", unsafe_allow_html=True)

# Learn more link
st.markdown("""
<div class="learn-more">
    <a href="#" class="learn-more-link">Learn how Reddit Answers works →</a>
</div>
""", unsafe_allow_html=True)

# from ui_components.suggestion_scroll import suggestion_scroll_ui

# topics = [
#     ("🎧", "best wireless ear buds"),
#     ("💸", "biggest investment mistakes"),
#     ("🧠", "ADHD study tips"),
#     ("💻", "best gaming laptop"),
#     ("🎭", "anime similar to demon slayer"),
#     ("💼", "should I change jobs"),
#     ("🎵", "obscure pop songs from the 90s"),
#     ("🎮", "best arkham game"),
#     ("🐱", "how to tell if a cut is infected"),
#     ("🎨", "learn to draw digitally"),
#     ("📺", "best adult animated series"),
#     ("🥽", "VR headset recommendations"),
# ]

# suggestion_scroll_ui(topics, num_rows=3)
