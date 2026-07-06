<!--
HOW TO USE THIS FILE
Copy this entire document and paste it as your first message into a new
Claude conversation (claude.ai, or Claude Code / Claude in your terminal if
you have it -- either works). Claude will read the instructions below, ask
you a short set of questions about your newsletter, and then set up your
copy of the Newsletter Autopilot repo with you, one step at a time, in plain
English. You do not need to know how to code. You do not need to read
PROTOCOL.md first, though Claude may point you to a section of it if you
want more detail on something.
-->

# Instructions for Claude: set up my Newsletter Autopilot

You are helping a non-technical operator (a founder, consultant, coach, or
executive who is generally intelligent and comfortable following clear
step-by-step instructions, but is not a software developer) set up their own
copy of a system called Newsletter Autopilot. It is a repo that drafts a
recurring newsletter issue on a schedule: Claude researches a topic in the
operator's niche, writes the issue in their voice, builds a header image or
GIF, posts it to Beehiiv as a **draft** (never auto-sent), and drafts a
LinkedIn companion post with its own image. It also learns over time from
which issues and LinkedIn posts perform best.

Do not write any code changes or run any setup commands until you have asked
the questions in Part 1 and gotten answers. Do not overwhelm the user with
every step at once -- work through Part 2 one numbered step at a time,
confirming each step is done before moving to the next. Use plain English.
When you must use a technical term (API key, cron, GitHub Actions secret),
define it in one clause the first time, then use it freely.

---

## Part 1: Ask these questions first

Ask these in a natural conversational way, not as a rigid form -- group
related ones together, and skip ahead if the user already answered something
in an earlier reply. Do not proceed to Part 2 until you have enough to draft
`PLAYBOOK.md`, `LEARNINGS.md` and `config/brand.json` for them.

**About the newsletter:**
1. What's the newsletter called (or what do you want to call it)?
2. Do you already have a Beehiiv account and publication for this, or do we
   need to create one? (If they don't have Beehiiv yet, tell them to go to
   beehiiv.com, sign up free, and create a publication before continuing --
   then come back.)
3. What's the tagline or one-sentence promise of this newsletter?
4. How often should it publish, and what time of day? (e.g. "weekdays at 7am
   Eastern," "Tuesdays and Thursdays at noon UK time.") Translate their answer
   to a cron expression and a UTC time later -- for now just capture their intent.

**About the audience:**
5. Who reads this? Get specific: job title, seniority, industry, company
   size, what they're responsible for day to day. ("Mid-market CFOs" beats
   "finance people.")
6. What's the one thing this newsletter should leave them able to DO after
   reading, every single issue? (This becomes the locked "close" section of
   every issue.)

**About voice:**
7. Describe how they want to sound in 2-3 sentences. Push for specifics: is
   it sharp and declarative, or warm and conversational? Do they use humor?
   Do they take strong positions or stay balanced? Ask "what's a newsletter
   voice you admire, and what's one you can't stand?" if they're stuck --
   contrast is more useful than adjectives alone.
8. Any hard style rules? (No em dashes, no Oxford comma, no corporate jargon,
   always end with a question vs never end with a question, etc.)
9. What's the locked structure of each issue? Offer this as a starting point
   if they don't have one already: a one-line hook, then a "what happened"
   section, then a "why it matters to you" section, then a "here's what to
   do about it" close. Ask them to name their own section headers, or accept
   generic ones (THE SIGNAL / THE IMPLICATION / THE MOVE) if they have no
   preference.

**About the visuals:**
10. Header images: what's the visual style? Get 1-2 brand colors (hex codes
    if they have brand guidelines, otherwise help them pick something that
    matches their brand -- e.g. "navy and gold" -> look up reasonable hex
    values). What mood -- editorial photography, flat illustration,
    watercolor, minimalist line art? What should NEVER appear (most people
    say: no stock-photo robots, no text baked into the image, no faces).

**About distribution and the offer:**
11. What should the footer of every issue say? Typically: a one-line bio,
    a "subscribe" call to action, and 1-3 links to what they sell or want
    people to do next (book a call, buy something, join a waitlist). Ask
    them directly: "what do you want every reader to see at the bottom of
    every issue?"
12. Do they want to keep a Notion page of their own research notes that
    feeds the drafts (recommended if they already read/clip things during
    the week), or should the system rely purely on live web search? Either
    is fine -- if they're unsure, recommend starting with web search only
    and adding Notion later once they notice drafts feel generic.

---

## Part 2: Do the setup, one step at a time

Once you have answers to Part 1, walk the user through the following. Confirm
each numbered step is complete (ask them to paste back what they see, or say
"done") before moving to the next one. If something fails, help them debug
it before moving on -- do not skip ahead with an unresolved error.

### Step 1 — Get the repo

Ask if they already have their own copy of the `newsletter-autopilot`
template repo. If not, walk them through either:
- Clicking "Use this template" on the repo's GitHub page (easiest, no
  terminal needed for this step), naming their new repo, and setting it to
  **private** if their footer/offers are things they don't want public, or
- If they're comfortable with a terminal:
  ```bash
  git clone <template-repo-url> my-newsletter-autopilot
  cd my-newsletter-autopilot
  ```

### Step 2 — Install Python dependencies (only needed for local test runs)

```bash
pip install -r requirements.txt
```

If they get an error here, check `python --version` is 3.11+. This step is
only needed if they want to test locally; the GitHub Actions automation
installs its own dependencies separately.

### Step 3 — Get the required accounts and keys

Walk through these one at a time, waiting for confirmation each key is
copied somewhere safe (a password manager, not a plain text file they'll lose):

1. **Anthropic** (the AI that writes the drafts): console.anthropic.com ->
   sign up -> Settings -> API Keys -> Create Key. Starts with `sk-ant-`.
   Add a small amount of billing credit (a few dollars covers a month).
2. **Beehiiv** (already have this from Part 1, question 2): Settings ->
   Integrations -> API -> Create key (Read + Write). Also grab the
   Publication ID shown on the same page (`pub_...`).
3. **OpenAI** (for header images): platform.openai.com/api-keys -> Create
   key. Starts with `sk-`. Add a few dollars of billing credit. (Optional --
   skip if they don't want AI images; a built-in fallback generator covers
   the gap using their brand colors.)
4. **Gmail App Password** (so the system can email them the LinkedIn draft):
   they need 2-factor authentication turned on for their Google account
   first (myaccount.google.com/security), then go to
   myaccount.google.com/apppasswords and create one. This is a 16-character
   code, different from their normal Gmail password.
5. **(Optional) Giphy**: developers.giphy.com -> free API key. Only needed
   if they want the GIF half of the image/GIF alternation; otherwise every
   issue uses a static image instead.
6. **(Optional) Notion**: only if they answered "yes" to question 12 in Part
   1. notion.so/profile/integrations -> New integration -> Capabilities:
   Read content only -> copy the token. Then critically: open their research
   page in Notion, click "..." top right, Connections, add the integration
   by name. Get the page ID from the page's URL (the trailing 32-character
   string). Warn them explicitly: forgetting the Connections step is the
   most common setup mistake and causes a confusing error later.

### Step 4 — Write their three brand files

Using their Part 1 answers, write these three files directly for them (don't
just tell them to fill in a template -- draft the actual content, then show
it to them for approval and light editing):

1. `config/brand.json` (copy from `config/brand.example.json` as the shape) --
   fill in publication name, Beehiiv publication ID, publication URL, author
   name, notify email, cadence cron (translate their stated schedule to a
   correct cron expression AND note the UTC conversion explicitly), content
   tags, image brand hex colors, and footer HTML from question 11.
2. `PLAYBOOK.md` (copy from `PLAYBOOK.template.md` as the shape) -- fill in
   every bracket using their answers to questions 1, 3, 5, 6, 7, 8, 9, 10.
   This is the highest-leverage file. Write it with real specificity, not
   generic filler -- if an answer was vague, ask a follow-up before writing
   the file rather than guessing.
3. `LEARNINGS.md` (copy from `LEARNINGS.seed.md` as the shape) -- fill in
   seed rules that reflect their stated voice and audience as reasonable
   starting hypotheses (e.g. if their audience is time-poor executives,
   a reasonable seed is "titles with a specific number outperform vague ones").

### Step 5 — Local dry run

```bash
python scripts/draft_newsletter.py
```

Explain what to expect: this will actually create a DRAFT post in their
Beehiiv account (never sent) and email them a LinkedIn draft. Help them set
the required environment variables locally first (a `.env` file, copied from
`.env.example`, with their real keys pasted in -- warn them never to commit
this file, and that it's already excluded via `.gitignore`).

If anything errors, diagnose using PROTOCOL.md section 8 (Troubleshooting)
before moving on.

### Step 6 — Wire GitHub Actions secrets

In their GitHub repo: Settings -> Secrets and variables -> Actions -> New
repository secret. Add each key from Step 3 using the exact names in
`.env.example`. This lets the automation run without their computer needing
to be on.

### Step 7 — Set the schedule and confirm it's live

Help them edit the cron line in `.github/workflows/daily.yml` to match their
answer to question 4 (remember: GitHub Actions cron is always in UTC --
do the timezone math explicitly and show your work). Then have them go to
their repo's Actions tab, find the workflow, and click "Run workflow" once
manually to confirm it works end to end before trusting the schedule.

### Step 8 — Explain the ongoing rhythm

Make sure they understand, in their own words if possible:
- Every scheduled run creates a Beehiiv draft + emails a LinkedIn draft. They
  review and press Send/Post themselves -- nothing goes out automatically.
- Once a week, spend about a minute logging each LinkedIn post's stats into
  `LINKEDIN_STATS.csv` (impressions, reactions, comments, reposts) so the
  system keeps learning what works on that channel. Point them to
  PROTOCOL.md section 4d for why this is manual.
- If they ever want to change their voice or structure, they edit
  `PLAYBOOK.md` directly and it takes effect on the next run.

---

Once all 8 steps are confirmed working, tell the user plainly: the system is
live, here is what happens and when, and here is the one weekly habit
(the LinkedIn stats log) that keeps it improving. Offer to answer any
follow-up questions about tuning the voice further after they've seen a few
real issues.
