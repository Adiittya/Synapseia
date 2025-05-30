# ui_components/memory_manager.py

import streamlit as st
from streamlit_timeline import timeline
from tools.custom_memories import get_all_memories, delete_memory_by_id
from datetime import datetime
from dateutil import parser
import json



def darken_color(hex_color, amount=0.1):
    """
    Darken the given hex color by the given amount (0 to 1).
    """
    hex_color = hex_color.lstrip('#')
    rgb = [int(hex_color[i:i+2], 16) for i in (0, 2, 4)]
    darkened = [max(0, int(c * (1 - amount))) for c in rgb]
    return '#{:02x}{:02x}{:02x}'.format(*darkened)

@st.dialog("📂 Memory Timeline")
def memory_manager_dialog():


    all_memories = get_all_memories()

    if not all_memories:
        st.info("No memories found.")
        return

    if "confirm_delete_id" not in st.session_state:
        st.session_state.confirm_delete_id = None
        
    base_color = "#1e1e1e"
    num_memories = len(all_memories)
    # Timeline section
    events = []
    for idx, memory in enumerate(all_memories):
        doc = memory.get("document", "Unknown memory")
        meta = memory.get("metadata", {})
        memory_id = memory.get("id")

        raw_timestamp = meta.get("day_date_time") or meta.get("timestamp")
        try:
            dt = parser.parse(raw_timestamp)
        except Exception:
            dt = datetime.now()
            
        dark_factor = idx / max(num_memories - 1, 1) * 0.6
        event_color = darken_color(base_color, dark_factor)

    
        
        events.append({
            "start_date": {
                "year": dt.year,
                "month": dt.month,
                "day": dt.day,
                "hour": dt.hour,
                "minute": dt.minute,
            },
            "text": {
                "headline": f"{meta.get('tags', '🧠 Memory')}",
                "text": f"{doc}<br><br><b>🕒 Timestamp:</b> {dt.strftime('%Y-%m-%d %H:%M')}"
            },
            "unique_id": memory_id,
                       "background": {
            "color": event_color  # dark gray background
    }
        })

    timeline_data = {
        "title": {
            "text": {
                "headline": "🧠 Your Memory Timeline",
                "text": "Visualize, scroll, and manage your memories."
            },
             "background": {
        "color": "#1e1e1e"  # dark gray background
    }
        },
        "events": events
    }

    st.markdown('<div class="timeline-container">', unsafe_allow_html=True)
    timeline(json.dumps(timeline_data), height=400)
    st.markdown('</div>', unsafe_allow_html=True)

    st.divider()
    st.subheader("🗃 Manage Individual Memories")

    st.markdown('<div class="memory-list-container">', unsafe_allow_html=True)
    
    for idx, memory in enumerate(all_memories):
        doc = memory.get("document", "Unknown memory")
        meta = memory.get("metadata", {})
        memory_id = memory.get("id")
        raw_timestamp = meta.get("day_date_time") or meta.get("timestamp")

        try:
            dt = parser.parse(raw_timestamp)
        except Exception:
            dt = datetime.now()

        with st.container():
            st.markdown(f"**📝 {meta.get('tags', 'No Tag')}**")
            st.markdown(doc)
            st.caption(f"🕒 {dt.strftime('%Y-%m-%d %H:%M')}")

            with st.expander("🗑️ Delete Memory", expanded=False):
                st.markdown(
                    '<p style="color:#b03a2e; font-weight:600; margin: 0 0 6px 0;">Are you sure you want to delete this memory?</p>', 
                    unsafe_allow_html=True
                )
                cols = st.columns([1, 1])
                with cols[0]:
                    if st.button("Yes, delete", key=f"confirm_delete_{memory_id}"):
                        success = delete_memory_by_id(memory_id)
                        if success:
                            
                            st.success("Memory deleted.")
                        else:
                            st.error("Failed to delete memory.")
                        st.rerun()
                        return f"Memory deleted with id {memory_id}"
                with cols[1]:
                    if st.button("Cancel", key=f"cancel_delete_{memory_id}"):
                        # Just close expander by rerunning or do nothing
                        pass

        st.divider()
