---
name: comcreate-brand
description: ComCreate's own brand system for documents. Produces PDFs, proposals, one-pagers, capability overviews, reports, SOWs and case-study sheets using the comcreate.io palette and logos, Geist headings, Geist Mono labels, left-aligned layouts and direct copy. Also supplies brand assets for DOCX, PPTX and Google Docs. Use when asked for a ComCreate-branded or on-brand document, PDF or deck styling. Do not use for white-label or client-branded work.
---

# ComCreate brand (documents)

This skill adapts the comcreate.io design system for documents. The public reference is
https://comcreate.io/design-system for the palette and assets. Document defaults are
Geist headings, direct section titles and left-aligned content, as specified below.

All script paths below are relative to this skill's directory.

## Trigger boundary

Use it for documents that ComCreate itself sends: proposals, capability overviews, reports,
SOWs, leave-behinds and case-study sheets.

Stop and ask which branding applies when the document is for a client deliverable, a
white-label engagement or another agency's brand. Those must not carry ComCreate marks.
Website UI work inside the comcreate.io repository uses the repository's tokens directly.

## Workflow

1. **Scaffold.** `scripts/new-doc.sh <out-dir> <name>` writes `<name>.html` from
   `templates/document.html` plus a self-contained `brand/` folder (CSS, fonts, logos).
2. **Fill.** Replace every `{{…}}` placeholder and delete the sections you don't need.
   `grep -n '{{' <name>.html` must return nothing. Components are listed in
   [references/components.md](references/components.md).
3. **Render.** `scripts/render-pdf.sh <name>.html` prints `<name>.pdf` with headless Chrome
   or Chromium. It also writes page previews to `<name>-preview/` and lists the embedded fonts.
4. **Inspect.** Read every preview image. Look for overflow, orphaned headings, empty trailing
   pages and cover collisions. Check that headings and body copy share the left gutter.
   The default font list must show Geist and GeistMono, with no Geist Pixel or fallback
   families. GeistPixel-Circle is expected only when explicitly requested.
5. **Hand off.** Report the PDF path, the page count and what you checked.

Requirements: Chrome or Chromium (set `CHROME=/path/to/chrome` if it is not found).
Poppler (`pdftoppm`, `pdffonts`) is needed for the previews and the font check. Without it
the PDF still renders, but you must say the inspection step was skipped.

## Visual rules

- **Paper first, dark acts.** Content pages use warm paper. The cover and closing page are
  blue-black sheets.
- **Cobalt is decisive, not decorative.** Use it for eyebrows, tags, links and the cobalt
  field (one per document, two at most). Never tint rules, icons or backgrounds with it.
- **Type roles.** Geist for headings and body copy; Geist Mono for labels and metadata.
  Geist Pixel is bundled as an optional asset, not a document default. Use it only when
  explicitly requested, and then only for headings.
- **Alignment.** Left-align headings and body copy to the same content gutter. Section
  indexes and eyebrows sit above the heading. Numeric table columns may align right.
- **Hairlines and whitespace carry the structure.** No rounded cards, drop shadows,
  gradients, left-border accent bars or decorative glyphs. Corners stay square.
- **Semantic colors** (success, warning, error) carry meaning only.
- **Logo.** Use the ink wordmark on paper and the reverse wordmark on dark or cobalt. Use the
  C mark where the wordmark would be redundant. It already appears in every content-page
  header and on the cover. Never stretch, rotate, recolor, shadow or separate the sparkle
  from the C. The cyan-to-violet sparkle inside the wordmark is part of the logo.

## Copy rules

- Write **ComCreate** with two capital Cs. All-caps appears only where CSS uppercases a mono
  label.
- Use descriptive headings such as "Project overview", "Deliverables", "Fees and payment"
  and "Client inputs". Avoid slogans, stacked sentence fragments and repeated contrast
  formulas in document headings.
- Omit "Draft for review", "Confidential", review-draft notices and similar document-status
  labels unless explicitly requested. This does not make proposed scope or terms agreed;
  keep their actual approval state clear in the relevant section.
- Don't use em-dashes for pacing. Use periods, commas, colons or parentheses, and `·` inside
  mono labels. En-dashes are fine for ranges such as `weeks 1–2`.
- Ground every claim. Take company facts, services and case-study numbers from comcreate.io
  (its public MCP server exposes `comcreate_about`, `comcreate_list_services` and
  `comcreate_case_studies`) or from an internal knowledge base when one is connected. Keep the
  timeframe and caveat that come with each metric. Never invent clients, outcomes,
  credentials, trust badges or products. If the facts are missing, ask.
- Case studies published under NDA stay anonymized exactly as the site words them.
- Public contact facts: `hello@comcreate.io`, `comcreate.io` and "San Diego, California" as
  the service area. There is no street address, so don't add one.

## Other formats

For DOCX, PPTX, Google Docs or Slides, take the colors, font fallbacks and logo PNGs from
[references/palette.md](references/palette.md). Let the format's own tooling handle file
mechanics. This skill supplies the values.

## Keeping it in sync (maintainers)

When the site's design system changes, a maintainer with the site's source runs
`scripts/sync-from-site.sh <site-source-dir>`. It re-copies the logos and fonts, re-exports
the PNGs and prints a `DRIFT` line for every token that no longer matches. Fix drift in
`templates/brand/brand.css` and `references/palette.md`, then bump the skill's version.
Using the skill never requires the site's source.
Asset sync does not change these document typography, alignment or copy defaults.
