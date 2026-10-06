# Page anatomy

Classes are defined in `templates/brand/brand.css`. Every piece below appears in `templates/document.html`.

| Piece | Markup | Notes |
|---|---|---|
| Cover / closing | `<section class="sheet sheet--dark">` | Full bleed, no running header or footer. `meta-row` on top, `cover__body` (eyebrow, pixel `h1`, `.lead`), `cover__foot` with the reverse wordmark. |
| C-mark frame | `.reg-frame` + `logo/mark-reverse.svg` | Hairline box with a `CC / 26` corner index. Cover only, once per document. |
| Flowing content | `<section class="section">` | Uses `@page` margins. The running header carries the ink C mark; the running footer reads `ComCreate · <doc>` and `NN / TT`. Set the footer label in the document's `<style>`. |
| Section head | `.section-head` → `__index` `01` + `.eyebrow` + `h2` | Two-digit indexes from `00`. Add `.break-before` to start a section on a new page. |
| Ledger | `.ledger > .ledger__row` (title / desc / `.tag`) | The site's signature list: ink top rule, hairline rows, cobalt mono tag. Prefer it to cards. |
| Rule row | `.rule-row` (`.tag` + `p`) | "THE RULE" plus one sentence. One takeaway per section. |
| Stat strip | `.stats` (`--cols`) `> .stat` | Every number needs a `.stat__note` with its source and timeframe. |
| Table | plain `<table>`, `td.num` | Mono uppercase header, ink rule, hairline rows, tabular numerals. |
| Note | `.note` | Recessed panel for assumptions and caveats. |
| Cobalt field | `.field-cobalt` | The ask, the price or the decision. One per document, two at most. |
| Dark panel | `.panel-dark` | A dark beat inside a light page. Sparingly. |
| Terminal block | `pre` with `.prompt` / `.dim` spans | Real commands and stacks only. Never invent a CLI or product. |
| Contents | `ol.index-list` | `01 Title …… 03`. Skip it below about four pages. |
| Bracket label | `.bracket` | `[ TEXT ]` with cobalt brackets. |
| Sign-off | `.signoff` | Two signature lines with mono labels. |
| Divider | `<div class="divider">◇</div>` | Hairline rule with a centered glyph, the site's section divider. |
| Display line | `.display` | Pixel display type on any element, for one statement outside a heading. |
| Keep together | `.keep` | Prevents a page break inside the block. |

## Page setup

- Default size is US Letter. For A4, add to the document's `<style>`:
  `@page { size: A4; } :root { --page-w: 210mm; --page-h: 297mm; }`
- For documents that will be physically printed, add `class="plain-paper"` to `<html>`.
  Content pages turn white; the cover and closing stay dark.
