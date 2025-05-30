import streamlit as st
import json

@st.dialog("📰 Search Sources")
def show_sources(json_string: str):
    """
    Show search results in a Streamlit dialog from a JSON string.
    Each result must have: 'title', 'url', 'content', and optional 'favicon_url'.
    """
    try:
        results = json.loads(json_string)
    except json.JSONDecodeError:
        st.error("Invalid JSON format.")
        return

    st.markdown("""
    <style>
    a:hover {
        color: #1e90ff !important;
        text-decoration: underline !important;
        cursor: pointer;
    }
    </style>
    """, unsafe_allow_html=True)

    for i, res in enumerate(results, start=1):
        with st.container():
            cols = st.columns([0.3, 1, 11])
            with cols[0]:
                st.markdown(f"<div style='color: #888; font-weight: 600;'>{i}.</div>", unsafe_allow_html=True)

            with cols[1]:
                if res.get("favicon_url"):
                    st.image(res["favicon_url"], width=28)

            with cols[2]:
                st.markdown(
                    f"""
                    <div style="margin-bottom: 0.4rem;">
                        <a href="{res['url']}" target="_blank" 
                           style="text-decoration: none; font-weight: 600; font-size: 1.05rem; color: #fafafa;">
                            {res['title']}
                        </a>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                snippet = res.get("content", "").strip().replace("\n", " ")
                short = snippet[:200] + "..." if len(snippet) > 200 else snippet
                st.markdown(
                    f"""
                    <div style="color: #ccc; font-size: 0.93rem; line-height: 1.5;">
                        {short}
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        st.divider()
