# ui_components/memory_manager.py

import streamlit as st
from streamlit_timeline import timeline
from tools.custom_memories import get_all_memories, delete_memory_by_id
from datetime import datetime
from dateutil import parser
import json

# ui_components/memory_manager.py

import streamlit as st
from streamlit_timeline import timeline
from tools.custom_memories import get_all_memories, delete_memory_by_id
from datetime import datetime
from dateutil import parser
import json


@st.dialog("📂 Memory Timeline")
def memory_manager_dialog():
    # CSS Styling for delete buttons and confirmation popup
    st.markdown(
        """
        <style>
        .trash-btn {
            background: none;
            border: none;
            cursor: pointer;
            color: #c0392b;
            font-size: 1.2rem;
            padding: 0 5px;
            transition: color 0.3s ease;
        }
        .trash-btn:hover {
            color: #e74c3c;
        }
        .confirm-dialog {
            background-color: #001F3F;
            color: white;
            padding: 1rem;
            border-radius: 8px;
            max-width: 320px;
            margin: 1rem auto;
            text-align: center;
        }
        .confirm-dialog button {
            margin: 0.5rem;
            padding: 6px 14px;
            border-radius: 6px;
            border: none;
            cursor: pointer;
            font-weight: 600;
        }
        .confirm-yes {
            background-color: #c0392b;
            color: white;
        }
        .confirm-no {
            background-color: #34495e;
            color: white;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    all_memories = get_all_memories()

    if not all_memories:
        st.info("No memories found.")
        return

    if "confirm_delete_id" not in st.session_state:
        st.session_state.confirm_delete_id = None

    # Timeline section
    events = []
    for memory in all_memories:
        doc = memory.get("document", "Unknown memory")
        meta = memory.get("metadata", {})
        memory_id = memory.get("id")

        raw_timestamp = meta.get("day_date_time") or meta.get("timestamp")
        try:
            dt = parser.parse(raw_timestamp)
        except Exception:
            dt = datetime.now()

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
        })

    timeline_data = {
        "title": {
            "text": {
                "headline": "🧠 Your Memory Timeline",
                "text": "Visualize, scroll, and manage your memories."
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
                with cols[1]:
                    if st.button("Cancel", key=f"cancel_delete_{memory_id}"):
                        # Just close expander by rerunning or do nothing
                        pass

        st.divider()
