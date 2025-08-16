from enums import Seniority
from typing import NamedTuple
from pydantic import BaseModel, Field


class Matching(NamedTuple):
    dancers_to_dances: dict[str, list[str]]
    dances_to_dancers: dict[str, list[str]]
    dance_tls: dict[str, list[str]]  # Track TLs for each dance


class Dance(BaseModel):
    name: str
    num_dancers: int


class Candidate(BaseModel):
    name: str
    seniority: Seniority
    max_dances: int
    max_rank: int

    dance_rankings: dict[int, str]

    lateness_score: int = 0
    busyness_score: int = 0

    dances_willing_to_tl: set[str] = Field(default_factory=set)
    allowed_co_tls: set[str] = Field(default_factory=set)