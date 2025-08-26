import streamlit as st
from schemas import Matching, Member


def top3_satisfaction_card(matching: Matching, members: list[Member]) -> None:
    """
    Display a card showing how many members got at least one dance in their top 3 preferences.
    
    Args:
        matching: The matching results containing dancers_to_dances mapping
        members: List of all members with their dance rankings
    """
    # Calculate members who got at least one dance in their top 3
    members_with_top3 = 0
    total_members = len(members)
    
    for member in members:
        # Get the dances assigned to this member
        assigned_dances = matching.dancers_to_dances.get(member.name, [])
        
        # Check if any assigned dance is in their top 3 rankings
        top3_dances = member.dance_rankings[:3] if len(member.dance_rankings) >= 3 else member.dance_rankings
        
        # Check if member got at least one dance from their top 3
        if any(dance in top3_dances for dance in assigned_dances):
            members_with_top3 += 1
    
    # Calculate percentage
    percentage = (members_with_top3 / total_members * 100) if total_members > 0 else 0
    
    # Display the card
    st.metric(
        label="Got at least one dance in their top 3",
        value=f"{members_with_top3} / {total_members}",
        delta=f"{percentage:.1f}%"
    )
