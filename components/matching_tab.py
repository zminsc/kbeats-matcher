import streamlit as st
import random
from copy import deepcopy

from components.dance_detail_view import dance_detail_view
from components.member_detail_view import member_detail_view
from components.top3_satisfaction_card import top3_satisfaction_card
from components.max_dances_satisfaction_card import max_dances_satisfaction_card
from schemas import Dance, Member, Matching, TLMatching
from services import match
from utils import (
    generate_dance_based_csv,
    generate_dancer_based_csv,
)


def _render_results(matching: Matching, members_snapshot: list[Member], dance_csv, dancer_csv) -> None:
    # Display results
    st.subheader("Matching Results")

    # Display satisfaction metrics
    col1, col2 = st.columns(2)
    with col1:
        top3_satisfaction_card(matching, members_snapshot)
    with col2:
        max_dances_satisfaction_card(matching, members_snapshot)

    st.divider()

    # Dance assignments table with download
    st.write("### Dance Assignments")
    st.dataframe(dance_csv)

    # Dancer assignments table with download
    st.write("### Dancer Assignments")
    st.dataframe(dancer_csv)


def matching_tab() -> None:
    if not st.session_state["members"] or not st.session_state["dances"]:
        st.warning("Please upload CSV files in the Setup tab first.")
        return

    with st.expander("Member Settings"):
        member_detail_view()
    with st.expander("Dance Settings"):
        dance_detail_view()

    st.divider()

    # Add button to run matcher
    if st.button("Run Matcher", type="primary"):
        try:
            random.seed()
            included_dances = [
                dance for dance in st.session_state["dances"] if dance.included
            ]
            matching, tl_matching = match(st.session_state["members"], included_dances)

            # Generate CSV data using a snapshot of current state
            members_snapshot: list[Member] = deepcopy(st.session_state["members"])
            dance_csv = generate_dance_based_csv(matching, included_dances, tl_matching)
            dancer_csv = generate_dancer_based_csv(
                matching, members_snapshot
            )

            # Persist results so they remain visible across reruns/edits
            st.session_state["matching_results"] = {
                "matching": matching,
                "members_snapshot": members_snapshot,
                "dance_csv": dance_csv,
                "dancer_csv": dancer_csv,
            }
        except Exception as e:
            import traceback

            st.error(f"Error running matcher: {e}")
            st.code(traceback.format_exc())

    # Always render last results if available
    results = st.session_state.get("matching_results")
    if results:
        _render_results(
            matching=results["matching"],
            members_snapshot=results["members_snapshot"],
            dance_csv=results["dance_csv"],
            dancer_csv=results["dancer_csv"],
        )
