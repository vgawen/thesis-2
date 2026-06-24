#!/usr/bin/env bash
# Round-3 reviewer ask #1 (highest ROI): replay the v1-exact repairs in the
# real ReproBreak Docker environment and convert the 62.4% "static repair
# proxy" into a real Playwright pass/fail measurement.
#
# PREREQUISITE (user action): install Docker Desktop for Mac.
#   brew install --cask docker
#   open -a Docker
#   # wait until docker info works, then run this script
#
# This file is now a thin wrapper around docker_replay_minimal.py. Use
# --limit/--ids for smoke tests before attempting all 58 v1-exact cases.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HEALREACT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
REPRO_ROOT="${REPRO_ROOT:-$HOME/Downloads/ReproBreak/ReproBreak-main}"
HEAL_OUT="${HEAL_OUT:-$HEALREACT_ROOT/bench/cases/koenig/_abl_w1_f1.json}"
RESULTS="${RESULTS:-$HEALREACT_ROOT/bench/cases/koenig/_docker_replay_minimal.json}"

step() { printf "\n\033[1;34m== %s ==\033[0m\n" "$*"; }

# --- 0. sanity ---------------------------------------------------------------
step "0. preflight"
if ! command -v docker >/dev/null; then
  echo "ERROR: docker not installed." >&2
  echo "  brew install --cask docker && open -a Docker" >&2
  exit 1
fi
if ! docker info >/dev/null 2>&1; then
  echo "ERROR: docker daemon not running. Start Docker Desktop." >&2
  exit 1
fi
if [[ ! -d "$REPRO_ROOT" ]]; then
  echo "ERROR: ReproBreak repo not found at $REPRO_ROOT" >&2
  exit 1
fi
if [[ ! -f "$HEAL_OUT" ]]; then
  echo "ERROR: heal_baseline output not found at $HEAL_OUT — run heal_baseline.py first" >&2
  exit 1
fi
if [[ -n "${PYTHON_BIN:-}" ]]; then
  :
elif [[ -x "$REPRO_ROOT/.venv/bin/python" ]]; then
  PYTHON_BIN="$REPRO_ROOT/.venv/bin/python"
else
  PYTHON_BIN="python3"
fi

# --- 1. run minimal replay ----------------------------------------------------
step "1. run minimal replay"
echo "ReproBreak root : $REPRO_ROOT"
echo "Heal output     : $HEAL_OUT"
echo "Results         : $RESULTS"
echo "Python          : $PYTHON_BIN"
echo
echo "Tip: smoke-test first, e.g.:"
echo "  $0 --limit 1"
echo "  $0 --ids 615,702,703"
echo

PYTHONUNBUFFERED=1 "$PYTHON_BIN" "$SCRIPT_DIR/docker_replay_minimal.py" \
  --repro-root "$REPRO_ROOT" \
  --heal-out "$HEAL_OUT" \
  --out "$RESULTS" \
  "$@"
