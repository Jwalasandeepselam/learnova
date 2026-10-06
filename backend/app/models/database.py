"""SQLAlchemy database models and repository pattern for Learnova.

Supports SQLite (local development) and PostgreSQL (production).
Includes thread-safe session management, table initialization, and clean repository abstractions.
"""

from datetime import datetime, timezone
import json
from typing import Any, Dict, Generator, List, Optional
import uuid

from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    create_engine,
    event,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker, Session

from app.config import settings

# Engine setup
DATABASE_URL = settings.DATABASE_URL
is_sqlite = DATABASE_URL.startswith("sqlite")

connect_args = {"check_same_thread": False} if is_sqlite else {}
engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=False,
    pool_pre_ping=True,
)

# Enable foreign keys and WAL mode for SQLite
if is_sqlite:
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ==============================================================================
# SQLAlchemy Models
# ==============================================================================

def utc_now() -> datetime:
    """Return timezone-aware current UTC datetime."""
    return datetime.now(timezone.utc)


class DocumentModel(Base):
    """Source document record representing uploaded learning materials."""

    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=lambda: f"doc_{uuid.uuid4().hex[:8]}")
    filename = Column(String(512), nullable=False)
    title = Column(String(512), nullable=True)
    file_path = Column(String(1024), nullable=False, default="")
    file_hash = Column(String(64), nullable=True, index=True)
    file_type = Column(String(128), nullable=False, default="application/pdf")
    mime_type = Column(String(128), nullable=False, default="application/pdf")
    file_size = Column(BigInteger, nullable=False, default=0)
    page_count = Column(Integer, nullable=False, default=0)
    word_count = Column(Integer, nullable=False, default=0)
    status = Column(String(32), nullable=False, default="PROCESSING", index=True)
    summary = Column(Text, nullable=True)
    topics_json = Column(Text, nullable=False, default="[]")
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    # Relationships
    chunks = relationship("DocumentChunkModel", back_populates="document", cascade="all, delete-orphan")
    sessions = relationship("LearningSessionModel", back_populates="document", cascade="all, delete-orphan")
    quiz_attempts = relationship("QuizAttemptModel", back_populates="document", cascade="all, delete-orphan")
    study_packs = relationship("StudyPackModel", back_populates="document", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_documents_status", "status"),
        Index("idx_documents_created_at", "created_at"),
    )

    @property
    def total_pages(self) -> int:
        return self.page_count

    @property
    def upload_date(self) -> datetime:
        return self.created_at

    def get_topics(self) -> List[Dict[str, Any]]:
        """Return parsed list of topics."""
        try:
            return json.loads(self.topics_json) if self.topics_json else []
        except Exception:
            return []

    def set_topics(self, topics: List[Dict[str, Any]]) -> None:
        """Serialize topics list to JSON string."""
        self.topics_json = json.dumps(topics)


class DocumentChunkModel(Base):
    """Segmented source text chunk with spatial/slide coordinates."""

    __tablename__ = "document_chunks"

    id = Column(String(64), primary_key=True, default=lambda: f"chk_{uuid.uuid4().hex[:12]}")
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    page_number = Column(Integer, nullable=False, default=1)
    slide_number = Column(Integer, nullable=True)
    section_title = Column(String(512), nullable=True)
    content = Column(Text, nullable=False)
    token_count = Column(Integer, nullable=False, default=0)
    embedding_json = Column(Text, nullable=True)
    metadata_json = Column(Text, nullable=False, default="{}")
    created_at = Column(DateTime(timezone=True), default=utc_now)

    # Relationships
    document = relationship("DocumentModel", back_populates="chunks")

    __table_args__ = (
        Index("idx_chunks_doc_idx", "document_id", "chunk_index"),
        Index("idx_chunks_doc_page", "document_id", "page_number"),
    )

    def get_metadata(self) -> Dict[str, Any]:
        """Return parsed chunk metadata dictionary."""
        try:
            return json.loads(self.metadata_json) if self.metadata_json else {}
        except Exception:
            return {}

    def set_metadata(self, metadata: Dict[str, Any]) -> None:
        """Serialize metadata dict to JSON string."""
        self.metadata_json = json.dumps(metadata)


class LearningSessionModel(Base):
    """Socratic tutoring dialogue state and message history."""

    __tablename__ = "learning_sessions"

    id = Column(String(36), primary_key=True, default=lambda: f"sess_{uuid.uuid4().hex[:8]}")
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(String(36), nullable=False, default="usr_default", index=True)
    topic_id = Column(String(64), nullable=True)
    current_topic = Column(String(255), nullable=True)
    session_mode = Column(String(32), nullable=False, default="SOCRATIC")
    current_step = Column(Integer, nullable=False, default=1)
    messages_json = Column(Text, nullable=False, default="[]")
    status = Column(String(32), nullable=False, default="ACTIVE")
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    # Relationships
    document = relationship("DocumentModel", back_populates="sessions")

    def get_messages(self) -> List[Dict[str, Any]]:
        """Return deserialized dialogue messages."""
        try:
            return json.loads(self.messages_json) if self.messages_json else []
        except Exception:
            return []

    def set_messages(self, messages: List[Dict[str, Any]]) -> None:
        """Serialize dialogue messages to JSON string."""
        self.messages_json = json.dumps(messages)


class QuizAttemptModel(Base):
    """Formative assessment attempt and score analytics."""

    __tablename__ = "quiz_attempts"

    id = Column(String(36), primary_key=True, default=lambda: f"att_{uuid.uuid4().hex[:8]}")
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(String(36), nullable=False, default="usr_default", index=True)
    topic_id = Column(String(64), nullable=True)
    score = Column(Float, nullable=False, default=0.0)
    score_percentage = Column(Float, nullable=False, default=0.0)
    total_questions = Column(Integer, nullable=False, default=0)
    correct_answers = Column(Integer, nullable=False, default=0)
    answers_json = Column(Text, nullable=False, default="[]")
    misconceptions_json = Column(Text, nullable=False, default="[]")
    time_spent_seconds = Column(Integer, nullable=False, default=0)
    completed_at = Column(DateTime(timezone=True), default=utc_now)

    # Relationships
    document = relationship("DocumentModel", back_populates="quiz_attempts")

    def get_answers(self) -> List[Dict[str, Any]]:
        """Return parsed submissions."""
        try:
            return json.loads(self.answers_json) if self.answers_json else []
        except Exception:
            return []

    def set_answers(self, answers: List[Dict[str, Any]]) -> None:
        """Serialize submissions to JSON string."""
        self.answers_json = json.dumps(answers)

    def get_misconceptions(self) -> List[Dict[str, Any]]:
        """Return parsed misconceptions."""
        try:
            return json.loads(self.misconceptions_json) if self.misconceptions_json else []
        except Exception:
            return []

    def set_misconceptions(self, misconceptions: List[Dict[str, Any]]) -> None:
        """Serialize misconceptions to JSON string."""
        self.misconceptions_json = json.dumps(misconceptions)


class StudentMasteryModel(Base):
    """Bayesian Knowledge Tracing and SM-2 spaced repetition state."""

    __tablename__ = "student_mastery"

    id = Column(String(36), primary_key=True, default=lambda: f"mst_{uuid.uuid4().hex[:8]}")
    student_id = Column(String(36), nullable=False, default="usr_default", index=True)
    topic_name = Column(String(255), nullable=False, index=True)
    topic_id = Column(String(64), nullable=True)
    document_id = Column(String(36), nullable=True, index=True)
    mastery_score = Column(Float, nullable=False, default=0.1)
    confidence = Column(String(32), nullable=False, default="LOW")
    attempts = Column(Integer, nullable=False, default=0)
    weak_concepts_json = Column(Text, nullable=False, default="[]")
    retention_strength = Column(Float, nullable=False, default=1.0)
    spaced_repetition_interval_days = Column(Integer, nullable=False, default=1)
    last_reviewed = Column(DateTime(timezone=True), default=utc_now)
    next_review_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    __table_args__ = (
        Index("idx_student_topic_name", "student_id", "topic_name"),
    )

    def get_weak_concepts(self) -> List[str]:
        """Return parsed weak concepts list."""
        try:
            return json.loads(self.weak_concepts_json) if self.weak_concepts_json else []
        except Exception:
            return []

    def set_weak_concepts(self, concepts: List[str]) -> None:
        """Serialize weak concepts list to JSON string."""
        self.weak_concepts_json = json.dumps(concepts)


class StudyPackModel(Base):
    """Generated study pack artifact with link to compiled PDF."""

    __tablename__ = "study_packs"

    id = Column(String(36), primary_key=True, default=lambda: f"pack_{uuid.uuid4().hex[:8]}")
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(512), nullable=False)
    pack_type = Column(String(64), nullable=False, default="comprehensive")
    content_json = Column(Text, nullable=False, default="{}")
    pdf_path = Column(String(1024), nullable=True)
    pdf_size_bytes = Column(BigInteger, nullable=False, default=0)
    status = Column(String(32), nullable=False, default="GENERATING", index=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    # Relationships
    document = relationship("DocumentModel", back_populates="study_packs")

    def get_content(self) -> Dict[str, Any]:
        """Return parsed study pack content dictionary."""
        try:
            return json.loads(self.content_json) if self.content_json else {}
        except Exception:
            return {}

    def set_content(self, content: Dict[str, Any]) -> None:
        """Serialize content dict to JSON string."""
        self.content_json = json.dumps(content)


# ==============================================================================
# Database Initialization & Session Dependency
# ==============================================================================

def init_db() -> None:
    """Create all tables in the database if they do not exist."""
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI database session dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ==============================================================================
# Repository Pattern Implementations
# ==============================================================================

class DocumentRepository:
    """Repository handling CRUD operations on DocumentModel."""

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        filename: str,
        file_path: str,
        mime_type: str = "application/pdf",
        file_size: int = 0,
        page_count: int = 0,
        word_count: int = 0,
        title: Optional[str] = None,
        file_hash: Optional[str] = None,
        status: str = "PROCESSING",
        doc_id: Optional[str] = None,
    ) -> DocumentModel:
        doc = DocumentModel(
            id=doc_id or f"doc_{uuid.uuid4().hex[:8]}",
            filename=filename,
            title=title or filename,
            file_path=file_path,
            mime_type=mime_type,
            file_type=mime_type,
            file_size=file_size,
            page_count=page_count,
            word_count=word_count,
            file_hash=file_hash,
            status=status,
        )
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)
        return doc

    def get_by_id(self, document_id: str) -> Optional[DocumentModel]:
        return self.db.query(DocumentModel).filter(DocumentModel.id == document_id).first()

    def get_by_hash(self, file_hash: str) -> Optional[DocumentModel]:
        return self.db.query(DocumentModel).filter(DocumentModel.file_hash == file_hash).first()

    def list(
        self,
        skip: int = 0,
        limit: int = 20,
        status: Optional[str] = None,
        search: Optional[str] = None,
    ) -> tuple[List[DocumentModel], int]:
        query = self.db.query(DocumentModel)
        if status:
            query = query.filter(DocumentModel.status == status)
        if search:
            query = query.filter(
                (DocumentModel.filename.ilike(f"%{search}%"))
                | (DocumentModel.title.ilike(f"%{search}%"))
            )
        total = query.count()
        items = query.order_by(DocumentModel.created_at.desc()).offset(skip).limit(limit).all()
        return items, total

    def update_status(self, document_id: str, status: str, summary: Optional[str] = None) -> Optional[DocumentModel]:
        doc = self.get_by_id(document_id)
        if doc:
            doc.status = status
            if summary is not None:
                doc.summary = summary
            doc.updated_at = utc_now()
            self.db.commit()
            self.db.refresh(doc)
        return doc

    def update_metadata(
        self,
        document_id: str,
        page_count: Optional[int] = None,
        word_count: Optional[int] = None,
        summary: Optional[str] = None,
        topics: Optional[List[Dict[str, Any]]] = None,
        status: Optional[str] = None,
    ) -> Optional[DocumentModel]:
        doc = self.get_by_id(document_id)
        if doc:
            if page_count is not None:
                doc.page_count = page_count
            if word_count is not None:
                doc.word_count = word_count
            if summary is not None:
                doc.summary = summary
            if topics is not None:
                doc.set_topics(topics)
            if status is not None:
                doc.status = status
            doc.updated_at = utc_now()
            self.db.commit()
            self.db.refresh(doc)
        return doc

    def delete(self, document_id: str) -> bool:
        doc = self.get_by_id(document_id)
        if doc:
            self.db.delete(doc)
            self.db.commit()
            return True
        return False


class ChunkRepository:
    """Repository handling CRUD operations on DocumentChunkModel."""

    def __init__(self, db: Session):
        self.db = db

    def bulk_create(self, chunks_data: List[Dict[str, Any]]) -> List[DocumentChunkModel]:
        chunk_models = []
        for c in chunks_data:
            chunk = DocumentChunkModel(
                id=c.get("id") or f"chk_{uuid.uuid4().hex[:12]}",
                document_id=c["document_id"],
                chunk_index=c["chunk_index"],
                page_number=c.get("page_number", 1),
                slide_number=c.get("slide_number"),
                section_title=c.get("section_title"),
                content=c["content"],
                token_count=c.get("token_count", 0),
                embedding_json=c.get("embedding_json"),
                metadata_json=json.dumps(c.get("metadata", {})),
            )
            chunk_models.append(chunk)
        self.db.add_all(chunk_models)
        self.db.commit()
        return chunk_models

    def get_by_document(self, document_id: str) -> List[DocumentChunkModel]:
        return (
            self.db.query(DocumentChunkModel)
            .filter(DocumentChunkModel.document_id == document_id)
            .order_by(DocumentChunkModel.chunk_index.asc())
            .all()
        )

    def count_by_document(self, document_id: str) -> int:
        return (
            self.db.query(DocumentChunkModel)
            .filter(DocumentChunkModel.document_id == document_id)
            .count()
        )

    def search_text(self, document_id: str, keyword: str, limit: int = 10) -> List[DocumentChunkModel]:
        return (
            self.db.query(DocumentChunkModel)
            .filter(
                DocumentChunkModel.document_id == document_id,
                DocumentChunkModel.content.ilike(f"%{keyword}%"),
            )
            .limit(limit)
            .all()
        )


class LearningSessionRepository:
    """Repository handling Socratic dialogues and sessions."""

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        document_id: str,
        student_id: str = "usr_default",
        topic_id: Optional[str] = None,
        current_topic: Optional[str] = None,
        session_mode: str = "SOCRATIC",
        session_id: Optional[str] = None,
    ) -> LearningSessionModel:
        sess = LearningSessionModel(
            id=session_id or f"sess_{uuid.uuid4().hex[:12]}",
            document_id=document_id,
            student_id=student_id,
            topic_id=topic_id,
            current_topic=current_topic,
            session_mode=session_mode,
        )
        self.db.add(sess)
        self.db.commit()
        self.db.refresh(sess)
        return sess

    def get_by_id(self, session_id: str) -> Optional[LearningSessionModel]:
        return (
            self.db.query(LearningSessionModel)
            .filter(LearningSessionModel.id == session_id)
            .first()
        )

    def append_message(
        self,
        session_id: str,
        role: str,
        content: str,
        citations: Optional[List[Dict[str, Any]]] = None,
    ) -> Optional[LearningSessionModel]:
        sess = self.get_by_id(session_id)
        if sess:
            msgs = sess.get_messages()
            msgs.append(
                {
                    "role": role,
                    "content": content,
                    "citations": citations or [],
                    "timestamp": utc_now().isoformat(),
                }
            )
            sess.set_messages(msgs)
            sess.updated_at = utc_now()
            self.db.commit()
            self.db.refresh(sess)
        return sess

    def advance_step(self, session_id: str) -> Optional[LearningSessionModel]:
        sess = self.get_by_id(session_id)
        if sess:
            sess.current_step += 1
            sess.updated_at = utc_now()
            self.db.commit()
            self.db.refresh(sess)
        return sess


class QuizAttemptRepository:
    """Repository handling formative quiz attempts and statistics."""

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        document_id: str,
        student_id: str,
        total_questions: int,
        correct_answers: int,
        score_percentage: float,
        answers: List[Dict[str, Any]],
        misconceptions: List[Dict[str, Any]],
        time_spent_seconds: int = 0,
        topic_id: Optional[str] = None,
    ) -> QuizAttemptModel:
        attempt = QuizAttemptModel(
            document_id=document_id,
            student_id=student_id,
            topic_id=topic_id,
            score=score_percentage / 100.0,
            score_percentage=score_percentage,
            total_questions=total_questions,
            correct_answers=correct_answers,
            time_spent_seconds=time_spent_seconds,
        )
        attempt.set_answers(answers)
        attempt.set_misconceptions(misconceptions)
        self.db.add(attempt)
        self.db.commit()
        self.db.refresh(attempt)
        return attempt

    def list_by_student(self, student_id: str, limit: int = 50) -> List[QuizAttemptModel]:
        return (
            self.db.query(QuizAttemptModel)
            .filter(QuizAttemptModel.student_id == student_id)
            .order_by(QuizAttemptModel.completed_at.desc())
            .limit(limit)
            .all()
        )


class StudentMasteryRepository:
    """Repository handling concept mastery and spaced repetition tracking."""

    def __init__(self, db: Session):
        self.db = db

    def get_topic_mastery(
        self, student_id: str, topic_name: str
    ) -> Optional[StudentMasteryModel]:
        return (
            self.db.query(StudentMasteryModel)
            .filter(
                StudentMasteryModel.student_id == student_id,
                StudentMasteryModel.topic_name == topic_name,
            )
            .first()
        )

    def upsert_mastery(
        self,
        student_id: str,
        topic_name: str,
        mastery_delta: float,
        topic_id: Optional[str] = None,
        document_id: Optional[str] = None,
        weak_concept: Optional[str] = None,
    ) -> StudentMasteryModel:
        record = self.get_topic_mastery(student_id, topic_name)
        now = utc_now()
        if not record:
            initial_score = max(0.0, min(1.0, 0.5 + mastery_delta))
            record = StudentMasteryModel(
                student_id=student_id,
                topic_name=topic_name,
                topic_id=topic_id,
                document_id=document_id,
                mastery_score=initial_score,
                confidence="HIGH" if initial_score >= 0.8 else ("MODERATE" if initial_score >= 0.5 else "LOW"),
                attempts=1,
                spaced_repetition_interval_days=3 if initial_score >= 0.8 else 1,
                last_reviewed=now,
                next_review_at=now,
            )
            if weak_concept:
                record.set_weak_concepts([weak_concept])
            self.db.add(record)
        else:
            record.attempts += 1
            new_score = max(0.0, min(1.0, record.mastery_score + mastery_delta))
            record.mastery_score = new_score
            record.last_reviewed = now

            # SuperMemo SM-2 interval heuristic
            if new_score >= 0.8:
                record.confidence = "HIGH"
                record.spaced_repetition_interval_days = min(30, record.spaced_repetition_interval_days * 2 + 1)
            elif new_score >= 0.5:
                record.confidence = "MODERATE"
                record.spaced_repetition_interval_days = max(1, record.spaced_repetition_interval_days)
            else:
                record.confidence = "LOW"
                record.spaced_repetition_interval_days = 1

            if weak_concept:
                weak = record.get_weak_concepts()
                if weak_concept not in weak:
                    weak.append(weak_concept)
                    record.set_weak_concepts(weak)

        self.db.commit()
        self.db.refresh(record)
        return record

    def list_by_student(
        self, student_id: str, document_id: Optional[str] = None
    ) -> List[StudentMasteryModel]:
        query = self.db.query(StudentMasteryModel).filter(
            StudentMasteryModel.student_id == student_id
        )
        if document_id:
            query = query.filter(StudentMasteryModel.document_id == document_id)
        return query.order_by(StudentMasteryModel.mastery_score.desc()).all()


class StudyPackRepository:
    """Repository handling StudyPackModel persistence."""

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        document_id: str,
        title: str,
        pack_type: str = "comprehensive",
        content: Optional[Dict[str, Any]] = None,
        status: str = "GENERATING",
    ) -> StudyPackModel:
        pack = StudyPackModel(
            document_id=document_id,
            title=title,
            pack_type=pack_type,
            status=status,
        )
        if content:
            pack.set_content(content)
        self.db.add(pack)
        self.db.commit()
        self.db.refresh(pack)
        return pack

    def get_by_id(self, pack_id: str) -> Optional[StudyPackModel]:
        return self.db.query(StudyPackModel).filter(StudyPackModel.id == pack_id).first()

    def update_pdf(
        self, pack_id: str, pdf_path: str, pdf_size_bytes: int, status: str = "READY"
    ) -> Optional[StudyPackModel]:
        pack = self.get_by_id(pack_id)
        if pack:
            pack.pdf_path = pdf_path
            pack.pdf_size_bytes = pdf_size_bytes
            pack.status = status
            self.db.commit()
            self.db.refresh(pack)
        return pack

    def list_by_document(self, document_id: str) -> List[StudyPackModel]:
        return (
            self.db.query(StudyPackModel)
            .filter(StudyPackModel.document_id == document_id)
            .order_by(StudyPackModel.created_at.desc())
            .all()
        )
