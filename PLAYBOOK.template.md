# PLAYBOOK.md — locked editorial contract (TEMPLATE)

Copy this file to `PLAYBOOK.md` and replace every `[BRACKETED]` value. This is
the ONE file the drafter treats as non-negotiable. `LEARNINGS.md` refines
*within* this contract; it never overrides it.

If you used the Claude paste-in setup (`CLAUDE_SETUP.md` / `START_HERE.md`),
Claude already asked you these questions and can write this file for you —
you should not need to fill in the brackets by hand.

## Publication

- Name: **[YOUR NEWSLETTER NAME]**
- Beehiiv publication ID: `[pub_xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx]` (also goes in `config/brand.json`)
- URL: [https://your-newsletter.beehiiv.com/]
- Cadence: [e.g. Mon-Thu, drafts generated 07:00 in your timezone]
- Audience: [who reads this -- be specific: title, seniority, company size/type, what they're responsible for]
- Tagline: [one sentence -- what this newsletter delivers, and how often]

## Voice

[2-4 sentences. Sharp and declarative? Warm and conversational? Academic and precise?
Name 2-3 things it is NOT, as much as what it is -- "not hype, not hedging" tells the
model more than "professional" does.]

## Locked body structure

[Describe the exact section order and what each section must contain. Example below --
replace with your own structure, or keep this one if it fits.]

```
<p><em>…one-line italic teaser hook…</em></p>

<h3>[SECTION 1 NAME, e.g. THE SIGNAL]</h3>
<p>…paragraph naming the event/story with an explicit date, in plain audience-native language…</p>
<p>…paragraph on what the event actually demands or means, still concrete…</p>

<h3>[SECTION 2 NAME, e.g. THE IMPLICATION]</h3>
<p><strong>…bolded one-sentence thesis…</strong> …the reasoning, tied to your newsletter's
   core thesis or worldview…</p>

<h3>[SECTION 3 NAME, e.g. THE MOVE]</h3>
<p>[The prescriptive close -- ONE concrete, scoped action the reader can take this
   week/day. Never end on a question. End on a sharpening line.]</p>
```

The script prepends a header image and appends the footer. The drafter never writes those.

## Footer (verbatim, appended by the script — also lives in `config/brand.json` as `footer_html`)

Write your own sign-off, subscribe CTA, and "work with me" links here. Keep it
in sync with `config/brand.json`'s `footer_html` field -- the script uses the
JSON version at runtime; this copy is for human reference.

## Image brand-lock

[Describe the visual style for your header images in one tight paragraph:
background treatment, one or two brand colors, mood/reference (e.g. "editorial
photography", "flat vector illustration", "watercolor"), what the image should
depict (one central metaphor of the day's topic). List what to NEVER include:
usually text, logos, faces, and whatever visual cliché is overused in your niche.]

Also set the hex values in `config/brand.json` under `image_brand` -- they drive
the fallback image generator when DALL-E is unavailable.

## Never

- Never publish. Always save as draft. You are the last human in the loop.
- Never repeat a topic from the last 7 published posts.
- Never write a headline without checking LEARNINGS.md first.
- [Add your own hard rules here.]
