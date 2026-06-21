/**
 * L1 intent labeller — GROUPING PASS (Round 2 of the L1 pilot).
 *
 * Difference from `label.ts`:
 *   - Groups sibling records under the same semantic container
 *     (form, ul, ol, nav, section, header, footer, aside, main,
 *     article, dialog, fieldset, table) and labels the whole group
 *     in ONE prompt. Lets a small model see sibling context and
 *     anchor labels like "apply-coupon" via the coupon-input sibling
 *     instead of pattern-matching `<form onSubmit>` → "submit-order".
 *   - Singletons fall back to the per-element prompt.
 *   - Groups larger than MAX_GROUP_SIZE also fall back per-element
 *     (a 30-element fieldset would blow the small model's working
 *     memory; better to lose context than emit garbage).
 *
 * Reuses the OpenAI-compatible client config from label.ts.
 *
 * Usage:
 *   tsx src/intent/label_grouped.ts <input.json> <output.json>
 */
import { readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";

const API_BASE = process.env.OPENAI_API_BASE ?? "http://localhost:11434/v1";
const API_KEY = process.env.OPENAI_API_KEY ?? "ollama";
const MODEL = process.env.HEALREACT_INTENT_MODEL ?? "qwen2.5:3b";
const MAX_GROUP_SIZE = 8;

const CONTAINERS = new Set([
  "form",
  "ul",
  "ol",
  "nav",
  "section",
  "header",
  "footer",
  "aside",
  "main",
  "article",
  "dialog",
  "fieldset",
  "table",
  "tr",
]);

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

type Judgement = { intent: string; confidence: number; rationale: string };

function describeRecord(rec: LocatorRecord): string {
  const handlers =
    [rec.hasOnClick && "onClick", rec.hasOnChange && "onChange", rec.hasOnSubmit && "onSubmit"]
      .filter(Boolean)
      .join(", ") || "—";
  return `<${rec.elementTag}> @L${rec.line}
  role=${rec.role ?? "—"}; aria-label=${rec.ariaLabel ?? "—"}; data-testid=${rec.testId ?? "—"}
  text=${rec.text ?? "—"}; i18n=${rec.i18nKey ?? "—"}; placeholder=${rec.placeholder ?? "—"}
  href=${rec.href ?? "—"}; handlers=${handlers}
  parent: ${rec.parentChain.join(" > ")}`;
}

/**
 * Group key: same component file + identical parentChain prefix up to and including
 * the nearest container ancestor. Records not under any container land in their own
 * single-element group.
 */
function groupKey(rec: LocatorRecord): string {
  for (let i = rec.parentChain.length - 1; i >= 0; i--) {
    if (CONTAINERS.has(rec.parentChain[i])) {
      const prefix = rec.parentChain.slice(0, i + 1).join("/");
      return `${rec.componentFile}::${prefix}`;
    }
  }
  return `${rec.componentFile}::__loose__::L${rec.line}`;
}

const SYSTEM_PROMPT_GROUP = `You label interactive UI elements in a React component with a stable, semantic INTENT.

You will receive multiple elements that appear TOGETHER inside the same container (e.g. the same <form>, <ul>, or <section>). USE SIBLING CONTEXT: e.g. a <form> containing a coupon input + apply button is "apply-coupon", NOT "submit-order".

Rules:
1. Each intent is kebab-case verb-noun: "submit-coupon", "remove-cart-item", "set-quantity", "open-checkout". The noun MUST be present (no bare "click").
2. The label MUST be the same across behaviour-preserving refactors (renamed class, swapped <button> for <a role="button">, copy edits, i18n key edits, wrapper divs).
3. Anchor on i18n keys, accessible name, sibling context, and parent-chain semantics. Ignore className and hash-styled CSS.
4. If an element is purely structural (label, decorative wrapper), output intent="non-interactive".
5. Lower confidence below 0.6 when unsure; below 0.3 when guessing.
6. Output STRICT JSON: {"intents":[{"index":0,"intent":"...","confidence":0.X,"rationale":"..."},...]} — one entry per input element, in input order. No prose, no markdown.`;

const SYSTEM_PROMPT_SOLO = `You label ONE interactive UI element with a stable, semantic INTENT.

Rules:
1. kebab-case verb-noun: "submit-coupon", "remove-cart-item", "set-quantity", "open-checkout". Noun MUST be present.
2. The label MUST be the same across behaviour-preserving refactors.
3. Anchor on i18n keys, accessible name, parent-chain semantics. Ignore className and hash-styled CSS.
4. If structural (label, wrapper), output intent="non-interactive".
5. Below 0.6 confidence when unsure.
6. Output STRICT JSON: {"intent":"...","confidence":0.X,"rationale":"..."}. No prose.`;

async function chat(systemPrompt: string, userPrompt: string): Promise<string> {
  const r = await fetch(`${API_BASE}/chat/completions`, {
    method: "POST",
    headers: { "content-type": "application/json", authorization: `Bearer ${API_KEY}` },
    body: JSON.stringify({
      model: MODEL,
      messages: [
        { role: "system", content: systemPrompt },
        { role: "user", content: userPrompt },
      ],
      temperature: 0.0,
      response_format: { type: "json_object" },
      stream: false,
    }),
  });
  if (!r.ok) throw new Error(`LLM HTTP ${r.status}: ${await r.text()}`);
  const j = (await r.json()) as { choices: [{ message: { content: string } }] };
  return j.choices[0]?.message?.content ?? "{}";
}

function parseJson<T>(raw: string): T {
  try {
    return JSON.parse(raw) as T;
  } catch {
    const m = raw.match(/\{[\s\S]*\}/);
    if (!m) throw new Error(`non-JSON model output: ${raw.slice(0, 200)}`);
    return JSON.parse(m[0]) as T;
  }
}

async function labelSolo(rec: LocatorRecord): Promise<Judgement> {
  const raw = await chat(SYSTEM_PROMPT_SOLO, `Element:\n${describeRecord(rec)}\n\nOutput strict JSON.`);
  const p = parseJson<Partial<Judgement>>(raw);
  return {
    intent: String(p.intent ?? "unknown"),
    confidence: typeof p.confidence === "number" ? p.confidence : 0,
    rationale: String(p.rationale ?? ""),
  };
}

async function labelGroup(group: LocatorRecord[]): Promise<Judgement[]> {
  const lines = group.map((r, i) => `[${i}] ${describeRecord(r)}`).join("\n\n");
  const containerHint =
    group[0].parentChain.length > 0 ? `container path: ${group[0].parentChain.join(" > ")}` : "";
  const user = `These ${group.length} elements appear together. ${containerHint}\n\n${lines}\n\nOutput strict JSON: {"intents":[{"index":<i>,"intent":"...","confidence":0.X,"rationale":"..."}, ...]} — one entry per element, in input order.`;
  const raw = await chat(SYSTEM_PROMPT_GROUP, user);
  const parsed = parseJson<{ intents?: Array<Partial<Judgement> & { index?: number }> }>(raw);
  const intents = parsed.intents ?? [];
  // Align by index; if model omitted an entry, fall back to per-element later.
  const out: Judgement[] = new Array(group.length);
  for (let i = 0; i < group.length; i++) {
    const hit = intents.find((x) => Number(x.index) === i) ?? intents[i];
    if (!hit) {
      out[i] = { intent: "unknown", confidence: 0, rationale: "model omitted this index" };
    } else {
      out[i] = {
        intent: String(hit.intent ?? "unknown"),
        confidence: typeof hit.confidence === "number" ? hit.confidence : 0,
        rationale: String(hit.rationale ?? ""),
      };
    }
  }
  return out;
}

async function main() {
  const [, , inPath, outPath] = process.argv;
  if (!inPath || !outPath) {
    console.error("usage: tsx src/intent/label_grouped.ts <input.json> <output.json>");
    process.exit(2);
  }
  const sheet = JSON.parse(readFileSync(resolve(inPath), "utf8")) as {
    generatedAt: string;
    srcRoot: string;
    count: number;
    records: LocatorRecord[];
  };

  // Group records, preserve original order via record index.
  const groups = new Map<string, { recIdx: number; rec: LocatorRecord }[]>();
  sheet.records.forEach((rec, recIdx) => {
    const k = groupKey(rec);
    if (!groups.has(k)) groups.set(k, []);
    groups.get(k)!.push({ recIdx, rec });
  });

  console.error(
    `labelling ${sheet.records.length} elements via ${MODEL} @ ${API_BASE} in ${groups.size} groups`,
  );
  for (const [k, g] of groups) {
    console.error(`  group ${k} → ${g.length} elements`);
  }

  const judgements: Judgement[] = new Array(sheet.records.length);
  const t0 = Date.now();
  let llmCalls = 0;

  for (const [k, entries] of groups) {
    if (entries.length === 1 || entries.length > MAX_GROUP_SIZE) {
      // Solo / oversized → per-element.
      for (const { recIdx, rec } of entries) {
        const tStart = Date.now();
        try {
          judgements[recIdx] = await labelSolo(rec);
          llmCalls++;
          console.error(
            `  [solo][rec ${recIdx}] ${rec.elementTag} L${rec.line} → "${judgements[recIdx].intent}" conf=${judgements[recIdx].confidence.toFixed(2)} (${Date.now() - tStart}ms)`,
          );
        } catch (e) {
          judgements[recIdx] = { intent: "unknown", confidence: 0, rationale: (e as Error).message };
          console.error(`  [solo][rec ${recIdx}] FAILED: ${(e as Error).message}`);
        }
      }
    } else {
      const tStart = Date.now();
      try {
        const res = await labelGroup(entries.map((e) => e.rec));
        llmCalls++;
        res.forEach((j, i) => {
          const recIdx = entries[i].recIdx;
          judgements[recIdx] = j;
          const rec = entries[i].rec;
          console.error(
            `  [group ${k.slice(-30)}][rec ${recIdx}] ${rec.elementTag} L${rec.line} → "${j.intent}" conf=${j.confidence.toFixed(2)}`,
          );
        });
        console.error(`  ↳ group total ${Date.now() - tStart}ms`);
      } catch (e) {
        console.error(`  [group ${k}] FAILED: ${(e as Error).message} — falling back per-element`);
        for (const { recIdx, rec } of entries) {
          try {
            judgements[recIdx] = await labelSolo(rec);
            llmCalls++;
          } catch (e2) {
            judgements[recIdx] = {
              intent: "unknown",
              confidence: 0,
              rationale: (e2 as Error).message,
            };
          }
        }
      }
    }
  }

  const total = Date.now() - t0;
  const out = sheet.records.map((rec, i) => ({
    ...rec,
    intent: judgements[i]?.intent ?? "unknown",
    intentConfidence: judgements[i]?.confidence ?? 0,
    intentRationale: judgements[i]?.rationale ?? "",
  }));

  writeFileSync(
    resolve(outPath),
    JSON.stringify(
      {
        ...sheet,
        labelledAt: new Date().toISOString(),
        labellerMode: "grouped",
        model: MODEL,
        apiBase: API_BASE,
        totalMs: total,
        llmCalls,
        groupCount: groups.size,
        records: out,
      },
      null,
      2,
    ) + "\n",
  );
  console.error(
    `done: ${sheet.records.length} elements via ${llmCalls} LLM calls in ${total}ms → ${outPath}`,
  );
}

void main();
