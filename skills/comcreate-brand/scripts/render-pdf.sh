#!/usr/bin/env bash
# Render a ComCreate HTML document to PDF with headless Chrome/Chromium, then
# rasterize every page to PNG so the result can be inspected before hand-off.
# Usage: render-pdf.sh <doc.html> [out.pdf]
# Set CHROME=/path/to/chrome if the browser is not found automatically.
set -euo pipefail
IN="${1:?usage: render-pdf.sh <doc.html> [out.pdf]}"
IN="$(cd "$(dirname "$IN")" && pwd)/$(basename "$IN")"
OUT="${2:-${IN%.html}.pdf}"
OUT="$(mkdir -p "$(dirname "$OUT")" && cd "$(dirname "$OUT")" && pwd)/$(basename "$OUT")"

find_chrome() {
  [[ -n "${CHROME:-}" ]] && { echo "$CHROME"; return; }
  local c
  for c in google-chrome-stable google-chrome chromium chromium-browser chrome; do
    command -v "$c" >/dev/null 2>&1 && { command -v "$c"; return; }
  done
  for c in "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
           "/Applications/Chromium.app/Contents/MacOS/Chromium"; do
    [[ -x "$c" ]] && { echo "$c"; return; }
  done
  return 1
}
CHROME_BIN="$(find_chrome)" || { echo "error: Chrome/Chromium not found; set CHROME=/path/to/chrome" >&2; exit 1; }

"$CHROME_BIN" --headless=new --disable-gpu --no-pdf-header-footer \
  --run-all-compositor-stages-before-draw --virtual-time-budget=5000 \
  --print-to-pdf="$OUT" "file://$IN" 2>/dev/null
[[ -s "$OUT" ]] || { echo "error: Chrome produced no PDF" >&2; exit 1; }
echo "pdf:     $OUT"

if command -v pdftoppm >/dev/null 2>&1; then
  PREV="${OUT%.pdf}-preview"
  rm -rf "$PREV" && mkdir -p "$PREV"
  pdftoppm -r 60 -png "$OUT" "$PREV/page"
  echo "pages:   $(ls "$PREV" | wc -l | tr -d ' ')"
  echo "preview: $PREV/ (inspect every page before hand-off)"
else
  echo "warning: pdftoppm (poppler) not found; previews skipped, inspect the PDF directly" >&2
fi

# Font check: Geist faces must be embedded; any other family is a fallback.
if command -v pdffonts >/dev/null 2>&1; then
  echo "fonts:   $(pdffonts "$OUT" | awk 'NR>2{print $1}' | sed 's/^[A-Z]*+//' | sort -u | tr '\n' ' ')"
else
  echo "warning: pdffonts (poppler) not found; font check skipped" >&2
fi
