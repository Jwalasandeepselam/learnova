"""
Learnova Socratic Pedagogical Tutor Engine
Coordinates interactive inquiry dialogues, adapts explanations across 8 pedagogical strategies,
and diagnoses student misconceptions.
"""

from typing import Dict, Any, List, Optional
import uuid
import logging
import re
import json

from backend.app.ai.providers import get_llm_provider, LLMProviderManager
from backend.app.ai.prompts import (
    TUTOR_SYSTEM_PROMPT,
    TEACH_ME_PROMPT,
    EXPLAIN_AGAIN_PROMPTS,
    ANSWER_EVALUATOR_PROMPT,
    format_prompt,
)
from backend.app.rag.retriever import get_retriever, Retriever, RetrievalResult

logger = logging.getLogger(__name__)


class TutorEngine:
    """
    Socratic Dialogue Engine implementing scaffolded inquiry,
    multi-strategy re-explanations, and formative misconception evaluation.
    """

    def __init__(
        self,
        llm_provider: Optional[LLMProviderManager] = None,
        retriever: Optional[Retriever] = None
    ):
        self.llm = llm_provider or get_llm_provider()
        self.retriever = retriever or get_retriever()
        # In-memory session tracking for active dialogues
        self._sessions: Dict[str, Dict[str, Any]] = {}

    def _get_or_create_session(self, session_id: Optional[str], topic_name: str, document_id: Optional[str]) -> str:
        sid = session_id or f"sess_{uuid.uuid4().hex[:12]}"
        if sid not in self._sessions:
            self._sessions[sid] = {
                "session_id": sid,
                "document_id": document_id,
                "topic_name": topic_name,
                "step_index": 0,
                "history": [],
                "current_question": None,
                "consecutive_errors": 0
            }
        return sid

    async def teach_concept(
        self,
        topic_name: str,
        document_id: Optional[str] = None,
        session_id: Optional[str] = None,
        pedagogical_mode: str = "socratic",
        preferred_difficulty: str = "intermediate"
    ) -> Dict[str, Any]:
        """
        Initiate or advance a teaching session on a concept.
        Executes first-principles scaffolding and returns a diagnostic check question.
        """
        sid = self._get_or_create_session(session_id, topic_name, document_id)
        session = self._sessions[sid]
        session["step_index"] += 1

        # 1. Retrieve grounded source excerpts
        retrieval: RetrievalResult = self.retriever.retrieve(
            query=f"{topic_name} fundamental principles equations definitions",
            document_id=document_id,
            top_k=4
        )
        context_str = retrieval.get_grounding_context()

        # 2. Build system and teach prompts
        system_inst = format_prompt(
            TUTOR_SYSTEM_PROMPT,
            topic_context=f"Topic: {topic_name} | Mode: {pedagogical_mode} | Difficulty: {preferred_difficulty}",
            retrieved_chunks=context_str
        )

        user_prompt = format_prompt(
            TEACH_ME_PROMPT,
            concept_name=topic_name,
            difficulty_level=preferred_difficulty,
            retrieved_chunks=context_str
        )

        # 3. Generate response via LLM
        response = await self.llm.generate(
            prompt=user_prompt,
            system_instruction=system_inst,
            json_mode=False,
            temperature=0.25
        )

        explanation_text = response.content

        # 4. Extract or format diagnostic check question
        diag_id = f"q_diag_{uuid.uuid4().hex[:8]}"
        diag_prompt = "Explain in your own words why this principle holds, and what happens when the threshold is not met."
        hints = [
            "Consider whether the interaction is continuous or one-to-one.",
            "Recall what property determines the threshold energy."
        ]

        # Extract question if marked in LLM response
        q_match = re.search(r"(?:Check Question|Formative Check Question|Question):\s*(.+?)(?=\n\n|\Z)", explanation_text, re.DOTALL | re.IGNORECASE)
        if q_match:
            diag_prompt = q_match.group(1).strip()

        session["current_question"] = {
            "question_id": diag_id,
            "prompt": diag_prompt,
            "hints": hints
        }

        # Track history
        session["history"].append({
            "step": session["step_index"],
            "role": "assistant",
            "mode": pedagogical_mode,
            "explanation": explanation_text,
            "question": diag_prompt
        })

        return {
            "session_id": sid,
            "step_index": session["step_index"],
            "topic_name": topic_name,
            "pedagogical_mode": pedagogical_mode,
            "scaffold_explanation": explanation_text,
            "diagnostic_question": {
                "question_id": diag_id,
                "question_type": "open_ended",
                "prompt": diag_prompt,
                "hints": hints
            },
            "citations": [c.to_dict() for c in retrieval.citations],
            "insufficient_context": retrieval.insufficient_context,
            "warning": retrieval.warning_message
        }

    async def explain_again(
        self,
        concept_name: str,
        desired_modality: str = "analogy",
        student_obstacle: Optional[str] = None,
        session_id: Optional[str] = None,
        document_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Provide an alternative explanation using one of 8 specific pedagogical modalities:
        simple, analogy, real_world, step_by_step, mathematical, visual, comparison, counterexample.
        """
        sid = self._get_or_create_session(session_id, concept_name, document_id)
        session = self._sessions[sid]

        modality = desired_modality.lower().strip()
        if modality not in EXPLAIN_AGAIN_PROMPTS:
            modality = "analogy"

        # Retrieve relevant context
        retrieval: RetrievalResult = self.retriever.retrieve(
            query=f"{concept_name} {student_obstacle or ''}",
            document_id=document_id or session.get("document_id"),
            top_k=3
        )
        context_str = retrieval.get_grounding_context()

        template = EXPLAIN_AGAIN_PROMPTS[modality]
        prompt = format_prompt(
            template,
            concept_name=concept_name,
            student_obstacle=student_obstacle or "I don't fully understand the core intuition.",
            retrieved_chunks=context_str
        )

        response = await self.llm.generate(
            prompt=prompt,
            system_instruction="You are an adaptive pedagogical explainer specializing in cognitive modalities.",
            json_mode=False,
            temperature=0.3
        )

        revised_text = response.content

        # Derive check question
        follow_up = f"How does this {modality} explanation help clarify the distinction you were stuck on?"
        q_match = re.search(r"(?:Check Question|Takeaway Question|Checkpoint):\s*(.+?)(?=\n\n|\Z)", revised_text, re.DOTALL | re.IGNORECASE)
        if q_match:
            follow_up = q_match.group(1).strip()

        session["history"].append({
            "step": session["step_index"],
            "role": "assistant",
            "action": "explain_again",
            "modality": modality,
            "revised_explanation": revised_text
        })

        return {
            "session_id": sid,
            "modality_used": modality,
            "revised_explanation": revised_text,
            "follow_up_check": {
                "prompt": follow_up
            },
            "citations": [c.to_dict() for c in retrieval.citations]
        }

    async def evaluate_answer(
        self,
        student_answer: str,
        question_id: Optional[str] = None,
        session_id: Optional[str] = None,
        question_prompt: Optional[str] = None,
        expected_criteria: Optional[str] = None,
        document_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Evaluate a student's answer, classify misconception type, and deliver guided scaffolding.
        """
        session = self._sessions.get(session_id or "", {})
        topic_name = session.get("topic_name", "Core Principles")
        
        # Use recorded question prompt if none passed
        if not question_prompt and session.get("current_question"):
            question_prompt = session["current_question"].get("prompt")
        question_prompt = question_prompt or "Explain the governing mechanism of this concept."

        # Retrieve source grounding
        retrieval: RetrievalResult = self.retriever.retrieve(
            query=f"{topic_name} {question_prompt}",
            document_id=document_id or session.get("document_id"),
            top_k=2
        )
        context_str = retrieval.get_grounding_context()

        eval_prompt = format_prompt(
            ANSWER_EVALUATOR_PROMPT,
            question_prompt=question_prompt,
            expected_criteria=expected_criteria or "Accurate understanding of first principles, discrete quanta, and threshold interaction.",
            student_answer=student_answer,
            retrieved_chunks=context_str
        )

        response = await self.llm.generate(
            prompt=eval_prompt,
            system_instruction="You are an expert misconception diagnostic assessor.",
            json_mode=True,
            temperature=0.1
        )

        data = response.structured
        if not data or not isinstance(data, dict):
            # Parse fallback JSON
            try:
                data = json.loads(re.sub(r"^```(?:json)?\s*|\s*```$", "", response.content.strip()))
            except Exception:
                data = {
                    "is_correct": False,
                    "confidence_score": 0.5,
                    "understanding_level": "PARTIAL",
                    "misconception_type": "CONCEPTUAL",
                    "misconception": {
                        "detected": True,
                        "category": "CONCEPTUAL",
                        "summary": "Partial mental model demonstrated.",
                        "explanation": "Review the individual interaction threshold vs collective intensity."
                    },
                    "scaffolded_hint": "Remember that energy is delivered in discrete packets.",
                    "mastery_delta": -0.05,
                    "next_action": "PROVIDE_HINT"
                }

        is_correct = data.get("is_correct", False)
        if session:
            if is_correct:
                session["consecutive_errors"] = 0
            else:
                session["consecutive_errors"] = session.get("consecutive_errors", 0) + 1

        return {
            "session_id": session_id,
            "question_id": question_id,
            "is_correct": is_correct,
            "understanding_level": data.get("understanding_level", "PARTIAL" if not is_correct else "PROFICIENT"),
            "confidence_score": data.get("confidence_score", 0.8),
            "misconception": data.get("misconception", {
                "detected": not is_correct,
                "category": data.get("misconception_type", "CONCEPTUAL" if not is_correct else "NONE"),
                "summary": "Check fundamental principle alignment.",
                "explanation": data.get("guided_hint", "")
            }),
            "scaffolded_hint": data.get("scaffolded_hint") or data.get("guided_hint", "Consider the first principles definition."),
            "pedagogical_prescription": data.get("pedagogical_prescription", "Review core threshold axioms."),
            "mastery_delta": data.get("mastery_delta", 0.10 if is_correct else -0.05),
            "next_action": data.get("next_action", "ADVANCE_CONCEPT" if is_correct else "PROVIDE_HINT")
        }


_global_tutor_engine: Optional[TutorEngine] = None

def get_tutor_engine() -> TutorEngine:
    global _global_tutor_engine
    if _global_tutor_engine is None:
        _global_tutor_engine = TutorEngine()
    return _global_tutor_engine
