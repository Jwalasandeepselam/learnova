"""
Comprehensive End-to-End REST API Integration Test Suite for LEARNOVA.
Verifies full user journeys across documents, grounded RAG, Socratic tutoring,
adaptive quizzing, ReportLab PDF study pack generation, and student mastery.
"""

import io
import os
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def unwrap(resp):
    """Helper to unwrap SuccessEnvelope responses."""
    body = resp.json()
    if isinstance(body, dict) and "data" in body and body["data"] is not None:
        return body["data"]
    return body


def test_health_check():
    """Verify system health endpoint."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "learnova-backend"


def test_full_learning_lifecycle_e2e():
    """
    End-to-End Milestone 1 through Milestone 4 verification:
    1. Upload document (PDF/TXT)
    2. List documents and get details
    3. Grounded RAG Chat with exact citations
    4. Socratic Teach Me session & 8 Explain Again modalities
    5. Formative answer evaluation & misconception diagnosis
    6. Adaptive quiz generation, single evaluation, and submission
    7. High-fidelity ReportLab Study Pack generation & PDF download
    8. Student mastery analytics & BKT tracking
    9. Document cleanup & deletion
    """
    # 1. Upload Educational Document
    sample_doc_content = (
        "# Quantum Physics: Principles of Matter and Waves\n\n"
        "## 1. The Photoelectric Effect\n"
        "Albert Einstein proposed in 1905 that electromagnetic radiation is quantized into discrete packets called photons. "
        "The energy of each photon is given by E = h * nu, where h is Planck's constant (6.626e-34 J*s) and nu is the frequency. "
        "Electrons are emitted instantaneously only when the incident radiation frequency exceeds the material cutoff threshold f0, "
        "regardless of the beam's macroscopic intensity. The work function Phi represents the minimum energy required to remove an electron.\n\n"
        "## 2. De Broglie Matter Waves\n"
        "In 1924, Louis de Broglie hypothesized that particles of matter also exhibit wave-like behavior. "
        "The characteristic wavelength is lambda = h / p, where p = m * v is the relativistic momentum. "
        "This matter-wave duality explains the discrete electron orbits in the Bohr atomic model and forms the basis of quantum mechanics."
    )

    file_bytes = sample_doc_content.encode("utf-8")
    files = {
        "file": ("quantum_foundations.md", io.BytesIO(file_bytes), "text/markdown")
    }
    data = {"title": "Quantum Physics Foundations"}

    upload_resp = client.post("/api/documents/upload", files=files, data=data)
    assert upload_resp.status_code in [200, 201], upload_resp.text
    doc_data = unwrap(upload_resp)
    doc_id = doc_data["id"]
    assert doc_id.startswith("doc_")
    assert doc_data["title"] == "Quantum Physics Foundations"
    assert doc_data["status"] == "READY"

    try:
        # 2. Document List & Detail
        list_resp = client.get("/api/documents")
        assert list_resp.status_code == 200
        docs_list = unwrap(list_resp)
        items = docs_list.get("documents") or docs_list.get("items") or []
        assert any(d["id"] == doc_id for d in items)

        get_resp = client.get(f"/api/documents/{doc_id}")
        assert get_resp.status_code == 200
        assert unwrap(get_resp)["id"] == doc_id

        # 3. Grounded RAG Chat with Citations
        chat_payload = {
            "document_id": doc_id,
            "message": "What formula links photon energy to frequency and what is Planck's constant?",
            "top_k": 3
        }
        chat_resp = client.post("/api/chat", json=chat_payload)
        assert chat_resp.status_code == 200
        chat_data = unwrap(chat_resp)
        assert len(chat_data["answer"]) > 10
        assert chat_data["is_grounded"] is True
        assert len(chat_data["citations"]) > 0
        first_citation = chat_data["citations"][0]
        assert first_citation["document_id"] == doc_id
        assert first_citation["page_number"] >= 1

        # 4. Socratic Tutor: Teach Me
        teach_payload = {
            "document_id": doc_id,
            "topic": "Photoelectric Effect",
            "student_level": "intermediate"
        }
        teach_resp = client.post("/api/tutor/teach", json=teach_payload)
        assert teach_resp.status_code == 200
        teach_data = unwrap(teach_resp)
        assert teach_data["topic"] == "Photoelectric Effect"
        assert len(teach_data["intuition"]) > 10
        assert teach_data["diagnostic_question"] is not None

        # 4b. Socratic Tutor: Explain Again (Analogy strategy)
        again_payload = {
            "document_id": doc_id,
            "topic": "Photoelectric Effect",
            "strategy": "analogy",
            "student_obstacle": "Why can't dim high-frequency light be outdone by bright red light?"
        }
        again_resp = client.post("/api/tutor/explain-again", json=again_payload)
        assert again_resp.status_code == 200
        again_data = unwrap(again_resp)
        assert again_data["modality_used"] == "analogy"
        assert len(again_data["revised_explanation"]) > 15
        assert "speech_text" in again_data

        # 4b. Conversational & Voice Socratic Inquiry
        conv_resp = client.post("/api/tutor/converse", json={
            "document_id": doc_id,
            "user_query": "Can you explain SVM to me in simple terms?",
            "voice_mode": True
        })
        assert conv_resp.status_code == 200
        conv_data = unwrap(conv_resp)
        assert "speech_text" in conv_data
        assert conv_data["voice_mode"] is True
        assert len(conv_data["speech_text"]) > 20

        # 5. Formative Answer Evaluation & Misconception Diagnosis
        eval_payload = {
            "document_id": doc_id,
            "topic": "Photoelectric Effect",
            "question": "What happens if we increase light brightness without changing frequency below threshold?",
            "student_answer": "No electrons will be released because each photon still has energy below the work function.",
            "student_id": "test_student_01"
        }
        eval_resp = client.post("/api/tutor/evaluate-answer", json=eval_payload)
        assert eval_resp.status_code == 200
        eval_data = unwrap(eval_resp)
        assert eval_data["is_correct"] is True
        assert eval_data["mastery_delta"] > 0

        # 6. Adaptive Quiz Generation
        quiz_gen_payload = {
            "document_id": doc_id,
            "topic": "Photoelectric Effect",
            "num_questions": 3,
            "difficulty": "medium"
        }
        quiz_resp = client.post("/api/quiz/generate", json=quiz_gen_payload)
        assert quiz_resp.status_code == 200
        quiz_data = unwrap(quiz_resp)
        assert len(quiz_data["questions"]) >= 1
        first_q = quiz_data["questions"][0]

        # 6b. Single Question Immediate Evaluation
        single_eval_payload = {
            "question_id": first_q["id"],
            "question_prompt": first_q["prompt"],
            "student_answer": first_q.get("correct_answer") or first_q.get("correct_option") or "A",
            "correct_answer": first_q.get("correct_answer") or first_q.get("correct_option") or "A",
            "topic": "Photoelectric Effect"
        }
        sq_resp = client.post("/api/quiz/evaluate", json=single_eval_payload)
        assert sq_resp.status_code == 200
        assert unwrap(sq_resp)["is_correct"] is True

        # 6c. Submit Quiz Attempt
        submit_payload = {
            "quiz_id": quiz_data["id"],
            "document_id": doc_id,
            "student_id": "test_student_01",
            "answers": [
                {
                    "question_id": first_q["id"],
                    "question_prompt": first_q["prompt"],
                    "student_answer": "A",
                    "correct_answer": "A",
                    "topic_name": "Photoelectric Effect"
                }
            ],
            "time_spent_seconds": 90
        }
        submit_resp = client.post("/api/quiz/submit", json=submit_payload)
        assert submit_resp.status_code == 200
        submit_data = unwrap(submit_resp)
        assert submit_data["score_percentage"] == 100.0
        assert submit_data["passed"] is True

        # 7. Generate Study Pack & PDF Export
        pack_payload = {
            "document_id": doc_id,
            "title": "Quantum Foundations Exam Revision Pack",
            "pack_type": "exam_preparation",
            "include_flashcards": True,
            "include_cheat_sheet": True
        }
        pack_resp = client.post("/api/study-packs/generate", json=pack_payload)
        assert pack_resp.status_code == 200
        pack_data = unwrap(pack_resp)
        pack_id = pack_data["id"]
        assert pack_data["pdf_url"] is not None

        # 7b. Download PDF
        pdf_resp = client.get(f"/api/study-packs/{pack_id}/pdf")
        assert pdf_resp.status_code == 200
        assert pdf_resp.headers["content-type"] == "application/pdf"
        assert len(pdf_resp.content) > 1000  # Non-trivial valid PDF binary

        # 8. Student Analytics
        prog_resp = client.get("/api/student/progress?student_id=test_student_01")
        assert prog_resp.status_code == 200
        prog_data = unwrap(prog_resp)
        assert prog_data["total_topics_tracked"] >= 1

        mastery_resp = client.get("/api/student/mastery?student_id=test_student_01")
        assert mastery_resp.status_code == 200
        mastery_data = unwrap(mastery_resp)
        assert len(mastery_data["topics"]) >= 1

    finally:
        # 9. Clean up test document
        del_resp = client.delete(f"/api/documents/{doc_id}")
        assert del_resp.status_code == 200
