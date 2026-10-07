"""
Standard Library Test Runner for Learnova AI, RAG, and Pedagogical Learning Core.
Runs without requiring third-party test runners.
"""

import sys
import os
import unittest
import asyncio
import tempfile
import gc
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir.parent))

from backend.app.rag.embeddings import (
    LocalEmbeddingProvider,
    GeminiEmbeddingProvider,
    get_embedding_provider
)
from backend.app.rag.vector_store import VectorStore, get_vector_store
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


class TestLearnovaCore(unittest.TestCase):

    def test_01_local_embeddings(self):
        provider = LocalEmbeddingProvider(dimension=384)
        self.assertEqual(provider.dimension, 384)
        
        vec1 = provider.embed_text("Photoelectric effect and photon energy quanta")
        vec2 = provider.embed_text("Photoelectric effect and photon energy quanta")
        vec3 = provider.embed_text("Completely unrelated botanical photosynthesis biological chloroplast")

        self.assertEqual(len(vec1), 384)
        self.assertEqual(len(vec2), 384)
        self.assertEqual(len(vec3), 384)
        self.assertEqual(vec1, vec2)

        dot_same = sum(a * b for a, b in zip(vec1, vec2))
        self.assertAlmostEqual(dot_same, 1.0, places=3)

        batch = provider.embed_batch(["First text", "Second text"])
        self.assertEqual(len(batch), 2)
        self.assertEqual(len(batch[0]), 384)

    def test_02_embedding_factory(self):
        provider = get_embedding_provider("local")
        self.assertIsNotNone(provider)
        self.assertGreater(provider.dimension, 0)

    def test_03_vector_store_crud_and_search(self):
        tmpdir = tempfile.mkdtemp()
        try:
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

            count = store.add_chunks(doc_id, chunks, embeddings)
            self.assertEqual(count, 3)
            self.assertEqual(store.count(doc_id), 3)

            q_vec = embedder.embed_text("photoelectric effect light quanta")
            results = store.search(q_vec, document_id=doc_id, top_k=2)

            self.assertLessEqual(len(results), 2)
            self.assertEqual(results[0]["id"], "chk_01")
            self.assertEqual(results[0]["page_number"], 3)
            self.assertIn("score", results[0])

            # Persistence test
            store_reloaded = VectorStore(db_path=db_path)
            self.assertEqual(store_reloaded.count(doc_id), 3)
            retrieved_chunk = store_reloaded.get_chunk("chk_02")
            self.assertIsNotNone(retrieved_chunk)
            self.assertEqual(retrieved_chunk["page_number"], 7)

            # Deletion test
            store_reloaded.delete_document(doc_id)
            self.assertEqual(store_reloaded.count(doc_id), 0)

            store.close()
            store_reloaded.close()
            del store
            del store_reloaded
            gc.collect()
        finally:
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_04_hybrid_retriever_and_citations(self):
        tmpdir = tempfile.mkdtemp()
        try:
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

            self.assertGreater(len(res.chunks), 0)
            self.assertGreater(len(res.citations), 0)
            top_citation = res.citations[0]
            self.assertEqual(top_citation.chunk_id, "chk_einstein")
            self.assertEqual(top_citation.page_number, 4)
            self.assertIn("[[Doc:doc_phys_01, Page:4, Chunk:chk_einstein]]", top_citation.to_envelope())

            sample_output = "As shown in [[Doc:doc_phys_01, Page:4, Chunk:chk_einstein]], photons carry discrete packets."
            all_valid, valid, hall = Retriever.verify_citations(sample_output, res.chunks)
            self.assertTrue(all_valid)
            self.assertIn("chk_einstein", valid)
            self.assertEqual(len(hall), 0)

            hall_output = "According to [[Doc:doc_phys_01, Page:99, Chunk:chk_fake_99]], magic occurs."
            all_valid, valid, hall = Retriever.verify_citations(hall_output, res.chunks)
            self.assertFalse(all_valid)
            self.assertIn("chk_fake_99", hall)

            store.close()
            del store
            del retriever
            gc.collect()
        finally:
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_05_mastery_tracker_bkt_and_sm2(self):
        tmpdir = tempfile.mkdtemp()
        try:
            db_path = str(Path(tmpdir) / "test_mastery.db")
            tracker = MasteryTracker(db_path=db_path)

            p1 = tracker.compute_bkt_update(0.10, is_correct=True)
            self.assertGreater(p1, 0.10)

            p0 = tracker.compute_bkt_update(0.50, is_correct=False)
            self.assertLess(p0, 0.50)

            sm2_good = tracker.compute_sm2_update(quality=5, repetition_count=0, easiness_factor=2.5, interval_days=1)
            self.assertEqual(sm2_good["repetition_count"], 1)
            self.assertEqual(sm2_good["interval_days"], 1)

            sm2_rep2 = tracker.compute_sm2_update(quality=5, repetition_count=1, easiness_factor=2.5, interval_days=1)
            self.assertEqual(sm2_rep2["repetition_count"], 2)
            self.assertEqual(sm2_rep2["interval_days"], 6)

            student_id = "usr_alice"
            topic_id = "top_duality"
            
            obs1 = tracker.record_observation(student_id, topic_id, is_correct=True, topic_name="Wave-Particle Duality")
            self.assertGreater(obs1["new_mastery"], 0.10)
            self.assertIn(obs1["status"], ["NOVICE", "DEVELOPING", "PROFICIENT", "MASTERED"])

            weak_list = tracker.get_weak_topics(student_id, threshold=0.99)
            self.assertGreaterEqual(len(weak_list), 1)
            self.assertEqual(weak_list[0]["topic_id"], topic_id)

            del tracker
            gc.collect()
        finally:
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_06_async_ai_components(self):
        async def run_async_tests():
            # 1. Local Fallback Provider
            provider = LocalFallbackProvider()
            res = await provider.generate(
                prompt="Teach me about wave particle duality from first principles",
                system_instruction=TUTOR_SYSTEM_PROMPT
            )
            self.assertIsNotNone(res.content)
            self.assertTrue("Intuition" in res.content or "photons" in res.content.lower())

            res_json = await provider.generate(
                prompt="Evaluate student answer: 'Because frequency exceeds cutoff' for misconception analysis (JSON)",
                json_mode=True
            )
            self.assertIsNotNone(res_json.structured)
            self.assertIn("is_correct", res_json.structured)

            # 2. Resilient Provider Manager
            manager = LLMProviderManager()
            res_mgr = await manager.generate("What is the work function in physics?")
            self.assertIsNotNone(res_mgr.content)

            # 3. Tutor Engine & 8 Modalities
            tutor = TutorEngine()
            teach_res = await tutor.teach_concept(
                topic_name="Cutoff Frequency & Work Function",
                pedagogical_mode="socratic",
                preferred_difficulty="intermediate"
            )
            self.assertIn("session_id", teach_res)
            self.assertIn("scaffold_explanation", teach_res)
            self.assertIn("diagnostic_question", teach_res)
            sid = teach_res["session_id"]

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
                self.assertEqual(again_res["modality_used"], mod)
                self.assertGreater(len(again_res["revised_explanation"]), 20)

            eval_res = await tutor.evaluate_answer(
                student_answer="Because energy is delivered in discrete packets h*nu.",
                session_id=sid
            )
            self.assertIn("is_correct", eval_res)
            self.assertIn("scaffolded_hint", eval_res)

            # 4. Document Analyzer & Study Packs
            analyzer = DocumentAnalyzer()
            analysis = await analyzer.analyze_document(
                document_id="doc_demo_01",
                title="Foundations of Quantum Mechanics",
                raw_text="Quantum mechanics governs discrete energy states and wave-particle duality."
            )
            self.assertIn("executive_summary", analysis)
            self.assertIn("topics", analysis)

            pack = await analyzer.generate_study_pack_content(
                document_id="doc_demo_01",
                pack_type="quick_revision"
            )
            self.assertIn("content_markdown", pack)

            # 5. Quiz Engine with indexed chunk
            v_store = get_vector_store()
            emb_prov = get_embedding_provider()
            v_store.add_chunks(
                document_id="doc_demo_01",
                chunks=[{
                    "id": "chk_demo_01",
                    "content": "Quantum physics deals with discrete energy states, photon interactions, and cutoff frequency.",
                    "page_number": 1
                }],
                embeddings=[emb_prov.embed_text("Quantum physics deals with discrete energy states, photon interactions, and cutoff frequency.")]
            )

            quiz_engine = QuizEngine()
            quiz_payload = await quiz_engine.generate_quiz(
                document_id="doc_demo_01",
                topic_ids=["top_01"],
                question_count=2,
                difficulty="intermediate"
            )
            self.assertIn("quiz_id", quiz_payload)
            self.assertGreaterEqual(len(quiz_payload["questions"]), 1)
            qid = quiz_payload["questions"][0]["id"]

            q_eval = await quiz_engine.evaluate_question(
                quiz_id=quiz_payload["quiz_id"],
                question_id=qid,
                submitted_answer="A"
            )
            self.assertIn("is_correct", q_eval)
            self.assertIn("explanation", q_eval)

            sub = await quiz_engine.evaluate_submission(
                quiz_id=quiz_payload["quiz_id"],
                submissions=[{"question_id": qid, "submitted_answer": "A"}],
                time_spent_seconds=45
            )
            self.assertIn("score_percentage", sub)
            self.assertIn("topic_breakdown", sub)

        asyncio.run(run_async_tests())

    def test_07_conversational_retrieval_and_tts_speech_cleaning(self):
        # 1. Test conversational query cleaning and keyword extraction in BM25 & Retriever
        cleaned_svm, tokens_svm = Retriever.clean_query("Can you explain SVM to me in simple terms?")
        self.assertIn("svm", tokens_svm)
        self.assertNotIn("can", tokens_svm)
        self.assertNotIn("explain", tokens_svm)
        self.assertNotIn("simple", tokens_svm)

        cleaned_margin, tokens_margin = Retriever.clean_query("What is margin?")
        self.assertIn("margin", tokens_margin)
        self.assertNotIn("what", tokens_margin)
        self.assertNotIn("is", tokens_margin)

        cleaned_fallback, tokens_fallback = Retriever.clean_query("I don't understand, give me an example")
        self.assertGreater(len(tokens_fallback), 0)

        # 2. Test Retriever on colloquial spoken queries against indexed material
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
                },
                {
                    "id": "chk_kernel_03",
                    "content": "The kernel trick maps input feature vectors into a higher-dimensional Hilbert space for linear separability.",
                    "page_number": 15,
                    "section_title": "Kernel Methods"
                }
            ]
            store.add_chunks(doc_id, chunks, [embedder.embed_text(c["content"]) for c in chunks])
            retriever = Retriever(vector_store=store, embedding_provider=embedder)

            # Query 1: Spoken inquiry for SVM in simple terms
            res1 = retriever.retrieve(
                query="Can you explain SVM to me in simple terms?",
                document_id=doc_id,
                top_k=2
            )
            self.assertFalse(res1.insufficient_context)
            self.assertGreater(len(res1.chunks), 0)
            self.assertEqual(res1.chunks[0]["id"], "chk_svm_01")

            # Query 2: Short spoken inquiry "What is margin?"
            res2 = retriever.retrieve(
                query="What is margin?",
                document_id=doc_id,
                top_k=2
            )
            self.assertFalse(res2.insufficient_context)
            self.assertGreater(len(res2.chunks), 0)
            self.assertEqual(res2.chunks[0]["id"], "chk_margin_02")

            # Query 3: Conversational confusion query
            res3 = retriever.retrieve(
                query="I don't understand, give me an example",
                document_id=doc_id,
                top_k=2
            )
            self.assertIsNotNone(res3)

        # 3. Test Text-to-Speech (TTS) Cleaning Engine
        raw_markdown_text = (
            "### 1. Intuition & The Core Axiom\n"
            "Light consists of discrete packets called **photons** [[Doc:doc_101, Page:4, Chunk:chk_01]].\n"
            "The energy relation is $E = h \\nu$, while wavelength is $\\lambda = \\frac{h}{p}$.\n"
            "| Parameter | Classical Wave | Quantum Reality |\n"
            "| :--- | :--- | :--- |\n"
            "| Energy Delivery | Continuous | Discrete |\n"
            "For more details, check `main_calc.py`."
        )

        spoken_clean = clean_for_speech(raw_markdown_text)

        # Check clean paragraphs and zero TTS symbol pollution
        self.assertNotIn("[[Doc:", spoken_clean)
        self.assertNotIn("###", spoken_clean)
        self.assertNotIn("**photons**", spoken_clean)
        self.assertIn("photons", spoken_clean)
        self.assertNotIn("| :--- |", spoken_clean)
        self.assertNotIn("| Parameter |", spoken_clean)
        self.assertNotIn("$", spoken_clean)
        self.assertNotIn("\\frac", spoken_clean)
        self.assertIn("nu", spoken_clean)
        self.assertIn("divided by", spoken_clean)

        # Test verbalized citation option
        spoken_verbalized = format_speech_response(raw_markdown_text, verbalize_citations=True)
        self.assertIn("page 4", spoken_verbalized)
        self.assertNotIn("[[Doc:", spoken_verbalized)

        # 4. Test Async Tutor Engine Conversational and Voice Turns
        async def run_voice_tutor_tests():
            tutor = TutorEngine()

            # A. Voice conversational inquiry
            conv_res = await tutor.converse(
                user_query="Can you explain SVM to me in simple terms?",
                voice_mode=True
            )
            self.assertIn("session_id", conv_res)
            self.assertTrue(conv_res["voice_mode"])
            self.assertIn("speech_text", conv_res)
            self.assertGreater(len(conv_res["speech_text"]), 20)
            self.assertNotIn("[[Doc:", conv_res["speech_text"])
            self.assertNotIn("**", conv_res["speech_text"])
            self.assertIn("diagnostic_question", conv_res)

            # B. Confusion follow-up turn in ongoing session
            conf_res = await tutor.converse(
                user_query="I don't understand, give me an example",
                session_id=conv_res["session_id"]
            )
            self.assertEqual(conf_res["intent"], "explain_again")
            self.assertIn("speech_text", conf_res)
            self.assertGreater(len(conf_res["speech_text"]), 20)

            # C. Verify teach_concept and explain_again populate speech_text
            teach_res = await tutor.teach_concept(topic_name="Support Vector Machines")
            self.assertIn("speech_text", teach_res)
            self.assertNotIn("[[Doc:", teach_res["speech_text"])

            again_res = await tutor.explain_again(concept_name="Margin", desired_modality="analogy")
            self.assertIn("speech_text", again_res)
            self.assertNotIn("[[Doc:", again_res["speech_text"])

        asyncio.run(run_voice_tutor_tests())


if __name__ == "__main__":
    unittest.main()
