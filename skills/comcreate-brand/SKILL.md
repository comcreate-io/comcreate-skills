---
name: comcreate-brand
description: ComCreate's own brand system for documents. Produces PDFs, proposals, one-pagers, capability overviews, reports, SOWs and case-study sheets that match comcreate.io (warm paper, near-black ink, decisive cobalt, Geist, Geist Mono and Geist Pixel type, hairline ledgers, mono labels), and supplies the palette and logos for DOCX, PPTX and Google Docs. Use when asked for a ComCreate-branded or on-brand document, PDF or deck styling. Do not use for white-label or client-branded work.
---

# ComCreate brand (documents)

This skill packages the comcreate.io design system for print. The site's repository is the
source of truth: `src/lib/styles/tokens.css` holds the tokens, `src/lib/data/designSystem.ts`
holds the asset catalog and usage rules, and https://comcreate.io/design-system is the
visual reference that the print layout is modeled on.

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
   pages and cover collisions. The font list must show Geist and GeistMono, plus
   GeistPixel-Circle when display type is used. Any other family means a fallback slipped in.
5. **Hand off.** Report the PDF path, the page count and what you checked.

Requirements: Chrome or Chromium (set `CHROME=/path/to/chrome` if it is not found).
Poppler (`pdftoppm`, `pdffonts`) is needed for the previews and the font check. Without it
the PDF still renders, but you must say the inspection step was skipped.

## Visual rules

- **Paper first, dark acts.** Content pages use warm paper. The cover and closing page are
  blue-black sheets.
- **Cobalt is decisive, not decorative.** Use it for eyebrows, tags, links and one cobalt
  field per document. Never tint rules, icons or backgrounds with it.
- **Type roles.** Geist for reading, Geist Mono for labels and metadata, and Geist Pixel only
  for `h1` and `h2` statements. Never set body copy in the pixel face.
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

## Keeping it in sync

`scripts/sync-from-site.sh <path-to-site-repo>` re-copies the logos and fonts from a checkout
of the comcreate.io repository, re-exports the PNGs, and prints a `DRIFT` line for every
token that no longer matches. When it reports drift, update `templates/brand/brand.css` and
`references/palette.md`, then bump the version in the catalog.
