# Newsletter Autopilot

> **New here? Start at [START_HERE.md](./START_HERE.md).** It tells you which
> document to read first depending on whether you're setting this up yourself
> or handing it to Claude to set up for you.
>
> **Want the full explanation of what this is and why it's built this way?**
> Read [PROTOCOL.md](./PROTOCOL.md). That's the canonical doc — twelve minutes,
> written for a non-developer operator, not an engineer.

---

A daily (or however-often-you-want) newsletter drafting engine: Claude reads
your research (a Notion catalog, or just live web search), drafts a full issue
in your voice, builds an on-brand header image or a keyword-relevant GIF
(alternating issue to issue), posts it to Beehiiv as a **draft only**, and
emails you a ready-to-paste LinkedIn post with its own image/GIF.

You are always the last human in the loop. Nothing sends or publishes itself.
The system also **learns continuously**: every run it reads how your last 30
Beehiiv issues performed (open rate, click rate) and — once you start logging
LinkedIn engagement in `LINKEDIN_STATS.csv` — how your LinkedIn posts perform
too, and folds evidence-based rules back into `LEARNINGS.md` before drafting
the next issue.

## What you fill in (only 4 things)

1. `config/brand.json` — copy from `config/brand.example.json`. Mechanical
   settings: your Beehiiv publication ID, footer HTML, cadence, image colors.
2. `PLAYBOOK.md` — copy from `PLAYBOOK.template.md`. Your voice, your locked
   body structure, your image brand-lock. This is the file that makes the
   output sound like you and nobody else.
3. `LEARNINGS.md` — copy from `LEARNINGS.seed.md`. Your starting beliefs about
   what works with your audience. The system refines this with real evidence
   over time.
4. Five GitHub Actions secrets (API keys) — see `.env.example`.

Everything else — the scripts, the workflow, the image/GIF alternation, the
learning loop — is already built and generic. You are not writing code.

## Architecture

```
GitHub Actions cron (your cadence)
        |
        v
scripts/draft_newsletter.py   <- orchestrator
   |        |         |
   v        v         v
learning_loop.py   header_asset.py   beehiiv_api.py
(Beehiiv +         (alternates       (create draft
 LinkedIn stats     image/GIF for     post via API)
 -> LEARNINGS.md)   email + LinkedIn)
```

Full file map, cost breakdown, troubleshooting and the reasoning behind every
choice: [PROTOCOL.md](./PROTOCOL.md).

## Quick start (once your 4 files above are filled in)

```bash
pip install -r requirements.txt
python scripts/draft_newsletter.py
```

Runs the full pipeline once, locally. Then wire the GitHub Actions secrets and
let the cron in `.github/workflows/daily.yml` take over.

---

Template forked in spirit (not in git history) from a production system called
The Leverage Signal. Nothing brand-specific from that system is in this
template — every string here is a placeholder for you to replace.
