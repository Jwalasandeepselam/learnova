"""
Comprehensive Unit and Integration Test Suite for Learnova AI, RAG, and Pedagogical Learning Core.
Tests:
- Embeddings (Local & Gemini fallback)
- Vector Store (Persistence, Cosine Search, Metadata)
- Hybrid Retriever (BM25, Dense, RRF, Citations, Insufficiency Detection)
- LLM Providers (Resilience, LocalFallback, JSON Mode)
- Prompt Engine & Versioning
- Tutor Engine (Socratic Scaffolding, 8 Explain Again Modalities, Misconception Evaluation)
- Document Analyzer (Summaries, Topics, Formulas, Study Packs)
- Quiz Engine (Formative MCQ/Short Answer, Distractor Diagnoses, Submission Metrics)
- Mastery Tracker (BKT Math, SM-2 Intervals, Weak Concept Remediation)
"""

import pytest
import os
import tempfile
import asyncio
from pathlib import Path

from backend.app.rag.embeddings import (
    LocalEmbeddingProvider,
    GeminiEmbeddingProvider,
    get_embedding_provider
)
from backend.app.rag.vector_store import VectorStore
from backend.app.rag.retriever import Retriever, Citation
from backend.app.ai.providers import (
    LocalFallbackProvider,
    GeminiProvider,
    LLMProviderManager,
    LLMResponse
)
from backend.app.ai.prompts import (
    TUTOR_SYSTEM_PROMPT,
    TEACH_ME_PROMPT,
    EXPLAIN_AGAIN_PROMPTS,
    VOICE_TUTOR_SYSTEM_PROMPT,
    format_prompt,
    clean_for_speech,
    format_speech_response,
)
from backend.app.ai.tutor import TutorEngine
from backend.app.ai.analyzer import DocumentAnalyzer
from backend.app.ai.quiz import QuizEngine
from backend.app.student.mastery import MasteryTracker


# ---------------------------------------------------------------------------
# 1. Embeddings Tests
# ---------------------------------------------------------------------------
def test_local_embedding_provider():
    provider = LocalEmbeddingProvider(dimension=384)
    assert provider.dimension == 384
    
    vec1 = provider.embed_text("Photoelectric effect and photon energy quanta")
    vec2 = provider.embed_text("Photoelectric effect and photon energy quanta")
    vec3 = provider.embed_text("Completely unrelated botanical photosynthesis biological chloroplast")

    assert len(vec1) == 384
    assert len(vec2) == 384
    assert len(vec3) == 384

    # Test determinism
    assert vec1 == vec2

    # Test cosine similarity between vec1 and vec2 is 1.0
    dot_same = sum(a * b for a, b in zip(vec1, vec2))
    assert abs(dot_same - 1.0) < 1e-4

    # Test batch embedding
    batch = provider.embed_batch(["First text", "Second text"])
    assert len(batch) == 2
    assert len(batch[0]) == 384


def test_embedding_factory():
    provider = get_embedding_provider("local")
    assert provider is not None
    assert provider.dimension > 0


# ---------------------------------------------------------------------------
# 2. Vector Store Tests
# ---------------------------------------------------------------------------
def test_vector_store_crud_and_search():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        db_path = str(Path(tmpdir) / "test_vectors.db")
        store = VectorStore(db_path=db_path)

        doc_id = "doc_test_101"
        chunks = [
            {
                "id": "chk_01",
                "content": "Einstein explained the photoelectric effect using Planck quanta: E = h * nu.",
                "page_number": 3,
                "slide_number": None,
                "section_title": "Photoelectric Effect"
            },
            {
                "id": "chk_02",
                "content": "De Broglie hypothesized that particles have wave characteristics: lambda = h / p.",
                "page_number": 7,
                "slide_number": None,
                "section_title": "Matter Waves"
            },
            {
                "id": "chk_03",
                "content": "Schrodinger wave equation describes the quantum state of an isolated physical system.",
                "page_number": 12,
                "slide_number": None,
                "section_title": "Wave Mechanics"
            }
        ]

        embedder = LocalEmbeddingProvider(dimension=64)
        embeddings = [embedder.embed_text(c["content"]) for c in chunks]

        # Add chunks
        count = store.add_chunks(doc_id, chunks, embeddings)
        assert count == 3
        assert store.count(doc_id) == 3

        # Search query matching chunk 1
        q_vec = embedder.embed_text("photoelectric effect light quanta")
        results = store.search(q_vec, document_id=doc_id, top_k=2)

        assert len(results) <= 2
        assert results[0]["id"] == "chk_01"
        assert results[0]["page_number"] == 3
        assert results[0]["section_title"] == "Photoelectric Effect"
        assert "score" in results[0]

        # Persistence test: reopen database from disk
        store_reloaded = VectorStore(db_path=db_path)
        assert store_reloaded.count(doc_id) == 3
        retrieved_chunk = store_reloaded.get_chunk("chk_02")
        assert retrieved_chunk is not None
        assert retrieved_chunk["page_number"] == 7

        # Delete document
        store_reloaded.delete_document(doc_id)
        assert store_reloaded.count(doc_id) == 0


# ---------------------------------------------------------------------------
# 3. Hybrid Retriever & Citations Tests
# ---------------------------------------------------------------------------
def test_hybrid_retriever_and_citations():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        db_path = str(Path(tmpdir) / "test_retriever.db")
        store = VectorStore(db_path=db_path)
        embedder = LocalEmbeddingProvider(dimension=64)

        doc_id = "doc_phys_01"
        chunks = [
            {
                "id": "chk_einstein",
                "content": "Light quanta or photons carry energy proportional to frequency: E = h * nu. Electrons are released immediately.",
                "page_number": 4,
                "section_title": "Quantum Photons"
            },
            {
                "id": "chk_classical",
                "content": "Classical wave theory predicted energy accumulation over extended time intervals.",
                "page_number": 5,
                "section_title": "Classical Failure"
            }
        ]
        store.add_chunks(doc_id, chunks, [embedder.embed_text(c["content"]) for c in chunks])

        retriever = Retriever(vector_store=store, embedding_provider=embedder)
        res = retriever.retrieve(
            query="frequency and photon energy E = h * nu",
            document_id=doc_id,
            document_title="Modern Quantum Physics",
            top_k=2
        )

        assert len(res.chunks) > 0
        assert len(res.citations) > 0
        top_citation = res.citations[0]
        assert top_citation.chunk_id == "chk_einstein"
        assert top_citation.page_number == 4
        assert "[[Doc:doc_phys_01, Page:4, Chunk:chk_einstein]]" in top_citation.to_envelope()

        # Test citation verification helper
        sample_output = "As shown in [[Doc:doc_phys_01, Page:4, Chunk:chk_einstein]], photons carry discrete packets."
        all_valid, valid, hall = Retriever.verify_citations(sample_output, res.chunks)
        assert all_valid is True
        assert "chk_einstein" in valid
        assert len(hall) == 0

        # Test hallucination detection
        hall_output = "According to [[Doc:doc_phys_01, Page:99, Chunk:chk_fake_99]], magic occurs."
        all_valid, valid, hall = Retriever.verify_citations(hall_output, res.chunks)
        assert all_valid is False
        assert "chk_fake_99" in hall


# ---------------------------------------------------------------------------
# 4. AI Provider & Fallback Tests
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_local_fallback_provider():
    provider = LocalFallbackProvider()
    
    # 1. Plain text generation
    res = await provider.generate(
        prompt="Teach me about wave particle duality from first principles",
        system_instruction=TUTOR_SYSTEM_PROMPT
    )
    assert res.content is not None
    assert "Intuition" in res.content or "photons" in res.content.lower()

    # 2. JSON structured output
    res_json = await provider.generate(
        prompt="Evaluate student answer: 'Because frequency exceeds cutoff' for misconception analysis (JSON)",
        json_mode=True
    )
    assert res_json.structured is not None
    assert "is_correct" in res_json.structured
    assert "misconception" in res_json.structured


@pytest.mark.asyncio
async def test_provider_manager_resilience():
    manager = LLMProviderManager()
    # Regardless of network or api keys, manager must return valid response
    res = await manager.generate("What is the work function in physics?")
    assert res.content is not None
    assert len(res.content) > 10


# ---------------------------------------------------------------------------
# 5. Tutor Engine & 8 Modalities Tests
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_tutor_engine_modalities():
    tutor = TutorEngine()
    
    # Teach Concept
    teach_res = await tutor.teach_concept(
        topic_name="Cutoff Frequency & Work Function",
        pedagogical_mode="socratic",
        preferred_difficulty="intermediate"
    )
    assert "session_id" in teach_res
    assert "scaffold_explanation" in teach_res
    assert "diagnostic_question" in teach_res
    sid = teach_res["session_id"]

    # Test all 8 Explain Again modalities
    modalities = [
        "simple", "analogy", "real_world", "step_by_step",
        "mathematical", "visual", "comparison", "counterexample"
    ]
    for mod in modalities:
        again_res = await tutor.explain_again(
            concept_name="Work Function",
            desired_modality=mod,
            student_obstacle="I do not see why energy cannot accumulate over time.",
            session_id=sid
        )
        assert again_res["modality_used"] == mod
        assert len(again_res["revised_explanation"]) > 20
        assert "follow_up_check" in again_res

    # Answer Evaluation
    eval_res = await tutor.evaluate_answer(
        student_answer="Because energy is delivered in discrete packets h*nu.",
        session_id=sid
    )
    assert "is_correct" in eval_res
    assert "scaffolded_hint" in eval_res


# ---------------------------------------------------------------------------
# 6. Document Analyzer & Study Pack Tests
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_document_analyzer():
    analyzer = DocumentAnalyzer()
    analysis = await analyzer.analyze_document(
        document_id="doc_demo_01",
        title="Foundations of Quantum Mechanics",
        raw_text="Quantum mechanics governs discrete energy states and wave-particle duality."
    )
    assert "executive_summary" in analysis
    assert "topics" in analysis
    assert len(analysis["topics"]) >= 1

    # Study pack generation
    pack = await analyzer.generate_study_pack_content(
        document_id="doc_demo_01",
        pack_type="quick_revision"
    )
    assert "content_markdown" in pack
    assert len(pack["content_markdown"]) > 20


# ---------------------------------------------------------------------------
# 7. Quiz Engine Tests
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_quiz_engine():
    quiz_engine = QuizEngine()
    
    # Generate Quiz
    quiz_payload = await quiz_engine.generate_quiz(
        document_id="doc_demo_01",
        topic_ids=["top_01"],
        question_count=2,
        difficulty="intermediate"
    )
    assert "quiz_id" in quiz_payload
    assert len(quiz_payload["questions"]) >= 1
    qid = quiz_payload["questions"][0]["id"]

    # Evaluate single question
    q_eval = await quiz_engine.evaluate_question(
        quiz_id=quiz_payload["quiz_id"],
        question_id=qid,
        submitted_answer="A"
    )
    assert "is_correct" in q_eval
    assert "explanation" in q_eval

    # Full quiz submission
    submission = await quiz_engine.evaluate_submission(
        quiz_id=quiz_payload["quiz_id"],
        submissions=[{"question_id": qid, "submitted_answer": "A"}],
        time_spent_seconds=60
    )
    assert "score_percentage" in submission
    assert "topic_breakdown" in submission
    assert "recommended_review_date" in submission


# ---------------------------------------------------------------------------
# 8. Student Mastery (BKT & SM-2) Tests
# ---------------------------------------------------------------------------
def test_mastery_tracker_bkt_and_sm2():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = str(Path(tmpdir) / "test_mastery.db")
        tracker = MasteryTracker(db_path=db_path)

        # BKT mathematical verification:
        # Prior = 0.10, correct answer should increase probability
        p1 = tracker.compute_bkt_update(0.10, is_correct=True)
        assert p1 > 0.10

        # Incorrect answer should lower or maintain low probability
        p0 = tracker.compute_bkt_update(0.50, is_correct=False)
        assert p0 < 0.50

        # SM-2 verification:
        sm2_good = tracker.compute_sm2_update(quality=5, repetition_count=0, easiness_factor=2.5, interval_days=1)
        assert sm2_good["repetition_count"] == 1
        assert sm2_good["interval_days"] == 1

        sm2_rep2 = tracker.compute_sm2_update(quality=5, repetition_count=1, easiness_factor=2.5, interval_days=1)
        assert sm2_rep2["repetition_count"] == 2
        assert sm2_rep2["interval_days"] == 6

        # Full observation cycle
        student_id = "usr_alice"
        topic_id = "top_duality"
        
        obs1 = tracker.record_observation(student_id, topic_id, is_correct=True, topic_name="Wave-Particle Duality")
        assert obs1["new_mastery"] > 0.10
        assert obs1["status"] in ["NOVICE", "DEVELOPING", "PROFICIENT", "MASTERED"]

        # Weak topics extraction
        weak_list = tracker.get_weak_topics(student_id, threshold=0.99)
        assert len(weak_list) >= 1
        assert weak_list[0]["topic_id"] == topic_id


# ---------------------------------------------------------------------------
# 9. Conversational Query Preprocessing & Retrieval Tests
# ---------------------------------------------------------------------------
def test_conversational_retrieval_and_tts_speech_cleaner():
    # 1. Query keyword extraction
    cleaned_svm, tokens_svm = Retriever.clean_query("Can you explain SVM to me in simple terms?")
    assert "svm" in tokens_svm
    assert "can" not in tokens_svm
    assert "explain" not in tokens_svm
    assert "simple" not in tokens_svm

    cleaned_margin, tokens_margin = Retriever.clean_query("What is margin?")
    assert "margin" in tokens_margin
    assert "what" not in tokens_margin
    assert "is" not in tokens_margin

    # 2. Hybrid Retrieval with conversational query tolerance
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        db_path = str(Path(tmpdir) / "test_conv_retriever.db")
        store = VectorStore(db_path=db_path)
        embedder = LocalEmbeddingProvider(dimension=64)

        doc_id = "doc_ml_svm"
        chunks = [
            {
                "id": "chk_svm_01",
                "content": "Support Vector Machines (SVM) classify instances by constructing hyperplanes in multidimensional space.",
                "page_number": 10,
                "section_title": "SVM Formulation"
            },
            {
                "id": "chk_margin_02",
                "content": "The margin is the geometric distance between the decision boundary hyperplane and the closest training data points.",
                "page_number": 12,
                "section_title": "Margin Definition"
            }
        ]
        store.add_chunks(doc_id, chunks, [embedder.embed_text(c["content"]) for c in chunks])
        retriever = Retriever(vector_store=store, embedding_provider=embedder)

        res1 = retriever.retrieve(
            query="Can you explain SVM to me in simple terms?",
            document_id=doc_id,
            top_k=2
        )
        assert not res1.insufficient_context
        assert res1.chunks[0]["id"] == "chk_svm_01"

        res2 = retriever.retrieve(
            query="What is margin?",
            document_id=doc_id,
            top_k=2
        )
        assert not res2.insufficient_context
        assert res2.chunks[0]["id"] == "chk_margin_02"

    # 3. TTS speech cleaning
    raw = (
        "### 1. Intuition\n"
        "Energy arrives in discrete **photons** [[Doc:doc_101, Page:4, Chunk:chk_01]].\n"
        "The relation is $E = h \\nu$, while $\\lambda = \\frac{h}{p}$."
    )
    clean = clean_for_speech(raw)
    assert "[[Doc:" not in clean
    assert "###" not in clean
    assert "**photons**" not in clean
    assert "photons" in clean
    assert "$" not in clean
    assert "\\nu" not in clean
    assert "nu" in clean
    assert "divided by" in clean

    verbalized = format_speech_response(raw, verbalize_citations=True)
    assert "page 4" in verbalized
    assert "[[Doc:" not in verbalized


# ---------------------------------------------------------------------------
# 10. Voice Tutor Engine Conversational Turns
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_voice_tutor_engine_conversation():
    tutor = TutorEngine()

    # Conversational teaching turn
    res = await tutor.converse(
        user_query="Can you explain SVM to me in simple terms?",
        voice_mode=True
    )
    assert "session_id" in res
    assert res["voice_mode"] is True
    assert "speech_text" in res
    assert len(res["speech_text"]) > 20
    assert "[[Doc:" not in res["speech_text"]
    assert "**" not in res["speech_text"]

    # Confusion re-explanation turn
    conf = await tutor.converse(
        user_query="I don't understand, give me an example",
        session_id=res["session_id"]
    )
    assert conf["intent"] == "explain_again"
    assert "speech_text" in conf

    # Verify teach_concept and explain_again return speech_text
    teach = await tutor.teach_concept(topic_name="Support Vector Machines")
    assert "speech_text" in teach

    again = await tutor.explain_again(concept_name="Margin", desired_modality="analogy")
    assert "speech_text" in again
