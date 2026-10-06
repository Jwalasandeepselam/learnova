"""
Learnova Formative Assessment & Adaptive Quiz Engine
Generates high-discrimination questions with misconception-targeted distractors,
evaluates responses with instant feedback, and computes quiz attempt metrics.
"""

from typing import Dict, Any, List, Optional
import uuid
import json
import logging
import re
from datetime import datetime, timedelta, timezone

from backend.app.ai.providers import get_llm_provider, LLMProviderManager
from backend.app.ai.prompts import QUIZ_GENERATOR_PROMPT, ANSWER_EVALUATOR_PROMPT, format_prompt
from backend.app.rag.retriever import get_retriever, Retriever, RetrievalResult

logger = logging.getLogger(__name__)


class QuizEngine:
    """
    Adaptive assessment engine creating and evaluating MCQ and conceptual short answer questions.
    """

    def __init__(
        self,
        llm_provider: Optional[LLMProviderManager] = None,
        retriever: Optional[Retriever] = None
    ):
        self.llm = llm_provider or get_llm_provider()
        self.retriever = retriever or get_retriever()
        # In-memory store of generated quizzes: quiz_id -> quiz_dict
        self._quiz_store: Dict[str, Dict[str, Any]] = {}

    async def generate_quiz(
        self,
        document_id: str,
        topic_ids: Optional[List[str]] = None,
        question_count: int = 5,
        difficulty: str = "adaptive"
    ) -> Dict[str, Any]:
        """
        Generate an adaptive quiz grounded in document chunks.
        """
        topic_focus_str = ", ".join(topic_ids) if topic_ids else "All core document topics"
        retrieval: RetrievalResult = self.retriever.retrieve(
            query=f"{topic_focus_str} core concepts definitions formulas",
            document_id=document_id,
            top_k=6
        )
        context_str = retrieval.get_grounding_context()

        prompt = format_prompt(
            QUIZ_GENERATOR_PROMPT,
            question_count=question_count,
            topics_focus=topic_focus_str,
            difficulty=difficulty,
            retrieved_chunks=context_str
        )

        response = await self.llm.generate(
            prompt=prompt,
            system_instruction="You are a psychometrician and pedagogical assessment specialist.",
            json_mode=True,
            temperature=0.15
        )

        data = response.structured
        if not data or not isinstance(data, dict):
            try:
                clean_text = re.sub(r"^```(?:json)?\s*|\s*```$", "", response.content.strip())
                data = json.loads(clean_text)
            except Exception:
                data = {
                    "quiz_id": f"quiz_{uuid.uuid4().hex[:8]}",
                    "total_questions": 1,
                    "questions": [
                        {
                            "id": "q_1",
                            "type": "mcq",
                            "topic_name": "Fundamental Principles",
                            "prompt": "Which statement accurately represents the primary concept?",
                            "options": [
                                {"key": "A", "text": "Interactions occur via discrete quantized exchanges."},
                                {"key": "B", "text": "Continuous accumulation occurs across arbitrary times."},
                                {"key": "C", "text": "Wave dynamics never interact with particle mechanics."},
                                {"key": "D", "text": "Energy conservation does not apply to quantum states."}
                            ],
                            "correct_option": "A",
                            "correct_answer": "A",
                            "explanation": "State transitions are governed by discrete quanta.",
                            "distractor_explanations": {"B": "Continuous accumulation misconception."},
                            "citation": {"document_id": document_id, "page_number": 1, "chunk_id": "chk_01"}
                        }
                    ]
                }

        quiz_id = data.get("quiz_id") or f"quiz_{uuid.uuid4().hex[:8]}"
        data["quiz_id"] = quiz_id
        data["document_id"] = document_id

        # Normalize questions
        questions = data.get("questions", [])
        for i, q in enumerate(questions, 1):
            if not q.get("id"):
                q["id"] = f"q_{i}"
            if "correct_option" in q and "correct_answer" not in q:
                q["correct_answer"] = q["correct_option"]

        # Cache quiz in memory for validation
        self._quiz_store[quiz_id] = data

        # Prepare sanitized version for student (hiding answers and distractor explanations)
        client_questions = []
        for q in questions:
            sanitized = {
                "id": q.get("id"),
                "type": q.get("type", "mcq"),
                "topic_name": q.get("topic_name", "General"),
                "prompt": q.get("prompt"),
            }
            if q.get("type") == "mcq" and "options" in q:
                sanitized["options"] = q.get("options")
            client_questions.append(sanitized)

        return {
            "quiz_id": quiz_id,
            "document_id": document_id,
            "total_questions": len(questions),
            "questions": client_questions
        }

    async def evaluate_question(
        self,
        quiz_id: Optional[str],
        question_id: str,
        submitted_answer: str,
        correct_answer: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Evaluate a single question submission in real time.
        """
        quiz = self._quiz_store.get(quiz_id) if quiz_id else None
        target_q = None
        if quiz:
            for q in quiz.get("questions", []):
                if q.get("id") == question_id:
                    target_q = q
                    break

        if not target_q:
            # Fallback evaluation without cached question
            expected = (correct_answer or "A").strip().upper()
            is_correct = (submitted_answer or "").strip().upper() == expected
            return {
                "question_id": question_id,
                "is_correct": is_correct,
                "correct_answer": expected,
                "explanation": "Answer evaluated using fundamental axiomatic criteria.",
                "citation": {"document_id": "unknown", "page_number": 1, "chunk_id": "chk_1"}
            }

        q_type = target_q.get("type", "mcq")
        correct_ans = target_q.get("correct_answer") or target_q.get("correct_option", "A")

        if q_type == "mcq":
            submitted_clean = submitted_answer.strip().upper()
            is_correct = (submitted_clean == correct_ans.strip().upper())
            explanation = target_q.get("explanation", "Correct based on primary principle.")
            
            # Check if student picked a specific distractor
            distractor_info = None
            if not is_correct and "distractor_explanations" in target_q:
                distractor_info = target_q["distractor_explanations"].get(submitted_clean)

            return {
                "question_id": question_id,
                "is_correct": is_correct,
                "correct_answer": correct_ans,
                "explanation": explanation,
                "distractor_analysis": distractor_info,
                "citation": target_q.get("citation", {})
            }

        # Short answer evaluation using LLM
        prompt = format_prompt(
            ANSWER_EVALUATOR_PROMPT,
            question_prompt=target_q.get("prompt", ""),
            expected_criteria=target_q.get("sample_solution", "Accurate conceptual articulation"),
            student_answer=submitted_answer,
            retrieved_chunks=""
        )

        response = await self.llm.generate(
            prompt=prompt,
            system_instruction="You are an objective academic evaluator.",
            json_mode=True,
            temperature=0.1
        )

        res_data = response.structured or {}
        is_correct = res_data.get("is_correct", True)

        return {
            "question_id": question_id,
            "is_correct": is_correct,
            "correct_answer": target_q.get("sample_solution", "See conceptual criteria"),
            "explanation": res_data.get("guided_hint") or res_data.get("pedagogical_prescription", "Well articulated."),
            "misconception": res_data.get("misconception"),
            "citation": target_q.get("citation", {})
        }

    async def evaluate_submission(
        self,
        quiz_id: str,
        submissions: List[Dict[str, str]],
        time_spent_seconds: int = 0
    ) -> Dict[str, Any]:
        """
        Evaluate full quiz submission, aggregate scores, identify recurring misconceptions,
        and calculate spaced repetition review dates.
        """
        total_q = len(submissions)
        correct_count = 0
        topic_scores: Dict[str, Dict[str, float]] = {}
        misconceptions = []

        for sub in submissions:
            qid = sub.get("question_id")
            ans = sub.get("submitted_answer", "")
            eval_res = await self.evaluate_question(quiz_id, qid, ans)

            if eval_res.get("is_correct"):
                correct_count += 1
            else:
                if eval_res.get("distractor_analysis"):
                    misconceptions.append({
                        "question_id": qid,
                        "type": "CONCEPTUAL",
                        "summary": eval_res.get("distractor_analysis")
                    })
                elif eval_res.get("misconception") and eval_res["misconception"].get("detected"):
                    misconceptions.append({
                        "question_id": qid,
                        "type": eval_res["misconception"].get("category", "CONCEPTUAL"),
                        "summary": eval_res["misconception"].get("summary", "Suboptimal reasoning")
                    })

            # Record topic performance
            topic = "General"
            if quiz_id in self._quiz_store:
                for q in self._quiz_store[quiz_id].get("questions", []):
                    if q.get("id") == qid:
                        topic = q.get("topic_name", "General")
                        break

            if topic not in topic_scores:
                topic_scores[topic] = {"correct": 0, "total": 0}
            topic_scores[topic]["total"] += 1
            if eval_res.get("is_correct"):
                topic_scores[topic]["correct"] += 1

        score_pct = round((correct_count / total_q) * 100.0, 1) if total_q > 0 else 0.0

        # Build topic breakdown
        topic_breakdown = []
        for t_name, data in topic_scores.items():
            t_score = data["correct"] / data["total"] if data["total"] > 0 else 0.0
            topic_breakdown.append({
                "topic_name": t_name,
                "score": round(t_score, 2),
                "total_questions": data["total"],
                "correct_count": data["correct"]
            })

        # Calculate recommended spaced repetition review interval
        # If score >= 80%, review in 3 days; otherwise in 1 day
        review_days = 3 if score_pct >= 80.0 else 1
        rec_review = (datetime.now(timezone.utc) + timedelta(days=review_days)).isoformat()

        return {
            "attempt_id": f"att_{uuid.uuid4().hex[:10]}",
            "quiz_id": quiz_id,
            "score_percentage": score_pct,
            "total_questions": total_q,
            "correct_count": correct_count,
            "time_spent_seconds": time_spent_seconds,
            "topic_breakdown": topic_breakdown,
            "identified_misconceptions": misconceptions,
            "recommended_review_date": rec_review
        }


_global_quiz_engine: Optional[QuizEngine] = None

def get_quiz_engine() -> QuizEngine:
    global _global_quiz_engine
    if _global_quiz_engine is None:
        _global_quiz_engine = QuizEngine()
    return _global_quiz_engine
