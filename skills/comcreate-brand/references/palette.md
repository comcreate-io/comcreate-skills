# Palette and type outside HTML

Use these for DOCX, PPTX, Google Docs, Google Slides or design tools. The values mirror
the comcreate.io design-system tokens; `scripts/sync-from-site.sh` reports drift.

| Role | Hex | Site token |
|---|---|---|
| Paper (page) | `#F8F7F3` | `--bg` |
| Surface (recessed) | `#F0EFE9` | `--surface` |
| Raised | `#FFFFFF` | `--raised` |
| Ink (text) | `#171714` | `--text` |
| Ink dim (secondary) | `#5F5F5B` | `--text-dim`, flattened on paper |
| Ink faint (meta) | `#6C6C69` | `--text-faint`, flattened on paper |
| Hairline | `#D8D7D0` | `--terminal-border` |
| Cobalt | `#1F5EFF` | `--accent` |
| Cobalt bright (on dark) | `#86A4FF` | `--accent-bright` |
| Dark background | `#0C0E13` | dark-zone `--bg` |
| Dark surface / raised | `#12151C` / `#181C24` | dark-zone `--surface` / `--raised` |
| Dark text / dim | `#F1F3F7` / `#A3A5A9` | dark-zone `--text` / `--text-dim` |
| Dark hairline | `#292E38` | dark-zone `--terminal-border` |
| Success / Warning / Error | `#2D8A4E` / `#DE9300` / `#DF202E` | semantic only |

## Fonts

- **Geist** (reading) and **Geist Mono** (labels, metadata) are on Google Fonts, so Google
  Docs and Slides have them. In DOCX/PPTX, embed them or fall back to Arial and Consolas.
- **Geist Pixel** (signature display) is not on Google Fonts. In Office formats, set display
  titles in Geist 600 with tight tracking, or place the title as a rendered image.
- All Geist faces are SIL OFL 1.1 (`templates/brand/fonts/GEIST-OFL-LICENSE.txt`).

## Logo files

`assets/png/{wordmark,mark}-{ink,reverse}.png` are 2400px-wide transparent exports for Office
formats. SVG masters live in `templates/brand/logo/`. Use the ink version on paper and the
reverse version on dark or cobalt.
