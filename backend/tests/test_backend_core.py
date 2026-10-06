"""Comprehensive automated tests for Learnova core backend architecture.

Tests configuration, Pydantic schemas, database models & repositories,
document parsers, semantic chunker, and ReportLab PDF exporter.
"""

from datetime import datetime, timezone
from pathlib import Path
import sys
import tempfile
import pytest

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.config import settings
from app.models.schemas import (
    ChatRequest,
    ChatResponse,
    CitationSchema,
    DocumentCreate,
    DocumentResponse,
    EvaluateAnswerRequest,
    EvaluateAnswerResponse,
    ExplainAgainRequest,
    ExplainAgainResponse,
    QuestionSchema,
    QuizGenerateRequest,
    QuizResponse,
    QuizSubmitRequest,
    QuizSubmitResponse,
    StudentMasteryResponse,
    StudentProgressResponse,
    StudyPackGenerateRequest,
    StudyPackResponse,
    TeachRequest,
    TeachResponse,
    TopicMasterySchema,
    TopicSchema,
)
from app.models.database import (
    Base,
    ChunkRepository,
    DocumentRepository,
    LearningSessionRepository,
    QuizAttemptRepository,
    SessionLocal,
    StudentMasteryRepository,
    StudyPackRepository,
    engine,
    init_db,
)
from app.ingestion.parsers import DocumentParser, ParsedDocument
from app.ingestion.chunker import SemanticChunker
from app.study_packs.pdf_exporter import StudyPackPdfExporter


def test_config():
    """Verify settings loading, type conversions, and directories."""
    assert isinstance(settings.CORS_ORIGINS, list)
    assert len(settings.CORS_ORIGINS) > 0
    assert settings.uploads_dir.exists()
    assert settings.study_packs_dir.exists()
    assert settings.chroma_dir.exists()


def test_schemas_validation():
    """Verify Pydantic v2 schemas instantiation and constraints."""
    # Document schemas
    topic = TopicSchema(
        id="top_01",
        name="Wave-Particle Duality",
        difficulty_level="INTERMEDIATE",
        chunk_count=12,
        mastery_score=0.85,
    )
    doc_resp = DocumentResponse(
        id="doc_test123",
        filename="quantum_physics.pdf",
        title="Quantum Physics Fundamentals",
        file_size=102400,
        mime_type="application/pdf",
        status="READY",
        total_pages=10,
        total_chunks=30,
        word_count=5000,
        topic_count=1,
        topics=[topic],
        created_at=datetime.now(timezone.utc),
    )
    assert doc_resp.id == "doc_test123"
    assert doc_resp.topics[0].name == "Wave-Particle Duality"

    # Chat schemas
    chat_req = ChatRequest(document_id="doc_test123", query="What is wave function?")
    assert chat_req.top_k == 4
    chat_resp = ChatResponse(
        conversation_id="conv_1",
        message_id="msg_1",
        response="The wave function describes probability amplitude.",
        citations=[
            CitationSchema(
                citation_id="cite_1",
                document_id="doc_test123",
                page_number=3,
                snippet="Psi is probability amplitude.",
                relevance_score=0.95,
            )
        ],
    )
    assert len(chat_resp.citations) == 1

    # Tutor schemas
    teach_req = TeachRequest(
        document_id="doc_test123",
        topic_id="top_01",
        pedagogical_mode="socratic",
    )
    assert teach_req.pedagogical_mode == "socratic"

    # Quiz schemas
    quiz_gen = QuizGenerateRequest(document_id="doc_test123", question_count=5)
    assert quiz_gen.question_count == 5

    # Study pack schemas
    sp_req = StudyPackGenerateRequest(
        document_id="doc_test123", title="Exam Mastery Pack"
    )
    assert sp_req.include_flashcards is True


def test_database_and_repositories():
    """Verify table creation and CRUD operations using repository pattern."""
    init_db()
    db = SessionLocal()
    try:
        doc_repo = DocumentRepository(db)
        chunk_repo = ChunkRepository(db)
        sess_repo = LearningSessionRepository(db)
        quiz_repo = QuizAttemptRepository(db)
        mastery_repo = StudentMasteryRepository(db)
        pack_repo = StudyPackRepository(db)

        # 1. Document CRUD
        doc_repo.delete("doc_test_unit")
        doc = doc_repo.create(
            filename="sample_notes.pdf",
            file_path="storage/uploads/sample_notes.pdf",
            file_size=2048,
            page_count=3,
            word_count=900,
            title="Sample Notes",
            doc_id="doc_test_unit",
        )
        assert doc.id == "doc_test_unit"
        assert doc.status == "PROCESSING"

        # Update status
        doc_updated = doc_repo.update_status(
            "doc_test_unit", status="READY", summary="Summary of sample notes."
        )
        assert doc_updated.status == "READY"
        assert doc_updated.summary == "Summary of sample notes."

        # 2. Chunk CRUD
        chunks = chunk_repo.bulk_create(
            [
                {
                    "id": "chk_test_unit_001",
                    "document_id": "doc_test_unit",
                    "chunk_index": 0,
                    "page_number": 1,
                    "section_title": "Overview",
                    "content": "Quantum mechanics is a fundamental theory in physics.",
                    "token_count": 10,
                },
                {
                    "id": "chk_test_unit_002",
                    "document_id": "doc_test_unit",
                    "chunk_index": 1,
                    "page_number": 2,
                    "section_title": "Wavefunction",
                    "content": "Born interpretation relates wavefunction to probability.",
                    "token_count": 9,
                },
            ]
        )
        assert len(chunks) == 2
        doc_chunks = chunk_repo.get_by_document("doc_test_unit")
        assert len(doc_chunks) == 2

        # 3. Learning Session
        sess = sess_repo.create(
            document_id="doc_test_unit",
            student_id="usr_test",
            current_topic="Wave-Particle Duality",
        )
        assert sess.current_step == 1
        sess_repo.append_message(sess.id, role="user", content="Explain duality.")
        sess_repo.append_message(
            sess.id, role="assistant", content="Think of ripples vs pebbles."
        )
        sess_repo.advance_step(sess.id)
        refreshed_sess = sess_repo.get_by_id(sess.id)
        assert refreshed_sess.current_step == 2
        assert len(refreshed_sess.get_messages()) == 2

        # 4. Quiz Attempt
        attempt = quiz_repo.create(
            document_id="doc_test_unit",
            student_id="usr_test",
            total_questions=2,
            correct_answers=2,
            score_percentage=100.0,
            answers=[{"question_id": "q1", "is_correct": True}],
            misconceptions=[],
            time_spent_seconds=60,
        )
        assert attempt.score_percentage == 100.0
        attempts = quiz_repo.list_by_student("usr_test")
        assert len(attempts) >= 1

        # 5. Student Mastery
        mastery = mastery_repo.upsert_mastery(
            student_id="usr_test",
            topic_name="Wave-Particle Duality",
            mastery_delta=0.35,
            document_id="doc_test_unit",
        )
        assert mastery.mastery_score >= 0.8
        assert mastery.confidence == "HIGH"

        # 6. Study Pack persistence
        pack = pack_repo.create(
            document_id="doc_test_unit",
            title="Wave Mechanics Pack",
            content={"summary": "Detailed summary"},
        )
        assert pack.status == "GENERATING"
        pack_repo.update_pdf(pack.id, pdf_path="dummy.pdf", pdf_size_bytes=5000)
        refreshed_pack = pack_repo.get_by_id(pack.id)
        assert refreshed_pack.status == "READY"
        assert refreshed_pack.pdf_size_bytes == 5000

        # Clean up
        doc_repo.delete("doc_test_unit")
        assert doc_repo.get_by_id("doc_test_unit") is None

    finally:
        db.close()


def test_document_parser():
    """Verify document parser extracts sections, pages, and metadata from text."""
    sample_text = """# Chapter 1: Foundations of Mechanics

Classical mechanics describes macroscopic objects moving at speeds much lower than light.

## Section 1.1: Newton's Laws of Motion

First law states an object at rest remains at rest unless acted upon by a net force.
Second law: F = m * a.
Third law: Action and reaction are equal and opposite.

# Chapter 2: Energy and Work

Work is scalar product of force and displacement.
"""
    parsed = DocumentParser.parse_file(
        file_source=sample_text.encode("utf-8"),
        original_filename="mechanics.md",
    )

    assert isinstance(parsed, ParsedDocument)
    assert parsed.filename == "mechanics.md"
    assert parsed.total_pages >= 1
    assert len(parsed.sections) >= 3
    assert parsed.word_count > 20
    assert any("Newton" in s.title or "Foundations" in s.title for s in parsed.sections)


def test_semantic_chunker():
    """Verify chunker creates properly sized chunks with page & section metadata."""
    sample_md = """# Modern Physics Introduction
The discovery of the photoelectric effect showed that light delivers energy in packets called photons.
Each photon carries energy proportional to frequency: E = h * nu.

## Compton Scattering
Arthur Compton demonstrated that X-ray photons collide with electrons like billiard balls.
This firmly established the corpuscular nature of electromagnetic radiation.
"""
    parsed = DocumentParser.parse_file(
        file_source=sample_md.encode("utf-8"),
        original_filename="modern_physics.md",
    )

    chunker = SemanticChunker(target_chunk_tokens=50, max_chunk_tokens=100)
    chunks = chunker.chunk_document(parsed, document_id="doc_modphys")

    assert len(chunks) >= 1
    for chunk in chunks:
        assert chunk.document_id == "doc_modphys"
        assert chunk.page_number >= 1
        assert chunk.token_count > 0
        assert chunk.content != ""


def test_pdf_exporter():
    """Verify ReportLab PDF exporter generates a styled PDF conforming to FigureAI tokens."""
    exporter = StudyPackPdfExporter()

    sample_pack_data = {
        "summary": "This study pack provides an axiomatic review of quantum harmonic oscillators and wavefunctions.",
        "key_concepts": [
            {
                "name": "Zero-Point Energy",
                "description": "The lowest possible energy that a quantum mechanical physical system may have.",
                "difficulty_level": "INTERMEDIATE",
            },
            {
                "name": "Hermite Polynomials",
                "description": "Orthogonal polynomials that form the eigenfunctions of the quantum oscillator.",
                "difficulty_level": "ADVANCED",
            },
        ],
        "formula_sheet": [
            {
                "name": "Oscillator Energy Levels",
                "formula": "E_n = (n + 1/2) hbar omega",
                "variables": "n = 0,1,2..., omega = angular frequency",
            },
            {
                "name": "de Broglie Wavelength",
                "formula": "lambda = h / p",
                "variables": "h = Planck constant, p = momentum",
            },
        ],
        "misconceptions": [
            {
                "misconception": "Ground state has zero kinetic energy.",
                "explanation": "Heisenberg uncertainty principle requires non-zero minimum energy Delta x * Delta p >= hbar/2.",
            }
        ],
        "practice_problems": [
            {
                "question": "Calculate the zero-point energy of an oscillator with frequency 10^14 Hz.",
                "answer": "E_0 = 1/2 * h * nu = 3.31 x 10^-20 J.",
                "explanation": "Apply n=0 in the energy eigenvalue equation.",
            }
        ],
        "flashcards": [
            {
                "front": "What is the ground state quantum number for a quantum harmonic oscillator?",
                "back": "n = 0, giving non-zero ground state energy E_0 = 1/2 hbar omega.",
            }
        ],
        "revision_checklist": [
            "Derive ladder operators a and a-dagger.",
            "Verify commutator [x, p] = i*hbar.",
            "Solve the ground state wavefunction normalization integral.",
        ],
    }

    pack_id = "pack_test_figureai"
    pdf_path, pdf_size = exporter.generate_pdf(
        pack_id=pack_id,
        title="Quantum Harmonic Oscillator Mastery Pack",
        pack_data=sample_pack_data,
        document_id="doc_phys_qho",
        filename="harmonic_oscillator.pdf",
    )

    path_obj = Path(pdf_path)
    assert path_obj.exists()
    assert pdf_size > 2000

    # Verify PDF signature (%PDF-)
    with open(path_obj, "rb") as f:
        header = f.read(5)
        assert header.startswith(b"%PDF-")


if __name__ == "__main__":
    print("Running Learnova core backend tests...")
    test_config()
    print("Config tests passed!")
    test_schemas_validation()
    print("Schemas tests passed!")
    test_database_and_repositories()
    print("Database & Repositories tests passed!")
    test_document_parser()
    print("Document Parser tests passed!")
    test_semantic_chunker()
    print("Semantic Chunker tests passed!")
    test_pdf_exporter()
    print("PDF Exporter tests passed!")
    print("All Learnova backend core tests passed successfully!")
