"""SQLite feedback store."""
from __future__ import annotations

import json
import sqlite3
import time
import uuid
from dataclasses import dataclass
from pathlib import Path


@dataclass
class FeedbackEvent:
    id: str
    session_id: str
    ts_ms: int
    predicted_intent: str
    predicted_emotion: str
    predicted_behavior: str
    confidence: float
    corrected_intent: str | None
    corrected_emotion: str | None
    corrected_behavior: str | None
    rating: int | None
    feature_sequence_json: str


class FeedbackStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def _conn(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init(self) -> None:
        with self._conn() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    dog_id TEXT,
                    started_ms INTEGER,
                    source TEXT
                );
                CREATE TABLE IF NOT EXISTS predictions (
                    id TEXT PRIMARY KEY,
                    session_id TEXT,
                    ts_ms INTEGER,
                    intent TEXT,
                    emotion TEXT,
                    behavior TEXT,
                    confidence REAL,
                    features_json TEXT,
                    sequence_json TEXT
                );
                CREATE TABLE IF NOT EXISTS feedback (
                    id TEXT PRIMARY KEY,
                    prediction_id TEXT,
                    ts_ms INTEGER,
                    rating INTEGER,
                    corrected_intent TEXT,
                    corrected_emotion TEXT,
                    corrected_behavior TEXT
                );
                """
            )

    def start_session(self, dog_id: str = "default", source: str = "webcam") -> str:
        sid = str(uuid.uuid4())
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO sessions (id, dog_id, started_ms, source) VALUES (?, ?, ?, ?)",
                (sid, dog_id, int(time.time() * 1000), source),
            )
        return sid

    def log_prediction(
        self,
        session_id: str,
        intent: str,
        emotion: str,
        behavior: str,
        confidence: float,
        features: dict,
        sequence: list[list[float]],
    ) -> str:
        pid = str(uuid.uuid4())
        with self._conn() as conn:
            conn.execute(
                """INSERT INTO predictions
                (id, session_id, ts_ms, intent, emotion, behavior, confidence, features_json, sequence_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    pid,
                    session_id,
                    int(time.time() * 1000),
                    intent,
                    emotion,
                    behavior,
                    confidence,
                    json.dumps(features),
                    json.dumps(sequence),
                ),
            )
        return pid

    def add_feedback(
        self,
        prediction_id: str,
        rating: int | None = None,
        corrected_intent: str | None = None,
        corrected_emotion: str | None = None,
        corrected_behavior: str | None = None,
    ) -> str:
        fid = str(uuid.uuid4())
        with self._conn() as conn:
            conn.execute(
                """INSERT INTO feedback
                (id, prediction_id, ts_ms, rating, corrected_intent, corrected_emotion, corrected_behavior)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    fid,
                    prediction_id,
                    int(time.time() * 1000),
                    rating,
                    corrected_intent,
                    corrected_emotion,
                    corrected_behavior,
                ),
            )
        return fid

    def export_training_json(self, out_path: Path) -> int:
        with self._conn() as conn:
            rows = conn.execute(
                """
                SELECT p.sequence_json, p.intent, p.emotion, p.behavior,
                       f.corrected_intent, f.corrected_emotion, f.corrected_behavior
                FROM feedback f
                JOIN predictions p ON p.id = f.prediction_id
                """
            ).fetchall()
        samples = []
        for seq_json, i, e, b, ci, ce, cb in rows:
            samples.append(
                {
                    "sequence": json.loads(seq_json),
                    "intent_id": ci or i,
                    "emotion_id": ce or e,
                    "behavior_id": cb or b,
                }
            )
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps({"samples": samples}, indent=2), encoding="utf-8")
        return len(samples)

    def recent_predictions(self, limit: int = 50) -> list[dict]:
        with self._conn() as conn:
            rows = conn.execute(
                """SELECT id, session_id, ts_ms, intent, emotion, behavior, confidence
                FROM predictions ORDER BY ts_ms DESC LIMIT ?""",
                (limit,),
            ).fetchall()
        return [
            {
                "id": r[0],
                "session_id": r[1],
                "ts_ms": r[2],
                "intent": r[3],
                "emotion": r[4],
                "behavior": r[5],
                "confidence": r[6],
            }
            for r in rows
        ]

    def metrics(self) -> dict:
        with self._conn() as conn:
            preds = conn.execute("SELECT COUNT(*) FROM predictions").fetchone()[0]
            fbs = conn.execute("SELECT COUNT(*) FROM feedback").fetchone()[0]
            positive = conn.execute("SELECT COUNT(*) FROM feedback WHERE rating >= 1").fetchone()[0]
        return {
            "predictions": preds,
            "feedback_events": fbs,
            "positive_ratings": positive,
        }
