#!/usr/bin/env bash
# Clone the three ReactHealBench apps + pin a known-green commit for each.
# Usage: bash scripts/bench_fetch.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
APPS_DIR="${ROOT}/bench/ReactHealBench/apps"
mkdir -p "${APPS_DIR}"

clone_pinned() {
  local repo="$1"; local dir="$2"; local ref="$3"
  local target="${APPS_DIR}/${dir}"
  if [ -d "${target}/.git" ]; then
    echo "✔ ${dir} already cloned"
  else
    echo "↓ cloning ${repo} → ${dir}"
    git clone --depth 50 "${repo}" "${target}"
  fi
  (cd "${target}" && git fetch --depth 50 origin "${ref}" 2>/dev/null || true)
  (cd "${target}" && git checkout "${ref}")
}

# App 1 — react-shopping-cart (small, real e-commerce semantics)
clone_pinned "https://github.com/jeffersonRibeiro/react-shopping-cart.git" \
  "react-shopping-cart" "master"

# App 2 — react-admin demo
clone_pinned "https://github.com/marmelab/react-admin.git" \
  "react-admin" "master"

# App 3 — excalidraw (subset: the start page is small + has rich a11y)
clone_pinned "https://github.com/excalidraw/excalidraw.git" \
  "excalidraw" "master"

echo
echo "✅ all 3 ReactHealBench apps fetched under ${APPS_DIR}"
echo "   next: cd <app> && npm install && npm run build  (per app's README)"
