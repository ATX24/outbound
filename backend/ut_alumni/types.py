from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class AlumniRecord:
    name: str
    ut_affiliation: str  # department, degree, year if known
    role: Optional[str]
    organization: Optional[str]
    location: Optional[str]
    prior_giving_signal: Optional[str] = None
    interests: list[str] = None  # tech/venture interests


@dataclass
class DonorSignal:
    url: str
    snippet: str
    tag: str  # donor roll, quote, sponsorship, foundation affiliation
