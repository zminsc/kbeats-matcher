import streamlit as st
import pandas as pd
from utils import find_column_match, find_max_dances_column, extract_ranking_columns, parse_dancer_rankings, find_tl_column, parse_tl_songs, perform_matching, find_considered_column, parse_max_considered_ranks, filter_rankings_by_max_considered

st.title("K-Beats Dance Matcher")
st.write("Upload a CSV file to view dance matching data")

uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    
    # Find the required columns with case-insensitive matching
    name_col = find_column_match(df.columns, ['name'])
    seniority_col = find_column_match(df.columns, ['seniority'])
    max_dances_col = find_max_dances_column(df.columns)
    
    if not all([name_col, seniority_col, max_dances_col]):
        st.error("Could not find required columns. Looking for: 'name', 'seniority', and 'max dances'")
        st.write("Available columns:", list(df.columns))
    else:
        st.success(f"Found columns: {name_col}, {seniority_col}, {max_dances_col}")
        
        # Extract ranking columns and parse rankings
        ranking_columns = extract_ranking_columns(df.columns)
        dancers_rankings = parse_dancer_rankings(df, name_col, ranking_columns)
        
        # Find TL and considered columns but don't parse yet
        tl_col_suggestion = find_tl_column(df.columns)
        considered_col_suggestion = find_considered_column(df.columns)
        
        # Store data in session state for later use
        st.session_state['dancers_rankings'] = dancers_rankings
        st.session_state['ranking_columns'] = ranking_columns
        st.session_state['df'] = df
        st.session_state['name_col'] = name_col
        
        st.info(f"Found {len(ranking_columns)} ranking columns")
        
        # Extract the relevant data
        relevant_data = df[[name_col, seniority_col, max_dances_col]].copy()
        relevant_data.columns = ['Name', 'Seniority', 'Max Dances']
        
        st.subheader("Confirm Data")
        st.write("Please review and confirm the data below.")
        
        # Column selections
        col1, col2 = st.columns(2)
        
        with col1:
            # TL Column Selection
            st.write("**Select TL Column:**")
            tl_column_options = ["None"] + list(df.columns)
            tl_col_index = 0
            if tl_col_suggestion and tl_col_suggestion in tl_column_options:
                tl_col_index = tl_column_options.index(tl_col_suggestion)
            
            selected_tl_col = st.selectbox(
                "TL preferences column:",
                options=tl_column_options,
                index=tl_col_index,
                help="Select the column that contains TL (team lead) preferences"
            )
        
        with col2:
            # Considered Column Selection
            st.write("**Select Max Considered Rank Column:**")
            considered_column_options = ["None"] + list(df.columns)
            considered_col_index = 0
            if considered_col_suggestion and considered_col_suggestion in considered_column_options:
                considered_col_index = considered_column_options.index(considered_col_suggestion)
            
            selected_considered_col = st.selectbox(
                "Max considered rank column:",
                options=considered_column_options,
                index=considered_col_index,
                help="Select the column that contains the maximum rank each dancer wants to be considered for"
            )
        
        # Create editable dataframe with name column enabled
        edited_data = st.data_editor(
            relevant_data,
            column_config={
                "Name": st.column_config.TextColumn(
                    "Name",
                    help="Name field"
                ),
                "Seniority": st.column_config.SelectboxColumn(
                    "Seniority",
                    options=["Freshman", "Sophomore", "Junior", "Senior"],
                    help="Select the seniority level"
                ),
                "Max Dances": st.column_config.NumberColumn(
                    "Max Dances",
                    help="Maximum number of dances",
                    min_value=1,
                    max_value=20,
                    step=1
                )
            },
            use_container_width=True,
            hide_index=True
        )
        
        # Check if data has been confirmed before
        data_confirmed = st.session_state.get('data_confirmed', False)
        
        if st.button("Confirm Data") or data_confirmed:
            if not data_confirmed:
                # First time confirmation
                st.session_state['data_confirmed'] = True
                st.session_state['confirmed_data'] = edited_data.copy()
                
                # Now parse TL songs and max considered ranks after confirmation
                if selected_tl_col != "None":
                    dancers_tl = parse_tl_songs(st.session_state['df'], st.session_state['name_col'], selected_tl_col)
                    st.session_state['dancers_tl'] = dancers_tl
                    st.session_state['tl_column'] = selected_tl_col
                else:
                    st.session_state['dancers_tl'] = {}
                    st.session_state['tl_column'] = None
                
                if selected_considered_col != "None":
                    dancers_max_rank = parse_max_considered_ranks(st.session_state['df'], st.session_state['name_col'], selected_considered_col)
                    st.session_state['dancers_max_rank'] = dancers_max_rank
                    st.session_state['considered_column'] = selected_considered_col
                else:
                    st.session_state['dancers_max_rank'] = {}
                    st.session_state['considered_column'] = None
                
                # Filter rankings based on max considered ranks
                filtered_rankings = filter_rankings_by_max_considered(
                    st.session_state['dancers_rankings'],
                    st.session_state.get('dancers_max_rank', {})
                )
                st.session_state['filtered_rankings'] = filtered_rankings
            
            # Use confirmed data
            confirmed_data = st.session_state.get('confirmed_data', edited_data)
            
            st.success("Data confirmed!")
            st.write("Confirmed data:")
            st.dataframe(confirmed_data, use_container_width=True)
            
            # Display dance rankings and TL songs for each dancer
            st.subheader("Dance Rankings and TL Preferences")
            if 'dancers_rankings' in st.session_state:
                filtered_rankings = st.session_state.get('filtered_rankings', st.session_state['dancers_rankings'])
                dancers_max_rank = st.session_state.get('dancers_max_rank', {})
                
                for dancer, original_rankings in st.session_state['dancers_rankings'].items():
                    filtered_dancer_rankings = filtered_rankings.get(dancer, {})
                    tl_songs = st.session_state.get('dancers_tl', {}).get(dancer, [])
                    max_rank = dancers_max_rank.get(dancer)
                    
                    max_rank_text = f" (max rank: {max_rank})" if max_rank else ""
                    with st.expander(f"{dancer}'s Preferences{max_rank_text}"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write("**Rankings (after filtering):**")
                            if filtered_dancer_rankings:
                                for rank, dance in sorted(filtered_dancer_rankings.items()):
                                    st.write(f"**{rank}.** {dance}")
                            else:
                                st.write("No rankings found")
                        
                        with col2:
                            st.write("**Willing to TL:**")
                            if tl_songs:
                                for song in tl_songs:
                                    st.write(f"• {song}")
                            else:
                                st.write("No TL preferences")
            
            # Matching Configuration
            st.subheader("Matching Configuration")
            
            # Get unique songs from filtered rankings
            all_songs = set()
            filtered_rankings = st.session_state.get('filtered_rankings', st.session_state['dancers_rankings'])
            for rankings in filtered_rankings.values():
                all_songs.update(rankings.values())
            all_songs = sorted(list(all_songs))
            
            least_max_songs = st.number_input(
                "Least Max Songs Threshold",
                min_value=1,
                max_value=10,
                value=2,
                help="Dancers with max songs <= this number get priority placement"
            )
            
            # Song configuration
            st.write("**Song Configuration:**")
            song_configs = {}
            
            for i, song in enumerate(all_songs):
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    st.write(f"**{song}**")
                with col2:
                    dancers_per_song = st.number_input(
                        f"Dancers",
                        min_value=1,
                        max_value=20,
                        value=8,
                        key=f"dancers_{i}",
                        help=f"Number of dancers for {song}"
                    )
                with col3:
                    tls_needed = st.number_input(
                        f"TLs",
                        min_value=0,
                        max_value=5,
                        value=1,
                        key=f"tl_{i}",
                        help=f"Number of team leaders for {song}"
                    )
                song_configs[song] = {
                    'tls_needed': tls_needed,
                    'dancers_per_song': dancers_per_song
                }
            
            # Store configuration in session state
            st.session_state['matching_config'] = {
                'least_max_songs': least_max_songs,
                'song_configs': song_configs
            }
            
            if st.button("Match", type="primary"):
                st.success("Starting matching process...")
                
                # Perform matching using filtered rankings
                song_assignments, dancer_assignments = perform_matching(
                    st.session_state.get('filtered_rankings', st.session_state['dancers_rankings']),
                    st.session_state.get('dancers_tl', {}),
                    confirmed_data,
                    st.session_state['matching_config']
                )
                
                # Store results in session state
                st.session_state['song_assignments'] = song_assignments
                st.session_state['dancer_assignments'] = dancer_assignments
                st.session_state['just_matched'] = True
                
                st.success("Matching completed!")
                
                # Display results
                st.subheader("Matching Results")
                
                # Song assignments table
                st.write("**Songs and Dancers:**")
                song_data = []
                for song, assignment in song_assignments.items():
                    song_data.append({
                        'Song': song,
                        'Dancers': ', '.join(assignment['dancers']),
                        'Team Leaders': ', '.join(assignment['tls']) if assignment['tls'] else 'None'
                    })
                
                song_df = pd.DataFrame(song_data)
                st.dataframe(song_df, use_container_width=True)
                
                # Dancer assignments table
                st.write("**Dancers and Songs:**")
                dancer_data = []
                for dancer, songs in dancer_assignments.items():
                    max_dances = int(confirmed_data[confirmed_data['Name'] == dancer]['Max Dances'].iloc[0])
                    dancer_data.append({
                        'Dancer': dancer,
                        'Number of Dances': len(songs),
                        'Max Dances': max_dances,
                        'Songs': ', '.join(songs)
                    })
                
                dancer_df = pd.DataFrame(dancer_data)
                st.dataframe(dancer_df, use_container_width=True)
        
        # Display previous results if they exist
        if 'song_assignments' in st.session_state and 'dancer_assignments' in st.session_state:
            if not st.session_state.get('just_matched', False):
                st.subheader("Previous Matching Results")
                st.info("Update the configuration above and click 'Match' again to re-run with new settings.")
                
                # Previous song assignments table
                st.write("**Previous Songs and Dancers:**")
                prev_song_data = []
                for song, assignment in st.session_state['song_assignments'].items():
                    prev_song_data.append({
                        'Song': song,
                        'Dancers': ', '.join(assignment['dancers']),
                        'Team Leaders': ', '.join(assignment['tls']) if assignment['tls'] else 'None'
                    })
                
                prev_song_df = pd.DataFrame(prev_song_data)
                st.dataframe(prev_song_df, use_container_width=True)
                
                # Previous dancer assignments table
                st.write("**Previous Dancers and Songs:**")
                prev_dancer_data = []
                for dancer, songs in st.session_state['dancer_assignments'].items():
                    # Get max dances from confirmed data
                    dancer_row = confirmed_data[confirmed_data['Name'] == dancer]
                    if not dancer_row.empty:
                        max_dances = int(dancer_row['Max Dances'].iloc[0])
                        prev_dancer_data.append({
                            'Dancer': dancer,
                            'Number of Dances': len(songs),
                            'Max Dances': max_dances,
                            'Songs': ', '.join(songs)
                        })
                
                if prev_dancer_data:
                    prev_dancer_df = pd.DataFrame(prev_dancer_data)
                    st.dataframe(prev_dancer_df, use_container_width=True)
        
        # Reset the just_matched flag
        if 'just_matched' in st.session_state:
            st.session_state['just_matched'] = False
