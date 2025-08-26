from collections import defaultdict
from copy import deepcopy
import random
from constants import SENIORITY_ORDER
from schemas import Member, Dance, Matching, TLMatching


def _get_eligible_members_by_dance(
    members: list[Member],
    dances: list[Dance],
    rank: int,
    dances_to_members: dict[str, list[str]],
    members_to_dances: dict[str, list[str]],
    is_tl: bool = False,
) -> dict[str, list[Member]]:
    eligible_members: dict[str, list[Member]] = defaultdict(list)

    for member in members:
        if rank >= len(member.dance_rankings):
            continue

        dance_name = member.dance_rankings[rank]
        dance = next((d for d in dances if d.name == dance_name))

        # filter out member if already in the dance
        if member.name in dances_to_members[dance_name]:
            continue

        # pass if dance is at full capacity
        if len(dances_to_members[dance_name]) >= dance.num_dancers:
            continue

        # pass if member doesn't want to be considered
        if len(members_to_dances[member.name]) >= member.max_dances:
            continue
        elif (rank + 1) > member.max_rank:
            continue
        elif is_tl and len(members_to_dances[member.name]) >= member.max_tl:
            continue
        elif is_tl and dance_name not in member.dances_willing_to_tl:
            continue

        eligible_members[dance_name].append(member)

    return eligible_members


def match_tls(members: list[Member], dances: list[Dance]) -> TLMatching:
    dances_to_tls: dict[str, list[str]] = defaultdict(list)
    tls_to_dances: dict[str, list[str]] = defaultdict(list)

    for i in range(len(dances)):
        dances_to_tl_members = _get_eligible_members_by_dance(
            members=members,
            dances=dances,
            rank=i,
            dances_to_members=dances_to_tls,
            members_to_dances=tls_to_dances,
            is_tl=True,
        )

        for dance_name, tl_members in dances_to_tl_members.items():
            if not tl_members:
                continue

            existing_tls = dances_to_tls[dance_name]
            # pass if TL limit reached. error if more than 2 TLs assigned.
            if len(existing_tls) > 2:
                raise ValueError("Can't assign more than 2 TLs per dance.")
            if len(existing_tls) == 2:
                continue

            # otherwise, fetch or select the first TL for the dance.
            first_tl_name = existing_tls[0] if len(existing_tls) == 1 else None
            first_tl: Member
            if first_tl_name:
                first_tl = next(c for c in members if c.name == first_tl_name)
            else:
                first_tl = random.choice(tl_members)
                dances_to_tls[dance_name].append(first_tl.name)
                tls_to_dances[first_tl.name].append(dance_name)

            # select a co-TL if possible.
            second_tl_members = [
                c
                for c in tl_members
                if c.name != first_tl.name
                and c.name in first_tl.allowed_co_tls
                and first_tl.name in c.allowed_co_tls
            ]
            if not second_tl_members:
                continue
            second_tl = random.choice(second_tl_members)
            dances_to_tls[dance_name].append(second_tl.name)
            tls_to_dances[second_tl.name].append(dance_name)

    return TLMatching(
        dances_to_tls,
        tls_to_dances,
    )


def match(
    members: list[Member],
    dances: list[Dance],
    tl_matching: TLMatching | None = None,
) -> tuple[Matching, TLMatching]:
    if not tl_matching:
        tl_matching = match_tls(members, dances)

    dances_to_dancers = {
        dance.name: deepcopy(tl_matching.dances_to_tls.get(dance.name, [])) for dance in dances
    }
    dancers_to_dances = {
        member.name: deepcopy(tl_matching.tls_to_dances.get(member.name, []))
        for member in members
    }

    for i in range(len(dances)):
        dances_to_candidates: dict[str, list[Member]] = _get_eligible_members_by_dance(
            members=members,
            dances=dances,
            rank=i,
            dances_to_members=dances_to_dancers,
            members_to_dances=dancers_to_dances,
        )

        for dance_name, candidates in dances_to_candidates.items():
            dance = next((d for d in dances if d.name == dance_name))
            num_missing_dancers = dance.num_dancers - len(dances_to_dancers[dance_name])

            shuffled_members: list[Member] = candidates[:]
            random.shuffle(shuffled_members)
            selected_dancers: list[Member] = sorted(
                shuffled_members,
                key=lambda x: (
                    SENIORITY_ORDER[x.seniority],
                    x.lateness_score,
                    x.busyness_score,
                ),
            )[:num_missing_dancers]

            dances_to_dancers[dance_name].extend(
                [dancer.name for dancer in selected_dancers]
            )
            for dancer in selected_dancers:
                dancers_to_dances[dancer.name].append(dance_name)

    matching = Matching(
        dances_to_dancers,
        dancers_to_dances,
    )

    return (
        matching,
        tl_matching,
    )
