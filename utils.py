import pandas as pd
import re
import streamlit as st

from streamlit.runtime.uploaded_file_manager import UploadedFile
from enums import Seniority
from schemas import Member, Dance, Matching, TLMatching
from copy import deepcopy


@st.cache_data
def process_rankings_csv(rankings_csv: UploadedFile) -> list[Member]:
    """
    Take a rankings CSV file and extract information about members.
    This CSV file is exported from a Google Sheets of Google Form
    responses for the following form: https://forms.gle/Mqfxd39KmzxE1SQUA

    This CSV file contains, for each member, basic information like name,
    seniority, max dances, and max rank.

    As well as their dance rankings, songs they're interested in TL-ing,
    and people they're willing to co-TL with.

    Args:
        rankings_csv: The CSV file of rankings and other information from the Google Form.

    Returns:
        A list of Member objects, representing each member in the CSV file.
    """
    df = pd.read_csv(rankings_csv)
    members: list[Member] = []

    def extract_dance_rankings(row: pd.Series, max_rank: int) -> list[str]:
        dance_rankings_dict = {}
        pattern = re.compile(r"Put your rankings here!\s*\[(\d+)\]")
        for col in row.index:
            match = pattern.search(col)
            if not match:
                continue
            dance_name = str(row[col])
            if not dance_name:
                continue
            rank = int(match.group(1))
            dance_rankings_dict[rank] = dance_name
        sorted_rankings = sorted(dance_rankings_dict.items())
        return [dance_name for _, dance_name in sorted_rankings[:max_rank]]

    def extract_dances_willing_to_tl(
        row: pd.Series, dance_rankings: list[str]
    ) -> set[str]:
        # not interested in TL-ing
        tl_interest = row["Are you interested in TL-ing any dances?"]
        if tl_interest == "No":
            return set()

        # willing to TL all
        tl_preference = row["Which dances are you interested in TL-ing?"]
        if tl_preference == "Any dance I'm in":
            return set(dance_rankings)

        # willing to TL specific dances
        specific_dances = set()
        dance_selection = row[
            'If you answered "Specific dances" to the question above, pick them here:'
        ]
        dance_names = [name.strip() for name in dance_selection.split(",")]
        specific_dances.update(dance_names)
        return specific_dances

    def extract_allowed_co_tls(row: pd.Series, all_member_names: list[str]) -> set[str]:
        # not interested in TL-ing
        tl_interest = row["Are you interested in TL-ing any dances?"]
        if tl_interest == "No":
            return set()

        # not willing to co-TL
        co_tl_willingness = row["Are you willing to co-TL?"]
        if co_tl_willingness == "No":
            return set()

        # willing to co-TL with anyone
        if co_tl_willingness == "Yes, with anyone":
            return set(all_member_names)

        # willing to co-TL with specific people
        specific_co_tls = set()
        co_tl_selection = row[
            'If you answered "Yes, with specific people" to the question above, pick them here:'
        ]
        co_tl_names = [name for name in co_tl_selection.split(",")]
        specific_co_tls.update(co_tl_names)
        return specific_co_tls

    all_member_names = [row["Name"] for _, row in df.iterrows()]

    for _, row in df.iterrows():
        name = str(row["Name"])
        seniority = Seniority[row["Seniority"].upper().replace(" ", "_")]
        max_dances = int(row["Max Dances"])
        max_rank = int(row["Max Rank"])
        max_tl = int(row["Max TL"]) if not pd.isna(row["Max TL"]) else 0

        dance_rankings = extract_dance_rankings(row, max_rank)
        dances_willing_to_tl = extract_dances_willing_to_tl(row, dance_rankings)
        allowed_co_tls = extract_allowed_co_tls(row, all_member_names)

        member = Member(
            name=name,
            seniority=seniority,
            max_dances=max_dances,
            max_rank=max_rank,
            max_tl=max_tl,
            dance_rankings=dance_rankings,
            dances_willing_to_tl=dances_willing_to_tl,
            allowed_co_tls=allowed_co_tls,
        )
        members.append(member)

    return members


@st.cache_data
def process_dances_csv(dances_csv: UploadedFile) -> list[Dance]:
    df = pd.read_csv(dances_csv)
    dances = []

    for _, row in df.iterrows():
        name = str(row["Dance"])
        num_dancers = int(row["No. of Dancers"])

        dance = Dance(name=name, num_dancers=num_dancers)
        dances.append(dance)

    return dances


def filter_member_rankings_by_valid_dances(
    members: list[Member], valid_dances: set[str]
) -> list[Member]:
    """
    filters member dance rankings to only include dances that exist in the valid dances set.
    also filters dances_willing_to_tl to only include valid dances.

    Args:
        members: list of Member objects to filter
        valid_dances: set of valid dance names from dances.csv

    Returns:
        list of Member objects with filtered dance rankings
    """
    filtered_members = []

    for member in members:
        # filter dance rankings to only include valid dances
        filtered_dance_rankings = [
            dance for dance in member.dance_rankings if dance in valid_dances
        ]

        # filter dances willing to TL to only include valid dances
        filtered_dances_willing_to_tl = {
            dance for dance in member.dances_willing_to_tl if dance in valid_dances
        }

        # create new member with filtered data
        filtered_member = Member(
            name=member.name,
            seniority=member.seniority,
            max_dances=member.max_dances,
            max_rank=member.max_rank,
            max_tl=member.max_tl,
            dance_rankings=filtered_dance_rankings,
            dances_willing_to_tl=filtered_dances_willing_to_tl,
            allowed_co_tls=member.allowed_co_tls,
            lateness_score=member.lateness_score,
            busyness_score=member.busyness_score,
        )
        filtered_members.append(filtered_member)

    return filtered_members


def generate_dance_based_csv(
    matching: Matching, dances: list[Dance], tl_matching: TLMatching
) -> pd.DataFrame:
    """
    Generate dance-based CSV with TL names in dedicated column.
    Ordered by num_dancers descending for each dance.
    Each dancer appears in a separate column.
    """
    dance_data = []

    # Sort dances by num_dancers descending
    sorted_dances = sorted(dances, key=lambda d: d.num_dancers, reverse=True)

    # Find maximum number of dancers (excluding TLs) to determine column count
    max_dancers = max(
        len(
            [
                person
                for person in matching.dances_to_dancers.get(dance.name, [])
                if person not in tl_matching.dances_to_tls.get(dance.name, [])
            ]
        )
        for dance in dances
    )

    for dance in sorted_dances:
        dance_name = dance.name
        all_people = matching.dances_to_dancers.get(dance_name, [])
        tls = tl_matching.dances_to_tls.get(dance_name, [])

        # Separate regular dancers from TLs
        dancers = [person for person in all_people if person not in tls]

        # Create row data with dance name and dancer count
        formatted_dance_name = f"{dance_name} ({dance.num_dancers})"
        row_data = {"Dance": formatted_dance_name}

        # Add TLs column - comma-delimited if multiple TLs
        tls_str = ", ".join(tls) if tls else ""
        row_data["TLs"] = tls_str

        # Add each dancer in separate columns, with first column labeled "Dancers"
        for i, dancer in enumerate(dancers):
            if i == 0:
                col_name = "Dancers"
            else:
                col_name = f" " * i  # Spaces for unique keys
            row_data[col_name] = dancer

        # Fill empty columns for dances with fewer dancers
        for i in range(len(dancers), max_dancers):
            if i == 0:
                col_name = "Dancers"
            else:
                col_name = f" " * i
            row_data[col_name] = ""

        dance_data.append(row_data)

    return pd.DataFrame(dance_data)


def generate_dancer_based_csv(
    matching: Matching, members: list[Member]
) -> pd.DataFrame:
    """
    Generate dancer-based CSV showing dances per dancer.
    Each dance appears in a separate column.
    """
    dancer_data = []

    # Create lookup for max_dances by dancer name and dance rankings
    max_dances_lookup = {member.name: member.max_dances for member in members}
    dance_rankings_lookup = {member.name: member.dance_rankings for member in members}

    # Find maximum number of dances to determine column count
    max_dances_count = (
        max(len(dances) for dances in matching.dancers_to_dances.values())
        if matching.dancers_to_dances
        else 0
    )

    for dancer, dances in sorted(matching.dancers_to_dances.items()):
        # Get max dances for this dancer
        dancer_max_dances = max_dances_lookup.get(dancer, 0)
        num_dances = len(dances)

        # Create row data with bolded dancer name and dance count
        formatted_dancer_name = f"{dancer} ({num_dances}/{dancer_max_dances})"
        row_data = {"Dancer": formatted_dancer_name}

        # Get dance rankings for this dancer
        dancer_rankings = dance_rankings_lookup.get(dancer, [])

        # Find the ranking (1-based) for each assigned dance
        dance_rankings_assigned = []
        for dance in dances:
            try:
                # Find the index (0-based) of the dance in their rankings and convert to 1-based
                ranking = dancer_rankings.index(dance) + 1
                dance_rankings_assigned.append(ranking)
            except ValueError:
                # Dance not found in rankings (shouldn't happen in normal operation)
                dance_rankings_assigned.append("N/A")

        # Sort the rankings and create comma-delimited string
        dance_rankings_assigned.sort()
        rankings_str = ",".join(str(r) for r in dance_rankings_assigned)
        row_data["Rankings"] = rankings_str

        # Add each dance in separate columns with proper column names
        for i, dance in enumerate(dances):
            col_name = f"Dance {i + 1}"
            row_data[col_name] = dance

        # Fill empty columns for dancers with fewer dances
        for i in range(len(dances), max_dances_count):
            col_name = f"Dance {i + 1}"
            row_data[col_name] = ""

        dancer_data.append(row_data)

    return pd.DataFrame(dancer_data)
