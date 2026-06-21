#!/usr/bin/env bash
# Round-3 reviewer ask #1 (highest ROI): replay the 58 v1-correct repairs in
# the real ReproBreak Docker environment and convert the 62.4% "static repair
# proxy" into a real Playwright pass/fail rate.
#
# PREREQUISITE (user action): install Docker Desktop for Mac.
#   brew install --cask docker
#   open -a Docker
#   # wait until docker info works, then run this script
#
# This script is a SKELETON / TODO — once Docker is available we wire up the
# ReproBreak `reproduce.py` pipeline. The intent is recorded here so the
# next session can pick this up in one shot.

set -euo pipefail

REPRO_ROOT="${REPRO_ROOT:-$HOME/Downloads/ReproBreak/ReproBreak-main}"
HEAL_OUT="${HEAL_OUT:-$(pwd)/healreact/bench/cases/koenig/_heal_baseline.json}"
RESULTS="${RESULTS:-$(pwd)/healreact/bench/cases/koenig/_docker_replay.json}"

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

# --- 1. extract the 58 v1-correct ids ----------------------------------------
step "1. extract v1-correct case ids"
python3 - <<PY > /tmp/heal_v1_correct_ids.txt
import json
data = json.load(open("$HEAL_OUT"))
ids = [r['id'] for r in data['rows'] if r['exact_match']]
print('\n'.join(str(i) for i in ids))
PY
N=$(wc -l < /tmp/heal_v1_correct_ids.txt | tr -d ' ')
echo "found $N v1-correct cases"

# --- 2. for each id, run ReproBreak reproduce.py with our patched selector ---
step "2. per-case replay (TODO — needs ReproBreak harness wiring)"
cat <<'EOF'
NEXT WORK (this is where the integration goes):

For each id in /tmp/heal_v1_correct_ids.txt:
  a. cd "$REPRO_ROOT" && python3 reproduce.py --id <id>
       => boots koenig at the break commit, runs the original failing test
          inside its dedicated docker container, expect FAIL
  b. patch test_file_snapshot.spec.js: replace old_locator with the v1
     proposed_selector (from healreact/bench/cases/koenig/<id>/_heal.json or
     the row in $HEAL_OUT)
  c. re-run reproduce.py with the patched test, capture:
       - exit code (0 = passed)
       - playwright stdout/stderr
       - presence of "element not found" / "Timeout" / assertion failures
  d. classify each case as:
       - true-pass        : runs green
       - resolver-correct-runtime-broken : our resolver said correct, but
                                            the real test still fails
                                            (e.g. visibility, waitFor, async)
       - infrastructure-fail : the case can't even be reproduced (env issue)

OUTPUT JSON SCHEMA -> $RESULTS :
  {
    "n": <num attempted>,
    "true_pass": <int>,
    "resolver_correct_runtime_broken": <int>,
    "infrastructure_fail": <int>,
    "true_pass_rate": <float>,
    "rows": [{"id": ..., "exit_code": ..., "verdict": ...}, ...]
  }

HEADLINE PAPER METRIC THIS PRODUCES:
  end-to-end repair pass rate = true_pass / 93
This is the number that converts our current "static repair proxy 62.4%"
into a publishable real-world Playwright pass rate — the single
highest-ROI ask from the Round-3 review.
EOF

echo
echo "[stub] not running per-case replay yet — wire up ReproBreak harness next."
exit 0
