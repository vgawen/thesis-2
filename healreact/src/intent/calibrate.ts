/**
 * L1 intent calibration layer.
 *
 * Takes an augmented LocatorSheet (output of `label.ts` or `label_grouped.ts`)
 * and applies deterministic post-hoc rules to (a) catch obviously bad labels
 * and zero-out their confidence, (b) boost confidence when the label
 * aligns with strong evidence (i18n key, aria-label, testid), (c) flag
 * cross-group label leakage.
 *
 * Pure: no LLM call, no network. Runs in <100ms on thousands of records.
 * Designed to be the cheap first-pass before any verifier-style re-prompt.
 *
 * Output: same shape, with `intentConfidence` rewritten and a
 * `calibrationFlags: string[]` field added per record.
 *
 * Usage:
 *   tsx src/intent/calibrate.ts <input.intent.json> <output.calibrated.json>
 */
import { readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";

type Record_ = {
  componentFile: string;
  componentName: string;
  elementTag: string;
  line: number;
  role: string | null;
  ariaLabel: string | null;
  testId: string | null;
  dataIntent: string | null;
  text: string | null;
  i18nKey: string | null;
  href: string | null;
  hasOnClick: boolean;
  hasOnChange: boolean;
  hasOnSubmit: boolean;
  parentChain: string[];
  intent: string | null;
  intentConfidence?: number;
  intentRationale?: string;
};

// Action verbs we accept as the first kebab token of an intent.
const ACTION_VERBS = new Set([
  "submit",
  "open",
  "close",
  "toggle",
  "set",
  "select",
  "apply",
  "remove",
  "delete",
  "add",
  "create",
  "save",
  "discard",
  "cancel",
  "edit",
  "search",
  "filter",
  "sort",
  "navigate",
  "go",
  "sign",
  "log",
  "show",
  "hide",
  "expand",
  "collapse",
  "play",
  "pause",
  "stop",
  "load",
  "upload",
  "download",
  "share",
  "copy",
  "paste",
  "cut",
  "click", // last-resort; will get its own demotion rule
]);

// Allowed "structural" labels.
const STRUCTURAL = new Set(["non-interactive", "structural", "presentational"]);

function isInteractive(rec: Record_): boolean {
  if (rec.hasOnClick || rec.hasOnChange || rec.hasOnSubmit) return true;
  const t = rec.elementTag.toLowerCase();
  if (["button", "a", "input", "select", "textarea", "form"].includes(t)) return true;
  if (rec.role && ["button", "link", "checkbox", "radio", "menuitem", "tab", "switch"].includes(rec.role)) return true;
  return false;
}

function tokenise(s: string | null | undefined): string[] {
  if (!s) return [];
  return s
    .toLowerCase()
    .replace(/[._\-/]/g, " ")
    .split(/\s+/)
    .filter((t) => t.length > 1);
}

function calibrate(records: Record_[]): {
  records: Array<Record_ & { calibrationFlags: string[] }>;
  summary: { total: number; demoted: number; boosted: number; flagged: number };
} {
  // Build cross-record leakage detector: which intents appear across groups?
  const intentLocations = new Map<string, Array<{ idx: number; container: string }>>();
  records.forEach((r, idx) => {
    if (!r.intent || STRUCTURAL.has(r.intent)) return;
    const container = r.parentChain.join("/");
    if (!intentLocations.has(r.intent)) intentLocations.set(r.intent, []);
    intentLocations.get(r.intent)!.push({ idx, container });
  });
  const leakyIntents = new Set<string>();
  for (const [intent, locs] of intentLocations) {
    const containers = new Set(locs.map((l) => l.container));
    if (containers.size >= 2) {
      // Same intent across structurally unrelated containers? Flag for review.
      const distinct = Array.from(containers).filter(
        (c, i, a) => !a.some((other, j) => i !== j && (c.startsWith(other) || other.startsWith(c))),
      );
      if (distinct.length >= 2) leakyIntents.add(intent);
    }
  }

  // Rule I (sibling collapse): if 2+ elements share the EXACT same intent AND
  // share a CONTAINER ancestor (fieldset / form / ul / ol / nav / etc.), the
  // labeller has almost certainly collapsed distinct controls. Flag all of them.
  // Threshold is 2 (not 3) because most fieldsets we care about have only 2-3 siblings.
  const CONTAINER_TAGS = new Set(["form", "fieldset", "ul", "ol", "nav", "section", "header", "footer", "aside", "main", "article", "dialog", "table", "tr"]);
  function nearestContainerPath(chain: string[]): string {
    // walk from leaf upward; return the path INCLUDING the first container tag we hit.
    for (let i = chain.length - 1; i >= 0; i--) {
      if (CONTAINER_TAGS.has(chain[i])) return chain.slice(0, i + 1).join("/");
    }
    return chain.join("/");
  }
  const siblingCollapseIdx = new Set<number>();
  // key = `${containerPath}\0${intent}\0${elementTag}` — same tag inside same container.
  // This excludes the legitimate `form(submit-x) + button(submit-x)` pattern (different tags)
  // while still catching `input + input + input` triplets with identical intent.
  const siblingBuckets = new Map<string, number[]>();
  records.forEach((r, idx) => {
    if (!r.intent || STRUCTURAL.has(r.intent)) return;
    const k = `${nearestContainerPath(r.parentChain)}\u0000${r.intent}\u0000${r.elementTag.toLowerCase()}`;
    if (!siblingBuckets.has(k)) siblingBuckets.set(k, []);
    siblingBuckets.get(k)!.push(idx);
  });
  for (const [, idxs] of siblingBuckets) {
    if (idxs.length >= 2) for (const i of idxs) siblingCollapseIdx.add(i);
  }

  const out: Array<Record_ & { calibrationFlags: string[] }> = [];
  let demoted = 0;
  let boosted = 0;
  let flagged = 0;
  for (let recIdx = 0; recIdx < records.length; recIdx++) {
    const r = records[recIdx];
    const flags: string[] = [];
    let conf = typeof r.intentConfidence === "number" ? r.intentConfidence : 0;
    const intent = (r.intent ?? "").toLowerCase().trim();
    const interactive = isInteractive(r);

    // Rule A: structural label on an interactive element → wrong.
    if (STRUCTURAL.has(intent) && interactive) {
      flags.push("structural-on-interactive");
      conf = 0;
      demoted++;
    }
    // Rule B: non-structural label on a non-interactive element → wrong.
    else if (!STRUCTURAL.has(intent) && !interactive && intent !== "unknown") {
      flags.push("interactive-label-on-structural");
      conf = Math.min(conf, 0.2);
      demoted++;
    }

    if (!STRUCTURAL.has(intent) && intent !== "unknown" && interactive) {
      const tokens = intent.split("-").filter(Boolean);
      // Rule C: no verb-noun structure.
      if (tokens.length < 2) {
        flags.push("missing-noun");
        conf = 0;
        demoted++;
      } else {
        // Rule D: first token must be a known action verb.
        if (!ACTION_VERBS.has(tokens[0])) {
          flags.push("non-verb-prefix");
          conf = Math.min(conf, 0.4);
          demoted++;
        }
        // Rule E: bare "click" with no noun (already caught by C) or as first verb (boring but legal).
        if (tokens[0] === "click" && tokens.length === 1) {
          flags.push("bare-click");
          conf = 0;
          demoted++;
        }
        // Rule F: i18n / accessible-name overlap → boost.
        const evidence = [
          ...tokenise(r.i18nKey),
          ...tokenise(r.ariaLabel),
          ...tokenise(r.testId),
          ...tokenise(r.dataIntent),
          ...tokenise(r.text),
          ...tokenise(r.href),
        ];
        const intentTokens = tokens;
        const overlap = intentTokens.filter((t) => evidence.includes(t)).length;
        if (overlap >= 1) {
          flags.push(`evidence-overlap-${overlap}`);
          conf = Math.min(1, conf + 0.1 * overlap);
          boosted++;
        } else if (evidence.length > 0) {
          flags.push("no-evidence-overlap");
          conf = Math.max(0, conf - 0.2);
        }
        // Rule G: "submit-*" intent but no <form> ancestor → wrong-ish.
        if (tokens[0] === "submit" && !r.parentChain.includes("form")) {
          flags.push("submit-without-form");
          conf = Math.max(0, conf - 0.4);
          demoted++;
        }
        // Rule H: leakage across unrelated containers (computed above).
        if (leakyIntents.has(intent)) {
          flags.push("leaked-across-groups");
          conf = Math.max(0, conf - 0.3);
          flagged++;
        }
        // Rule I: sibling collapse inside the same container (fieldset/form/ul/...).
        if (siblingCollapseIdx.has(recIdx)) {
          flags.push("siblings-collapsed");
          conf = Math.max(0, conf - 0.4);
        }
        // Rule J: noun token must NOT be the elementTag itself. Catches the
        // degenerate `submit-form`, `click-button`, `toggle-checkbox`,
        // `search-input` pattern where the labeller fell back on the tag name.
        const TAG_NOUNS = new Set([
          "button", "input", "form", "checkbox", "select", "link", "textbox",
          "field", "control", "element", "tag", "node", "div", "span", "anchor",
        ]);
        const tagLike = tokens.slice(1).some((t) => TAG_NOUNS.has(t) || t === r.elementTag.toLowerCase());
        if (tagLike) {
          flags.push("tag-as-noun");
          conf = Math.max(0, conf - 0.4);
          demoted++;
        }
      }
    }

    if (flags.length > 0) flagged++;
    out.push({ ...r, intentConfidence: Math.round(conf * 100) / 100, calibrationFlags: flags });
  }

  return { records: out, summary: { total: records.length, demoted, boosted, flagged } };
}

function main() {
  const [, , inPath, outPath] = process.argv;
  if (!inPath || !outPath) {
    console.error("usage: tsx src/intent/calibrate.ts <input.json> <output.json>");
    process.exit(2);
  }
  const sheet = JSON.parse(readFileSync(resolve(inPath), "utf8")) as {
    records: Record_[];
    [k: string]: unknown;
  };

  const { records, summary } = calibrate(sheet.records);
  writeFileSync(
    resolve(outPath),
    JSON.stringify(
      { ...sheet, calibratedAt: new Date().toISOString(), calibrationSummary: summary, records },
      null,
      2,
    ) + "\n",
  );

  // Print a per-record diff to stderr.
  console.error(`calibrated ${summary.total} records: ${summary.demoted} demoted, ${summary.boosted} boosted, ${summary.flagged} flagged`);
  records.forEach((r, i) => {
    const before = sheet.records[i].intentConfidence ?? 0;
    const after = r.intentConfidence ?? 0;
    if (Math.abs(before - after) > 0.001 || r.calibrationFlags.length > 0) {
      const dir = after > before ? "↑" : after < before ? "↓" : " ";
      console.error(
        `  [${i}] ${r.elementTag} L${r.line} "${r.intent}"  ${before.toFixed(2)} ${dir} ${after.toFixed(2)}  [${r.calibrationFlags.join(",")}]`,
      );
    }
  });
}

main();
