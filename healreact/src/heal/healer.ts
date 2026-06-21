/**
 * L3 — LLM closed-loop healer (skeleton).
 *
 * Wired up in Stage 2 of the research pipeline. Reads failure context
 * + LocatorSheet diff + Fiber-tree dump, calls an LLM to propose a
 * patch, then hands off to src/oracle/replay.ts for behavioural
 * verification before commit.
 *
 * NOTE: This file intentionally stays as a typed skeleton until
 * Pilot is green. The LLM client (OpenAI / DeepSeek / local vLLM) is
 * injected, so the rest of the pipeline can be exercised end-to-end
 * with a deterministic mock LLM first.
 */
import type { Page } from "@playwright/test";

export interface FailureContext {
  testFile: string;
  failingStep: string;          // e.g. "intent('add-to-cart-button')"
  intentLabel: string;
  errorMessage: string;
  domSnapshot: string;          // truncated outerHTML
  fiberTreeDump?: string;       // optional, when react-devtools backend is attached
  screenshotPath?: string;
  consoleLog: string[];
  networkHar?: string;
}

export interface RepairPatch {
  kind: "selector_rewrite" | "wait_strategy" | "step_replacement" | "likely_real_defect";
  newCode?: string;
  rationale: string;
  confidence: number;           // 0..1
  fallbackRung?: string;        // which deterministic rung succeeded, if any
}

export interface LLMClient {
  // Pluggable so we can swap OpenAI / Anthropic / local vLLM.
  propose(ctx: FailureContext, ladderHints: string[]): Promise<RepairPatch>;
}

export interface OracleVerifier {
  verify(page: Page, patch: RepairPatch, ctx: FailureContext): Promise<{
    ok: boolean;
    behaviouralDiff?: string;
  }>;
}

export interface FixMemory {
  lookup(componentHash: string, failureFingerprint: string): RepairPatch | null;
  record(componentHash: string, failureFingerprint: string, patch: RepairPatch): void;
}

export interface HealerDeps {
  llm: LLMClient;
  oracle: OracleVerifier;
  memory: FixMemory;
}

export async function heal(
  page: Page,
  ctx: FailureContext,
  deps: HealerDeps,
  componentHash: string,
  failureFingerprint: string,
): Promise<RepairPatch> {
  // 1. Fix-memory first
  const remembered = deps.memory.lookup(componentHash, failureFingerprint);
  if (remembered) {
    const verdict = await deps.oracle.verify(page, remembered, ctx);
    if (verdict.ok) return remembered;
  }
  // 2. LLM proposes
  const patch = await deps.llm.propose(ctx, []);
  if (patch.kind === "likely_real_defect") return patch;
  // 3. Oracle gates the commit
  const verdict = await deps.oracle.verify(page, patch, ctx);
  if (verdict.ok) {
    deps.memory.record(componentHash, failureFingerprint, patch);
    return patch;
  }
  return {
    kind: "likely_real_defect",
    rationale: `LLM patch failed oracle: ${verdict.behaviouralDiff ?? "unknown diff"}`,
    confidence: 1 - patch.confidence,
  };
}
