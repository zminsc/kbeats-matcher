import streamlit as st

from schemas import Dance, Member


def update_members_for_dance(dance_idx: int, included: bool) -> None:
    if not st.session_state["members"] or not st.session_state["original_members"]:
        return

    dance: Dance = st.session_state["dances"][dance_idx]
    members: list[Member] = st.session_state["members"]
    if included:
        for member in members:
            original_member: Member = st.session_state["original_members"][member.name]

            # update dance_rankings
            member.dance_rankings = [
                dance_name for dance_name in original_member.dance_rankings
                if dance_name == dance.name
                or st.session_state["dances_index"][dance_name].included
            ]

            # update max_rank
            if dance.name in original_member.dance_rankings:
                dance_idx = original_member.dance_rankings.index(dance.name)
                if dance_idx < original_member.max_rank:
                    member.max_rank += 1
            
            # update dances_willing_to_tl
            if dance.name in original_member.dances_willing_to_tl:
                member.dances_willing_to_tl.add(dance.name)
    else:
        for member in members:
            original_member: Member = st.session_state["original_members"][member.name]

            # update dance_rankings
            member.dance_rankings = [
                dance_name for dance_name in original_member.dance_rankings
                if dance_name != dance.name
                and st.session_state["dances_index"][dance_name].included
            ]

            # update max_rank
            if dance.name in original_member.dance_rankings:
                dance_idx = original_member.dance_rankings.index(dance.name)
                if dance_idx < original_member.max_rank:
                    member.max_rank -= 1
            
            # update dances_willing_to_tl
            if dance.name in member.dances_willing_to_tl:
                member.dances_willing_to_tl.remove(dance.name)

def handle_num_dancers_change(dance_idx: int) -> None:
    key = f"num_dancers_{dance_idx}"
    if key not in st.session_state:
        return
    new_value = st.session_state[key]
    st.session_state["dances"][dance_idx].num_dancers = new_value


def handle_included_change(dance_idx: int) -> None:
    key = f"included_{dance_idx}"
    if key not in st.session_state:
        return
    new_value = st.session_state[key]
    dance = st.session_state["dances"][dance_idx]
    dance.included = new_value
    update_members_for_dance(dance_idx, new_value)


def dance_detail_view() -> None:
    if not st.session_state["dances"]:
        return

    for idx, dance in enumerate(st.session_state["dances"]):
        col1, col2, col3 = st.columns([3, 1, 0.5])
        with col1:
            st.markdown(dance.name)
        with col2:
            st.number_input(
                f"Number of members for {dance.name}",
                min_value=1,
                value=dance.num_dancers,
                key=f"num_dancers_{idx}",
                label_visibility="collapsed",
                on_change=handle_num_dancers_change,
                args=(idx,),
            )
        with col3:
            st.toggle(
                f"Whether {dance.name} is included in the matching",
                value=dance.included,
                key=f"included_{idx}",
                label_visibility="collapsed",
                on_change=handle_included_change,
                args=(idx,),
            )
