"""
Chat API Router.
Provides grounded RAG Q&A with strict citations over ingested course material.
"""

import uuid
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from backend.app.models.database import get_db, DocumentRepository, LearningSessionRepository
from backend.app.models.schemas import (
    ChatRequest,
    ChatResponse,
    CitationSchema,
    SuccessEnvelope,
)
from backend.app.rag.vector_store import get_vector_store
from backend.app.rag.embeddings import get_embedding_provider
from backend.app.rag.retriever import Retriever
from backend.app.ai.providers import get_llm_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post(
    "",
    response_model=SuccessEnvelope[ChatResponse],
    summary="Ask questions grounded in uploaded document with citations"
)
async def ask_chat(
    req: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    Retrieves the most relevant chunks from the specified document,
    prompts the LLM with strict grounding instructions,
    and returns an answer accompanied by verbatim source citations.
    """
    doc_repo = DocumentRepository(db)
    sess_repo = LearningSessionRepository(db)

    doc = doc_repo.get_by_id(req.document_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document '{req.document_id}' not found.")

    query_text = getattr(req, "query", None) or getattr(req, "message", "")
    if not query_text:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    # 1. Retrieve relevant chunks
    vector_store = get_vector_store()
    embedder = get_embedding_provider()
    retriever = Retriever(vector_store=vector_store, embedding_provider=embedder)

    retrieval_result = retriever.retrieve(
        query=query_text,
        document_id=req.document_id,
        document_title=doc.title,
        top_k=req.top_k or 4
    )

    # 2. Build Grounded Context
    context_chunks = retrieval_result.chunks
    citations = []
    for cit in retrieval_result.citations:
        citations.append(CitationSchema(
            citation_id=f"cite_{cit.chunk_id}",
            document_id=cit.document_id,
            page_number=cit.page_number or 1,
            chunk_id=cit.chunk_id,
            snippet=cit.snippet,
            relevance_score=getattr(cit, "relevance_score", 0.85)
        ))

    context_str = "\n\n".join([
        f"--- Source Chunk [Page {c.get('page_number', 1)}, Section: '{c.get('section_title', 'General')}'] ---\n{c.get('content', '')}"
        for c in context_chunks
    ])

    system_instruction = (
        "You are LEARNOVA, an expert AI Personal Teaching Assistant. "
        "Answer the student's question based strictly on the provided context excerpts from the student's course material. "
        "Cite the specific page numbers or sections whenever making factual claims using format [[Doc:<id>, Page:<p>, Chunk:<k>]]. "
        "If the answer is not present in the excerpts, clearly state that the uploaded document does not cover this detail, "
        "and distinguish any general academic guidance from source facts. "
        "Never fabricate page numbers or quotations. Maintain an encouraging, precise, and intellectually rigorous tone."
    )

    user_prompt = (
        f"Document: {doc.title}\n\n"
        f"Source Excerpts:\n{context_str}\n\n"
        f"Student Question: {query_text}\n\n"
        "Provide a clear, grounded explanation with page citations:"
    )

    llm_manager = get_llm_manager()
    try:
        llm_response = await llm_manager.generate(
            prompt=user_prompt,
            system_instruction=system_instruction,
            temperature=0.2
        )
        answer_text = llm_response.content
    except Exception as e:
        logger.error("LLM Generation failed: %s", e)
        answer_text = (
            f"Based on your document '{doc.title}', here is the key concept:\n\n"
            + (context_chunks[0].get("content") if context_chunks else "No specific text found.")
        )

    # Update or create session
    conv_id = req.conversation_id or f"conv_{uuid.uuid4().hex[:12]}"
    try:
        sess = sess_repo.get_by_id(conv_id)
        if not sess:
            sess = sess_repo.create(
                document_id=req.document_id,
                student_id="usr_figure_01",
                session_id=conv_id
            )
        sess_repo.append_message(conv_id, role="user", content=query_text)
        sess_repo.append_message(conv_id, role="assistant", content=answer_text)
    except Exception as e:
        logger.warning("Could not persist learning session turns: %s", e)

    response_payload = ChatResponse(
        conversation_id=conv_id,
        session_id=conv_id,
        message_id=f"msg_{uuid.uuid4().hex[:8]}",
        response=answer_text,
        answer=answer_text,
        citations=citations,
        grounded=not retrieval_result.insufficient_context and bool(context_chunks),
        is_grounded=not retrieval_result.insufficient_context and bool(context_chunks),
        confidence=0.92 if context_chunks else 0.50
    )

    return SuccessEnvelope(data=response_payload)
