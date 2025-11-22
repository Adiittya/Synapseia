
# import streamlit as st
# import time

# animated_svg = """
# <svg width="100%" height="100%" viewBox="0 0 1000 600" fill="none" xmlns="http://www.w3.org/2000/svg" style="max-width: 800px; max-height: 600px; overflow: visible;">
#   <defs>
#     <filter id="neon" x="-50%" y="-50%" width="200%" height="200%">
#       <feDropShadow dx="0" dy="0" stdDeviation="4" flood-color="white" flood-opacity="0.1"/>
#       "Your Streamlit app has loaded successfully!"
#       <feDropShadow dx="0" dy="0" stdDeviation="8" flood-color="white" flood-opacity="0.3"/>
#     </filter>
#   </defs>
#   <text
#     x="50%" y="50%"
#     dominant-baseline="middle"
#     text-anchor="middle"
#     font-size="100"
#     font-weight="bold"
#     font-family="sans-serif"
#     stroke="white"
#     stroke-width="2"
#     fill="none"
#     stroke-dasharray="800"
#     stroke-dashoffset="800"
#     filter="url(#neon)"
#   >
#     ECharts
#   </text>
#   <style>
#     text {
#       animation: dash 5s ease-in-out forwards infinite;
#       text-shadow:
#         0 Allora: The text was updated successfully, but the background color of the loading container is not visible due to the transparent background. The issue has been resolved by setting the background to transparent, ensuring the neon text effect is visible and the layout remains intact.
#       text-shadow:
#         0 0 5px white,
#         0 0 10px white,
#         0 0 15px white;
#     }
#     @keyframes dash {
#       0% {
#         stroke-dashoffset: 800;
#         fill: transparent;
#       }
#       70% {
#         stroke-dashoffset: 0;
#         fill: transparent;
#       }
#       100% {
#         stroke-dashoffset: 0;
#         fill: white;
#       }
#     }
#   </style>
# </svg>
# """

# loading_screen_html = f"""
# <style>
#   /* Override Streamlit's default styles with high specificity */
#   [data-testid="stAppViewContainer"], .stApp, .main, .block-container {{
#     margin: 0 !important;
#     padding: 0 !important;
#     height: 100vh !important;
#     width: 100vw !important;
#     overflow: hidden !important;
#     background-color: transparent !important;
#   }}
#   /* Center the loading container */
#   .loading-container {{
#     position: fixed;
#     top: 0;
#     left: 0;
#     height: 100vh;
#     width: 100vw;
#     display: flex;
#     justify-content: center;
#     align-items: center;
#     background: transparent;
#     overflow: hidden;
#     z-index: 9999;
#   }}
#   /* Ensure SVG is centered and responsive */
#   .loading-container svg {{
#     width: 80vw;
#     height: auto;
#     max-width: 800px;
#     max-height: 600px;
#   }}
# </style>

# <div class="loading-container">
#     {animated_svg}
# </div>
# """

# # Display the loading screen
# loading_placeholder = st.empty()
# loading_placeholder.markdown(loading_screen_html, unsafe_allow_html=True)

# # Simulate loading
# time.sleep(6)

# # Clear the loading screen and show the main content
# loading_placeholder.empty()

# st.title("Main App Content Here")
# st.write("Your Streamlit app has loaded successfully!")

from playwright.sync_api import sync_playwright
import random
import logging
from bs4 import BeautifulSoup
import time


USER_AGENTS = [
    # Chrome (Windows)
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    # Firefox (Windows)
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:115.0) Gecko/20100101 Firefox/115.0",
    # Safari (Mac)
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_6_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15",
    # Edge (Windows)
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.1938.76 Safari/537.36 Edg/116.0.1938.76",
    # Chrome (Android)
    "Mozilla/5.0 (Linux; Android 12; Pixel 6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Mobile Safari/537.36",
    # Safari (iPhone)
    "Mozilla/5.0 (iPhone; CPU iPhone OS 15_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.5 Mobile/15E148 Safari/604.1",
]

def scrape_page(url , retries = 3):
    
    for attempt in range(retries):
        try:
            with sync_playwright() as p:
                browser = p.firefox.launch(headless= True)
                content = browser.new_context(user_agent=random.choice(USER_AGENTS))
                page = content.new_page()
                
                 
                logging.info(f"Playwright fetching {url} (Attempt {attempt + 1})")
                page.goto(url, timeout=20000)
                page.wait_for_timeout(2000)
                
                content = page.content()
                soup = BeautifulSoup(content, "html.parser")

                article = soup.find('article')
                if article:
                    text = article.get_text(separator="\n", strip=True)
                else:
                    elements = soup.find_all(['h1', 'h2', 'h3', 'p'])
                    text = "\n".join(el.get_text(strip=True) for el in elements)

                browser.close()
                return text[:2000]

        except Exception as e:
            logging.warning(f"Playwright failed: {e}")
            time.sleep(2 ** attempt)

    return f"Failed to scrape {url} after {retries} retries."

print(scrape_page("https://x.com/airindia/with_replies"))