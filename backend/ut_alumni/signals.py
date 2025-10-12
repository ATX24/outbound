from __future__ import annotations

from typing import List, Dict
from bs4 import BeautifulSoup

KEYWORDS: list[tuple[str, str]] = [
    ("Alumni", "UT Alumni"),
    ("Donor", "Donor"),
    ("Endowment", "Endowment"),
    ("Gift", "Gift"),
    ("Philanthropy", "Philanthropy"),
    ("Sponsorship", "Sponsorship"),
    ("Foundation", "Foundation"),
    ("Advisory", "Advisory"),
    ("Board", "Board"),
]


def extract_donor_signals(html: str, url: str) -> List[Dict[str, str]]:
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ", strip=True)
    found: list[dict[str, str]] = []
    lower = text.lower()
    for needle, tag in KEYWORDS:
        if needle.lower() in lower:
            node = soup.find(string=lambda s: isinstance(s, str) and needle.lower() in s.lower())
            snippet = (node.parent.get_text(" ", strip=True) if node and node.parent else needle)[:240]
            found.append({
                "url": url,
                "snippet": snippet,
                "tag": tag,
            })
    return found
