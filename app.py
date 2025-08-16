import streamlit as st
import pandas as pd
from services import Matcher
from utils import parse_candidates_csv, parse_dances_csv, adjust_rankings_after_exclusion, generate_dance_based_csv, generate_dancer_based_csv

# Initialize session state
if 'parsed_candidates' not in st.session_state:
    st.session_state.parsed_candidates = None
if 'parsed_dances' not in st.session_state:
    st.session_state.parsed_dances = None

st.title("K-Beats Dance Matcher")

# Navigation
tab1, tab2 = st.tabs(["Setup", "Matching"])

with tab1:
    st.header("Setup")
    
    # Side-by-side file uploaders
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Rankings CSV")
        rankings_file = st.file_uploader("Upload rankings CSV", type=['csv'], key="rankings")
        
    with col2:
        st.subheader("Dances CSV")
        dances_file = st.file_uploader("Upload dances CSV", type=['csv'], key="dances")
    
    # Process uploaded files
    if rankings_file and dances_file:
        try:
            candidates = parse_candidates_csv(rankings_file)
            dances = parse_dances_csv(dances_file)
            
            # Store in session state
            st.session_state.parsed_candidates = candidates
            st.session_state.parsed_dances = dances
            
            st.success("Files uploaded successfully!")
            
            # Master pane - list of members
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.subheader("Team Members")
                
                # Initialize selected member in session state if not exists
                if 'selected_member_index' not in st.session_state:
                    st.session_state.selected_member_index = 0
                
                # Use radio buttons for better visibility of all members
                selected_index = st.radio(
                    "Select a member:",
                    range(len(candidates)),
                    format_func=lambda i: candidates[i].name,
                    key="member_selector"
                )
                
                selected_member = candidates[selected_index].name
            
            with col2:
                if selected_member:
                    # Find the selected candidate
                    candidate = next(c for c in candidates if c.name == selected_member)
                    
                    st.subheader(f"{candidate.name}")
                    
                    # Display candidate details
                    col2a, col2b = st.columns(2)
                    
                    with col2a:
                        st.markdown(f"""
* {candidate.seniority.value.capitalize()}
* Max Dances: {candidate.max_dances}
* Max Rank: {candidate.max_rank}
""".strip())
                    
                    with col2b:
                        if candidate.allowed_co_tls:
                            st.write("**Allowed Co-TLs:**")
                            for co_tl in candidate.allowed_co_tls:
                                st.write(f"- {co_tl}")
                    
                    # Score adjustments section
                    st.markdown("### Score Adjustments")
                    col_lat, col_busy = st.columns(2)
                    
                    with col_lat:
                        new_lateness = st.number_input(
                            "Lateness Score",
                            min_value=-10,
                            max_value=10,
                            value=candidate.lateness_score,
                            help="Penalty for being late (-10 to 10)",
                            key=f"lateness_{candidate.name}"
                        )
                    
                    with col_busy:
                        new_busyness = st.number_input(
                            "Busyness Score", 
                            min_value=-10,
                            max_value=10,
                            value=candidate.busyness_score,
                            help="Penalty for being busy (-10 to 10)",
                            key=f"busyness_{candidate.name}"
                        )
                    
                    # Update the candidate scores if changed
                    if new_lateness != candidate.lateness_score or new_busyness != candidate.busyness_score:
                        # Find and update the candidate in the stored list
                        for i, c in enumerate(st.session_state.parsed_candidates):
                            if c.name == candidate.name:
                                st.session_state.parsed_candidates[i].lateness_score = new_lateness
                                st.session_state.parsed_candidates[i].busyness_score = new_busyness
                                break
                    
                    # Willing to TL section
                    if candidate.dances_willing_to_tl:
                        st.markdown("### Willing to TL")
                        willing_to_tl_list = "\n".join([f"* {dance}" for dance in candidate.dances_willing_to_tl])
                        st.markdown(willing_to_tl_list)
                    else:
                        st.markdown("### Willing to TL")
                        st.write("None")
                    
                    # Song rankings
                    st.markdown("### Song Rankings")
                    if candidate.dance_rankings:
                        rankings_list = "\n".join([
                            f"{rank}. {dance}" 
                            for rank, dance in sorted(candidate.dance_rankings.items())
                        ])
                        st.markdown(rankings_list)
                    else:
                        st.write("No rankings provided")
                        
        except Exception as e:
            st.error(f"Error processing files: {e}")

with tab2:
    st.header("Matching")
    
    if st.session_state.parsed_candidates and st.session_state.parsed_dances:
        # Dance exclusion section
        st.subheader("Exclude Dances")
        st.write("Select dances to exclude from matching. Rankings will be automatically adjusted.")
        
        # Get all dance names from the parsed dances
        all_dance_names = [dance.name for dance in st.session_state.parsed_dances]
        
        # Multi-select for excluding dances
        excluded_dances = st.multiselect(
            "Dances to exclude:",
            options=all_dance_names,
            key="excluded_dances"
        )
        
        if excluded_dances:
            st.info(f"Excluding {len(excluded_dances)} dance(s): {', '.join(excluded_dances)}")
        
        st.divider()
        
        # Add button to run matcher
        if st.button("Run Matcher", type="primary"):
            try:
                import random
                random.seed()
                
                # Apply dance exclusions and adjust rankings
                excluded_dances_set = set(excluded_dances) if excluded_dances else set()
                
                # Filter out excluded dances from the dances list
                filtered_dances = [
                    dance for dance in st.session_state.parsed_dances 
                    if dance.name not in excluded_dances_set
                ]
                
                # Adjust candidate rankings to account for excluded dances
                adjusted_candidates = adjust_rankings_after_exclusion(
                    st.session_state.parsed_candidates, 
                    excluded_dances_set
                )
                
                matcher = Matcher(adjusted_candidates, filtered_dances)
                matching = matcher.run()
                
                # Display results
                st.subheader("Matching Results")
                
                # Generate CSV data
                dance_csv = generate_dance_based_csv(matching, filtered_dances)
                dancer_csv = generate_dancer_based_csv(matching, adjusted_candidates)
                
                # Dance assignments table with download
                st.write("### Dance Assignments")
                st.dataframe(dance_csv)
                
                # Dancer assignments table with download
                st.write("### Dancer Assignments")
                st.dataframe(dancer_csv)
                
            except Exception as e:
                st.error(f"Error running matcher: {e}")
    else:
        st.warning("Please upload CSV files in the Setup tab first.")