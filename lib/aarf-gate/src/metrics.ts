import type { GateDecision } from "./types.js";

export function summarizeDecisions(decisions: GateDecision[]): Record<GateDecision, number> {
  return decisions.reduce(
    (acc, d) => {
      acc[d] += 1;
      return acc;
    },
    { pass: 0, review: 0, reject: 0 } as Record<GateDecision, number>,
  );
}
