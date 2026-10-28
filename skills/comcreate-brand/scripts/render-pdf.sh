#!/usr/bin/env bash
# Render a ComCreate HTML document to PDF with headless Chrome/Chromium, then
# rasterize every page to PNG so the result can be inspected before hand-off.
# Usage: render-pdf.sh <doc.html> [out.pdf]
# Set CHROME=/path/to/chrome if the browser is not found automatically.
set -euo pipefail
IN="${1:?usage: render-pdf.sh <doc.html> [out.pdf]}"
[[ -f "$IN" ]] || { echo "error: input not found: $IN" >&2; exit 1; }
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

URI="$(python3 -c 'import pathlib, sys; print(pathlib.Path(sys.argv[1]).as_uri())' "$IN")"
LOG="$(mktemp)"
trap 'rm -f "$LOG"' EXIT
rm -f "$OUT"
if ! "$CHROME_BIN" --headless=new --disable-gpu --no-pdf-header-footer \
  --run-all-compositor-stages-before-draw --virtual-time-budget=5000 \
  --print-to-pdf="$OUT" "$URI" 2>"$LOG" || [[ ! -s "$OUT" ]]; then
  echo "error: Chrome produced no PDF. Browser output:" >&2
  tail -n 20 "$LOG" >&2
  exit 1
fi
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

# Font check: expect Geist and Geist Mono by default. Pixel is explicit opt-in only.
if command -v pdffonts >/dev/null 2>&1; then
  echo "fonts:   $(pdffonts "$OUT" | awk 'NR>2{print $1}' | sed 's/^[A-Z]*+//' | sort -u | tr '\n' ' ')"
else
  echo "warning: pdffonts (poppler) not found; font check skipped" >&2
fi
