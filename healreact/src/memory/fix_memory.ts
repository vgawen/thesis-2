/**
 * Fix memory — in-process map keyed by `${componentHash}|${failureFingerprint}`.
 * Stage 2 swaps for an on-disk JSONL store with provenance.
 */
import type { RepairPatch, FixMemory } from "../heal/healer.js";

export class InMemoryFixStore implements FixMemory {
  private store = new Map<string, RepairPatch>();
  lookup(componentHash: string, failureFingerprint: string): RepairPatch | null {
    return this.store.get(`${componentHash}|${failureFingerprint}`) ?? null;
  }
  record(componentHash: string, failureFingerprint: string, patch: RepairPatch): void {
    this.store.set(`${componentHash}|${failureFingerprint}`, patch);
  }
}
