#!/usr/bin/env python3
"""
Daily newsletter draft generator -- generic template, works for any Beehiiv
publication + Claude + (optional) Notion research catalog.

Fires on your chosen cadence via GitHub Actions cron (see config/brand.json
"cadence_cron" and .github/workflows/daily.yml).

Pipeline:
  0. LEARN — pull last 30 published Beehiiv posts + stats, and the manual
     LinkedIn engagement log (LINKEDIN_STATS.csv). Call Claude the analyst
     to update LEARNINGS.md with any new evidence-based rules from both channels.
  1. DRAFT — call Claude with web_search + PLAYBOOK.md + LEARNINGS.md.
     Get structured JSON: title, subtitle, subject, preview, body, image
     prompts (email + LinkedIn), GIF keywords (email + LinkedIn), LinkedIn copy.
  2. HEADER ASSET — alternates AI-generated static image / keyword-relevant GIF
     issue to issue for both the email header and the LinkedIn post. If DALL-E
     fails, falls back to the PIL-based brand-aligned generator.
  3. HOST — commit any generated images to the repo -> stable public URL.
     GIFs are already hosted by Giphy; nothing to commit.
  4. DRAFT POST — POST to Beehiiv as DRAFT (never publish).
  5. LINKEDIN — email the LinkedIn copy + its image/GIF to your own Gmail
     for copy-paste.
  6. COUNTER — advance the issue counter that drives the next alternation.

Every step logs. Nothing publishes. Nothing sends externally except the
self-email of the LinkedIn copy.

See PROTOCOL.md for the full walkthrough of every step and every setting.
"""

from __future__ import annotations

import json
import os
import smtplib
import subprocess
import sys
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

import anthropic

from beehiiv_api import create_draft_post
from brand_config import load_brand, load_learnings, load_playbook
from header_asset import bump_issue_count, build_header_asset
from learning_loop import load_linkedin_stats, pull_recent_dataset, update_learnings
from notion_research import notion_configured, pull_research_catalog_text

DRAFTER_MODEL = "claude-opus-4-7"
ANALYST_MODEL = "claude-opus-4-7"

REQUIRED_ENV = [
    "ANTHROPIC_API_KEY",
    "BEEHIIV_API_KEY",
    "OPENAI_API_KEY",
    "GMAIL_ADDRESS",
    "GMAIL_APP_PASSWORD",
]

REPO_ROOT = Path(__file__).resolve().parents[1]

DRAFTER_TEMPLATE = """You are drafting today's edition of this newsletter.

Two files govern you:

===== PLAYBOOK.md (LOCKED — do not violate) =====
{playbook}

===== LEARNINGS.md (evidence-based rules — bias hard toward CONFIRMED and STRENGTHENED entries) =====
{learnings}

{research_block}

PROCESS:
  1. Web-search for news from the last 24-48 hours in your niche (per PLAYBOOK.md's
     audience and topic scope). If a research catalog is provided above, treat it
     as your primary source of specificity (named entities, numbers, quotes you
     already collected) and use web_search to verify freshness and fill gaps --
     don't ignore your own curated research in favor of generic search results.
  2. Pick ONE signal/story per the playbook and learnings criteria.
  3. Draft in the LOCKED body structure from PLAYBOOK.md. Do NOT include a header
     image or footer; the script adds both.
  4. Apply LEARNINGS.md ruthlessly -- whatever CONFIRMED / STRENGTHENED rules
     exist, apply them to the title, hook and body.

Return ONE JSON object with these exact keys, no prose outside the JSON,
no code fences:
{{
  "title": str,
  "subtitle": str,
  "subject_line": str,
  "email_preview_text": str,
  "body_html": str,
  "image_prompt": str,
  "image_alt": str,
  "gif_keywords": str,
  "linkedin_text": str,
  "linkedin_image_prompt": str,
  "linkedin_gif_keywords": str,
  "signal_summary": str,
  "passed_on": [str, str]
}}

"image_prompt" / "linkedin_image_prompt": on-brand static-image prompts (locked
image brand from PLAYBOOK.md) for the email header and the LinkedIn image respectively.
These are only used on issues where the alternation picks a static image.

"gif_keywords" / "linkedin_gif_keywords": 2-4 plain-English keywords (the day's
named entity + theme) used to search Giphy on issues where the alternation picks
a GIF instead. Keep them short and literal, not poetic -- they are search terms.

LinkedIn text must contain the literal token `[POST_URL]` where the link goes.
The script replaces it with the public post URL after the draft is created.
"""


def check_env() -> None:
    missing = [k for k in REQUIRED_ENV if not os.environ.get(k)]
    if missing:
        sys.exit(f"Missing required env vars: {', '.join(missing)}")


def today_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def today_human() -> str:
    return datetime.now(timezone.utc).strftime("%A, %B %d, %Y")


def strip_json_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```", 2)[1]
        if text.lstrip().lower().startswith("json"):
            text = text.split("\n", 1)[1]
    return text.strip().rstrip("`").strip()


def git_commit_and_push(paths: list[str], message: str) -> None:
    if not os.environ.get("GITHUB_ACTIONS"):
        print("      (skipping git push — not in GitHub Actions)")
        return
    subprocess.run(["git", "config", "user.email", "actions@github.com"], check=True)
    subprocess.run(["git", "config", "user.name", "Newsletter Autopilot Bot"], check=True)
    for p in paths:
        subprocess.run(["git", "add", p], check=True)
    diff = subprocess.run(["git", "diff", "--cached", "--quiet"]).returncode
    if diff == 0:
        print("      (nothing changed, nothing to push)")
        return
    subprocess.run(["git", "commit", "-m", message], check=True)
    subprocess.run(["git", "push"], check=True)


def raw_url_for(rel_path: str) -> str:
    repo = os.environ.get("GITHUB_REPOSITORY", "OWNER/REPO")
    branch = os.environ.get("GITHUB_REF_NAME", "main")
    return f"https://raw.githubusercontent.com/{repo}/{branch}/{rel_path}"


def draft_newsletter(playbook: str, learnings: str) -> dict:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    research = pull_research_catalog_text() if notion_configured() else None
    research_block = (
        f"===== YOUR NOTION RESEARCH CATALOG (most recent entries) =====\n{research}\n"
        if research
        else "(No Notion research catalog configured -- rely on web_search alone.)"
    )
    resp = client.messages.create(
        model=DRAFTER_MODEL,
        max_tokens=8000,
        system=DRAFTER_TEMPLATE.format(playbook=playbook, learnings=learnings, research_block=research_block),
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        messages=[
            {
                "role": "user",
                "content": (
                    f"Today is {today_human()}. Draft today's issue. "
                    "Do the web search, apply the LEARNINGS.md rules to the title "
                    "especially, and return the JSON."
                ),
            }
        ],
    )
    text = "".join(getattr(b, "text", "") for b in resp.content)
    return json.loads(strip_json_fences(text))


def email_linkedin_to_self(draft: dict, public_url: str, linkedin_image_url: str, brand: dict) -> None:
    text = draft["linkedin_text"].replace("[POST_URL]", public_url)
    body = (
        f"Image (download and upload to LinkedIn, or right-click > copy image if it's a GIF):\n"
        f"{linkedin_image_url}\n\n"
        f"---\n\n"
        f"{text}"
    )
    msg = MIMEMultipart()
    msg["From"] = os.environ["GMAIL_ADDRESS"]
    msg["To"] = brand["notify_email"]
    msg["Subject"] = f"LinkedIn — {today_iso()} — {draft['title']}"
    msg.attach(MIMEText(body, "plain", "utf-8"))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(os.environ["GMAIL_ADDRESS"], os.environ["GMAIL_APP_PASSWORD"])
        s.send_message(msg)


def main() -> None:
    check_env()
    os.chdir(REPO_ROOT)
    brand = load_brand()
    print("─" * 64)
    print(f" {brand['publication_name']} — {today_human()}")
    print("─" * 64)

    # 0 · LEARN
    print("[0/6] Pulling last 30 published posts + LinkedIn log, updating LEARNINGS.md…")
    dataset = pull_recent_dataset(brand["beehiiv_publication_id"], limit=30)
    linkedin_rows = load_linkedin_stats()
    print(f"      Pulled {len(dataset)} Beehiiv posts, {len(linkedin_rows)} LinkedIn log rows.")
    if dataset or linkedin_rows:
        try:
            update_learnings(dataset, linkedin_rows, model=ANALYST_MODEL)
            git_commit_and_push(["LEARNINGS.md"], f"learnings update {today_iso()}")
        except Exception as e:
            print(f"      Analyst update failed ({e}). Continuing with existing learnings.")
    else:
        print("      No dataset yet (probably first run). Using seed learnings.")

    playbook = load_playbook()
    learnings = load_learnings()

    # 1 · DRAFT
    print("[1/6] Drafting via Claude + web_search…")
    draft = draft_newsletter(playbook, learnings)
    print(f"      Title: {draft['title']}")
    print(f"      Signal: {draft['signal_summary']}")

    # 2 · HEADER ASSET (alternates image/GIF by issue count -- see header_asset.py)
    print("[2/6] Building header asset (image/GIF alternation)…")
    date = today_iso()
    header_asset = build_header_asset(
        image_prompt=draft["image_prompt"],
        gif_keywords=draft["gif_keywords"],
        out_dir=REPO_ROOT / "assets" / "headers",
        slug=date,
        image_brand=brand["image_brand"],
    )
    linkedin_asset = build_header_asset(
        image_prompt=draft["linkedin_image_prompt"],
        gif_keywords=draft["linkedin_gif_keywords"],
        out_dir=REPO_ROOT / "assets" / "linkedin",
        slug=f"{date}-linkedin",
        image_brand=brand["image_brand"],
    )
    print(f"      Header: {header_asset['kind']}. LinkedIn: {linkedin_asset['kind']}.")

    # 3 · HOST
    print("[3/6] Committing any generated images to repo for stable URLs…")
    to_commit = [str(a["path"].relative_to(REPO_ROOT)) for a in (header_asset, linkedin_asset) if a["path"]]
    if to_commit:
        git_commit_and_push(to_commit, f"header assets {date}")
    image_url = header_asset["remote_url"] or raw_url_for(str(header_asset["path"].relative_to(REPO_ROOT)))
    linkedin_image_url = linkedin_asset["remote_url"] or raw_url_for(
        str(linkedin_asset["path"].relative_to(REPO_ROOT))
    )
    print(f"      Header URL: {image_url}")
    print(f"      LinkedIn image URL: {linkedin_image_url}")

    # 4 · DRAFT POST
    print("[4/6] Creating Beehiiv draft…")
    header_html = (
        f'<figure><img src="{image_url}" alt="{draft["image_alt"]}" '
        f'style="width:100%;height:auto;display:block;"/></figure>'
    )
    body_html = header_html + draft["body_html"] + brand["footer_html"]
    result = create_draft_post(
        brand["beehiiv_publication_id"],
        title=draft["title"],
        subtitle=draft["subtitle"],
        body_html=body_html,
        email_subject_line=draft["subject_line"],
        email_preview_text=draft["email_preview_text"],
        thumbnail_url=image_url,
        content_tags=brand.get("content_tags"),
    )
    post_id = result.get("id", "")
    public_url = result.get("web_url", "")
    editor_url = f"https://app.beehiiv.com/posts/{post_id}/edit"

    # 5 · LINKEDIN
    print("[5/6] Emailing LinkedIn copy + image/GIF to you…")
    email_linkedin_to_self(draft, public_url, linkedin_image_url, brand)

    # 6 · ISSUE COUNTER
    print("[6/6] Advancing issue counter for next alternation…")
    bump_issue_count()

    print("\n✅ Done.")
    print(f"   Editor:  {editor_url}")
    print(f"   Public:  {public_url}")
    print(f"   Signal:  {draft['signal_summary']}")
    print(f"   Passed:  " + " | ".join(draft.get("passed_on", [])))


if __name__ == "__main__":
    main()
