from copy import deepcopy
import streamlit as st
from utils import (
    process_rankings_csv,
    process_dances_csv,
)
from components.dances_by_top_3_chart import dances_by_top_3_chart, dances_bottom_third_percentile_chart


def handle_rankings_csv_upload() -> None:
    if "rankings_csv" not in st.session_state:
        return
    if not st.session_state["rankings_csv"]:
        return
    rankings_csv = st.session_state["rankings_csv"]
    members = sorted(process_rankings_csv(rankings_csv), key=lambda x: x.name)
    st.session_state["members"] = deepcopy(members)
    st.session_state["original_members"] = {
        member.name: deepcopy(member) for member in members
    }


def handle_dances_csv_upload() -> None:
    if "dances_csv" not in st.session_state:
        return
    if not st.session_state["dances_csv"]:
        return
    dances_csv = st.session_state["dances_csv"]
    st.session_state["dances"] = sorted(
        process_dances_csv(dances_csv), key=lambda x: x.name
    )
    st.session_state["dances_index"] = {
        dance.name: dance for dance in st.session_state["dances"]
    }


def setup_tab() -> None:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Rankings CSV")
        st.file_uploader(
            "Upload your rankings CSV file here:",
            type="csv",
            key="rankings_csv",
            on_change=handle_rankings_csv_upload,
        )
    with col2:
        st.subheader("Dances CSV")
        st.file_uploader(
            "Upload your dances CSV file here:",
            type="csv",
            key="dances_csv",
            on_change=handle_dances_csv_upload,
        )

    if not st.session_state.get("members") or not st.session_state.get("dances"):
        return

    st.success("Files processed successfully!")

    # Display the dance rankings charts
    dances_by_top_3_chart()
    dances_bottom_third_percentile_chart()
