#!/usr/bin/env bash
# Re-sync brand assets from the comcreate.io repo (source of truth) and flag
# token drift between the site's tokens.css and this skill's brand.css.
# Usage: sync-from-site.sh <path-to-site-repo>   (or set COMCREATE_SITE_REPO)
# The site repo is the SvelteKit app that serves comcreate.io (it contains
# src/lib/styles/tokens.css and static/logo.svg).
set -euo pipefail
SKILL="$(cd "$(dirname "$0")/.." && pwd)"
REPO="${1:-${COMCREATE_SITE_REPO:-}}"
[[ -n "$REPO" ]] || { echo "usage: sync-from-site.sh <path-to-site-repo>" >&2; exit 2; }
[[ -f "$REPO/src/lib/styles/tokens.css" && -f "$REPO/static/logo.svg" ]] || {
  echo "error: $REPO does not look like the comcreate.io site repo" >&2; exit 2; }
B="$SKILL/templates/brand"
cp "$REPO/static/logo.svg"                         "$B/logo/wordmark-ink.svg"
cp "$REPO/static/logo-dark.svg"                    "$B/logo/wordmark-reverse.svg"
cp "$REPO/static/brand/comcreate-mark-ink.svg"     "$B/logo/mark-ink.svg"
cp "$REPO/static/brand/comcreate-mark-reverse.svg" "$B/logo/mark-reverse.svg"
cp "$REPO/static/fonts/Geist-Variable.woff2" "$REPO/static/fonts/GeistMono-Variable.woff2" \
   "$REPO/static/fonts/GeistPixel-Circle.woff2" "$REPO/static/fonts/GeistPixel-Square.woff2" \
   "$REPO/static/brand/fonts/GEIST-OFL-LICENSE.txt" "$B/fonts/"
if command -v magick >/dev/null 2>&1; then
  for f in "$B"/logo/*.svg; do
    magick -background none -density 600 "$f" -resize 2400x "$SKILL/assets/png/$(basename "${f%.svg}").png"
  done
else
  echo "warning: ImageMagick not found; assets/png not re-exported" >&2
fi
echo "assets synced from $REPO"

# Token drift: compare hex tokens in the site's light :root and dark-zone blocks
# against this skill's brand.css.
python3 - "$REPO/src/lib/styles/tokens.css" "$B/brand.css" <<'PY'
import re, sys
site, mine = (open(p, encoding="utf-8").read() for p in sys.argv[1:3])

def block(css, opener):
    start = css.index(opener)
    return css[start:css.index("\n}", start)]

def hexes(css):
    return {m[0]: m[1].lower() for m in re.findall(r"--([a-z0-9-]+):\s*(#[0-9a-fA-F]{3,8})\s*;", css)}

light = hexes(block(site, ":root {"))
dark = hexes(block(site, ":root[data-footer-dark] {"))
skill = hexes(block(mine, ":root {"))
pairs = [(light, t, t) for t in ["bg", "surface", "raised", "text", "terminal-accent",
                                  "terminal-dim", "terminal-border", "accent", "accent-bright"]]
pairs.append((light, "terminal-green", "color-success"))
pairs += [(dark, t, "dark-" + t) for t in ["bg", "surface", "raised", "text"]]
pairs.append((dark, "terminal-border", "dark-border"))

drift = False
for source, site_name, skill_name in pairs:
    a, b = source.get(site_name), skill.get(skill_name)
    if a and a != b:
        print(f"DRIFT --{site_name}: site {a}, skill {b}")
        drift = True
print("tokens: update templates/brand/brand.css and references/palette.md" if drift else "tokens: in sync")
PY
