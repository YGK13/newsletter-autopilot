"""
Beehiiv REST API v2 client. Fully generic -- no publication is hardcoded here.

Docs: https://developers.beehiiv.com/

We rely on stable v2 endpoints:
  GET  /publications/{pub_id}/posts               list posts
  GET  /publications/{pub_id}/posts/{post_id}     post detail (includes stats)
  POST /publications/{pub_id}/posts               create post

If Beehiiv changes field names, adjust here — everything else in the pipeline
depends on this module's normalised return shapes, not raw responses.
"""

from __future__ import annotations

import os
from typing import Any

import requests

BASE = "https://api.beehiiv.com/v2"


def _headers() -> dict[str, str]:
    key = os.environ["BEEHIIV_API_KEY"]
    return {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def list_published_posts(publication_id: str, limit: int = 30) -> list[dict[str, Any]]:
    """Return the N most recent PUBLISHED posts, newest first, with basic metadata."""
    out: list[dict[str, Any]] = []
    page = 1
    while len(out) < limit:
        r = requests.get(
            f"{BASE}/publications/{publication_id}/posts",
            headers=_headers(),
            params={
                "status": "confirmed",  # v2 uses 'confirmed' for published
                "order_by": "publish_date",
                "direction": "desc",
                "limit": min(50, limit - len(out)),
                "page": page,
                "expand[]": "stats",
            },
            timeout=30,
        )
        r.raise_for_status()
        body = r.json()
        data = body.get("data", [])
        if not data:
            break
        out.extend(data)
        pagination = body.get("pagination", {})
        if page >= pagination.get("total_pages", page):
            break
        page += 1
    return out[:limit]


def get_post_detail(publication_id: str, post_id: str) -> dict[str, Any]:
    """Fetch a single post with expanded stats."""
    r = requests.get(
        f"{BASE}/publications/{publication_id}/posts/{post_id}",
        headers=_headers(),
        params={"expand[]": ["stats", "free_email_content", "premium_email_content"]},
        timeout=30,
    )
    r.raise_for_status()
    return r.json().get("data", {})


def create_draft_post(
    publication_id: str,
    *,
    title: str,
    subtitle: str,
    body_html: str,
    email_subject_line: str,
    email_preview_text: str,
    thumbnail_url: str,
    content_tags: list[str] | None = None,
) -> dict[str, Any]:
    """Create a post in DRAFT state. Never publishes."""
    payload = {
        "title": title,
        "subtitle": subtitle,
        "body_content": body_html,
        "status": "draft",
        "content_tags": content_tags or [],
        "email_subject_line": email_subject_line,
        "email_preview_text": email_preview_text,
        "thumbnail_url": thumbnail_url,
    }
    r = requests.post(
        f"{BASE}/publications/{publication_id}/posts",
        headers=_headers(),
        json=payload,
        timeout=60,
    )
    if r.status_code >= 400:
        raise RuntimeError(f"Beehiiv create_draft failed {r.status_code}: {r.text[:500]}")
    return r.json().get("data", {})


def normalise_stats(post: dict[str, Any]) -> dict[str, Any]:
    """
    Return a flat dict of the metrics we care about, regardless of how Beehiiv
    nests them. Missing values default to None so downstream analysis stays robust.
    """
    stats = post.get("stats") or {}
    email = stats.get("email") or {}
    web = stats.get("web") or {}
    clicks = stats.get("clicks") or {}

    def pct(num: int | None, den: int | None) -> float | None:
        if not num or not den:
            return None
        try:
            return round(100 * num / den, 2)
        except ZeroDivisionError:
            return None

    return {
        "id": post.get("id"),
        "title": post.get("title"),
        "subtitle": post.get("subtitle"),
        "publish_date": post.get("publish_date") or post.get("displayed_date"),
        "web_url": post.get("web_url"),
        "subject_line": post.get("email_subject_line"),
        # email
        "email_recipients": email.get("recipients"),
        "email_opens": email.get("opens"),
        "email_unique_opens": email.get("unique_opens"),
        "email_open_rate": pct(email.get("unique_opens"), email.get("recipients")),
        "email_clicks": email.get("clicks"),
        "email_unique_clicks": email.get("unique_clicks"),
        "email_ctr": pct(email.get("unique_clicks"), email.get("recipients")),
        # web
        "web_views": web.get("views"),
        "web_clicks": web.get("clicks"),
        # top links
        "top_clicked_urls": clicks.get("top_urls"),
    }
