import streamlit as st
import random
from copy import deepcopy

from components.dance_detail_view import dance_detail_view
from components.member_detail_view import member_detail_view
from components.top3_satisfaction_card import top3_satisfaction_card
from components.max_dances_satisfaction_card import max_dances_satisfaction_card
from schemas import Dance, Member
from services import match
from utils import (
    generate_dance_based_csv,
    generate_dancer_based_csv,
)


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
            included_dances = [dance for dance in st.session_state["dances"] if dance.included]
            matching, tl_matching = match(
                st.session_state["members"], included_dances
            )

            # Display results
            st.subheader("Matching Results")
            
            # Display satisfaction metrics
            col1, col2 = st.columns(2)
            with col1:
                top3_satisfaction_card(matching, st.session_state["members"])
            with col2:
                max_dances_satisfaction_card(matching, st.session_state["members"])
            
            st.divider()

            # Generate CSV data
            dance_csv = generate_dance_based_csv(
                matching, included_dances, tl_matching
            )
            dancer_csv = generate_dancer_based_csv(
                matching, st.session_state["members"]
            )

            # Dance assignments table with download
            st.write("### Dance Assignments")
            st.dataframe(dance_csv)

            # Dancer assignments table with download
            st.write("### Dancer Assignments")
            st.dataframe(dancer_csv)

        except Exception as e:
            import traceback

            st.error(f"Error running matcher: {e}")
            st.code(traceback.format_exc())
