"""Document management and ingestion routes."""

from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
from typing import List, Optional
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.config import settings
from app.models.database import DocumentRepository, ChunkRepository, get_db
from app.models.schemas import (
    DocumentResponse,
    DocumentListResponse,
    PaginationSchema,
    DocumentAnalysisRequest,
    DocumentAnalysisResponse,
    SuccessEnvelope,
    TopicSchema,
)
from app.ingestion.parsers import DocumentParser
from app.ingestion.chunker import SemanticChunker
from backend.app.rag.vector_store import get_vector_store
from backend.app.rag.embeddings import get_embedding_provider
from backend.app.ai.analyzer import get_document_analyzer

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.get("", response_model=SuccessEnvelope[DocumentListResponse])
async def list_documents(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db),
):
    repo = DocumentRepository(db)
    skip = (page - 1) * limit
    items, total = repo.list(skip=skip, limit=limit, status=status_filter, search=search)
    total_pages = max(1, (total + limit - 1) // limit)

    response_items = []
    for doc in items:
        topics_data = [TopicSchema(**t) for t in doc.get_topics()] if doc.get_topics() else None
        response_items.append(
            DocumentResponse(
                id=doc.id,
                filename=doc.filename,
                title=doc.title,
                file_size=doc.file_size,
                mime_type=doc.mime_type,
                status=doc.status,
                total_pages=doc.page_count,
                total_chunks=len(doc.chunks) if doc.chunks else 0,
                word_count=doc.word_count,
                topic_count=len(topics_data) if topics_data else 0,
                summary=doc.summary,
                topics=topics_data,
                created_at=doc.created_at,
                updated_at=doc.updated_at,
            )
        )

    list_payload = DocumentListResponse(
        items=response_items,
        pagination=PaginationSchema(
            total_items=total,
            total_pages=total_pages,
            current_page=page,
            page_size=limit,
        ),
    )
    return SuccessEnvelope(data=list_payload)


@router.post("/upload", response_model=SuccessEnvelope[DocumentResponse])
async def upload_document(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    # Read file content
    contents = await file.read()
    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    file_hash = hashlib.sha256(contents).hexdigest()
    doc_repo = DocumentRepository(db)
    chunk_repo = ChunkRepository(db)

    # Check duplicate
    existing = doc_repo.get_by_hash(file_hash)
    if existing:
        topics_data = [TopicSchema(**t) for t in existing.get_topics()] if existing.get_topics() else None
        return SuccessEnvelope(
            data=DocumentResponse(
                id=existing.id,
                filename=existing.filename,
                title=existing.title,
                file_size=existing.file_size,
                mime_type=existing.mime_type,
                status=existing.status,
                total_pages=existing.page_count,
                total_chunks=len(existing.chunks) if existing.chunks else 0,
                word_count=existing.word_count,
                topic_count=len(topics_data) if topics_data else 0,
                summary=existing.summary,
                topics=topics_data,
                created_at=existing.created_at,
                updated_at=existing.updated_at,
            )
        )

    doc_id = f"doc_{uuid.uuid4().hex[:8]}"
    save_path = settings.uploads_dir / f"{doc_id}_{file.filename}"
    with open(save_path, "wb") as f:
        f.write(contents)

    # Parse document
    parsed = DocumentParser.parse_file(contents, original_filename=file.filename)

    # Create document record
    doc = doc_repo.create(
        filename=file.filename,
        file_path=str(save_path),
        mime_type=file.content_type or "application/pdf",
        file_size=len(contents),
        page_count=parsed.total_pages,
        word_count=parsed.word_count,
        title=title or file.filename.rsplit(".", 1)[0].replace("_", " "),
        file_hash=file_hash,
        status="PROCESSING",
        doc_id=doc_id,
    )

    # Chunk and embed
    chunker = SemanticChunker(target_chunk_tokens=500, max_chunk_tokens=800, overlap_tokens=100)
    semantic_chunks = chunker.chunk_document(parsed, document_id=doc_id)

    vector_store = get_vector_store()
    embedder = get_embedding_provider()

    chunk_dicts = [c.to_dict() for c in semantic_chunks]
    embeddings = embedder.embed_batch([c["content"] for c in chunk_dicts])
    vector_store.add_chunks(doc_id, chunk_dicts, embeddings)

    # Persist chunks in relational DB
    db_chunks = []
    for c in chunk_dicts:
        db_chunks.append({
            "id": c["id"],
            "document_id": doc_id,
            "chunk_index": c["chunk_index"],
            "page_number": c.get("page_number", 1),
            "slide_number": c.get("slide_number"),
            "section_title": c.get("section_title"),
            "content": c["content"],
            "token_count": c.get("token_count", 0),
            "metadata": c.get("metadata", {}),
        })
    chunk_repo.bulk_create(db_chunks)

    # Run quick document analysis for topics and summary
    analyzer = get_document_analyzer()
    analysis = await analyzer.analyze_document(
        document_id=doc_id,
        title=doc.title,
        raw_text=parsed.raw_text,
    )

    doc_repo.update_metadata(
        document_id=doc_id,
        summary=analysis.get("executive_summary", ""),
        topics=analysis.get("topics", []),
        status="READY",
    )

    refreshed = doc_repo.get_by_id(doc_id)
    topics_data = [TopicSchema(**t) for t in refreshed.get_topics()] if refreshed.get_topics() else None

    return SuccessEnvelope(
        data=DocumentResponse(
            id=refreshed.id,
            filename=refreshed.filename,
            title=refreshed.title,
            file_size=refreshed.file_size,
            mime_type=refreshed.mime_type,
            status=refreshed.status,
            total_pages=refreshed.page_count,
            total_chunks=len(chunk_dicts),
            word_count=refreshed.word_count,
            topic_count=len(topics_data) if topics_data else 0,
            summary=refreshed.summary,
            topics=topics_data,
            created_at=refreshed.created_at,
            updated_at=refreshed.updated_at,
        )
    )


@router.get("/{document_id}", response_model=SuccessEnvelope[DocumentResponse])
async def get_document(
    document_id: str,
    db: Session = Depends(get_db),
):
    repo = DocumentRepository(db)
    doc = repo.get_by_id(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document '{document_id}' not found.")

    topics_data = [TopicSchema(**t) for t in doc.get_topics()] if doc.get_topics() else None
    return SuccessEnvelope(
        data=DocumentResponse(
            id=doc.id,
            filename=doc.filename,
            title=doc.title,
            file_size=doc.file_size,
            mime_type=doc.mime_type,
            status=doc.status,
            total_pages=doc.page_count,
            total_chunks=len(doc.chunks) if doc.chunks else 0,
            word_count=doc.word_count,
            topic_count=len(topics_data) if topics_data else 0,
            summary=doc.summary,
            topics=topics_data,
            created_at=doc.created_at,
            updated_at=doc.updated_at,
        )
    )


@router.post("/{document_id}/analyze", response_model=SuccessEnvelope[DocumentAnalysisResponse])
async def analyze_document(
    document_id: str,
    req: DocumentAnalysisRequest,
    db: Session = Depends(get_db),
):
    repo = DocumentRepository(db)
    doc = repo.get_by_id(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document '{document_id}' not found.")

    analyzer = get_document_analyzer()
    analysis = await analyzer.analyze_document(document_id=document_id, title=doc.title)

    repo.update_metadata(
        document_id=document_id,
        summary=analysis.get("executive_summary", doc.summary),
        topics=analysis.get("topics", doc.get_topics()),
        status="READY",
    )

    topics_data = [TopicSchema(**t) for t in analysis.get("topics", [])]
    return SuccessEnvelope(
        data=DocumentAnalysisResponse(
            document_id=document_id,
            status="ANALYZED",
            executive_summary=analysis.get("executive_summary"),
            topics_extracted=len(topics_data),
            key_formulas_extracted=len(analysis.get("key_formulas", [])),
            prerequisites_mapped=sum(len(t.prerequisites) for t in topics_data),
            topics=topics_data,
        )
    )


@router.delete("/{document_id}", response_model=SuccessEnvelope[dict])
async def delete_document(
    document_id: str,
    db: Session = Depends(get_db),
):
    repo = DocumentRepository(db)
    doc = repo.get_by_id(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document '{document_id}' not found.")

    # Remove file on disk if exists
    if doc.file_path and os.path.exists(doc.file_path):
        try:
            os.remove(doc.file_path)
        except Exception:
            pass

    # Remove vector index
    vector_store = get_vector_store()
    vector_store.delete_document(document_id)

    # Delete relational record
    repo.delete(document_id)
    return SuccessEnvelope(data={"deleted": True, "document_id": document_id})
