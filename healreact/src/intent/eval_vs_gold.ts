/**
 * Quick eval: compare any number of intent JSONs against a gold proposal.
 *
 *   tsx src/intent/eval_vs_gold.ts <gold.json> <sheetA.json> [sheetB.json ...]
 *
 * gold.json schema: { records: [{ idx, goldIntent, interactive, ... }] }
 * sheet schema: { records: [{ intent, intentConfidence, verifier?: { intent } }] }
 *
 * We compute three flavours of match:
 *   - exact: sheet.intent === goldIntent
 *   - lenient: same verb prefix AND noun token overlap >= 1
 *   - interactive-class: both either "non-interactive" or both not
 */
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

function tokens(s: string): { verb: string | null; nouns: Set<string> } {
  if (!s) return { verb: null, nouns: new Set() };
  const ts = s.toLowerCase().split("-").filter(Boolean);
  return { verb: ts[0] ?? null, nouns: new Set(ts.slice(1)) };
}

function lenient(a: string, b: string): boolean {
  if (a === b) return true;
  const A = tokens(a);
  const B = tokens(b);
  if (A.verb !== B.verb) return false;
  for (const n of A.nouns) if (B.nouns.has(n)) return true;
  return false;
}

function finalIntent(rec: any): string {
  if (rec.verifier && rec.verifier.intent) return rec.verifier.intent;
  return rec.intent ?? "";
}

function keyOf(rec: { componentFile?: string; elementTag?: string; line?: number }): string {
  return `${rec.componentFile}:L${rec.line}:${rec.elementTag}`;
}

function main() {
  const [, , goldPath, ...sheetPaths] = process.argv;
  if (!goldPath || sheetPaths.length === 0) {
    console.error("usage: tsx eval_vs_gold.ts <gold.json> <sheetA.json> [...]");
    process.exit(2);
  }
  const gold = JSON.parse(readFileSync(resolve(goldPath), "utf8"));
  const goldRecs = gold.records as Array<{ key: string; goldIntent: string; interactive: boolean }>;
  const goldByKey = new Map(goldRecs.map((g) => [g.key, g]));

  console.log(`\nGold: ${goldPath}  (${goldRecs.length} records)\n`);

  const rows: any[] = [];
  for (const sp of sheetPaths) {
    const s = JSON.parse(readFileSync(resolve(sp), "utf8"));
    let exact = 0;
    let len = 0;
    let cls = 0;
    let missing = 0;
    const wrong: Array<{ key: string; gold: string; got: string }> = [];
    s.records.forEach((r: any) => {
      const k = keyOf(r);
      const g = goldByKey.get(k);
      if (!g) { missing++; return; }
      const got = finalIntent(r);
      if (got === g.goldIntent) exact++;
      if (lenient(got, g.goldIntent)) len++;
      const gNon = g.goldIntent === "non-interactive";
      const aNon = got === "non-interactive";
      if (gNon === aNon) cls++;
      if (got !== g.goldIntent) wrong.push({ key: k, gold: g.goldIntent, got });
    });
    rows.push({ sheet: sp.split("/").pop(), exact, lenient: len, intClass: cls, missing, wrong });
  }

  const total = goldRecs.length;
  console.log("| sheet                                  | exact | lenient | int-class | missing |");
  console.log("| -------------------------------------- | ----- | ------- | --------- | ------- |");
  for (const r of rows) {
    console.log(
      `| ${r.sheet.padEnd(38)} | ${String(r.exact).padStart(2)}/${total} | ${String(r.lenient).padStart(2)}/${total}   | ${String(r.intClass).padStart(2)}/${total}     | ${String(r.missing).padStart(3)}     |`,
    );
  }
  console.log("\nWrong predictions per sheet:");
  for (const r of rows) {
    console.log(`\n  ${r.sheet}:`);
    for (const w of r.wrong) {
      console.log(`    ${w.key.padEnd(50)}  gold="${w.gold}"  got="${w.got}"`);
    }
  }
}

main();
