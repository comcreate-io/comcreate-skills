---
name: klientboost-playbook
description: Write and operate like an outcome marketing agency in the KlientBoost mold, and draw pitch charts in that shape using whatever stack and design tokens the current repo already has. Use when drafting agency sites, proposals, lead magnets, landing pages, PPC/CRO plans, case studies, marketing charts, growth grids, funnel graphs, or when the user mentions KlientBoost, outcome marketing, SKAGs, Breadcrumb Technique, or charts like that.
---

# KlientBoost playbook

Apply the **operating system**, not the brand. Steal the mechanics. Do not clone headlines, trademarks (Kite, Growth Grid, Boost Sauce, KlientBoost Kitchen), case-study numbers, or client lists.

This skill binds to the **host project**. It must not bring its own app, palette, or chart library. Bind to the project you are already in.

## In the host project (do this first)

Before writing copy, pages, or charts:

1. **Detect the stack.** Look at the repo root: `package.json`, `pyproject.toml`, `Gemfile`, existing `app/` or `src/`. Use that language and those components. Do not scaffold Next.js, Vite, or a chart studio.
2. **Detect design language.** Prefer existing tokens over any palette in this skill (there is none). Search `globals.css`, `tailwind.config.*`, `theme.ts`, CSS variables (`--background`, `--foreground`, `--primary`, `--chart-*`), and sibling UI. Paper / ink / stroke / up to four brand fills come from **this** project. If fills are missing, use monochrome tints of ink on paper.
3. **Reuse what they draw with.** If the repo already has Recharts, Chart.js, Visx, shadcn charts, matplotlib, or HTML tables — use that. Do not add a second chart library. Do not add fonts (Caveat, Nunito) unless the project already loads them.
4. **Put work where their work lives.** A growth grid on a marketing page belongs next to that page, in their layout and routing. A dashboard chart belongs in their dashboard folder.

Read the matching reference only when the task needs it:

- Voice, headlines, proof language → [references/voice-and-copy.md](references/voice-and-copy.md)
- Lead magnet, pricing, page architecture → [references/offers-and-pages.md](references/offers-and-pages.md)
- Named PPC / CRO / email recipes → [references/tactics.md](references/tactics.md)
- Pitch charts and graphs → [references/charts.md](references/charts.md)

## What they actually sell

They do not sell "PPC management." They sell **hitting a business goal**, with paid media as one lever.

The commercial stack, in order:

1. **Outcome** — pipeline, revenue, profit, SQL volume. Not clicks.
2. **Accountability** — every service has a goal. Pace KPI% against time%. If a service is behind, add resources. If it cannot hit, kill it.
3. **Financial math** — rank the next dollar by revenue ROI and speed (CRO and landing pages often beat more ad spend).
4. **Channel execution** — paid search, paid social, CRO, landing pages, SEO, email, creative, BI. One roof so ads and post-click experience move together.
5. **Proprietary ops** — software that tracks goal pacing, ICP traffic quality, anomalies, and recommended next moves.

Default engagement: **ads + landing pages + CRO + attribution in one retainer**, not a media-only scope.

## How they win the sale

The whole site is one funnel. Primary CTA is never "Contact us."

**Give away a $10k-feeling marketing plan.** The plan is the product demo: ICP jobs-to-be-done, competitor ads/keywords, mocked ads and landing pages, CRM conversion assumptions, and a ranked investment grid. Pricing appears as **three options** inside that plan, with an ROI story of how fast the retainer pays for itself.

The plan page **shows the deliverable first**, then asks the visitor to continue. That is their own Breadcrumb Technique: easy yes before the hard ask.

Proof is industrial:

- Live goal-hit rate in the sticky bar ("We hit 83% of client goals in Q2")
- Volume claims (200+ case studies, 600+ reviews, 250+ active clients)
- Celebrity operator quotes (CRO/PPC names the buyer already trusts)
- Objection-indexed reviews (cost, speed, proactivity, "bad things")
- "Take our ideas even if we don't work together"

## How they run the work

| Cadence | What it is for |
| --- | --- |
| North-star / business KPI | What leadership actually watches (leads, pipeline, revenue) |
| Channel KPI | What the team can move this month (CVR, CPA, qualified traffic) |
| Experiment KPI | The single metric on a 2-week test |

Prioritize tests with **ICE** (Impact, Confidence, Ease). Cap experiments at ~two weeks. Do not run a six-month "redesign" as one test.

**KPI% vs time%** decides action size. Behind on the goal with 40% of the quarter left → bigger moves, more people, or cut the tactic. Ahead → scale the winner with the financial math already done.

Optimize to **closed-won / pipeline**, not form fills. Connect ads to CRM. Bid and report on quality of traffic (ICP share), not just volume.

## Copy defaults

- Specific numbers beat adjectives. If you cannot cite a real number, do not invent one.
- Insult the **category** ("typical agencies"), never the prospect.
- H1 = outcome. H2 = contrast or proof. CTA = the plan / the next easy yes.
- Name the tactic. A named recipe is more memorable than a best-practice paragraph.
- Humor is allowed if the sentence still sells. Cut jokes that do not carry a point.
- One primary CTA per view. Repeat it; do not add a second competing action.

Full voice rules and rewrite patterns: [references/voice-and-copy.md](references/voice-and-copy.md)

## Page defaults

Every money page:

1. Sticky proof + CTA
2. Outcome H1 / contrast H2
3. Single primary CTA
4. Mechanism (why this works)
5. Named proof (logos, case studies, reviews)
6. Checklist of work included (make "doing the job" visible)
7. Engagement menu (audit → manage → performance)
8. FAQ as objections
9. Same CTA again

Do not publish a pricing table. Reverse-engineer budget from the goal. Offer faster / slower / more-channels options.

## Landing-page defaults

Paid traffic does not hit a homepage.

- Message match from keyword → ad → headline → hero
- Attention ratio near 1:1 (one page, one action, no nav)
- Breadcrumb forms for high-ask CTAs (quote, demo, consult): easy anonymous questions first, name/email/phone last
- Fewer fields only for low-ask CTAs (ebook, webinar)
- ICE-ranked tests, single-variable when traffic is thin
- Confirmation page has a next step

## Hard rules

- Do not copy KlientBoost trademarks, mascots, exact headlines, or their published metrics as if they were ours.
- Do not claim case-study results you cannot source.
- Do not sell hours as the product. Sell goals, options, and time-to-payback.
- Do not separate "we'll get the clicks" from "the page has to convert."
- If a channel cannot be tied to a business goal, do not recommend it.
- Do not ship a standalone chart app, a canned candy palette, or a new framework to "demo" this skill.
