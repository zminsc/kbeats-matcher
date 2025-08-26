import streamlit as st
import textwrap
from schemas import Member


def update_selected_member_lateness_score() -> None:
    if "selected_member_idx" not in st.session_state:
        return
    idx = st.session_state["selected_member_idx"]
    selected_member: Member = st.session_state["members"][idx]
    selected_member.lateness_score = st.session_state[
        f"lateness_{selected_member.name.lower().replace(' ', '_')}"
    ]


def update_selected_member_busyness_score() -> None:
    if "selected_member_idx" not in st.session_state:
        return
    idx = st.session_state["selected_member_idx"]
    selected_member: Member = st.session_state["members"][idx]
    selected_member.busyness_score = st.session_state[
        f"busyness_{selected_member.name.lower().replace(' ', '_')}"
    ]


def member_detail_view() -> None:
    if not st.session_state["members"]:
        return

    col1, col2 = st.columns([1, 3])
    with col1:
        st.subheader("Members")
        st.session_state["selected_member_idx"] = st.radio(
            "Select a member:",
            range(len(st.session_state["members"])),
            index=0,
            format_func=lambda i: st.session_state["members"][i].name,
            key="member_selector",
        )
    with col2:
        selected_member: Member = st.session_state["members"][
            st.session_state["selected_member_idx"]
        ]

        st.subheader(f"{selected_member.name}")
        st.markdown(
            textwrap.dedent(f"""
                * {selected_member.seniority.value.capitalize()}
                * Max Dances: {selected_member.max_dances}
                * Max Rank: {selected_member.max_rank}
            """).strip()
        )

        st.markdown("### Score adjustments:")
        st.number_input(
            "Lateness score",
            min_value=0,
            value=selected_member.lateness_score,
            key="lateness_" + "_".join(selected_member.name.lower().split()),
            on_change=update_selected_member_lateness_score,
        )
        st.number_input(
            "Busyness score",
            min_value=0,
            value=selected_member.busyness_score,
            key="busyness_" + "_".join(selected_member.name.lower().split()),
            on_change=update_selected_member_busyness_score,
        )

        if selected_member.dances_willing_to_tl:
            st.markdown("### Willing to TL:")
            st.markdown(
                "\n".join(
                    sorted(
                        [
                            f"* {dance_name}"
                            for dance_name in selected_member.dances_willing_to_tl
                        ]
                    )
                )
            )

        if selected_member.allowed_co_tls:
            st.markdown("### Would be co-TLs with:")
            st.markdown(
                "\n".join([f"* {co_tl}" for co_tl in selected_member.allowed_co_tls])
            )

        st.markdown("### Dance rankings (up to max rank)")
        if selected_member.dance_rankings:
            truncated_rankings = selected_member.dance_rankings[
                : selected_member.max_rank
            ]
            st.markdown(
                "\n".join(
                    [
                        f"{i + 1}. {dance_name}"
                        for i, dance_name in enumerate(truncated_rankings)
                    ]
                )
            )
