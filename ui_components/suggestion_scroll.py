import streamlit as st
import math
import streamlit.components.v1 as components

def suggestion_scroll_ui(topics: list, num_rows: int = 3):
    """
    topics → list of (emoji, text) tuples
    num_rows → how many rows you want to display
    """

    # ---------------- CSS ----------------
    st.markdown("""
<style>

    /* match Streamlit top padding */
    .main .block-container { 
        padding-top: 3rem; 
        max-width: 100%; 
    }

    /* soft gradient fade edges */
    .scroll-container {
        overflow-x: hidden;
        white-space: nowrap;
        margin-bottom: 1rem;
        padding: 0.5rem 0;
        position: relative;
    }

    .scroll-container::before,
    .scroll-container::after {
        content: '';
        position: absolute;
        top: 0; 
        bottom: 0;
        width: 120px;
        pointer-events: none;
        z-index: 10;
    }

    /* match #0f0f0f background fade */
    .scroll-container::before {
        left: 0;
        background: linear-gradient(to right, #0f0f0f 0%, transparent 100%);
    }
    .scroll-container::after {
        right: 0;
        background: linear-gradient(to left, #0f0f0f 0%, transparent 100%);
    }

    /* scrolling rows */
    .scroll-row, .scroll-row-reverse {
        display: inline-flex;
        gap: 0.55rem;
    }

    .scroll-row {
        animation: scroll 55s linear infinite;
    }
    .scroll-row-reverse {
        animation: scroll-reverse 60s linear infinite;
    }

    .scroll-row:hover,
    .scroll-row-reverse:hover {
        animation-play-state: paused;
    }

    /* ================================ */
    /*     ULTRA MINIMAL TOPIC CHIP     */
    /* ================================ */
    .topic-btn {
        display: inline-block;
        background: rgba(255, 255, 255, 0.03); /* subtle translucent */
        padding: 0.50rem 1.15rem;
        border-radius: 40px;
        font-size: 0.90rem;
        color: #e6e6e6;
        border: 1px solid rgba(255, 255, 255, 0.06); /* faint border */
        cursor: pointer;
        white-space: nowrap;
        user-select: none;

        /* minimal shadows + smooth transitions */
        transition: all 0.25s ease;
    }

    .topic-btn:hover {
        background: rgba(255, 255, 255, 0.06); /* slightly brighter */
        border-color: rgba(255, 255, 255, 0.12);
        transform: translateY(-1.5px);
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.35);
    }

    /* animations */
    @keyframes scroll {
        from { transform: translateX(0); }
        to   { transform: translateX(-50%); }
    }
    @keyframes scroll-reverse {
        from { transform: translateX(-50%); }
        to   { transform: translateX(0); }
    }
    
    /* default (laptop/desktop) - keep as is */
    .scroll-container::before,
    .scroll-container::after {
        width: 120px;
    }

    /* MOBILE FIX — reduce gradient width on phones */
    @media (max-width: 600px) {
        .scroll-container::before,
        .scroll-container::after {
            width: 40px !important;   /* much narrower */
        }
    }

</style>
""", unsafe_allow_html=True)

    # -------------- Split topics into rows ----------------
    if num_rows <= 0:
        num_rows = 1

    per_row = math.ceil(len(topics) / num_rows)
    rows = [topics[i:i + per_row] for i in range(0, len(topics), per_row)]

    # -------------- Render rows ----------------
    def create_scroll_row(row_topics, reverse=False):
        rclass = "scroll-row-reverse" if reverse else "scroll-row"
        html = ""
        dup = row_topics * 3
        for emoji, text in dup:
            # FIXED: Changed from div to button and added proper attributes
            html += f'<button type="button" class="topic-btn" data-value="{text}">{emoji} {text}</button>'

        return f'<div class="{rclass}">{html}</div>'

    for i, row in enumerate(rows):
        reverse = (i % 2 == 1)
        st.markdown(
            f"""
            <div class="scroll-container">
                {create_scroll_row(row, reverse=reverse)}
            </div>
            """,
            unsafe_allow_html=True
        )