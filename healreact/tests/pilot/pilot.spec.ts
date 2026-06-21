/**
 * Pilot — 5 breakages × 3 mutations on react-shopping-cart.
 *
 * Skipped by default (HEALREACT_RUN_PILOT=1 to enable) because:
 *   1. The benchmark app must be fetched (`npm run bench:fetch`) and
 *      served on $HEALREACT_BASE_URL.
 *   2. The healer needs an LLM client (OPENAI_API_KEY or a local vLLM
 *      endpoint via HEALREACT_LLM_BASE_URL).
 *
 * Each pilot case has an `expected_outcome`:
 *   - "heal"        → healer must produce a verified patch
 *   - "flag_defect" → healer must surface LIKELY_REAL_DEFECT (false-heal probe)
 *
 * Pilot gate (EXPERIMENT_PLAN §Pilot):
 *   - ≥3/5 breakages successfully healed
 *   - ≥2/3 mutations correctly flagged (NOT silently healed)
 */
import { test, expect } from "@playwright/test";
import { readFileSync, existsSync } from "node:fs";
import { resolve } from "node:path";

const PILOT_ENABLED = process.env.HEALREACT_RUN_PILOT === "1";
const CASES_PATH = resolve(
  process.cwd(),
  "bench/ReactHealBench/breakages/react-shopping-cart/pilot.jsonl",
);

interface PilotCase {
  case_id: string;
  test_file: string;
  broken_step: string;
  breakage_category: string;
  expected_outcome: "heal" | "flag_defect";
  mutation_id: string | null;
}

function loadCases(): PilotCase[] {
  if (!existsSync(CASES_PATH)) return [];
  return readFileSync(CASES_PATH, "utf8")
    .trim()
    .split("\n")
    .filter(Boolean)
    .map((l) => JSON.parse(l));
}

test.describe("Pilot — react-shopping-cart", () => {
  test.skip(!PILOT_ENABLED, "Pilot disabled. Set HEALREACT_RUN_PILOT=1 and configure LLM key.");

  const cases = loadCases();
  test.skip(cases.length === 0, `No pilot cases at ${CASES_PATH}. Build the bench first.`);

  for (const c of cases) {
    test(`${c.case_id} [${c.expected_outcome}] — ${c.breakage_category}`, async ({ page }) => {
      // Stage 2 will:
      //   1. Navigate to the failing test's entry URL
      //   2. Drive the test up to `broken_step`
      //   3. Catch failure → invoke healer (src/heal/healer.ts)
      //   4. Assert expected_outcome
      // This file currently only loads cases and gives the structure;
      // the healer wiring lands in Stage 2.
      expect(["heal", "flag_defect"]).toContain(c.expected_outcome);
    });
  }
});
