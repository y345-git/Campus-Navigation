import streamlit as st

def init_session_state():
    defaults = {
        "phase": "idle",
        "campus_path": [],
        "b1_path": [],
        "distance_to_college": 0,
        "total_distance": 0,
        "source": "Gate 2",
        "destination": "Library",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

def rerun():
    try:
        st.experimental_rerun()
    except Exception:
        pass
