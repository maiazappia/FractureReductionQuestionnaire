# test_session.py
import streamlit as st
import os
import json
from datetime import datetime

st.set_page_config(page_title="TEST session_state", layout="centered")

# versione per assicurarsi che il file sia quello giusto
APP_VERSION = "session-test-v1"
st.write("APP_VERSION:", APP_VERSION)
st.write("cwd:", os.getcwd())
st.write("file exists:", os.path.isfile("test_session.py"))

# simple parameters
PARAMS = ["A", "B", "C"]

# initialize defaults (safe keys)
for p in PARAMS:
    k_rank = f"rank_{p}"
    k_points = f"points_{p}"
    k_like = f"likert_{p}"
    if k_rank not in st.session_state:
        st.session_state[k_rank] = 1
    if k_points not in st.session_state:
        st.session_state[k_points] = 0
    if k_like not in st.session_state:
        st.session_state[k_like] = 4

st.header("TEST: set values and submit")

for p in PARAMS:
    st.selectbox(f"Rank {p}", options=[1,2,3,4,5], key=f"rank_{p}")
    st.number_input(f"Points {p}", min_value=0, max_value=100, step=1, key=f"points_{p}")
    st.slider(f"Likert {p}", min_value=1, max_value=7, step=1, key=f"likert_{p}")

if st.button("Submit test"):
    # snapshot to show exactly what is in session_state
    snapshot = {}
    for p in PARAMS:
        snapshot[p] = {
            "rank_key": f"rank_{p}",
            "points_key": f"points_{p}",
            "likert_key": f"likert_{p}",
            "rank_value": st.session_state.get(f"rank_{p}"),
            "points_value": st.session_state.get(f"points_{p}"),
            "likert_value": st.session_state.get(f"likert_{p}"),
        }
    st.markdown("### SESSION SNAPSHOT (json)")
    st.json(snapshot)
    # also print to server logs
    print("SERVER LOG - SESSION SNAPSHOT:", json.dumps(snapshot))
    st.success("Submitted (snapshot printed in page and server logs).")
