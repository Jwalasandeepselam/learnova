"""
Quiz API Router.
Handles formative question generation, instant single-question grading,
and full quiz attempt submission with mastery tracking.
"""

import uuid
import logging
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from backend.app.models.database import (
    get_db,
    DocumentRepository,
    QuizAttemptRepository,
    StudentMasteryRepository
)
from backend.app.models.schemas import (
    QuizGenerateRequest,
    QuizResponse,
    QuestionSchema,
    QuizOptionSchema,
    QuestionEvaluationRequest,
    QuestionEvaluationResponse,
    QuizSubmitRequest,
    QuizSubmitResponse,
    TopicBreakdownSchema,
    CitationSchema,
    SuccessEnvelope,
)
from backend.app.ai.quiz import get_quiz_engine
from backend.app.student.mastery import get_mastery_tracker

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/quiz", tags=["Quiz"])


@router.post(
    "/generate",
    response_model=SuccessEnvelope[QuizResponse],
    summary="Generate adaptive quiz grounded in document"
)
async def generate_quiz(
    req: QuizGenerateRequest,
    db: Session = Depends(get_db)
):
    """
    Synthesizes adaptive questions (MCQs, short answer, conceptual) with targeted distractors
    grounded in the uploaded document.
    """
    doc_repo = DocumentRepository(db)
    doc = doc_repo.get_by_id(req.document_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document '{req.document_id}' not found.")

    quiz_engine = get_quiz_engine()
    q_count = req.get_count() if hasattr(req, "get_count") else (req.num_questions or req.question_count or 5)
    t_ids = req.topic_ids or ([req.topic] if req.topic else None)

    raw_quiz = await quiz_engine.generate_quiz(
        document_id=req.document_id,
        topic_ids=t_ids,
        question_count=q_count,
        difficulty=req.difficulty or "adaptive"
    )

    questions_out: List[QuestionSchema] = []
    for q in raw_quiz.get("questions", []):
        options = None
        if q.get("options"):
            options = []
            for opt in q["options"]:
                if isinstance(opt, dict):
                    options.append(QuizOptionSchema(key=opt.get("key", "A"), text=opt.get("text", "")))
                elif isinstance(opt, str):
                    # In case options are string array ["A) Option 1", ...]
                    parts = opt.split(")", 1)
                    key = parts[0].strip() if len(parts) > 1 else "A"
                    text = parts[1].strip() if len(parts) > 1 else opt
                    options.append(QuizOptionSchema(key=key, text=text))

        questions_out.append(QuestionSchema(
            id=q.get("id", f"q_{uuid.uuid4().hex[:6]}"),
            type=q.get("type", "mcq"),
            topic_id=q.get("topic_id"),
            prompt=q.get("prompt", ""),
            options=options,
            correct_option=q.get("correct_option"),
            correct_answer=q.get("correct_answer") or q.get("correct_option")
        ))

    payload = QuizResponse(
        quiz_id=raw_quiz.get("quiz_id", f"quiz_{uuid.uuid4().hex[:10]}"),
        id=raw_quiz.get("quiz_id", f"quiz_{uuid.uuid4().hex[:10]}"),
        document_id=req.document_id,
        total_questions=len(questions_out),
        questions=questions_out
    )

    return SuccessEnvelope(data=payload)


@router.post(
    "/evaluate",
    response_model=SuccessEnvelope[QuestionEvaluationResponse],
    summary="Evaluate a single quiz answer immediately"
)
async def evaluate_single_question(
    req: QuestionEvaluationRequest
):
    """Provides immediate formative feedback and misconception analysis for a single answer."""
    quiz_engine = get_quiz_engine()
    submitted_ans = req.get_answer() if hasattr(req, "get_answer") else (req.submitted_answer or req.student_answer or "")
    res = await quiz_engine.evaluate_question(
        quiz_id=req.quiz_id,
        question_id=req.question_id or "q_single",
        submitted_answer=submitted_ans,
        correct_answer=req.correct_answer
    )

    cit_dict = res.get("citation")
    cit_schema = None
    if cit_dict and isinstance(cit_dict, dict) and cit_dict.get("chunk_id"):
        cit_schema = CitationSchema(
            citation_id=f"cite_{cit_dict.get('chunk_id')}",
            document_id=cit_dict.get("document_id", "unknown"),
            page_number=cit_dict.get("page_number", 1),
            chunk_id=cit_dict.get("chunk_id"),
            snippet=cit_dict.get("snippet", ""),
            relevance_score=0.9
        )

    payload = QuestionEvaluationResponse(
        question_id=req.question_id,
        is_correct=res.get("is_correct", False),
        correct_answer=res.get("correct_answer", req.correct_answer or "A"),
        explanation=res.get("explanation", "Evaluated against ground truth."),
        citation=cit_schema
    )

    return SuccessEnvelope(data=payload)


@router.post(
    "/submit",
    response_model=SuccessEnvelope[QuizSubmitResponse],
    summary="Submit complete quiz attempt and record mastery"
)
async def submit_quiz(
    req: QuizSubmitRequest,
    db: Session = Depends(get_db)
):
    """
    Grades the entire attempt, records attempt history, and updates the student's
    Bayesian Knowledge Tracing mastery profile in the database.
    """
    quiz_engine = get_quiz_engine()
    quiz_repo = QuizAttemptRepository(db)
    mastery_repo = StudentMasteryRepository(db)
    mastery_tracker = get_mastery_tracker()

    submissions = req.get_submissions() if hasattr(req, "get_submissions") else (req.submissions or req.answers or [])
    sub_dicts = [{"question_id": s.question_id, "submitted_answer": s.get_answer()} for s in submissions]

    eval_result = await quiz_engine.evaluate_submission(
        quiz_id=req.quiz_id,
        submissions=sub_dicts,
        time_spent_seconds=req.time_spent_seconds
    )

    total_q = eval_result.get("total_questions", len(submissions))
    correct_count = eval_result.get("correct_count", 0)
    score_pct = eval_result.get("score_percentage", 0.0)

    # Convert topic breakdown
    topic_breakdown_out: List[TopicBreakdownSchema] = []
    student_id = req.student_id or "usr_figure_01"
    doc_id = req.document_id or "doc_default"

    for tb in eval_result.get("topic_breakdown", []):
        t_name = tb.get("topic_name", "Core Principles")
        t_score = float(tb.get("score", 0.0))
        t_correct = t_score >= 0.7

        # Update cognitive mastery tracker (BKT + SM-2)
        m_update = mastery_tracker.record_observation(
            student_id=student_id,
            topic_id=f"top_{t_name.lower().replace(' ', '_')[:24]}",
            is_correct=t_correct,
            topic_name=t_name
        )
        new_mastery = m_update.get("new_mastery", 0.5)

        # Update DB repository
        try:
            mastery_repo.upsert_mastery(
                student_id=student_id,
                topic_name=t_name,
                mastery_delta=0.10 if t_correct else -0.05,
                document_id=doc_id
            )
        except Exception as e:
            logger.warning("Could not persist mastery in DB: %s", e)

        topic_breakdown_out.append(TopicBreakdownSchema(
            topic_id=f"top_{t_name.lower().replace(' ', '_')[:24]}",
            topic_name=t_name,
            score=min(1.0, max(0.0, t_score)),
            new_mastery_level=min(1.0, max(0.0, new_mastery))
        ))

    # Parse recommended review date
    rec_date_str = eval_result.get("recommended_review_date")
    rec_date = None
    if rec_date_str:
        try:
            rec_date = datetime.fromisoformat(rec_date_str.replace("Z", "+00:00"))
        except Exception:
            rec_date = datetime.now(timezone.utc)

    # Save attempt in DB
    misc_list = [m.get("summary") if isinstance(m, dict) else str(m) for m in eval_result.get("identified_misconceptions", [])]
    attempt = quiz_repo.create(
        document_id=doc_id,
        student_id=student_id,
        total_questions=total_q,
        correct_answers=correct_count,
        score_percentage=score_pct,
        answers=sub_dicts,
        misconceptions=eval_result.get("identified_misconceptions", []),
        time_spent_seconds=req.time_spent_seconds
    )

    passed = eval_result.get("passed", score_pct >= 70.0)

    payload = QuizSubmitResponse(
        attempt_id=attempt.id,
        quiz_id=req.quiz_id,
        score_percentage=score_pct,
        total_questions=total_q,
        correct_count=correct_count,
        time_spent_seconds=req.time_spent_seconds,
        passed=passed,
        topic_breakdown=topic_breakdown_out,
        identified_misconceptions=misc_list,
        recommended_review_date=rec_date
    )

    return SuccessEnvelope(data=payload)
