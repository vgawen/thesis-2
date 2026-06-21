/**
 * L1 intent labeller — first end-to-end LLM call in HealReact.
 *
 * Reads a LocatorSheet.json (from src/ast/extractor.ts), asks a local LLM
 * via Ollama's OpenAI-compatible endpoint for a stable semantic intent
 * label per interactive element, writes the augmented sheet back.
 *
 * Provider-agnostic: any OpenAI-compatible API works
 * (Ollama, MLX-LM server, vLLM, OpenAI cloud, DeepSeek, Together, ...).
 *
 *   OPENAI_API_BASE   default: http://localhost:11434/v1   (Ollama)
 *   OPENAI_API_KEY    default: "ollama"                    (any non-empty)
 *   HEALREACT_INTENT_MODEL  default: "qwen2.5:3b"
 *
 * Usage:
 *   tsx src/intent/label.ts <input-locator-sheet.json> <output-augmented.json>
 *
 * Example:
 *   tsx src/intent/label.ts \
 *     tests/fixtures/LocatorSheet.json \
 *     tests/fixtures/LocatorSheet.intent.json
 */
import { readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";

const API_BASE = process.env.OPENAI_API_BASE ?? "http://localhost:11434/v1";
const API_KEY = process.env.OPENAI_API_KEY ?? "ollama";
const MODEL = process.env.HEALREACT_INTENT_MODEL ?? "qwen2.5:3b";

type LocatorRecord = {
  componentFile: string;
  componentName: string;
  elementTag: string;
  line: number;
  column: number;
  role: string | null;
  ariaLabel: string | null;
  testId: string | null;
  dataIntent: string | null;
  id: string | null;
  name: string | null;
  placeholder: string | null;
  text: string | null;
  i18nKey: string | null;
  className: string | null;
  href: string | null;
  hasOnClick: boolean;
  hasOnChange: boolean;
  hasOnSubmit: boolean;
  parentChain: string[];
  intent: string | null;
};

type IntentJudgement = {
  intent: string; // kebab-case verb-noun, e.g. "submit-coupon"
  confidence: number; // 0..1
  rationale: string; // <=140 chars, why this label
};

const SYSTEM_PROMPT = `You label interactive UI elements in React components with a stable, semantic INTENT.

The intent is the user's *goal* when interacting with this element — NOT the implementation detail.

Rules:
1. Use kebab-case, verb-noun form: "submit-coupon", "remove-cart-item", "set-quantity", "open-checkout".
2. The label MUST be the same across behaviour-preserving refactors: renamed class, swapped <button> for <a role="button">, copy edits, i18n key changes, wrapper divs.
3. Use the i18n key, accessible name, and parent context as semantic anchors; ignore className, hash-styled CSS, and DOM position.
4. If the element is structural (no user action), output intent="non-interactive".
5. If unsure, output a best-guess and lower confidence below 0.6.
6. Output STRICT JSON: {"intent": "...", "confidence": 0.X, "rationale": "..."}. No prose, no markdown.`;

function buildUserPrompt(rec: LocatorRecord): string {
  return `Component: ${rec.componentName} (${rec.componentFile}:${rec.line})
Tag: <${rec.elementTag}>
Role: ${rec.role ?? "—"}
aria-label: ${rec.ariaLabel ?? "—"}
data-testid: ${rec.testId ?? "—"}
data-intent (already set): ${rec.dataIntent ?? "—"}
id: ${rec.id ?? "—"}
name: ${rec.name ?? "—"}
placeholder: ${rec.placeholder ?? "—"}
visible text: ${rec.text ?? "—"}
i18n key: ${rec.i18nKey ?? "—"}
href: ${rec.href ?? "—"}
event handlers: ${[rec.hasOnClick && "onClick", rec.hasOnChange && "onChange", rec.hasOnSubmit && "onSubmit"].filter(Boolean).join(", ") || "—"}
parent chain (root → leaf): ${rec.parentChain.join(" > ")}

Output strict JSON with keys intent, confidence, rationale.`;
}

async function labelOne(rec: LocatorRecord, signal?: AbortSignal): Promise<IntentJudgement> {
  const body = {
    model: MODEL,
    messages: [
      { role: "system", content: SYSTEM_PROMPT },
      { role: "user", content: buildUserPrompt(rec) },
    ],
    temperature: 0.0,
    response_format: { type: "json_object" },
    stream: false,
  };
  const r = await fetch(`${API_BASE}/chat/completions`, {
    method: "POST",
    headers: { "content-type": "application/json", authorization: `Bearer ${API_KEY}` },
    body: JSON.stringify(body),
    signal,
  });
  if (!r.ok) throw new Error(`LLM HTTP ${r.status}: ${await r.text()}`);
  const j = (await r.json()) as { choices: [{ message: { content: string } }] };
  const raw = j.choices[0]?.message?.content ?? "{}";
  let parsed: unknown;
  try {
    parsed = JSON.parse(raw);
  } catch (e) {
    // Some models wrap JSON in markdown despite response_format. Strip and retry.
    const m = raw.match(/\{[\s\S]*\}/);
    if (!m) throw new Error(`non-JSON model output: ${raw.slice(0, 200)}`);
    parsed = JSON.parse(m[0]);
  }
  const p = parsed as Partial<IntentJudgement>;
  return {
    intent: String(p.intent ?? "unknown"),
    confidence: typeof p.confidence === "number" ? p.confidence : 0,
    rationale: String(p.rationale ?? ""),
  };
}

async function main() {
  const [, , inPath, outPath] = process.argv;
  if (!inPath || !outPath) {
    console.error("usage: tsx src/intent/label.ts <input.json> <output.json>");
    process.exit(2);
  }
  const sheet = JSON.parse(readFileSync(resolve(inPath), "utf8")) as {
    generatedAt: string;
    srcRoot: string;
    count: number;
    records: LocatorRecord[];
  };

  console.error(`labelling ${sheet.records.length} elements via ${MODEL} @ ${API_BASE}`);
  const t0 = Date.now();
  const out: LocatorRecord[] = [];
  for (const [i, rec] of sheet.records.entries()) {
    const tStart = Date.now();
    try {
      const j = await labelOne(rec);
      const augmented: LocatorRecord & { intentConfidence: number; intentRationale: string } = {
        ...rec,
        intent: j.intent,
        intentConfidence: j.confidence,
        intentRationale: j.rationale,
      };
      out.push(augmented);
      const dt = Date.now() - tStart;
      console.error(
        `  [${i + 1}/${sheet.records.length}] ${rec.elementTag} L${rec.line} → intent="${j.intent}" conf=${j.confidence.toFixed(2)} (${dt}ms)`,
      );
    } catch (e) {
      console.error(`  [${i + 1}/${sheet.records.length}] FAILED: ${(e as Error).message}`);
      out.push(rec);
    }
  }
  const total = Date.now() - t0;

  writeFileSync(
    resolve(outPath),
    JSON.stringify(
      {
        ...sheet,
        labelledAt: new Date().toISOString(),
        model: MODEL,
        apiBase: API_BASE,
        totalMs: total,
        records: out,
      },
      null,
      2,
    ) + "\n",
  );
  console.error(`done: ${sheet.records.length} elements in ${total}ms → ${outPath}`);
}

void main();
