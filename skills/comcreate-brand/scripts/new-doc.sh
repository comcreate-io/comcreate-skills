#!/usr/bin/env bash
# Scaffold a ComCreate-branded print document.
# Usage: new-doc.sh <output-dir> [name]   → <output-dir>/<name>.html + <output-dir>/brand/
set -euo pipefail
SKILL="$(cd "$(dirname "$0")/.." && pwd)"
OUT="${1:?usage: new-doc.sh <output-dir> [name]}"
NAME="${2:-document}"
mkdir -p "$OUT"
rm -rf "$OUT/brand"
cp -r "$SKILL/templates/brand" "$OUT/brand"
if [[ -e "$OUT/$NAME.html" ]]; then
  echo "kept existing $OUT/$NAME.html (brand/ refreshed)"
else
  cp "$SKILL/templates/document.html" "$OUT/$NAME.html"
  echo "created $OUT/$NAME.html"
fi
