# Pitch charts (shape only)

Draw marketing charts the way a KlientBoost marketing-plan page *behaves*: thick strokes, numbers on the marks, a one-line doodle, KPI pills that change the grid. **Do not use their candy palette.** Colors, type, and libraries come from the host project.

## Bind to this repo

1. Find tokens, in this order:
   - CSS variables: `--background`, `--foreground`, `--primary`, `--secondary`, `--accent`, `--border`, `--muted`, `--chart-1`…`--chart-4`
   - Tailwind / theme files: `bg-background`, `text-foreground`, `border-border`
   - A `theme.ts` / design-tokens module already in the repo
   - Sibling components (buttons, cards, tables) — copy their radius, border width, and type scale
2. Map them to roles:

   | Role | Job | If missing |
   | --- | --- | --- |
   | Paper | Chart / row background | White or the page background |
   | Ink | Headlines and values | Near-black / `--foreground` |
   | Stroke | Axes, outlines, Venn pills | Ink or `--border` darkened |
   | Muted | Subheads, axis labels | Ink mixed toward paper |
   | Mist | Zebra rows | Paper mixed ~5% toward ink |
   | Line | Light grid | Stroke mixed ~70% toward paper |
   | Fill 1–4 | You / series / chips / headers | `--primary` then `--chart-*`. If none, **ink tints on paper** |
   | Doodle | Handwriting overlay | Fill 2, or italic body in Fill 2 |
   | On-fill | Type sitting on a fill | Ink if the fill is light, paper if the fill is dark |

3. **Never assume white type on a fill.** Check luminance.
4. **Never add Chart.js / Recharts / D3 / a font** just to satisfy this skill. Use HTML+SVG, or whatever is already a dependency.
5. Interactive bits (KPI pills, month toggle) should use the project's existing `Button` / toggle, not a new kit.

## Structural rules

1. **Hard outline, generous radius.** Circles, cards, tables: 2–3px stroke, radius in the project's large-radius token (or 16–28px if they have none).
2. **Put the number on the mark.** `43%` above the funnel dot. `1.6×` in the legend bar. No hover-only headline number.
3. **Color blocks as legend.** Flush full-width bars under multi-series lines. Contrasting type. Entity name on the second line.
4. **KPI pills change the chart.** Growth grid re-ranks when the selected KPI changes.
5. **Doodle overlay.** One sentence, slightly rotated, in the doodle color. It teaches ("CRO usually beats more spend"), it does not decorate.
6. **Filled table headers** (Fill 1 or Fill 4), uppercase ~11px column labels, paper/mist zebra rows.
7. **Smooth lines, fat dots.** ~4px stroke, ~7px points with a paper halo. Dotted horizontal grid only.
8. **Venn is infographic, not math.** Overlapping disks, optional multiply blend, thick stroke, dark rounded labels on the **lower rim**.

## Six types

Use the project's data. The rows below are *shape*, not numbers to copy.

### Growth grid

Ranked "where the next dollar goes" table.

- Row of pill toggles: Lead, MQL, SQL, Customer, ROAS, Revenue, Profit (or the KPIs this product actually has).
- Selected pill = Fill 1 + on-fill type.
- Columns: Priority, gain, what, investment, speed.
- Changing the pill swaps the ranked rows. CRO / pages should often beat "spend more" when the story is revenue or profit.

Implementation: an HTML `<table>` (or the project's Table primitive) is enough. Do not reach for a chart library.

### Velocity lines

Multi-series over a few periods (months).

- Smooth path, 4px stroke, dots with paper halo.
- Y ticks as multipliers (`0.65×`) or the unit the data uses.
- Under the plot: N flush bars, one per series, Fill 1–N, summary number on line 1, name on line 2.

Implementation: inline SVG if the project has no line-chart helper. If Recharts/Chart.js exists, turn off default grid chrome and restyle to stroke + fills above.

### Stage area

Funnel conversion by stage (Traffic → Closed, or this product's stages).

- Area fill = Fill 1 at ~55% opacity. Line = stroke. Dots = Fill 2.
- Percent label above each dot. Stage name on the x-axis. Dashed drop from dot to axis.
- Optional Current / Last period pills using Fill 2 when selected.

Values are **stage conversion**, not remaining volume — a later stage can read higher than an earlier one.

### Overlap circles

Who shares query / audience / backlink space.

- 3–4 disks, Fills 1–4, thick stroke, labels in stroke-colored pills on the rim.
- Names from the actual domains or products. Do not stamp `competitor.com` on every circle.

Implementation: SVG `<circle>` + `<rect>` pills. Skip a Venn math library.

### Leader quadrant

Satisfaction (X) vs presence (Y), or the two axes this narrative needs.

- Rounded plot frame, light grid, hard cross at mid.
- Corner chips: Contenders / Leaders / Niche / High Performers (or local names) in Fills 1–4.
- Everyone is a small stroke-colored dot. The subject is a larger Fill-1 disk labeled `YOU` (or the product name) in on-fill type.

### Opportunity table

Keyword or gap list.

- Header in Fill 4 (or Fill 1 if only one brand color exists).
- Columns: item, volume or size, cost, call.
- High / Medium as pills in Fill 3 / Fill 2.

## Frame

Every chart sits in a rounded, stroked card:

- Headline (ink, extra-bold)
- One-line subhead (muted)
- Doodle, top-right, rotated ~−6deg
- Chart body

Use the project's Card if it already has a thick border. If not, a `div` with `border-2` and the stroke token is enough.

## What not to copy

G2 Grid branding, trophy mascots, KlientBoost live client numbers, cyan/coral/cream as a default theme, and any standalone "chart studio" app. Keep the shape. Inherit the site.
