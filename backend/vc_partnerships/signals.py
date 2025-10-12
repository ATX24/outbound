from __future__ import annotations

from typing import List, Dict
from bs4 import BeautifulSoup

KEYWORDS: list[tuple[str, str]] = [
    ("Partners", "Partners"),
    ("University Programs", "University Programs"),
    ("Community", "Community"),
    ("Open Innovation", "Open Innovation"),
    ("Research", "Research"),
    ("DevRel", "Developer Relations"),
    ("Developer Relations", "Developer Relations"),
    ("Hackathon", "Hackathon"),
    ("Campus", "Campus"),
    ("Case Studies", "Case Studies"),
]


def extract_partnership_signals(html: str, url: str, company_domain: str) -> List[Dict[str, str]]:
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ", strip=True)
    found: list[dict[str, str]] = []
    for needle, as_type in KEYWORDS:
        if needle.lower() in text.lower():
            node = soup.find(string=lambda s: isinstance(s, str) and needle.lower() in s.lower())
            snippet = (node.parent.get_text(" ", strip=True) if node and node.parent else needle)[:240]
            found.append({
                "company_domain": company_domain,
                "url": url,
                "signal_type": as_type,
                "snippet": snippet,
            })
    return found
