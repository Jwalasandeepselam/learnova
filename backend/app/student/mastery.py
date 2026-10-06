"""
Learnova Student Mastery Tracking & Cognitive Retention Engine
Implements Bayesian Knowledge Tracing (BKT) and SuperMemo SM-2 Spaced Repetition algorithms.
Maintains persistent student topic mastery and identifies weak concepts for targeted remediation.
"""

from typing import Dict, Any, List, Optional
from contextlib import contextmanager
import math
import sqlite3
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import logging

from backend.app.core.config import settings

logger = logging.getLogger(__name__)


class MasteryTracker:
    """
    Cognitive mastery tracker modeling student latent knowledge probabilities
    via Bayesian Knowledge Tracing (BKT) and scheduling reviews with SuperMemo SM-2.
    """

    # Default BKT parameters
    DEFAULT_P_L0 = 0.10  # Initial prior knowledge probability
    DEFAULT_P_T = 0.15   # Probability of learning concept on practice step (transition rate)
    DEFAULT_P_G = 0.20   # Probability of lucky guess
    DEFAULT_P_S = 0.05   # Probability of accidental slip
    MASTERY_THRESHOLD = 0.85

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            Path(settings.STORAGE_DIR).mkdir(parents=True, exist_ok=True)
            self.db_path = str(Path(settings.STORAGE_DIR) / "mastery.db")
        else:
            self.db_path = db_path
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        self._init_db()

    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_db(self) -> None:
        """Initialize SQLite tables for student mastery persistence."""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS student_mastery (
                    id TEXT PRIMARY KEY,
                    student_id TEXT NOT NULL,
                    topic_id TEXT NOT NULL,
                    topic_name TEXT,
                    mastery_score REAL NOT NULL DEFAULT 0.10,
                    confidence_level TEXT NOT NULL DEFAULT 'LOW',
                    status TEXT NOT NULL DEFAULT 'NOVICE',
                    attempts_count INTEGER NOT NULL DEFAULT 0,
                    correct_count INTEGER NOT NULL DEFAULT 0,
                    easiness_factor REAL NOT NULL DEFAULT 2.5,
                    repetition_count INTEGER NOT NULL DEFAULT 0,
                    interval_days INTEGER NOT NULL DEFAULT 1,
                    last_practiced_at TIMESTAMP,
                    next_review_at TIMESTAMP,
                    misconceptions_history_json TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(student_id, topic_id)
                );
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_mast_student ON student_mastery(student_id);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_mast_topic ON student_mastery(topic_id);")
            conn.commit()

    def _classify_status(self, score: float) -> str:
        if score >= 0.85:
            return "MASTERED"
        elif score >= 0.70:
            return "PROFICIENT"
        elif score >= 0.40:
            return "DEVELOPING"
        return "NOVICE"

    def _classify_confidence(self, attempts: int, score: float) -> str:
        if attempts >= 5 and score >= 0.75:
            return "HIGH"
        elif attempts >= 3:
            return "MODERATE"
        return "LOW"

    def compute_bkt_update(
        self,
        current_p_l: float,
        is_correct: bool,
        p_t: float = DEFAULT_P_T,
        p_g: float = DEFAULT_P_G,
        p_s: float = DEFAULT_P_S
    ) -> float:
        """
        Bayesian Knowledge Tracing (BKT) update equation.
        Computes posterior P(L_t | obs) then updates with learning transition P(T):
        P(L_{t+1}) = P(L_t | obs) + (1 - P(L_t | obs)) * P(T)
        """
        p_l = max(0.01, min(0.99, current_p_l))

        if is_correct:
            # P(L|obs=1) = (P(L) * (1 - P(S))) / (P(L) * (1 - P(S)) + (1 - P(L)) * P(G))
            num = p_l * (1.0 - p_s)
            den = (p_l * (1.0 - p_s)) + ((1.0 - p_l) * p_g)
        else:
            # P(L|obs=0) = (P(L) * P(S)) / (P(L) * P(S)) + ((1 - P(L)) * (1 - P(G)))
            num = p_l * p_s
            den = (p_l * p_s) + ((1.0 - p_l) * (1.0 - p_g))

        p_posterior = num / den if den > 0 else p_l

        # Next step knowledge prediction incorporating transition rate
        next_p_l = p_posterior + ((1.0 - p_posterior) * p_t)
        return round(max(0.02, min(0.98, next_p_l)), 4)

    def compute_sm2_update(
        self,
        quality: int,
        repetition_count: int,
        easiness_factor: float,
        interval_days: int
    ) -> Dict[str, Any]:
        """
        SuperMemo SM-2 Interval and Easiness Factor Update.
        quality: 0 (blackout) to 5 (perfect instant recall).
        """
        q = max(0, min(5, quality))
        ef = easiness_factor

        # EF' = max(1.3, EF + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02)))
        new_ef = ef + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
        new_ef = max(1.3, round(new_ef, 3))

        if q >= 3:
            # Successful recall
            new_n = repetition_count + 1
            if new_n == 1:
                new_interval = 1
            elif new_n == 2:
                new_interval = 6
            else:
                new_interval = max(1, int(round(interval_days * new_ef)))
        else:
            # Failed recall, reset interval
            new_n = 0
            new_interval = 1

        return {
            "repetition_count": new_n,
            "easiness_factor": new_ef,
            "interval_days": new_interval
        }

    def record_observation(
        self,
        student_id: str,
        topic_id: str,
        is_correct: bool,
        topic_name: Optional[str] = None,
        quality_score: Optional[int] = None,
        misconception_tag: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Record a student's answer observation on a topic and update BKT and SM-2 state.
        """
        now = datetime.now(timezone.utc)
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM student_mastery WHERE student_id = ? AND topic_id = ?",
                (student_id, topic_id)
            )
            row = cursor.fetchone()

            if row:
                current_p_l = row["mastery_score"]
                attempts = row["attempts_count"] + 1
                corrects = row["correct_count"] + (1 if is_correct else 0)
                ef = row["easiness_factor"]
                reps = row["repetition_count"]
                interval = row["interval_days"]
                misc_list = json.loads(row["misconceptions_history_json"] or "[]")
                t_name = topic_name or row["topic_name"] or topic_id
            else:
                current_p_l = self.DEFAULT_P_L0
                attempts = 1
                corrects = 1 if is_correct else 0
                ef = 2.5
                reps = 0
                interval = 1
                misc_list = []
                t_name = topic_name or topic_id

            # 1. Update BKT
            new_p_l = self.compute_bkt_update(current_p_l, is_correct)
            status = self._classify_status(new_p_l)
            confidence = self._classify_confidence(attempts, new_p_l)

            # 2. Update SM-2
            if quality_score is None:
                quality_score = 5 if is_correct else 1

            sm2 = self.compute_sm2_update(quality_score, reps, ef, interval)
            next_review = now + timedelta(days=sm2["interval_days"])

            # 3. Track misconceptions
            if misconception_tag and not is_correct:
                misc_list.append({
                    "timestamp": now.isoformat() + "Z",
                    "tag": misconception_tag
                })

            record_id = f"mst_{student_id}_{topic_id}"
            conn.execute("""
                INSERT INTO student_mastery (
                    id, student_id, topic_id, topic_name, mastery_score,
                    confidence_level, status, attempts_count, correct_count,
                    easiness_factor, repetition_count, interval_days,
                    last_practiced_at, next_review_at, misconceptions_history_json,
                    updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(student_id, topic_id) DO UPDATE SET
                    topic_name = excluded.topic_name,
                    mastery_score = excluded.mastery_score,
                    confidence_level = excluded.confidence_level,
                    status = excluded.status,
                    attempts_count = excluded.attempts_count,
                    correct_count = excluded.correct_count,
                    easiness_factor = excluded.easiness_factor,
                    repetition_count = excluded.repetition_count,
                    interval_days = excluded.interval_days,
                    last_practiced_at = excluded.last_practiced_at,
                    next_review_at = excluded.next_review_at,
                    misconceptions_history_json = excluded.misconceptions_history_json,
                    updated_at = excluded.updated_at;
            """, (
                record_id, student_id, topic_id, t_name, new_p_l,
                confidence, status, attempts, corrects,
                sm2["easiness_factor"], sm2["repetition_count"], sm2["interval_days"],
                now.isoformat() + "Z", next_review.isoformat() + "Z", json.dumps(misc_list),
                now.isoformat() + "Z"
            ))
            conn.commit()

        delta = round(new_p_l - current_p_l, 4)
        return {
            "student_id": student_id,
            "topic_id": topic_id,
            "topic_name": t_name,
            "previous_mastery": current_p_l,
            "new_mastery": new_p_l,
            "mastery_delta": delta,
            "status": status,
            "confidence_level": confidence,
            "attempts_count": attempts,
            "success_rate": round(corrects / attempts, 2),
            "next_review_at": next_review.isoformat() + "Z",
            "interval_days": sm2["interval_days"]
        }

    def get_student_mastery(self, student_id: str) -> List[Dict[str, Any]]:
        """Retrieve complete topic mastery profile for a student."""
        results = []
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM student_mastery WHERE student_id = ? ORDER BY mastery_score ASC",
                (student_id,)
            )
            for row in cursor.fetchall():
                results.append({
                    "topic_id": row["topic_id"],
                    "topic_name": row["topic_name"] or row["topic_id"],
                    "mastery_score": row["mastery_score"],
                    "confidence_level": row["confidence_level"],
                    "status": row["status"],
                    "attempts_count": row["attempts_count"],
                    "correct_count": row["correct_count"],
                    "interval_days": row["interval_days"],
                    "last_practiced_at": row["last_practiced_at"],
                    "next_review_at": row["next_review_at"]
                })
        return results

    def get_weak_topics(self, student_id: str, threshold: float = 0.60) -> List[Dict[str, Any]]:
        """Identify topics where the student's mastery is below threshold, prioritized for review."""
        mastery = self.get_student_mastery(student_id)
        weak = [t for t in mastery if t["mastery_score"] < threshold]
        weak.sort(key=lambda x: x["mastery_score"])
        return weak

    def get_due_reviews(self, student_id: str) -> List[Dict[str, Any]]:
        """Identify topics whose scheduled SuperMemo review date is on or before today."""
        now_str = datetime.now(timezone.utc).isoformat()
        results = []
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM student_mastery 
                WHERE student_id = ? AND next_review_at <= ?
                ORDER BY mastery_score ASC
            """, (student_id, now_str))
            for row in cursor.fetchall():
                results.append({
                    "topic_id": row["topic_id"],
                    "topic_name": row["topic_name"],
                    "mastery_score": row["mastery_score"],
                    "interval_days": row["interval_days"],
                    "next_review_at": row["next_review_at"]
                })
        return results


_global_mastery_tracker: Optional[MasteryTracker] = None

def get_mastery_tracker() -> MasteryTracker:
    global _global_mastery_tracker
    if _global_mastery_tracker is None:
        _global_mastery_tracker = MasteryTracker()
    return _global_mastery_tracker
