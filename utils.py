import re
import pandas as pd


def find_column_match(columns, target_patterns):
    """Find column that matches target patterns case-insensitively"""
    for col in columns:
        col_lower = col.lower()
        for pattern in target_patterns:
            if pattern.lower() in col_lower:
                return col
    return None


def find_max_dances_column(columns):
    """Find 'max dances' column with flexible character matching between 'max' and 'dances'"""
    pattern = r'max\s*.*?\s*dances?'
    for col in columns:
        if re.search(pattern, col.lower()):
            return col
    return None


def extract_ranking_columns(columns):
    """Extract dance ranking columns by finding numbers in square brackets"""
    ranking_pattern = r'\[(\d+)\.?\]'
    ranking_columns = {}
    
    for col in columns:
        match = re.search(ranking_pattern, col)
        if match:
            rank_number = int(match.group(1))
            ranking_columns[rank_number] = col
    
    return ranking_columns


def find_tl_column(columns):
    """Find column containing 'TL' (case-sensitive)"""
    for col in columns:
        if 'TL' in col:
            return col
    return None


def find_considered_column(columns):
    """Find column containing 'considered' (case-insensitive)"""
    for col in columns:
        if 'considered' in col.lower():
            return col
    return None


def parse_tl_songs(df, name_col, tl_col):
    """Parse TL songs for each dancer from comma-delimited values"""
    dancers_tl = {}
    
    if tl_col is None:
        return dancers_tl
    
    for _, row in df.iterrows():
        dancer_name = row[name_col]
        tl_songs_raw = row[tl_col]
        
        if pd.notna(tl_songs_raw) and str(tl_songs_raw).strip():
            tl_songs = [song.strip() for song in str(tl_songs_raw).split(',') if song.strip()]
            dancers_tl[dancer_name] = tl_songs
        else:
            dancers_tl[dancer_name] = []
    
    return dancers_tl


def parse_max_considered_ranks(df, name_col, considered_col):
    """Parse max considered ranks for each dancer"""
    dancers_max_rank = {}
    
    if considered_col is None:
        return dancers_max_rank
    
    for _, row in df.iterrows():
        dancer_name = row[name_col]
        max_rank_raw = row[considered_col]
        
        if pd.notna(max_rank_raw) and str(max_rank_raw).strip():
            try:
                max_rank = int(str(max_rank_raw).strip())
                dancers_max_rank[dancer_name] = max_rank
            except ValueError:
                dancers_max_rank[dancer_name] = None
        else:
            dancers_max_rank[dancer_name] = None
    
    return dancers_max_rank


def filter_rankings_by_max_considered(dancers_rankings, dancers_max_rank):
    """Filter rankings based on max considered rank for each dancer"""
    filtered_rankings = {}
    
    for dancer, rankings in dancers_rankings.items():
        max_rank = dancers_max_rank.get(dancer)
        if max_rank is None:
            # No limit specified, keep all rankings
            filtered_rankings[dancer] = rankings.copy()
        else:
            # Filter out rankings beyond max considered rank
            filtered_rankings[dancer] = {
                rank: song for rank, song in rankings.items()
                if rank <= max_rank
            }
    
    return filtered_rankings


def parse_dancer_rankings(df, name_col, ranking_columns):
    """Parse dance rankings for each dancer"""
    dancers_rankings = {}
    
    for _, row in df.iterrows():
        dancer_name = row[name_col]
        rankings = {}
        
        for rank, col in ranking_columns.items():
            dance = row[col]
            if pd.notna(dance) and dance.strip():
                rankings[rank] = dance.strip()
        
        dancers_rankings[dancer_name] = rankings
    
    return dancers_rankings


def perform_matching(dancers_rankings, dancers_tl, edited_data, matching_config):
    """Perform the dance matching algorithm"""
    
    # Convert edited_data to dictionary for easier access
    dancer_info = {}
    for _, row in edited_data.iterrows():
        dancer_info[row['Name']] = {
            'max_dances': int(row['Max Dances']),
            'seniority': row['Seniority']
        }
    
    # Initialize results
    song_assignments = {}
    dancer_assignments = {}
    
    # Get configuration
    least_max_songs = matching_config['least_max_songs']
    song_configs = matching_config['song_configs']
    
    # Initialize song assignments
    for song in song_configs.keys():
        song_assignments[song] = {
            'dancers': [],
            'tls': [],
            'tls_needed': song_configs[song]['tls_needed'],
            'dancers_per_song': song_configs[song]['dancers_per_song']
        }
    
    # Initialize dancer assignments
    for dancer in dancers_rankings.keys():
        dancer_assignments[dancer] = []
    
    # Priority placement for dancers with low max songs
    priority_dancers = [
        dancer for dancer, info in dancer_info.items() 
        if info['max_dances'] <= least_max_songs
    ]
    
    # Sort priority dancers by max songs (lowest first)
    priority_dancers.sort(key=lambda d: dancer_info[d]['max_dances'])
    
    # Phase 1: Priority placement
    for rank in range(1, 17):  # Up to 16 rankings
        for dancer in priority_dancers:
            if len(dancer_assignments[dancer]) >= dancer_info[dancer]['max_dances']:
                continue
                
            rankings = dancers_rankings.get(dancer, {})
            if rank not in rankings:
                continue
                
            song = rankings[rank]
            if song not in song_assignments:
                continue
                
            # Check if song has space
            if len(song_assignments[song]['dancers']) < song_assignments[song]['dancers_per_song']:
                # Check if someone with higher priority (lower rank) wants this song
                higher_priority_conflict = False
                for other_dancer in priority_dancers:
                    if other_dancer == dancer:
                        continue
                    if len(dancer_assignments[other_dancer]) >= dancer_info[other_dancer]['max_dances']:
                        continue
                    other_rankings = dancers_rankings.get(other_dancer, {})
                    for other_rank in range(1, rank):
                        if other_rank in other_rankings and other_rankings[other_rank] == song:
                            if len(song_assignments[song]['dancers']) >= song_assignments[song]['dancers_per_song'] - 1:
                                higher_priority_conflict = True
                                break
                    if higher_priority_conflict:
                        break
                
                if not higher_priority_conflict:
                    song_assignments[song]['dancers'].append(dancer)
                    dancer_assignments[dancer].append(song)
    
    # Phase 2: General placement for remaining dancers
    remaining_dancers = [
        dancer for dancer in dancers_rankings.keys() 
        if dancer not in priority_dancers
    ]
    
    # Sort by seniority (Senior > Junior > Sophomore > Freshman)
    seniority_order = {'Senior': 4, 'Junior': 3, 'Sophomore': 2, 'Freshman': 1}
    remaining_dancers.sort(key=lambda d: seniority_order.get(dancer_info[d]['seniority'], 0), reverse=True)
    
    for rank in range(1, 17):
        for dancer in remaining_dancers:
            if len(dancer_assignments[dancer]) >= dancer_info[dancer]['max_dances']:
                continue
                
            rankings = dancers_rankings.get(dancer, {})
            if rank not in rankings:
                continue
                
            song = rankings[rank]
            if song not in song_assignments:
                continue
                
            # Check if song has space
            if len(song_assignments[song]['dancers']) < song_assignments[song]['dancers_per_song']:
                song_assignments[song]['dancers'].append(dancer)
                dancer_assignments[dancer].append(song)
    
    # Phase 3: Assign TLs
    for song, assignment in song_assignments.items():
        tls_needed = assignment['tls_needed']
        potential_tls = []
        
        # Get dancers in this song who are willing to TL
        for dancer in assignment['dancers']:
            dancer_tl_songs = dancers_tl.get(dancer, [])
            # Check if any TL song matches this song (case-insensitive partial match)
            for tl_song in dancer_tl_songs:
                if tl_song.lower() in song.lower() or song.lower() in tl_song.lower():
                    potential_tls.append(dancer)
                    break
        
        # Sort potential TLs by seniority
        potential_tls.sort(key=lambda d: seniority_order.get(dancer_info[d]['seniority'], 0), reverse=True)
        
        # Assign TLs up to the needed amount
        assignment['tls'] = potential_tls[:tls_needed]
    
    return song_assignments, dancer_assignments