# LEARNINGS.md — evidence-based editorial rules (SEED TEMPLATE)

Copy this file to `LEARNINGS.md` and replace the bracketed seed rules with your
own priors -- your best guess, before you have any data, about what makes a
title/hook/topic work for YOUR audience. The learning loop reads this file at
the start of every draft and updates it at the end of every run.

It is APPEND-and-ANNOTATE — rules are never deleted, only annotated with new evidence.

Each entry has a **status**:
- `SEED` — your prior belief, entered before there is data.
- `EMERGING` — one or two posts of evidence.
- `CONFIRMED` — consistent evidence over 5+ posts.
- `STRENGTHENED` — the pattern got stronger with new data.
- `WEAKENED` — new data pushed against it.
- `REFUTED` — evidence now contradicts. (Keep the entry; annotate.)

---

## Title & subject line

- **[SEED]** [Your prior about what wins on open rate -- e.g. second-person pronouns, named entities, numbers, questions vs statements.]
- **[SEED]** [A second prior, if you have one.]

## Body voice

- **[SEED]** [What must appear in paragraph 1 -- e.g. an explicit date, a number, a named company.]
- **[SEED]** [What your signature structural move is -- e.g. a contrast frame, a before/after, a myth-vs-reality.]

## The close / call to action

- **[SEED]** [What the final section must always do -- e.g. one concrete action, never a question, always dated.]

## Signal / topic selection

- **[SEED]** [What kind of stories hit your audience hardest -- be specific to your niche.]
- **[SEED]** Do not repeat a topic covered in the last 7 published posts.
- **[SEED]** [Recency preference, if any -- e.g. "stories from the last 48 hours outperform older news re-framed."]

## Image

- **[SEED]** [Your image brand-lock, restated briefly -- keep in sync with PLAYBOOK.md.]
- **[SEED]** GIF issues (see PLAYBOOK.md alternation rule) trade brand-lock for topical relevance and shareability. Keywords should name the day's entity and theme plainly, not poetically — Giphy search rewards literal terms.

## LinkedIn hook

_Populated once LINKEDIN_STATS.csv has 2+ logged posts. Until then, the drafter
follows the same hook instincts as the email subject line._

- **[SEED]** [Your prior about what wins on LinkedIn -- usually: name a number or entity in the first two lines, above the "see more" fold.]
- **[SEED]** Comments and reposts are weighted higher than reactions when judging what's working (see `scripts/learning_loop.py` — `reactions + comments*3 + reposts*5`) because they're harder to earn and signal deeper resonance, not just a passive scroll-stop.

---

## Analytics log

_Automatically updated by the learning loop. Each run appends a dated block
with the Beehiiv metric snapshot (median open rate, median CTR, top/bottom
posts) and, once logged, the LinkedIn metric snapshot (median engagement rate,
top/bottom posts), plus any new rules the analyst extracted from either channel._
