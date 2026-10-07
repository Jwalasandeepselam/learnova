"""
Tutor API Router.
Implements the interactive Socratic AI Teacher, multi-strategy re-explanations,
and formative misconception evaluation.
"""

import re
import uuid
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from backend.app.models.database import (
    get_db,
    DocumentRepository,
    LearningSessionRepository,
    StudentMasteryRepository
)
from backend.app.models.schemas import (
    TeachRequest,
    TeachResponse,
    ExplainAgainRequest,
    ExplainAgainResponse,
    EvaluateAnswerRequest,
    EvaluateAnswerResponse,
    ConverseRequest,
    ConverseResponse,
    DiagnosticQuestionSchema,
    FollowUpCheckSchema,
    MisconceptionSchema,
    CitationSchema,
    SuccessEnvelope,
)
from backend.app.ai.tutor import get_tutor_engine

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/tutor", tags=["Tutor"])


@router.post(
    "/teach",
    response_model=SuccessEnvelope[TeachResponse],
    summary="Teach a concept step-by-step interactively"
)
async def teach_concept(
    req: TeachRequest,
    db: Session = Depends(get_db)
):
    """
    Deconstructs a topic into intuitive foundations, technical first principles,
    an illustrative analogy, a practical application, and an active recall check question.
    """
    doc_repo = DocumentRepository(db)
    sess_repo = LearningSessionRepository(db)

    doc = doc_repo.get_by_id(req.document_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document '{req.document_id}' not found.")

    # Determine topic name
    topic_name = "Core Principles"
    if req.topic:
        topic_name = req.topic
    elif req.topic_id:
        doc_topics = doc.get_topics() or []
        for t in doc_topics:
            if t.get("id") == req.topic_id or t.get("name") == req.topic_id:
                topic_name = t.get("name", req.topic_id)
                break
        if topic_name == "Core Principles":
            topic_name = req.topic_id
    elif doc.title:
        topic_name = doc.title

    tutor = get_tutor_engine()
    result = await tutor.teach_concept(
        topic_name=topic_name,
        document_id=req.document_id,
        session_id=req.session_id,
        pedagogical_mode=req.pedagogical_mode or "socratic",
        preferred_difficulty=req.preferred_difficulty or "intermediate"
    )

    sid = result.get("session_id", req.session_id or f"sess_{uuid.uuid4().hex[:12]}")
    dq = result.get("diagnostic_question", {})
    diagnostic_schema = DiagnosticQuestionSchema(
        question_id=dq.get("question_id", f"q_diag_{uuid.uuid4().hex[:8]}"),
        question_type=dq.get("question_type", "open_ended"),
        prompt=dq.get("prompt", f"Explain how {topic_name} operates under core boundary conditions."),
        hints=dq.get("hints", [])
    )

    citations = [
        CitationSchema(
            citation_id=f"cite_{c.get('chunk_id')}",
            document_id=c.get("document_id", req.document_id),
            page_number=c.get("page_number", 1),
            chunk_id=c.get("chunk_id"),
            snippet=c.get("snippet", ""),
            relevance_score=c.get("relevance_score", 0.9)
        )
        for c in result.get("citations", [])
    ]

    # Save session turn
    try:
        sess = sess_repo.get_by_id(sid)
        if not sess:
            sess_repo.create(
                document_id=req.document_id,
                student_id="usr_figure_01",
                session_id=sid,
                topic_id=req.topic_id,
                current_topic=topic_name,
                session_mode=req.pedagogical_mode or "SOCRATIC"
            )
        sess_repo.append_message(sid, role="assistant", content=result.get("scaffold_explanation", ""))
    except Exception as e:
        logger.warning("Could not persist tutor session: %s", e)

    scaffold = result.get("scaffold_explanation", "")

    # Extract pedagogical sections if present
    def _extract_section(text: str, pattern: str) -> Optional[str]:
        m = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        return m.group(1).strip() if m else None

    intuition = _extract_section(scaffold, r"(?:### 1\. Intuition.*?|\bIntuition:?)\n+(.*?)(?=\n+###|\Z)") or (scaffold[:300] if scaffold else "Core intuitive foundation.")
    technical = _extract_section(scaffold, r"(?:### 2\. (?:First Principles|The Physical|Technical).*?|\bTechnical:?)\n+(.*?)(?=\n+###|\Z)") or scaffold
    analogy = _extract_section(scaffold, r"(?:### 3\. (?:Concrete )?Analogy.*?|\bAnalogy:?)\n+(.*?)(?=\n+###|\Z)")
    real_world = _extract_section(scaffold, r"(?:### 4\. (?:Real-World|Practical).*?|\bReal-World:?)\n+(.*?)(?=\n+###|\Z)")

    payload = TeachResponse(
        session_id=sid,
        step_index=result.get("step_index", 1),
        topic_name=topic_name,
        topic=topic_name,
        pedagogical_mode=req.pedagogical_mode or "socratic",
        scaffold_explanation=scaffold,
        intuition=intuition,
        technical_concept=technical,
        analogy=analogy,
        real_world_example=real_world,
        diagnostic_question=diagnostic_schema,
        citations=citations,
        speech_text=result.get("speech_text")
    )

    return SuccessEnvelope(data=payload)


@router.post(
    "/explain-again",
    response_model=SuccessEnvelope[ExplainAgainResponse],
    summary="Adapt explanation using targeted cognitive modality"
)
async def explain_again(
    req: ExplainAgainRequest,
    db: Session = Depends(get_db)
):
    """
    When a student says 'I don't understand', never repeats the same text.
    Adapts across 8 cognitive modalities: simpler, analogy, real_world, step_by_step,
    mathematical, visual, comparison, or counterexample.
    """
    sess_repo = LearningSessionRepository(db)
    concept_name = req.get_concept() if hasattr(req, "get_concept") else (req.target_concept or req.topic or "Core Concept")
    modality = req.get_modality() if hasattr(req, "get_modality") else (req.desired_modality or req.strategy or "analogy")
    obstacle = req.student_obstacle or req.current_obstacle
    sid = req.session_id or f"sess_{uuid.uuid4().hex[:12]}"

    # Map frontend 'simpler' or 'example' to tutor engine modal tags
    modality_map = {
        "simpler": "simple",
        "example": "real_world",
    }
    mapped_modality = modality_map.get(modality, modality)

    tutor = get_tutor_engine()
    result = await tutor.explain_again(
        concept_name=concept_name,
        desired_modality=mapped_modality,
        student_obstacle=obstacle,
        session_id=sid
    )

    fu = result.get("follow_up_check", {})
    follow_up_schema = FollowUpCheckSchema(
        prompt=fu.get("prompt", f"How does this {modality} perspective help clarify {concept_name}?")
    )

    try:
        sess_repo.append_message(sid, role="assistant", content=result.get("revised_explanation", ""))
    except Exception as e:
        logger.warning("Could not update session history: %s", e)

    payload = ExplainAgainResponse(
        session_id=sid,
        modality_used=result.get("modality_used", mapped_modality),
        revised_explanation=result.get("revised_explanation", ""),
        topic=concept_name,
        follow_up_check=follow_up_schema,
        speech_text=result.get("speech_text")
    )

    return SuccessEnvelope(data=payload)


@router.post(
    "/evaluate-answer",
    response_model=SuccessEnvelope[EvaluateAnswerResponse],
    summary="Evaluate student response and diagnose misconceptions"
)
async def evaluate_answer(
    req: EvaluateAnswerRequest,
    db: Session = Depends(get_db)
):
    """
    Evaluates student response, identifies misconception category (conceptual, procedural,
    factual, terminological), provides constructive guidance, and updates student topic mastery.
    """
    tutor = get_tutor_engine()
    sess_repo = LearningSessionRepository(db)
    mastery_repo = StudentMasteryRepository(db)

    sid = req.session_id or f"sess_{uuid.uuid4().hex[:12]}"
    sess = sess_repo.get_by_id(sid)
    topic_name = req.topic or (sess.current_topic if sess and sess.current_topic else "Fundamental Concept")
    doc_id = req.document_id or (sess.document_id if sess else None)

    eval_result = await tutor.evaluate_answer(
        student_answer=req.student_answer,
        question_id=req.question_id,
        session_id=sid,
        question_prompt=req.question,
        document_id=doc_id
    )

    is_correct = eval_result.get("is_correct", False)
    misc_dict = eval_result.get("misconception", {})
    mastery_delta = eval_result.get("mastery_delta", 0.10 if is_correct else -0.05)

    # Persist student response in session
    try:
        sess_repo.append_message(req.session_id, role="user", content=req.student_answer)
    except Exception as e:
        logger.warning("Could not record student answer in session: %s", e)

    # Update Student Mastery in SQLite
    student_id = "usr_figure_01"
    try:
        mastery_repo.upsert_mastery(
            student_id=student_id,
            topic_name=topic_name,
            mastery_delta=mastery_delta,
            document_id=doc_id,
            weak_concept=misc_dict.get("summary") if not is_correct else None
        )
    except Exception as e:
        logger.warning("Could not persist student mastery: %s", e)

    misc_schema = MisconceptionSchema(
        detected=misc_dict.get("detected", not is_correct),
        category=misc_dict.get("category", "NONE" if is_correct else "CONCEPTUAL"),
        summary=misc_dict.get("summary", "Accurate mental model demonstrated." if is_correct else "Concept requires refinement."),
        explanation=misc_dict.get("explanation", "Grounded in source principles." if is_correct else "Review the governing threshold relationships.")
    )

    payload = EvaluateAnswerResponse(
        is_correct=is_correct,
        understanding_level=eval_result.get("understanding_level", "COMPLETE" if is_correct else "PARTIAL"),
        misconception=misc_schema,
        scaffolded_hint=eval_result.get("scaffolded_hint", "Consider the discrete relationship between energy and frequency."),
        mastery_delta=mastery_delta,
        next_action=eval_result.get("next_action", "PROCEED" if is_correct else "PROVIDE_HINT")
    )

    return SuccessEnvelope(data=payload)


@router.post(
    "/converse",
    response_model=SuccessEnvelope[ConverseResponse],
    summary="Conversational and voice Socratic inquiry"
)
async def converse(
    req: ConverseRequest,
    db: Session = Depends(get_db)
):
    """
    Handle natural spoken or conversational queries:
    - 'Can you explain SVM to me in simple terms?'
    - 'What is margin?'
    - 'I don't understand, give me an example'
    Outputs Socratic guidance with speech_text optimized for Text-to-Speech (TTS).
    """
    sess_repo = LearningSessionRepository(db)
    tutor = get_tutor_engine()

    result = await tutor.converse(
        user_query=req.user_query,
        document_id=req.document_id,
        session_id=req.session_id,
        voice_mode=req.voice_mode,
        preferred_difficulty=req.preferred_difficulty or "intermediate"
    )

    sid = result.get("session_id", req.session_id or f"sess_{uuid.uuid4().hex[:12]}")
    dq = result.get("diagnostic_question", {})
    diagnostic_schema = DiagnosticQuestionSchema(
        question_id=dq.get("question_id", f"q_diag_{uuid.uuid4().hex[:8]}"),
        question_type=dq.get("question_type", "open_ended"),
        prompt=dq.get("prompt", "What do you think is the key takeaway?"),
        hints=dq.get("hints", [])
    ) if dq else None

    citations = [
        CitationSchema(
            citation_id=f"cite_{c.get('chunk_id')}",
            document_id=c.get("document_id", req.document_id or "unknown"),
            page_number=c.get("page_number", 1),
            chunk_id=c.get("chunk_id"),
            snippet=c.get("snippet", ""),
            relevance_score=c.get("relevance_score", 0.9)
        )
        for c in result.get("citations", [])
    ]

    try:
        sess = sess_repo.get_by_id(sid)
        if not sess and req.document_id:
            sess_repo.create(
                document_id=req.document_id,
                student_id="usr_figure_01",
                session_id=sid,
                topic_id=None,
                current_topic=result.get("topic_name", "Conversational Inquiry"),
                session_mode="VOICE_SOCRATIC" if req.voice_mode else "SOCRATIC"
            )
        sess_repo.append_message(sid, role="user", content=req.user_query)
        sess_repo.append_message(sid, role="assistant", content=result.get("scaffold_explanation", ""))
    except Exception as e:
        logger.warning("Could not persist converse session: %s", e)

    payload = ConverseResponse(
        session_id=sid,
        intent=result.get("intent", "teach_concept"),
        topic_name=result.get("topic_name", "Conversational Inquiry"),
        pedagogical_mode=result.get("pedagogical_mode", "voice_socratic" if req.voice_mode else "socratic"),
        scaffold_explanation=result.get("scaffold_explanation", ""),
        speech_text=result.get("speech_text"),
        diagnostic_question=diagnostic_schema,
        citations=citations,
        voice_mode=req.voice_mode
    )

    return SuccessEnvelope(data=payload)
