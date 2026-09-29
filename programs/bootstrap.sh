#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-$(cd "$(dirname "$0")/.." && pwd)}"
python "$ROOT/programs/ofg_index.py" --root "$ROOT"
python "$ROOT/programs/ofg_rehydrate.py" --root "$ROOT" --thread 1 --generation 2 --output "$ROOT/state/T1-G2_REHYDRATION_CAPSULE.json"
python "$ROOT/programs/ofg_rehydrate.py" --root "$ROOT" --thread 2 --generation 2 --output "$ROOT/state/T2-G2_REHYDRATION_CAPSULE.json"
python "$ROOT/programs/ofg_rehydrate.py" --root "$ROOT" --thread 4 --generation 2 --output "$ROOT/state/T4-G2_REHYDRATION_CAPSULE.json"
python "$ROOT/programs/ofg_rehydrate.py" --root "$ROOT" --thread 5 --generation 2 --output "$ROOT/state/T5-G2_REHYDRATION_CAPSULE.json"
echo '{"status":"PASS","next":"use ofg_retrieve.py or paste the generated rehydration capsule into the successor thread"}'
