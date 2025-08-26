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

    # Create dataframe sorted by frequency (descending)
    if dance_counts:
        chart_data = pd.DataFrame(
            [
                {"dance": dance, "frequency": count}
                for dance, count in dance_counts.most_common()
            ]
        )

        st.subheader("Most Popular Dances")

        # Create horizontal Altair chart with explicit ordering
        chart = (
            alt.Chart(chart_data)
            .mark_bar()
            .encode(
                x=alt.X("frequency:Q", title="Appearances in Top 3"),
                y=alt.Y("dance:N", sort=None, title=None),
                tooltip=["dance", "frequency"],
            )
            .properties(height=400)
        )

        st.altair_chart(chart, use_container_width=True)
    else:
        st.subheader("Dances by Top 3 Rankings")
        st.info("No dance rankings data available.")
