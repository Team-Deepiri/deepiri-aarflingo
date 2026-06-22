import type { CouplingMatrix, ForbiddenPair, GateDecision, TriadPrediction } from "./types.js";

export function isForbidden(
  prediction: TriadPrediction,
  forbidden: ForbiddenPair[],
): boolean {
  return forbidden.some((rule) => {
    const intentOk = rule.intent === undefined || rule.intent === prediction.intent_id;
    const emotionOk = rule.emotion === undefined || rule.emotion === prediction.emotion_id;
    const behaviorOk = rule.behavior === undefined || rule.behavior === prediction.behavior_id;
    return intentOk && emotionOk && behaviorOk;
  });
}

export function couplingWeight(
  prediction: TriadPrediction,
  matrix: CouplingMatrix,
): number {
  const hit = matrix.triples.find(
    (t) =>
      t.intent === prediction.intent_id &&
      t.emotion === prediction.emotion_id &&
      t.behavior === prediction.behavior_id,
  );
  return hit?.weight ?? 0;
}

export function gatePrediction(
  prediction: TriadPrediction,
  matrix: CouplingMatrix,
  reviewThreshold = 0.5,
): GateDecision {
  if (isForbidden(prediction, matrix.forbidden_pairs)) {
    return "reject";
  }
  if (prediction.confidence < reviewThreshold) {
    return "review";
  }
  if (couplingWeight(prediction, matrix) <= 0) {
    return "review";
  }
  return "pass";
}
