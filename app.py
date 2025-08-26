import streamlit as st
from components.matching_tab import matching_tab
from components.setup_tab import setup_tab

if "members" not in st.session_state:
    st.session_state["members"] = None
if "dances" not in st.session_state:
    st.session_state["dances"] = None
if "dances_index" not in st.session_state:
    st.session_state["dances_index"] = {}
if "original_members" not in st.session_state:
    st.session_state["original_members"] = None

st.title("K-Beats Dance Matcher")

tab1, tab2 = st.tabs(["Setup", "Matching"])

with tab1:
    setup_tab()
with tab2:
    matching_tab()
