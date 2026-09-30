# The Newsletter Autopilot Protocol

**Canonical, version-controlled. This is the document the repo ships against.**
Generalized from a production system called The Leverage Signal, rebuilt so
any newsletter operator can run it on their own brand, their own audience and
their own Beehiiv publication.

---

## Read this first

If you run a newsletter and are not a developer, this is the document you
actually read. Skip `README.md` if you want the engineering map. This
protocol is the operating model: what the system is, who it is for, why the
pieces are arranged the way they are, and how to run it without writing code.

Twelve minutes of reading. The system buys back several hours a week of
newsletter writing, from week one.

---

## 1. Who this is for

This protocol is built for one kind of reader-operator. If three of the five
below describe you, this is for you.

1. You run something -- a consultancy, a practice, a small company, a
   founder-led business, a coaching or advisory service. Your day is judgment
   calls, not typing.
2. You already publish, or want to. A Beehiiv newsletter, an email list, a
   LinkedIn presence. You know publishing is leverage. You also know it eats
   real hours every week.
3. You have a point of view. You can name the trap your audience is in and
   the move they should make. You are not trying to be a generalist blogger.
4. You are tech-fluent but not a developer. You can paste an API key, run one
   command in a terminal, and follow numbered steps. You do not want to sit
   in an editor debugging code.
5. You value your editorial judgment, not your typing speed. You want a
   system that drafts in your voice well enough that your only job in the
   morning is to read, tighten, and press Send.

This protocol gives you back the writing hours and keeps the judgment in your
hands. It does not autopilot your voice. It does the staging. You do the
final ten percent that makes it sound like you.

---

## 2. What this actually is

A recurring companion issue -- daily, or however often you choose -- to
whatever your primary newsletter cadence is. The discipline:

- One idea per issue. Not three, not five.
- One prescriptive close per issue -- a specific, named action, never a
  question.
- A locked body structure that repeats issue to issue, so readers know what
  they're getting (you define this structure once, in `PLAYBOOK.md`).
- A header asset that **alternates between a brand-locked AI-generated image
  and a keyword-relevant GIF**, issue to issue -- so the visual stays fresh
  without losing brand consistency every other day.
- A LinkedIn companion post with its **own** image/GIF, drafted alongside the
  email issue, ready to copy-paste.
- A learning loop that reads how your last 30 Beehiiv issues performed, and
  -- once you start logging it -- how your LinkedIn posts performed, and
  folds evidence-based rules back into your editorial playbook before the
  next draft.

The reader walks away with a single decision they can make today. That is
the contract you are setting up.

---

## 3. The engine, one paragraph at a time

The engine is a small Python project that runs in a few minutes, on whatever
schedule you pick, inside GitHub Actions (free, no server to maintain).

A cron fires `scripts/draft_newsletter.py`. The script optionally reads your
Notion research catalog (if you keep one -- entirely optional, see section
4c), then Claude does two calls: an **analyst** call that reads your recent
Beehiiv performance and LinkedIn log and updates `LEARNINGS.md` with new
evidence-based rules, and a **drafter** call (with live web search) that
writes the full issue plus a LinkedIn variant, following `PLAYBOOK.md`
(locked) and `LEARNINGS.md` (evolving). The engine then builds the header
image or GIF (alternating issue to issue -- see section 4b), posts the draft
to Beehiiv (**status: draft, never send**), and emails you the LinkedIn copy
and its image/GIF so you can review and post both by hand.

Total cost: a few dollars a month in API calls. Total time from your fingers:
five to ten minutes a day.

**Why this two-file split (`PLAYBOOK.md` + `LEARNINGS.md`) instead of one:**
your voice and structure are things YOU decide and rarely change --
`PLAYBOOK.md` is locked, edited by you, on purpose. What actually moves
opens/clicks/engagement is an empirical question the system should keep
answering for you -- `LEARNINGS.md` is a living document, edited by the
analyst call every run, append-only so you can always see how a rule came to
be trusted (or not).

**Why `config/brand.json` is separate from both:** it holds mechanical
settings (publication ID, footer HTML, image hex colors, cron schedule) that
have nothing to do with voice or evidence. Keeping mechanics, voice and
evidence in three separate files means editing one never risks breaking
another.

---

## 4. Design decisions worth understanding

### 4a. Why Beehiiv

Beehiiv has a real API for programmatic draft creation (Substack does not),
strong growth tooling, and an editor clean enough that your daily review is
actually five minutes, not twenty. The Beehiiv MCP (Model Context Protocol)
server is also worth knowing about: if you use Claude Desktop or Claude Code
for your own interactive editorial work (not just the automated pipeline),
installing Beehiiv's MCP lets you ask Claude things like "pull my last 10
issues' open rates and tell me what's working" in plain conversation, without
writing any code. The automated pipeline in this repo uses Beehiiv's REST API
directly (`scripts/beehiiv_api.py`) because it needs to run unattended on a
schedule; the MCP path is for you, interactively, on top of the same account.

### 4b. Why the image/GIF alternation, and its honest tradeoff

A header image every single day, from the same generator, starts to look
repetitive fast -- readers notice a pattern before they notice a signal. A
GIF every day loses your brand entirely; Giphy has no idea what your brand
colors are. Alternating gets you both: half your issues carry a fully
brand-locked, generated image; the other half carry a keyword-relevant GIF
that trades brand consistency for freshness and shareability.

The alternation is driven by a persistent counter
(`state/issue_count.json`), not the calendar date, so a skipped issue (an
off-day, an outage, a holiday) never desyncs the pattern -- issue N+1 always
gets the opposite kind from issue N, regardless of when it actually runs.

If a GIF issue's Giphy search comes back empty (or you never set
`GIPHY_API_KEY`), the engine silently falls back to a static image for that
issue instead of failing. You will never get a broken or missing header.

### 4c. Why Notion research is optional, not required

Two honest paths exist for grounding your drafts in real information:

1. **Pure web search** (default, zero setup). Claude's `web_search` tool
   finds fresh news in your niche every run. Good enough for most operators,
   especially early on.
2. **Your own Notion research catalog** (optional, `scripts/notion_research.py`).
   If you spend part of your week clipping articles, jotting numbers, or
   noting conversations that are relevant to your niche, keep one Notion page
   as a running catalog. Set `NOTION_API_KEY` and `NOTION_PAGE_ID` and the
   engine pulls that page's text into the drafter's context every run,
   alongside its own web search. This produces sharper, more original issues
   because you're feeding the model things a generic search will never
   surface -- your own observations.

Start with path 1. Add path 2 once you notice your drafts feel generic and
you have opinions a search engine can't find. There is no wrong choice; the
system works identically either way and never fails if Notion is unconfigured.

### 4d. Why LinkedIn learning is a manual CSV, not an API pull

LinkedIn does not offer a self-serve analytics API for a personal profile --
that access requires a partnership agreement most individual operators will
never have. Rather than skip LinkedIn from the learning loop entirely, this
protocol asks you to spend about thirty seconds a week: open each LinkedIn
post from the week, click "View analytics," and add one row to
`LINKEDIN_STATS.csv` (date, post URL, hook text, impressions, reactions,
comments, reposts). The analyst call reads this file every run and treats a
pattern proven on LinkedIn as a hypothesis (not a confirmed rule) for the
email side, and vice versa, until each channel's own data backs it up. Skip a
week and nothing breaks -- the loop just keeps using whatever evidence exists
so far.

---

## 5. Install in about thirty minutes

If you have never installed anything from GitHub before, read this section
once top to bottom, then start. Or -- easier -- paste `CLAUDE_SETUP.md` into
a Claude conversation and let it walk you through these same steps
interactively, asking about your brand along the way.

### Prerequisites

- Node is not needed; this repo is Python. Python 3.11 or later --
  check with `python --version`.
- Git -- check with `git --version`.
- A GitHub account, and a terminal you're comfortable in (Windows: PowerShell
  or Git Bash. Mac: Terminal).

### Step 1: get your own copy of this repo

Use "Use this template" on GitHub if this repo is marked as a template, or
clone it and re-point the remote to a new repo you create:

```bash
git clone <this-repo-url> my-newsletter-autopilot
cd my-newsletter-autopilot
pip install -r requirements.txt
```

**Make your copy private** if your footer, pricing or CTAs are things you
don't want public. Nothing in this repo is secret by design (API keys never
get committed -- they live only in GitHub Actions secrets and your local
`.env`), but your brand voice and offers in `PLAYBOOK.md` might be things you
want to keep to yourself.

### Step 2: get four required keys, and up to two optional ones

1. **Anthropic API key.** console.anthropic.com -> API Keys -> Create key.
   Starts with `sk-ant-`.
2. **Beehiiv API key + publication ID.** app.beehiiv.com -> your publication
   -> Settings -> Integrations -> API -> create a key (Read + Write). The
   publication ID is on the same page, format `pub_...`. Create the
   publication first if this is a new one, separate from your main newsletter
   if you want a distinct cadence/brand for it.
3. **OpenAI API key** (for DALL-E 3 header images). platform.openai.com/api-keys.
   Starts with `sk-`. If you skip this, every static-image issue falls back
   to a built-in generator using your brand colors -- less unique, but never broken.
4. **Gmail address + App Password** (to receive your LinkedIn draft).
   myaccount.google.com/apppasswords -- requires 2FA on the account. This is
   a 16-character app password, NOT your regular Gmail password.
5. **(Optional) Giphy API key.** developers.giphy.com -- free. Powers the GIF
   half of the alternation. Without it, every issue is a static image instead.
6. **(Optional) Notion integration token + page ID.** See section 4c. Only
   needed if you're keeping your own research catalog.

### Step 3: fill in your four brand files

```bash
cp config/brand.example.json config/brand.json
cp PLAYBOOK.template.md PLAYBOOK.md
cp LEARNINGS.seed.md LEARNINGS.md
```

Fill in every bracketed value. `config/brand.json` is mechanical (IDs, colors,
cron, footer). `PLAYBOOK.md` is your voice and structure -- the highest-
leverage file in the whole repo; spend real time on it. `LEARNINGS.md` is
your starting beliefs; the system will refine them with evidence.

### Step 4: local dry run

```bash
DRY_RUN=1 python scripts/draft_newsletter.py   # research + analyst + draft, writes/sends nothing
python scripts/draft_newsletter.py             # the real thing
```

The first command prints the drafted title, subject and body size and stops
before any image, commit, Beehiiv draft or email. The second posts a real DRAFT to Beehiiv (never sends) and emails you the LinkedIn
copy. Open the Beehiiv editor link the script prints. Read the draft. If the
voice is off, tune `PLAYBOOK.md` and rerun -- each run costs a few cents.

### Step 5: wire GitHub Actions secrets

Repo -> Settings -> Secrets and variables -> Actions -> New repository secret.
Add every key from Step 2 with the exact names in `.env.example`.

### Step 6: adjust the cron and let it run

Edit `.github/workflows/daily.yml`'s cron expression to match your cadence
and timezone (also update `config/brand.json`'s `cadence_cron` note for your
own reference -- the workflow file is the one that actually governs
scheduling). GitHub Actions cron runs in UTC; do the timezone math once and
you're done. From here it runs itself.

---

## 6. Daily flow once it's running

```
[cron fires]        Engine runs. A few minutes.
[a few min later]   Beehiiv draft exists. LinkedIn email lands in your inbox.
[your review time]  Open Beehiiv, read, edit if needed, press Send.
                     Open the LinkedIn email, download the image/GIF, paste
                     the copy into LinkedIn, post.
[weekly, ~1 min]    Log each LinkedIn post's stats into LINKEDIN_STATS.csv.
```

Active time from your fingers: five to ten minutes a day, plus a minute a
week for the LinkedIn log.

---

## 7. What this protocol is not

- Not a "post and forget" system. Every draft waits for your review. There is
  no code path to auto-send.
- Not a distribution platform. You still post the LinkedIn variant yourself.
  Owning the publish click is part of the discipline.
- Not a subscriber management tool.
- Not an analytics dashboard -- Beehiiv's UI and your own LinkedIn analytics
  view are your dashboards. This system reads them, it doesn't replace them.
- Not generic once you've filled in `PLAYBOOK.md`. The voice rules are yours.
  If you hand this repo to someone else, they fork the structure, not your voice.

---

## 8. Troubleshooting (the real failures, in order of frequency)

1. **Beehiiv 401.** API key wrong or revoked. Regenerate, update the secret, rerun.
2. **Beehiiv 403 on draft creation.** Some Beehiiv plans gate the Posts API.
   Check your plan; the error message from `beehiiv_api.py` will say so directly.
3. **`ANTHROPIC_API_KEY reads as empty`.** Almost always a `.env` file saved
   with a UTF-8 BOM (Windows Notepad or PowerShell `Out-File` do this). Recreate
   the file in VS Code, or use `[System.IO.File]::WriteAllText(path, content,
   [System.Text.UTF8Encoding]::new($false))` in PowerShell to avoid the BOM.
4. **Claude returns malformed JSON.** Rare with Opus. If it happens, increase
   `max_tokens` in `draft_newsletter.py`'s `draft_newsletter()` call, or add
   "Return ONLY raw JSON, no markdown fences" more forcefully to the prompt.
5. **`object_not_found` from Notion (if you're using it).** You created the
   integration but never shared your research page with it -- open the page,
   "..." menu, Connections, add your integration. This is the single most
   common Notion setup failure.
6. **GIF issues always fall back to static images.** `GIPHY_API_KEY` is
   unset, or Giphy has no result for your keywords -- check that
   `gif_keywords` in the drafted JSON are literal search terms, not poetic prompts.

---

## 9. Iteration roadmap

After your first ten issues:

- Open `LEARNINGS.md`'s Analytics log. Look for the weak-spot pattern that
  repeats across issues -- that's a `PLAYBOOK.md` problem, not a one-off.
- Start logging `LINKEDIN_STATS.csv` weekly if you haven't -- the LinkedIn
  side of the learning loop is inert without it.
- Talk to a few readers who forward your issues often. What would they pay
  for? That's your next tier, not a feature of this repo.

---

*The Newsletter Autopilot Protocol. Generalized template -- your copy, your voice, your rules.*
