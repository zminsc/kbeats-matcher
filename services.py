import random
from collections import defaultdict

from constants import SENIORITY_ORDER
from schemas import Candidate, Dance, Matching

class Matcher:

    def __init__(self, candidates: list[Candidate], dances: list[Dance]) -> None:
        self.candidates = {candidate.name: candidate for candidate in candidates}
        self.dances = {dance.name: dance for dance in dances}

    def run(self) -> Matching:
        tl_matching = self._match_tls()
        return self._match_candidates(tl_matching)
    
    def _match_tls(self) -> Matching:
        dances_to_dancers: dict[str, list[str]] = defaultdict(list)

        for i in range(1, len(self.dances) + 1):
            dances_to_candidates: dict[str, list[Candidate]] = defaultdict(list)

            for candidate in self.candidates.values():
                if i not in candidate.dance_rankings:
                    continue
                n_ranked_dance_name = candidate.dance_rankings[i]
                if n_ranked_dance_name in candidate.dances_willing_to_tl:
                    dances_to_candidates[n_ranked_dance_name].append(candidate)

            for dance_name, candidates in dances_to_candidates.items():
                num_existing_tls = len(dances_to_dancers[dance_name])

                if num_existing_tls == 2:
                    # co-TLs have already been assigned / selected
                    continue
                elif num_existing_tls == 1:
                    # filter candidates based on who the assigned TL is willing to co-TL with
                    existing_tl = self.candidates[dances_to_dancers[dance_name][0]]
                    candidates = [c for c in candidates if c.name in existing_tl.allowed_co_tls]

                selected_tls = self._resolve_tl_tiebreaks(candidates, (num_existing_tls == 0))
                selected_tl_names = [tl.name for tl in selected_tls]
                dances_to_dancers[dance_name].extend(selected_tl_names)

        dancers_to_dances = defaultdict(list)
        for dance_name, dancer_names in dances_to_dancers.items():
            for dancer_name in dancer_names:
                dancers_to_dances[dancer_name].append(dance_name)

        return Matching(
            dancers_to_dances,
            dances_to_dancers,
            {k: list(v) for k, v in dances_to_dancers.items()},
        )
    
    def _match_candidates(self, tl_matching: Matching) -> Matching:
        dancers_to_dances = tl_matching.dancers_to_dances
        dances_to_dancers = tl_matching.dances_to_dancers
        dance_tls = tl_matching.dance_tls

        for i in range(1, len(self.dances) + 1):
            dances_to_candidates: dict[str, list[Candidate]] = defaultdict(list)

            remaining_candidates = [
                candidate for candidate in self.candidates.values()
                if len(dancers_to_dances.get(candidate.name, [])) < candidate.max_dances
                and i <= candidate.max_rank
            ]

            for candidate in remaining_candidates:
                if i not in candidate.dance_rankings:
                    continue
                n_ranked_dance_name = candidate.dance_rankings[i]

                # could have already been selected as TL
                if candidate.name not in dances_to_dancers[n_ranked_dance_name]:
                    dances_to_candidates[n_ranked_dance_name].append(candidate)
            
            for dance_name, candidates in dances_to_candidates.items():
                dancers_needed = self.dances[dance_name].num_dancers - len(dances_to_dancers[dance_name])
                selected_candidates = self._resolve_tiebreaks_using_heuristics(candidates, dancers_needed)
                selected_candidate_names = [c.name for c in selected_candidates]
                dances_to_dancers[dance_name].extend(selected_candidate_names)

                for selected_candidate_name in selected_candidate_names:
                    if selected_candidate_name not in dancers_to_dances:
                        dancers_to_dances[selected_candidate_name] = []
                    dancers_to_dances[selected_candidate_name].append(dance_name)

        return Matching(
            dancers_to_dances,
            dances_to_dancers,
            dance_tls,
        )
    
    def _resolve_tl_tiebreaks(self, candidates: list[Candidate], finding_co_tl: bool) -> list[Candidate]:
        if len(candidates) == 0:
            return []
        
        tls = self._resolve_tiebreaks_random(candidates, 1)

        if len(tls) == 0 or not finding_co_tl:
            return tls

        co_tl_candidates = [c for c in candidates if c.name in tls[0].allowed_co_tls and tls[0].name in c.allowed_co_tls]
        tls.extend(self._resolve_tiebreaks_random(co_tl_candidates, 1))
        return tls

    def _resolve_tiebreaks_random(self, candidates: list[Candidate], num_spots: int) -> list[Candidate]:
        if num_spots == 0:
            return []
        if len(candidates) <= num_spots:
            return candidates

        # completely random selection for TL tiebreaks
        shuffled_candidates = candidates[:]
        random.shuffle(shuffled_candidates)
        return shuffled_candidates[:num_spots]
    
    def _resolve_tiebreaks_using_heuristics(self, candidates: list[Candidate], num_spots: int) -> list[Candidate]:
        if num_spots == 0:
            return []
        if len(candidates) <= num_spots:
            return candidates

        # shuffle candidates to randomize order among exact ties
        shuffled_candidates = candidates[:]
        random.shuffle(shuffled_candidates)
        
        sorted_candidates = sorted(
            shuffled_candidates,
            key=lambda c: (
                SENIORITY_ORDER[c.seniority],
                c.max_dances,
                c.lateness_score,
                c.busyness_score,
            )
        )

        return sorted_candidates[:num_spots]