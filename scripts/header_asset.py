"""
Header asset generator — alternates AI-generated static image and keyword-relevant
GIF from one issue to the next, for both the Beehiiv header and the LinkedIn post.

Alternation is driven by a persistent issue counter (state/issue_count.json), not
the date, so it survives skipped days (holidays, off-days, outages) without drifting:
  issue #1 (even count=0) -> STATIC IMAGE
  issue #2 (odd  count=1) -> GIF
  issue #3 (even count=2) -> STATIC IMAGE
  ...

STATIC IMAGE: DALL-E 3, falls back to the PIL brand generator (fallback_header.py)
using your config/brand.json image_brand palette.
GIF: Giphy keyword search (free API), falls back to the same static-image path if
GIPHY_API_KEY is unset or Giphy has no result. Giphy cannot honor a custom brand
palette the way a generated image can -- that tradeoff is intentional and documented
in PROTOCOL.md. Keywords should be the day's named entity + theme, not poetic prompts.
"""

from __future__ import annotations

import base64
import json
import os
from pathlib import Path
from typing import Any

import requests

from fallback_header import build_fallback_header

STATE_PATH = Path(__file__).resolve().parents[1] / "state" / "issue_count.json"


def _read_issue_count() -> int:
    if not STATE_PATH.exists():
        return 0
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8")).get("count", 0)
    except (json.JSONDecodeError, OSError):
        return 0


def bump_issue_count() -> int:
    """Increment and persist the issue counter. Call once per real run, after asset selection."""
    count = _read_issue_count() + 1
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps({"count": count}), encoding="utf-8")
    return count


def next_asset_kind() -> str:
    """'image' on even counts, 'gif' on odd counts. Does not mutate state."""
    return "gif" if _read_issue_count() % 2 == 1 else "image"


def _generate_image_dalle(prompt: str) -> bytes:
    r = requests.post(
        "https://api.openai.com/v1/images/generations",
        headers={"Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}"},
        json={
            "model": "dall-e-3",
            "prompt": prompt,
            "size": "1792x1024",
            "quality": "hd",
            "n": 1,
            "response_format": "b64_json",
        },
        timeout=180,
    )
    r.raise_for_status()
    return base64.b64decode(r.json()["data"][0]["b64_json"])


def _search_giphy(keywords: str) -> dict[str, Any] | None:
    key = os.environ.get("GIPHY_API_KEY")
    if not key:
        return None
    try:
        r = requests.get(
            "https://api.giphy.com/v1/gifs/search",
            params={"api_key": key, "q": keywords, "limit": 5, "rating": "pg-13"},
            timeout=20,
        )
        r.raise_for_status()
        data = r.json().get("data", [])
        if not data:
            return None
        best = data[0]
        return {
            "url": best["images"]["original"]["url"],
            "still_url": best["images"]["original_still"]["url"],
            "title": best.get("title") or keywords,
        }
    except (requests.RequestException, KeyError, IndexError):
        return None


def build_header_asset(
    *, image_prompt: str, gif_keywords: str, out_dir: Path, slug: str, image_brand: dict[str, str]
) -> dict[str, Any]:
    """
    Returns {"kind": "image"|"gif", "path": Path|None, "remote_url": str|None, "alt": str}.
    - kind "image": path is a local PNG to commit to the repo for a stable raw.githubusercontent URL.
    - kind "gif": remote_url is Giphy's hosted URL (no local file, no need to commit/host it).
    image_brand must have background_hex, accent_hex, accent_dim_hex, accent_bright_hex
    (see config/brand.example.json) -- used only by the PIL fallback path.
    """
    kind = next_asset_kind()
    out_dir.mkdir(parents=True, exist_ok=True)

    if kind == "gif":
        hit = _search_giphy(gif_keywords)
        if hit:
            return {"kind": "gif", "path": None, "remote_url": hit["url"], "alt": hit["title"]}
        print("      Giphy search failed or no key set -- falling back to static image for this issue.")
        kind = "image"

    out = out_dir / f"{slug}.png"
    try:
        out.write_bytes(_generate_image_dalle(image_prompt))
        print("      DALL-E 3 rendered OK.")
    except Exception as e:
        print(f"      DALL-E failed ({e}). Using PIL fallback.")
        build_fallback_header(
            out,
            background_hex=image_brand["background_hex"],
            accent_hex=image_brand["accent_hex"],
            accent_dim_hex=image_brand["accent_dim_hex"],
            accent_bright_hex=image_brand["accent_bright_hex"],
            seed=abs(hash(slug)) % (2**31),
        )
    return {"kind": "image", "path": out, "remote_url": None, "alt": image_prompt[:120]}
