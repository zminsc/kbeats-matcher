import pandas as pd
import re
from schemas import Candidate, Dance, Matching
from enums import Seniority
from copy import deepcopy

def parse_candidates_csv(uploaded_file) -> list[Candidate]:
    df = pd.read_csv(uploaded_file)
    candidates = []
    
    for _, row in df.iterrows():
        # Dynamically find ranking columns by looking for [i.] pattern
        dance_rankings = {}
        for col in df.columns:
            match = re.search(r'\[(\d+)\.\]', col)
            if match:
                rank = int(match.group(1))
                if pd.notna(row[col]):
                    dance_rankings[rank] = row[col]
        
        # Parse TL preferences (comma-separated values)
        tl_dances = set()
        if 'TL' in df.columns and pd.notna(row['TL']) and row['TL'].strip():
            tl_dances = {dance.strip() for dance in row['TL'].split(',')}
        
        candidate = Candidate(
            name=row['Name'],
            seniority=Seniority(row['Seniority'].upper()),
            max_dances=int(row['Max Dances']),
            max_rank=int(row['Max Rank']),
            dance_rankings=dance_rankings,
            dances_willing_to_tl=tl_dances
        )
        candidates.append(candidate)
    
    return candidates

def parse_dances_csv(uploaded_file) -> list[Dance]:
    df = pd.read_csv(uploaded_file)
    dances = []
    
    for _, row in df.iterrows():
        dance = Dance(
            name=row['Dance'],
            num_dancers=int(row['No. of Dancers'])
        )
        dances.append(dance)
    
    return dances


def adjust_rankings_after_exclusion(candidates: list[Candidate], excluded_dances: set[str]) -> list[Candidate]:
    """
    Adjust candidate rankings after excluding dances.
    When dances are excluded, shift up rankings of all songs after excluded dances.
    """
    if not excluded_dances:
        return candidates
    
    adjusted_candidates = []
    
    for candidate in candidates:
        adjusted_candidate = deepcopy(candidate)
        new_rankings = {}
        
        # Build list of non-excluded dances in ranking order
        ranked_dances = []
        for rank in sorted(candidate.dance_rankings.keys()):
            dance = candidate.dance_rankings[rank]
            if dance not in excluded_dances:
                ranked_dances.append(dance)
        
        # Reassign rankings starting from 1
        for new_rank, dance in enumerate(ranked_dances, 1):
            new_rankings[new_rank] = dance
        
        adjusted_candidate.dance_rankings = new_rankings
        adjusted_candidates.append(adjusted_candidate)
    
    return adjusted_candidates


def generate_dance_based_csv(matching: Matching, dances: list[Dance]) -> pd.DataFrame:
    """
    Generate dance-based CSV with TL names bolded.
    Ordered by num_dancers descending for each dance.
    Each dancer appears in a separate column.
    """
    dance_data = []
    
    # Sort dances by num_dancers descending
    sorted_dances = sorted(dances, key=lambda d: d.num_dancers, reverse=True)
    
    # Find maximum number of dancers to determine column count
    max_dancers = max(len(matching.dances_to_dancers.get(dance.name, [])) for dance in dances)
    
    for dance in sorted_dances:
        dance_name = dance.name
        dancers = matching.dances_to_dancers.get(dance_name, [])
        tls = matching.dance_tls.get(dance_name, [])
        
        # Create row data with bolded dance name and dancer count
        formatted_dance_name = f"**{dance_name}** ({dance.num_dancers})"
        row_data = {"Dance": formatted_dance_name}
        
        # Add each dancer in separate columns, bolding TLs
        for i, dancer in enumerate(dancers):
            col_name = "" if i == 0 else f" " * (i)  # Empty or spaces for unique keys
            if dancer in tls:
                row_data[col_name] = f"**{dancer}**"
            else:
                row_data[col_name] = dancer
        
        # Fill empty columns for dances with fewer dancers
        for i in range(len(dancers), max_dancers):
            col_name = f" " * i if i > 0 else ""
            row_data[col_name] = ""
        
        dance_data.append(row_data)
    
    return pd.DataFrame(dance_data)


def generate_dancer_based_csv(matching: Matching, candidates: list[Candidate]) -> pd.DataFrame:
    """
    Generate dancer-based CSV showing dances per dancer.
    Each dance appears in a separate column.
    """
    dancer_data = []
    
    # Create lookup for max_dances by dancer name
    max_dances_lookup = {candidate.name: candidate.max_dances for candidate in candidates}
    
    # Find maximum number of dances to determine column count
    max_dances_count = max(len(dances) for dances in matching.dancers_to_dances.values()) if matching.dancers_to_dances else 0
    
    for dancer, dances in sorted(matching.dancers_to_dances.items()):
        # Get max dances for this dancer
        dancer_max_dances = max_dances_lookup.get(dancer, 0)
        num_dances = len(dances)
        
        # Create row data with bolded dancer name and dance count
        formatted_dancer_name = f"**{dancer}** ({num_dances}/{dancer_max_dances})"
        row_data = {"Dancer": formatted_dancer_name}
        
        # Add each dance in separate columns
        for i, dance in enumerate(dances):
            col_name = "" if i == 0 else f" " * (i)  # Empty or spaces for unique keys
            row_data[col_name] = dance
        
        # Fill empty columns for dancers with fewer dances
        for i in range(len(dances), max_dances_count):
            col_name = f" " * i if i > 0 else ""
            row_data[col_name] = ""
        
        dancer_data.append(row_data)
    
    return pd.DataFrame(dancer_data)