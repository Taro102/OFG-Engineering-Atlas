#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-$(cd "$(dirname "$0")/.." && pwd)}"
PYTHON="${PYTHON:-python}"
MODE=(); if [[ "${2:-}" == "--candidate" ]]; then MODE=(--candidate); fi
"$PYTHON" "$ROOT/programs/ofg_current.py" --root "$ROOT" "${MODE[@]}"
"$PYTHON" "$ROOT/programs/ofg_index.py" --root "$ROOT" "${MODE[@]}"
for t in 1 2 4 5; do
  "$PYTHON" "$ROOT/programs/ofg_rehydrate.py" --root "$ROOT" --thread "$t" "${MODE[@]}" --output "$ROOT/generated/rehydration/T$t.json"
done
echo '{"status":"PASS","authority_effect":"NONE","outputs":"generated/"}'
