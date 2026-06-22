import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import { gatePrediction } from "../src/gate.js";
import type { CouplingMatrix, TriadPrediction } from "../src/types.js";

const matrix = JSON.parse(
  readFileSync(resolve(__dirname, "../../../ethogram/coupling-matrix.json"), "utf-8"),
) as CouplingMatrix;

describe("gatePrediction", () => {
  it("passes valid play bow triple", () => {
    const pred: TriadPrediction = {
      intent_id: "solicit_play",
      emotion_id: "excited",
      behavior_id: "play_bow",
      confidence: 0.9,
      ts_ms: 1,
    };
    expect(gatePrediction(pred, matrix)).toBe("pass");
  });

  it("rejects forbidden rest + play_bow", () => {
    const pred: TriadPrediction = {
      intent_id: "rest",
      emotion_id: "calm",
      behavior_id: "play_bow",
      confidence: 0.9,
      ts_ms: 2,
    };
    expect(gatePrediction(pred, matrix)).toBe("reject");
  });
});
