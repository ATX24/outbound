from __future__ import annotations

from typing import Iterable, List, Dict
from bs4 import BeautifulSoup

KEYWORDS: list[tuple[str, str]] = [
    ("University Relations", "University Relations"),
    ("University Recruiting", "University Recruiting"),
    ("Academic Partnerships", "Academic Partnerships"),
    ("Developer Relations", "Developer Relations"),
    ("DevRel", "Developer Relations"),
    ("Research", "Research"),
    ("AI/ML", "AI/ML"),
    ("Education", "Education"),
    ("Campus", "Campus"),
    ("Hackathon", "Hackathon"),
    ("Fellowship", "Fellowship"),
    ("Internship", "Internship"),
    ("RFP", "RFP"),
    ("Call for Proposals", "RFP"),
]


def extract_signals_from_html(html: str, url: str) -> List[Dict[str, str]]:
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ", strip=True)
    found: list[dict[str, str]] = []

    for needle, as_type in KEYWORDS:
        if needle.lower() in text.lower():
            # try to find a nearby snippet
            snippet = _find_snippet(soup, needle)
            found.append({
                "url": url,
                "signal_type": as_type,
                "snippet": snippet or needle,
                "source": "html",
            })
    return found


def _find_snippet(soup: BeautifulSoup, needle: str) -> str | None:
    node = soup.find(string=lambda s: isinstance(s, str) and needle.lower() in s.lower())
    if not node:
        return None
    parent = node.parent
    if not parent:
        return node.strip()[:240]
    snippet_text = parent.get_text(" ", strip=True)
    return snippet_text[:240]
