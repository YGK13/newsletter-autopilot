"""
Optional Notion research catalog reader.

If you'd rather curate your own research (clippings, data points, quotes,
observations from your week) instead of relying purely on Claude's live web
search, keep a single Notion page as your research catalog and set
NOTION_API_KEY + NOTION_PAGE_ID as secrets. This module pulls that page's
text and hands it to the drafter alongside its own web search.

If NOTION_API_KEY / NOTION_PAGE_ID are unset, the drafter just uses web_search
on its own -- this whole module is skipped. Nothing breaks either way.

Setup (see PROTOCOL.md section 5 for the full walkthrough):
  1. notion.so/profile/integrations -> New integration -> Capabilities: Read
     content only -> copy the token (starts with ntn_ or secret_).
  2. Open your research page in Notion -> "..." menu -> Connections -> add
     your integration. Skipping this step is the #1 setup failure -- the API
     returns object_not_found until you do it.
  3. Copy the page ID from the page's URL (the trailing 32-char hex string).

Structure your page however you like. A simple convention that works well:
one dated heading per day (`# July 6, 2026`) with bullet points underneath.
The whole page's text is passed to Claude, which is capable of finding the
freshest, most relevant entries on its own -- no strict parser to fight with.
"""

from __future__ import annotations

import os
from typing import Any

import requests

NOTION_BASE = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"


def notion_configured() -> bool:
    return bool(os.environ.get("NOTION_API_KEY") and os.environ.get("NOTION_PAGE_ID"))


def _headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {os.environ['NOTION_API_KEY']}",
        "Notion-Version": NOTION_VERSION,
    }


def _rich_text_to_plain(rich_text: list[dict[str, Any]]) -> str:
    return "".join(t.get("plain_text", "") for t in rich_text)


def _block_to_line(block: dict[str, Any]) -> str | None:
    btype = block.get("type")
    payload = block.get(btype, {})
    rich_text = payload.get("rich_text")
    if rich_text is None:
        return None
    text = _rich_text_to_plain(rich_text)
    if not text.strip():
        return None
    prefix = {
        "heading_1": "# ",
        "heading_2": "## ",
        "heading_3": "### ",
        "bulleted_list_item": "- ",
        "numbered_list_item": "1. ",
        "quote": "> ",
    }.get(btype, "")
    return f"{prefix}{text}"


def pull_research_catalog_text(max_chars: int = 12000) -> str | None:
    """Returns the page's text (headings + paragraphs + list items), or None if
    Notion isn't configured or the pull fails -- callers should treat None as
    'skip, rely on web_search only', never as a fatal error."""
    if not notion_configured():
        return None
    page_id = os.environ["NOTION_PAGE_ID"]
    lines: list[str] = []
    cursor: str | None = None
    try:
        while True:
            params = {"start_cursor": cursor} if cursor else {}
            r = requests.get(
                f"{NOTION_BASE}/blocks/{page_id}/children",
                headers=_headers(),
                params=params,
                timeout=30,
            )
            r.raise_for_status()
            body = r.json()
            for block in body.get("results", []):
                line = _block_to_line(block)
                if line:
                    lines.append(line)
            if not body.get("has_more"):
                break
            cursor = body.get("next_cursor")
    except requests.RequestException as e:
        print(f"      Notion pull failed ({e}). Continuing on web_search alone.")
        return None

    text = "\n".join(lines)
    if len(text) > max_chars:
        text = text[-max_chars:]  # keep the most recent (bottom-of-page) entries
    return text or None
