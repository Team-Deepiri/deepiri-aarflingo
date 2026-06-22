export interface TriadPrediction {
  intent_id: string;
  emotion_id: string;
  behavior_id: string;
  confidence: number;
  ts_ms: number;
}

export interface CouplingTriple {
  intent: string;
  emotion: string;
  behavior: string;
  weight: number;
}

export interface ForbiddenPair {
  intent?: string;
  emotion?: string;
  behavior?: string;
}

export interface CouplingMatrix {
  version: string;
  triples: CouplingTriple[];
  forbidden_pairs: ForbiddenPair[];
}

export type GateDecision = "pass" | "review" | "reject";
