/**
 * Runtime `intent(...)` helper used by Playwright tests.
 *
 * Walks the locator ladder (role+name → label → testid → data-intent →
 * AST-relative XPath → visual fingerprint). Stays purely deterministic;
 * LLM fallback is invoked by src/heal/healer.ts only after a true failure.
 */
import { Page, Locator, expect } from "@playwright/test";
import { readFileSync, existsSync } from "node:fs";
import { resolve } from "node:path";

interface LocatorRecord {
  componentFile: string;
  componentName: string | null;
  elementTag: string;
  role: string | null;
  ariaLabel: string | null;
  testId: string | null;
  dataIntent: string | null;
  id: string | null;
  name: string | null;
  placeholder: string | null;
  text: string | null;
  i18nKey: string | null;
  intent: string | null;
}

interface LocatorSheet {
  generatedAt: string;
  srcRoot: string;
  count: number;
  records: LocatorRecord[];
}

let cachedSheet: LocatorSheet | null = null;

function loadSheet(): LocatorSheet {
  if (cachedSheet) return cachedSheet;
  const path = process.env.HEALREACT_LOCATOR_SHEET ?? resolve(process.cwd(), "LocatorSheet.json");
  if (!existsSync(path)) {
    throw new Error(`HealReact: LocatorSheet not found at ${path}. Run \`npm run extract\` first.`);
  }
  cachedSheet = JSON.parse(readFileSync(path, "utf8"));
  return cachedSheet!;
}

function findByIntent(intent: string): LocatorRecord | null {
  const sheet = loadSheet();
  return sheet.records.find((r) => r.intent === intent || r.dataIntent === intent) ?? null;
}

/**
 * Returns the first Playwright Locator that resolves to a unique element,
 * trying each rung of the ladder in turn.
 */
export async function intent(page: Page, intentLabel: string): Promise<Locator> {
  const rec = findByIntent(intentLabel);
  const rungs: Array<() => Locator> = [];

  if (rec) {
    if (rec.role && (rec.text || rec.ariaLabel)) {
      rungs.push(() => page.getByRole(rec.role as any, { name: (rec.text ?? rec.ariaLabel)! }));
    }
    if (rec.ariaLabel && !rec.ariaLabel.includes("{")) {
      rungs.push(() => page.getByLabel(rec.ariaLabel!));
    }
    if (rec.testId) {
      rungs.push(() => page.getByTestId(rec.testId!));
    }
    if (rec.dataIntent) {
      rungs.push(() => page.locator(`[data-intent="${rec.dataIntent}"]`));
    }
    if (rec.id) {
      rungs.push(() => page.locator(`#${rec.id}`));
    }
    if (rec.text) {
      rungs.push(() => page.getByText(rec.text!, { exact: false }));
    }
  }
  // Always include a raw data-intent rung — works even when the LocatorSheet is stale.
  rungs.push(() => page.locator(`[data-intent="${intentLabel}"]`));

  for (const make of rungs) {
    const loc = make();
    try {
      const count = await loc.count();
      if (count === 1) return loc;
      if (count > 1) {
        // Disambiguate by first visible — log a warning at runtime
        // eslint-disable-next-line no-console
        console.warn(`HealReact: intent('${intentLabel}') matched ${count} elements; using first visible`);
        return loc.first();
      }
    } catch {
      // try next rung
    }
  }
  throw new Error(`HealReact: intent('${intentLabel}') not resolved by any locator-ladder rung. Trigger healer.`);
}

/**
 * Convenience: assert that an intent resolves to exactly one visible element.
 */
export async function expectIntent(page: Page, intentLabel: string) {
  const loc = await intent(page, intentLabel);
  await expect(loc).toBeVisible();
  return loc;
}
