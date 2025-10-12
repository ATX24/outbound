from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator
from playwright.sync_api import sync_playwright


@contextmanager
def browser_context(headless: bool = True) -> Iterator[tuple]:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page()
        try:
            yield page, browser
        finally:
            browser.close()


def fetch_html(url: str, wait_until: str = "networkidle", headless: bool = True) -> str:
    with browser_context(headless=headless) as (page, _browser):
        page.goto(url, wait_until=wait_until)
        return page.content()
