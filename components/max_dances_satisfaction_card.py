import streamlit as st
from schemas import Matching, Member


def max_dances_satisfaction_card(matching: Matching, members: list[Member]) -> None:
    """
    Display a card showing how many members got at least (max_dances - 2) dances.
    This measures success in giving members who want many dances close to their desired amount.

    Args:
        matching: The matching results containing dancers_to_dances mapping
        members: List of all members with their max_dances preferences
    """
    # Calculate members who got at least (max_dances - 2) dances
    members_satisfied = 0
    total_members = len(members)

    for member in members:
        # Get the number of dances assigned to this member
        assigned_dances = matching.dancers_to_dances.get(member.name, [])
        num_assigned = len(assigned_dances)

        # Check if they got at least (max_dances - 2) dances
        # This means we successfully gave them close to their desired maximum
        min_required_for_satisfaction = max(0, member.max_dances - 2)

        if num_assigned >= min_required_for_satisfaction:
            members_satisfied += 1

    # Calculate percentage
    percentage = (members_satisfied / total_members * 100) if total_members > 0 else 0

    # Display the card
    st.metric(
        label="Within 2 dances of their max",
        value=f"{members_satisfied} / {total_members}",
        delta=f"{percentage:.1f}%",
    )
