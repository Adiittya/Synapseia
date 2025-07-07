
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

from parse import generate_github_page
from tools.custom_scrapper import search_and_scrape

search_and_scrape("hello")
#tool for storing user preference / memories
# generate_github_page("https://github.com/adiittya/finbuddy")