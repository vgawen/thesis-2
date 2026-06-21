/**
 * Behavioural-replay oracle (skeleton).
 *
 * Given a healed test execution, compares the post-heal network call
 * sequence + visible assertion outcomes against the pre-break green
 * baseline's HAR. Canonicalises volatile fields (timestamps, UUIDs,
 * JWTs) before diffing.
 *
 * Filled in Stage 2 once we have real HAR captures.
 */

export interface CanonicaliseRule {
  pathPattern: RegExp;       // e.g. /\/api\/order\/\d+/
  redactJsonFields: string[]; // ["createdAt", "id", "token", ...]
}

export const DEFAULT_RULES: CanonicaliseRule[] = [
  { pathPattern: /.*/, redactJsonFields: ["createdAt", "updatedAt", "id", "uuid", "token", "expiresAt", "nonce"] },
];

export function canonicaliseHar(har: string, rules: CanonicaliseRule[] = DEFAULT_RULES): string {
  // Minimal stub — Stage 2 replaces with proper HAR walker.
  let out = har;
  for (const r of rules) {
    for (const f of r.redactJsonFields) {
      const re = new RegExp(`"${f}"\\s*:\\s*"[^"]+"`, "g");
      out = out.replace(re, `"${f}":"<redacted>"`);
    }
  }
  return out;
}

export function diffCanonicalised(baselineHar: string, currentHar: string): string | null {
  const a = canonicaliseHar(baselineHar);
  const b = canonicaliseHar(currentHar);
  return a === b ? null : "har_mismatch"; // Stage 2: structural diff with line context
}
