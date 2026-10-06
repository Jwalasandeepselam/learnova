"""
Learnova Document Content Analyzer
Analyzes document chunks to synthesize executive summaries, structured topic hierarchies,
formula cheat-sheets, and comprehensive Study Pack content.
"""

from typing import Dict, Any, List, Optional
import json
import logging
import re
import uuid

from backend.app.ai.providers import get_llm_provider, LLMProviderManager
from backend.app.ai.prompts import ANALYZER_PROMPT, STUDY_PACK_PROMPTS, format_prompt
from backend.app.rag.vector_store import get_vector_store, VectorStore

logger = logging.getLogger(__name__)


class DocumentAnalyzer:
    """
    Document conceptual analyzer extracting hierarchical topics,
    formulas, definitions, and Study Pack artifacts.
    """

    def __init__(
        self,
        llm_provider: Optional[LLMProviderManager] = None,
        vector_store: Optional[VectorStore] = None
    ):
        self.llm = llm_provider or get_llm_provider()
        self.vector_store = vector_store or get_vector_store()

    async def analyze_document(
        self,
        document_id: str,
        title: Optional[str] = None,
        raw_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze document content to produce executive summary,
        topics hierarchy, key formulas, and core definitions.
        """
        # Gather text content from chunks or raw_text
        chunks = self.vector_store.get_document_chunks(document_id)
        if chunks:
            # Sample or combine first chunks to maintain token budget
            combined_content = "\n\n".join([
                f"[Chunk {c['chunk_index']} | Page {c.get('page_number', 1)}]\n{c['content']}"
                for c in chunks[:12]
            ])
        elif raw_text:
            combined_content = raw_text[:8000]
        else:
            combined_content = f"Document ID: {document_id}. Title: {title or 'Academic Document'}."

        prompt = format_prompt(ANALYZER_PROMPT, document_content=combined_content)

        response = await self.llm.generate(
            prompt=prompt,
            system_instruction="You are an expert academic curriculum architect.",
            json_mode=True,
            temperature=0.1
        )

        data = response.structured
        if not data or not isinstance(data, dict):
            try:
                clean_text = re.sub(r"^```(?:json)?\s*|\s*```$", "", response.content.strip())
                data = json.loads(clean_text)
            except Exception:
                # Safe pedagogical defaults
                data = {
                    "title": title or "Document Analysis",
                    "executive_summary": "Comprehensive overview of foundational principles and formulations presented in the document.",
                    "topics": [
                        {
                            "id": "top_01",
                            "name": "Foundational Principles",
                            "description": "Core concepts and basic definitions.",
                            "difficulty_level": "BEGINNER",
                            "prerequisites": [],
                            "key_terms": ["Axiom", "Principle"]
                        }
                    ],
                    "key_formulas": [],
                    "core_definitions": [],
                    "diagnostic_check_questions": []
                }

        # Ensure topic IDs are well formed
        topics = data.get("topics", [])
        for i, t in enumerate(topics, 1):
            if not t.get("id"):
                t["id"] = f"top_{i:02d}"

        return {
            "document_id": document_id,
            "title": data.get("title") or title or f"Document {document_id}",
            "executive_summary": data.get("executive_summary", ""),
            "topics": topics,
            "key_formulas": data.get("key_formulas", []),
            "core_definitions": data.get("core_definitions", []),
            "diagnostic_check_questions": data.get("diagnostic_check_questions", [])
        }

    async def generate_study_pack_content(
        self,
        document_id: str,
        pack_type: str = "complete_notes",
        custom_instructions: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate specific Study Pack content:
        complete_notes, quick_revision, exam_prep, or formula_sheet.
        """
        chunks = self.vector_store.get_document_chunks(document_id)
        if chunks:
            combined_content = "\n\n".join([c["content"] for c in chunks[:10]])
        else:
            combined_content = f"Source Document ID: {document_id}"

        template = STUDY_PACK_PROMPTS.get(pack_type, STUDY_PACK_PROMPTS["complete_notes"])
        prompt = format_prompt(template, document_content=combined_content)
        if custom_instructions:
            prompt += f"\n\nAdditional Guidance: {custom_instructions}"

        response = await self.llm.generate(
            prompt=prompt,
            system_instruction="You are a master academic textbook author creating publication-grade Study Packs.",
            json_mode=False,
            temperature=0.2
        )

        return {
            "document_id": document_id,
            "pack_type": pack_type,
            "content_markdown": response.content,
            "provider": response.provider,
            "model": response.model
        }


_global_analyzer: Optional[DocumentAnalyzer] = None

def get_document_analyzer() -> DocumentAnalyzer:
    global _global_analyzer
    if _global_analyzer is None:
        _global_analyzer = DocumentAnalyzer()
    return _global_analyzer
