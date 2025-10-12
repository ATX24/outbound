from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class PortfolioCompany:
    name: str
    domain: Optional[str]
    description: Optional[str]
    tags: list[str]
    investors: list[str]
    funding_stage: Optional[str]


@dataclass
class PartnershipSignal:
    company_domain: str
    url: str
    signal_type: str  # Partners, University Programs, Open Innovation, etc.
    snippet: str
