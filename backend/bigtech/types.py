from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class PageRecord:
    url: str
    source: str  # e.g., careers, research, engineering blog
    raw_html_len: int


@dataclass
class SignalRecord:
    url: str
    signal_type: str  # e.g., Hackathon, Fellowship, RFP
    snippet: str
    source: str  # e.g., html, firecrawl


@dataclass
class ContactRecord:
    name: str
    title: str
    email: Optional[str]
    organization: Optional[str] = None
