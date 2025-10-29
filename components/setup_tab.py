from copy import deepcopy
import streamlit as st
from utils import (
    process_rankings_csv,
    process_dances_csv,
    filter_member_rankings_by_valid_dances,
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
    # reset filtering flag so rankings are re-filtered when both CSVs are available
    st.session_state["rankings_filtered"] = False


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
    # reset filtering flag so rankings are re-filtered when both CSVs are available
    st.session_state["rankings_filtered"] = False


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

    # filter member rankings to only include valid dances
    # this ensures rankings.csv dances that aren't in dances.csv are excluded
    if not st.session_state.get("rankings_filtered"):
        valid_dances = {dance.name for dance in st.session_state["dances"]}
        filtered_members = filter_member_rankings_by_valid_dances(
            st.session_state["members"], valid_dances
        )
        st.session_state["members"] = filtered_members
        st.session_state["original_members"] = {
            member.name: deepcopy(member) for member in filtered_members
        }
        st.session_state["rankings_filtered"] = True

    st.success("Files processed successfully!")

    # Display the dance rankings charts
    dances_by_top_3_chart()
    dances_bottom_third_percentile_chart()
