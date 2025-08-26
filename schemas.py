from typing import NamedTuple
from enums import Seniority
from pydantic import BaseModel, Field


class Matching(NamedTuple):
    dances_to_dancers: dict[str, list[str]]
    dancers_to_dances: dict[str, list[str]]


class TLMatching(NamedTuple):
    dances_to_tls: dict[str, list[str]]
    tls_to_dances: dict[str, list[str]]


class Dance(BaseModel):
    name: str
    num_dancers: int
    included: bool = True


class Member(BaseModel):
    name: str
    seniority: Seniority
    max_dances: int
    max_rank: int

    dance_rankings: list[str]

    lateness_score: int = 0
    busyness_score: int = 0

    max_tl: int
    dances_willing_to_tl: set[str] = Field(default_factory=set)
    allowed_co_tls: set[str] = Field(default_factory=set)
