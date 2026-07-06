"""
Continuous learning loop -- generic, works for any newsletter using this template.

Every run:
  1. Pull the last 30 published Beehiiv posts + their stats, and the manually
     logged LinkedIn engagement rows (LINKEDIN_STATS.csv).
  2. Ask Claude the analyst to compare top-quartile vs bottom-quartile posts
     across open rate/CTR (Beehiiv) and reactions/comments per impression
     (LinkedIn), look at title/hook features, and update LEARNINGS.md with
     any new evidence-supported rules for BOTH channels.
  3. Return the current LEARNINGS.md contents so the drafter can use them.

The playbook is append-and-annotate:
  - Existing SEED rules stay; the analyst marks them CONFIRMED / STRENGTHENED /
    WEAKENED / REFUTED based on the new data.
  - New patterns (2+ posts of evidence) get added as EMERGING.
  - Nothing is deleted. The full history is in git.

LinkedIn has no self-serve analytics API for a personal profile, so the loop
reads a small CSV you fill in from LinkedIn's own post-analytics view
(30 seconds, once a week is enough). See LINKEDIN_STATS.csv for the format.
"""

from __future__ import annotations

import csv
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import anthropic

from beehiiv_api import list_published_posts, normalise_stats

REPO_ROOT = Path(__file__).resolve().parents[1]
LEARNINGS_PATH = REPO_ROOT / "LEARNINGS.md"
LINKEDIN_STATS_PATH = REPO_ROOT / "LINKEDIN_STATS.csv"

ANALYST_SYSTEM = """You are the performance analyst for this newsletter, across both
its distribution channels: the Beehiiv email/web post and the LinkedIn post that
goes out alongside it.

You will receive:
  1. The current LEARNINGS.md — the evidence-based editorial playbook so far.
  2. A JSON table of the last 30 published Beehiiv posts with metrics
     (open rate, CTR, subject line, title, etc.).
  3. A JSON table of manually-logged LinkedIn posts with metrics (impressions,
     reactions, comments, reposts, hook text) -- may be empty if the log is new.

Your job:
  A) Rank Beehiiv posts by email open rate. Compare the top quartile vs the
     bottom quartile on TITLE features: pronouns, suspense/expectation-break
     framing, named entities, concrete vs abstract verbs, punctuation, length.
  B) Do the same for CTR (unique clicks / recipients).
  C) If LinkedIn rows exist, rank by (reactions + comments*3 + reposts*5) /
     impressions -- comments and reposts are weighted higher because they are
     harder to get and signal stronger resonance. Compare the top vs bottom
     posts on HOOK features (first two lines above "see more"): pronoun use,
     number-in-line-2, named-entity-by-line-3, sentence length.
  D) Look at TOPIC / signal category on both channels -- which types of
     stories over-perform, and does a topic that wins on Beehiiv also win on
     LinkedIn, or do the two channels reward different things?
  E) Update LEARNINGS.md following the append-and-annotate rules in the file
     itself. Specifically:
       - For each existing rule with new evidence: annotate with a bullet
         beneath it: `- [YYYY-MM-DD] STRENGTHENED / WEAKENED / CONFIRMED /
         REFUTED — <one line of evidence>`
       - For NEW patterns you see with at least 2 data points: add them as
         `[EMERGING]` rules with the same annotation format.
       - Keep Beehiiv-specific and LinkedIn-specific rules in their own
         sections. A rule proven on one channel is a hypothesis, not evidence,
         on the other -- mark cross-channel carryover as `[EMERGING]`, not
         `[CONFIRMED]`, until the other channel's own data confirms it.
       - Never delete a rule.
       - Preserve the section headings and overall structure of the file.
       - Append a dated block to the `## Analytics log` section at the bottom
         with the metric snapshot for BOTH channels (omit LinkedIn's block if
         the log is empty).

Return ONLY the full updated LEARNINGS.md text — no code fences, no preamble,
no commentary. It will be written back to disk verbatim.
"""


def _feature_extract(title: str | None) -> dict[str, Any]:
    """Cheap title features so the analyst has structured signal."""
    t = (title or "").lower()
    return {
        "has_you": any(w in t.split() for w in ("you", "your", "yours", "you're", "yourself")),
        "has_suspense_word": any(
            phrase in t
            for phrase in (
                "no more",
                "just expired",
                "stop ",
                "already",
                "quietly",
                "just made",
                "wait-and-see",
                "the era of",
                "just put",
            )
        ),
        "word_count": len(t.split()),
        "has_colon": ":" in (title or ""),
        "has_number": any(ch.isdigit() for ch in (title or "")),
    }


def pull_recent_dataset(publication_id: str, limit: int = 30) -> list[dict[str, Any]]:
    posts = list_published_posts(publication_id, limit=limit)
    rows: list[dict[str, Any]] = []
    for p in posts:
        row = normalise_stats(p)
        row["title_features"] = _feature_extract(row.get("title"))
        rows.append(row)
    return rows


def load_linkedin_stats() -> list[dict[str, Any]]:
    """
    Read LINKEDIN_STATS.csv (date, post_url, hook_text, impressions, reactions,
    comments, reposts). Returns [] if the file doesn't exist or has only the
    header row -- that's the normal state until the first weekly log-in.
    """
    if not LINKEDIN_STATS_PATH.exists():
        return []
    rows: list[dict[str, Any]] = []
    with LINKEDIN_STATS_PATH.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            try:
                impressions = int(row.get("impressions") or 0)
                reactions = int(row.get("reactions") or 0)
                comments = int(row.get("comments") or 0)
                reposts = int(row.get("reposts") or 0)
            except ValueError:
                continue
            engagement_rate = (
                round(100 * (reactions + comments * 3 + reposts * 5) / impressions, 2) if impressions else None
            )
            rows.append(
                {
                    "date": row.get("date"),
                    "post_url": row.get("post_url"),
                    "hook_text": row.get("hook_text"),
                    "impressions": impressions or None,
                    "reactions": reactions,
                    "comments": comments,
                    "reposts": reposts,
                    "engagement_rate": engagement_rate,
                }
            )
    return rows


def update_learnings(dataset: list[dict[str, Any]], linkedin_rows: list[dict[str, Any]], model: str) -> str:
    """Call Claude the analyst, write the returned markdown back to LEARNINGS.md, return it."""
    current = LEARNINGS_PATH.read_text(encoding="utf-8")
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    user_content = (
        f"Today: {datetime.now(timezone.utc).strftime('%Y-%m-%d')}\n\n"
        f"===== CURRENT LEARNINGS.md =====\n{current}\n"
        f"===== BEEHIIV POSTS DATASET (last {len(dataset)}) =====\n{json.dumps(dataset, indent=2)}\n"
        f"===== LINKEDIN LOG (last {len(linkedin_rows)} rows) =====\n{json.dumps(linkedin_rows, indent=2)}\n"
    )

    resp = client.messages.create(
        model=model,
        max_tokens=8000,
        system=ANALYST_SYSTEM,
        messages=[{"role": "user", "content": user_content}],
    )
    updated = "".join(getattr(b, "text", "") for b in resp.content).strip()
    if updated.startswith("```"):
        updated = updated.split("```", 2)[1]
        if updated.lstrip().lower().startswith("markdown"):
            updated = updated.split("\n", 1)[1]
        updated = updated.rstrip("`").strip()

    LEARNINGS_PATH.write_text(updated, encoding="utf-8")
    return updated
