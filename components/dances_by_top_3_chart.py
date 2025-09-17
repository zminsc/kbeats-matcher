import streamlit as st
import pandas as pd
import altair as alt
from collections import Counter


def dances_by_top_3_chart() -> None:
    if not st.session_state["dances"] or not st.session_state["members"]:
        return

    # Count dances that appear in members' top rankings (limited by min(3, max_rank))
    dance_counts = Counter()

    for member in st.session_state["members"]:
        # Get the effective top rank limit (minimum of 3 and member's max_rank)
        effective_top_limit = min(3, member.max_rank)

        # Count dances in the member's top rankings up to the effective limit
        for i in range(min(effective_top_limit, len(member.dance_rankings))):
            dance_name = member.dance_rankings[i]
            dance_counts[dance_name] += 1

    # Ensure all dances are included, even those with 0 appearances in top 3
    all_dance_names = {dance.name for dance in st.session_state["dances"] if dance.included}
    for dance_name in all_dance_names:
        if dance_name not in dance_counts:
            dance_counts[dance_name] = 0

    # Create dataframe sorted by frequency (descending)
    if dance_counts:
        chart_data = pd.DataFrame(
            [
                {"dance": dance, "frequency": count}
                for dance, count in dance_counts.most_common()
            ]
        )

        st.subheader("Most Popular Dances")

        # Calculate dynamic height based on number of dances (minimum 30px per dance, minimum 300px total)
        num_dances = len(chart_data)
        chart_height = max(300, num_dances * 30)

        # Create horizontal Altair chart with explicit ordering
        chart = (
            alt.Chart(chart_data)
            .mark_bar()
            .encode(
                x=alt.X("frequency:Q", title="Appearances in Top 3"),
                y=alt.Y("dance:N", sort=None, title=None),
                tooltip=["dance", "frequency"],
            )
            .properties(height=chart_height)
        )

        st.altair_chart(chart, use_container_width=True)
    else:
        st.subheader("Dances by Top 3 Rankings")
        st.info("No dance rankings data available.")


def dances_bottom_third_percentile_chart() -> None:
    if not st.session_state["dances"] or not st.session_state["members"]:
        return

    # Count dances that appear in members' bottom third percentile rankings
    dance_counts = Counter()

    for member in st.session_state["members"]:
        total_rankings = len(member.dance_rankings)
        if total_rankings <= 3:
            # If member has 3 or fewer rankings, skip (no meaningful bottom third)
            continue
        
        # Calculate bottom third: start from the 67th percentile position
        bottom_third_start = int(total_rankings * 0.67)
        
        # Count dances in the bottom third of rankings
        for i in range(bottom_third_start, total_rankings):
            if i < len(member.dance_rankings):
                dance_name = member.dance_rankings[i]
                dance_counts[dance_name] += 1

    # Ensure all dances are included, even those with 0 appearances in bottom third
    all_dance_names = {dance.name for dance in st.session_state["dances"] if dance.included}
    for dance_name in all_dance_names:
        if dance_name not in dance_counts:
            dance_counts[dance_name] = 0

    # Create dataframe sorted by frequency (descending)
    if dance_counts:
        chart_data = pd.DataFrame(
            [
                {"dance": dance, "frequency": count}
                for dance, count in dance_counts.most_common()
            ]
        )

        st.subheader("Least Popular Dances")

        # Calculate dynamic height based on number of dances (minimum 30px per dance, minimum 300px total)
        num_dances = len(chart_data)
        chart_height = max(300, num_dances * 30)

        # Create horizontal Altair chart with explicit ordering
        chart = (
            alt.Chart(chart_data)
            .mark_bar()
            .encode(
                x=alt.X("frequency:Q", title="Appearances in Bottom Third"),
                y=alt.Y("dance:N", sort=None, title=None),
                tooltip=["dance", "frequency"],
            )
            .properties(height=chart_height)
        )

        st.altair_chart(chart, use_container_width=True)
    else:
        st.subheader("Dances by Bottom Third Rankings")
        st.info("No dance rankings data available or insufficient ranking data.")
