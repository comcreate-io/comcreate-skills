#!/usr/bin/env bash
# Scaffold a ComCreate-branded print document.
# Usage: new-doc.sh <output-dir> [name]   → <output-dir>/<name>.html + <output-dir>/brand/
# An existing <output-dir>/brand/ is refreshed only if this script created it.
set -euo pipefail
SKILL="$(cd "$(dirname "$0")/.." && pwd)"
OUT="${1:?usage: new-doc.sh <output-dir> [name]}"
NAME="${2:-document}"
MARKER=".comcreate-brand"
mkdir -p "$OUT"
if [[ -e "$OUT/brand" ]]; then
  if [[ ! -f "$OUT/brand/$MARKER" ]]; then
    echo "error: $OUT/brand exists and was not created by new-doc.sh; refusing to replace it" >&2
    exit 1
  fi
  rm -rf "$OUT/brand"
fi
cp -R "$SKILL/templates/brand" "$OUT/brand"
touch "$OUT/brand/$MARKER"
if [[ -e "$OUT/$NAME.html" ]]; then
  echo "kept existing $OUT/$NAME.html (brand/ refreshed)"
else
  cp "$SKILL/templates/document.html" "$OUT/$NAME.html"
  echo "created $OUT/$NAME.html"
fi
