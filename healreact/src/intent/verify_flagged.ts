/**
 * L1 verify pass — cheap-then-expensive (UTFix-style).
 *
 * Reads two calibrated sheets (e.g. 3B + 7B), takes the UNION of records
 * that either model flagged via calibrate.ts, and re-prompts the verifier
 * model (default qwen2.5-coder:7b) with the rejected guesses as negative
 * context. Only flagged records are sent — non-flagged ones pass through
 * with their primary (first-sheet) label intact.
 *
 * Usage:
 *   tsx src/intent/verify_flagged.ts \
 *      <primary.calibrated.json> <secondary.calibrated.json> <out.verified.json>
 *
 * Env:
 *   HEALREACT_VERIFY_MODEL   (default qwen2.5-coder:7b)
 *   OPENAI_API_BASE          (default http://localhost:11434/v1)
 *   OPENAI_API_KEY           (default ollama)
 */
import { readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";

type Sheet = {
  records: Array<{
    componentFile: string;
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
    calibrationFlags?: string[];
  }>;
  [k: string]: unknown;
};

const API_BASE = process.env.OPENAI_API_BASE ?? "http://localhost:11434/v1";
const API_KEY = process.env.OPENAI_API_KEY ?? "ollama";
const MODEL = process.env.HEALREACT_VERIFY_MODEL ?? "qwen2.5-coder:7b";

const SYSTEM = `You label ONE interactive UI element with a stable, semantic INTENT.

OUTPUT: strict JSON only, no prose: {"intent":"...","confidence":0.0-1.0,"rationale":"<=25 words"}.

INTENT FORMAT: "<verb>-<noun>[-<modifier>]", kebab-case ASCII. Verb must come from:
  submit, open, close, toggle, set, select, apply, enter, remove, delete, add, create,
  save, discard, cancel, edit, search, sort, navigate-to, sign-in, sign-up, sign-out,
  log-in, log-out, expand, collapse, play, pause, upload, download, share, copy.

INTERACTIVE DETECTION (HARD RULES — do not violate):
  - elementTag in {button, a, input, select, textarea, form} ⇒ ALWAYS interactive.
  - role in {button, link, checkbox, radio, menuitem, tab, switch, textbox, searchbox, combobox, option} ⇒ ALWAYS interactive.
  - hasOnClick or hasOnChange or hasOnSubmit is true ⇒ ALWAYS interactive.
  - Only when NONE of the above is true should you output intent="non-interactive".
  - You MUST NOT use "non-interactive" as a safe escape for an element that satisfies the rules above. Doing so is the worst possible failure.

ANCHORS (trust in this priority): aria-label > testId > dataIntent > i18nKey > text > href > parentChain.

NOUN RULE (do not violate):
- The noun part of the intent MUST describe the BUSINESS purpose of the element, not its HTML tag.
- FORBIDDEN nouns: button, input, form, checkbox, select, link, textbox, field, control, element, div, span, anchor.
- Forbidden examples: "submit-form", "click-button", "toggle-checkbox", "search-input", "submit-button".
- If the element has a meaningful 'name' attribute (e.g. name="notifyEmail"), USE IT as the noun source — "toggle-email-notification" beats "toggle-checkbox".
- If the element has a meaningful i18nKey (e.g. "settings.notifications.weeklyDigest"), USE IT — "toggle-weekly-digest" beats "toggle-notification".

The two prior model guesses below are just hints — they may both be wrong. Trust the ELEMENT EVIDENCE, not the priors. You may copy a prior verbatim, fix its noun/verb, or propose a completely new intent.`;

function buildUser(rec: Sheet["records"][number], priors: Array<{ model: string; intent: string | null; flags: string[] }>): string {
  const ev = {
    elementTag: rec.elementTag,
    role: rec.role,
    ariaLabel: rec.ariaLabel,
    testId: rec.testId,
    dataIntent: rec.dataIntent,
    name: (rec as any).name ?? null,
    placeholder: (rec as any).placeholder ?? null,
    text: rec.text,
    i18nKey: rec.i18nKey,
    href: rec.href,
    hasOnClick: rec.hasOnClick,
    hasOnChange: rec.hasOnChange,
    hasOnSubmit: rec.hasOnSubmit,
    parentChain: rec.parentChain,
    componentFile: rec.componentFile,
    line: rec.line,
  };
  return [
    "ELEMENT EVIDENCE (JSON):",
    JSON.stringify(ev, null, 2),
    "",
    "PRIOR GUESSES (hints — may be wrong):",
    ...priors.map(
      (p) => `  - ${p.model}: ${JSON.stringify(p.intent)}` + (p.flags.length ? `   (calibrator notes: ${p.flags.join(", ")})` : ""),
    ),
    "",
    'Emit your verdict as JSON: {"intent":"...","confidence":0.0,"rationale":"..."}',
  ].join("\n");
}

async function chat(system: string, user: string): Promise<string> {
  const r = await fetch(`${API_BASE}/chat/completions`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${API_KEY}` },
    body: JSON.stringify({
      model: MODEL,
      temperature: 0,
      response_format: { type: "json_object" },
      messages: [
        { role: "system", content: system },
        { role: "user", content: user },
      ],
    }),
  });
  if (!r.ok) throw new Error(`chat failed ${r.status}: ${await r.text()}`);
  const j: any = await r.json();
  return j.choices?.[0]?.message?.content ?? "";
}

function parseJson(s: string): { intent: string | null; confidence: number; rationale: string } {
  const start = s.indexOf("{");
  const end = s.lastIndexOf("}");
  if (start < 0 || end < 0) return { intent: null, confidence: 0, rationale: "parse-fail" };
  try {
    const o = JSON.parse(s.slice(start, end + 1));
    return {
      intent: typeof o.intent === "string" ? o.intent : null,
      confidence: typeof o.confidence === "number" ? Math.max(0, Math.min(1, o.confidence)) : 0,
      rationale: typeof o.rationale === "string" ? o.rationale.slice(0, 200) : "",
    };
  } catch {
    return { intent: null, confidence: 0, rationale: "parse-fail" };
  }
}

async function main() {
  const [, , primaryPath, secondaryPath, outPath] = process.argv;
  if (!primaryPath || !secondaryPath || !outPath) {
    console.error("usage: tsx src/intent/verify_flagged.ts <primary.json> <secondary.json> <out.json>");
    process.exit(2);
  }
  const primary = JSON.parse(readFileSync(resolve(primaryPath), "utf8")) as Sheet;
  const secondary = JSON.parse(readFileSync(resolve(secondaryPath), "utf8")) as Sheet;
  if (primary.records.length !== secondary.records.length) {
    throw new Error(`record count mismatch ${primary.records.length} vs ${secondary.records.length}`);
  }
  const primaryModel = (primary as any).model ?? "primary";
  const secondaryModel = (secondary as any).model ?? "secondary";

  const flaggedIdx: number[] = [];
  for (let i = 0; i < primary.records.length; i++) {
    const a = primary.records[i].calibrationFlags ?? [];
    const b = secondary.records[i].calibrationFlags ?? [];
    if (a.length > 0 || b.length > 0) flaggedIdx.push(i);
  }
  console.error(`verifying ${flaggedIdx.length}/${primary.records.length} flagged records via ${MODEL}`);

  const out = primary.records.map((r) => ({ ...r, verifier: null as null | { intent: string | null; confidence: number; rationale: string; flippedFrom: string | null } }));

  const t0 = Date.now();
  let guardTriggered = 0;
  for (const i of flaggedIdx) {
    const rec = primary.records[i];
    const priors = [
      { model: primaryModel, intent: primary.records[i].intent, flags: primary.records[i].calibrationFlags ?? [] },
      { model: secondaryModel, intent: secondary.records[i].intent, flags: secondary.records[i].calibrationFlags ?? [] },
    ];
    const t = Date.now();
    try {
      const raw = await chat(SYSTEM, buildUser(rec, priors));
      const v = parseJson(raw);

      // HARD GUARD: verifier MUST NOT escape to "non-interactive" on a clearly interactive element.
      const tag = rec.elementTag.toLowerCase();
      const definitelyInteractive =
        ["button", "a", "input", "select", "textarea", "form"].includes(tag) ||
        rec.hasOnClick || rec.hasOnChange || rec.hasOnSubmit ||
        (rec.role && ["button", "link", "checkbox", "radio", "menuitem", "tab", "switch", "textbox", "searchbox", "combobox", "option"].includes(rec.role));
      let guarded = "";
      if (definitelyInteractive && v.intent === "non-interactive") {
        guardTriggered++;
        guarded = " [GUARD: kept primary]";
        v.intent = rec.intent;
        v.confidence = Math.min(0.5, v.confidence);
        v.rationale = `[guard] verifier proposed non-interactive on a definitely-interactive ${tag}; kept primary label`;
      }

      const flipped = v.intent !== rec.intent ? rec.intent : null;
      out[i].verifier = { ...v, flippedFrom: flipped };
      const dir = flipped ? "→" : "=";
      console.error(`  [${i}] ${rec.elementTag} L${rec.line} ${JSON.stringify(rec.intent)} ${dir} ${JSON.stringify(v.intent)} c=${v.confidence.toFixed(2)} (${Date.now() - t}ms)${guarded}`);
    } catch (e: any) {
      console.error(`  [${i}] FAILED: ${e.message}`);
    }
  }
  if (guardTriggered > 0) console.error(`hard-guard rescued ${guardTriggered} records`);

  writeFileSync(
    resolve(outPath),
    JSON.stringify(
      {
        verifiedAt: new Date().toISOString(),
        verifier: MODEL,
        primary: primaryPath,
        secondary: secondaryPath,
        flaggedCount: flaggedIdx.length,
        records: out,
      },
      null,
      2,
    ) + "\n",
  );
  console.error(`done in ${((Date.now() - t0) / 1000).toFixed(1)}s → ${outPath}`);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
