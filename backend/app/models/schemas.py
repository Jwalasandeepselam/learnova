"""Pydantic v2 schemas for Learnova REST API.

All request and response structures strictly adhere to API.md and OpenAPI 3.1 specifications.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Generic, List, Optional, TypeVar
import uuid

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


# ==============================================================================
# Meta & Envelope Schemas
# ==============================================================================

class MetaSchema(BaseModel):
    """Standard response metadata containing timestamp and request tracking ID."""

    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="ISO 8601 UTC timestamp of response generation",
    )
    request_id: str = Field(
        default_factory=lambda: f"req_{uuid.uuid4().hex[:8]}",
        description="Unique request trace identifier",
    )

    model_config = ConfigDict(from_attributes=True)


class ErrorDetail(BaseModel):
    """Normalized error detail body."""

    code: str = Field(..., description="Machine-readable error constant")
    message: str = Field(..., description="Human-readable explanation of error")
    details: Optional[Dict[str, Any]] = Field(
        default=None, description="Granular error debug context"
    )

    model_config = ConfigDict(from_attributes=True)


class ErrorResponse(BaseModel):
    """Standardized API error envelope."""

    success: bool = Field(default=False)
    error: ErrorDetail
    meta: MetaSchema = Field(default_factory=MetaSchema)

    model_config = ConfigDict(from_attributes=True)


class SuccessEnvelope(BaseModel, Generic[T]):
    """Standardized API success envelope wrapper."""

    success: bool = Field(default=True)
    data: T
    meta: MetaSchema = Field(default_factory=MetaSchema)

    model_config = ConfigDict(from_attributes=True)


class PaginationSchema(BaseModel):
    """Pagination tracking block."""

    total_items: int = Field(..., description="Total count of items matching query")
    total_pages: int = Field(..., description="Total available pages")
    current_page: int = Field(..., description="Active page number (1-indexed)")
    page_size: int = Field(..., description="Number of items returned per page")

    model_config = ConfigDict(from_attributes=True)


# ==============================================================================
# Document Management Schemas
# ==============================================================================

class TopicSchema(BaseModel):
    """Extracted conceptual topic within a source document."""

    id: str = Field(..., description="Topic unique identifier (top_...)")
    name: str = Field(..., description="Topic title or heading name")
    description: Optional[str] = Field(
        default=None, description="Conceptual synopsis of topic"
    )
    difficulty_level: str = Field(
        default="INTERMEDIATE",
        description="Pedagogical difficulty: BEGINNER | INTERMEDIATE | ADVANCED",
    )
    chunk_count: int = Field(
        default=0, description="Number of indexed chunks covering this topic"
    )
    mastery_score: Optional[float] = Field(
        default=None, ge=0.0, le=1.0, description="Active student mastery score"
    )
    prerequisites: List[str] = Field(
        default_factory=list, description="IDs or names of prerequisite topics"
    )
    key_terms: List[str] = Field(
        default_factory=list, description="Extracted vocabulary and formulas"
    )

    model_config = ConfigDict(from_attributes=True)


class DocumentChunkSchema(BaseModel):
    """Segmented source text chunk with location coordinates."""

    id: str = Field(..., description="Chunk identifier (chk_...)")
    document_id: str = Field(..., description="Associated document ID")
    chunk_index: int = Field(..., description="0-indexed position within document")
    page_number: int = Field(..., description="1-indexed source document page")
    slide_number: Optional[int] = Field(
        default=None, description="Presentation slide number if PPTX"
    )
    section_title: Optional[str] = Field(
        default=None, description="Section heading context"
    )
    content: str = Field(..., description="Text content within chunk")
    token_count: int = Field(default=0, description="Token length of chunk")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Arbitrary chunk metadata"
    )

    model_config = ConfigDict(from_attributes=True)


class DocumentCreate(BaseModel):
    """Optional payload when uploading or initializing a document."""

    title: Optional[str] = Field(
        default=None, description="Optional human-readable document title"
    )


class DocumentResponse(BaseModel):
    """Document metadata, status, and summary payload."""

    id: str = Field(..., description="Document identifier (doc_...)")
    filename: str = Field(..., description="Original uploaded filename")
    title: Optional[str] = Field(
        default=None, description="Display title of document"
    )
    file_size: int = Field(..., description="Size in bytes")
    mime_type: str = Field(..., description="MIME type e.g. application/pdf")
    status: str = Field(
        default="PROCESSING",
        description="Ingestion status: PROCESSING | READY | FAILED",
    )
    total_pages: int = Field(default=0, description="Total pages or slides in file")
    total_chunks: int = Field(default=0, description="Number of generated chunks")
    word_count: int = Field(default=0, description="Total word count")
    topic_count: int = Field(default=0, description="Total identified topics")
    summary: Optional[str] = Field(
        default=None, description="Executive conceptual summary"
    )
    topics: Optional[List[TopicSchema]] = Field(
        default=None, description="Parsed topics if available"
    )
    created_at: datetime = Field(..., description="Upload timestamp")
    updated_at: Optional[datetime] = Field(
        default=None, description="Last update timestamp"
    )

    model_config = ConfigDict(from_attributes=True)


class DocumentListResponse(BaseModel):
    """Paginated list of documents."""

    items: List[DocumentResponse]
    pagination: PaginationSchema

    model_config = ConfigDict(from_attributes=True)


class DocumentAnalysisRequest(BaseModel):
    """Request payload to trigger deep concept and formula analysis."""

    force_recompute: bool = Field(default=False)
    extract_formulas: bool = Field(default=True)
    extract_flashcards: bool = Field(default=True)


class DocumentAnalysisResponse(BaseModel):
    """Result of deep concept extraction and document outline analysis."""

    document_id: str
    status: str = Field(default="ANALYZED")
    executive_summary: Optional[str] = None
    topics_extracted: int = 0
    key_formulas_extracted: int = 0
    prerequisites_mapped: int = 0
    topics: Optional[List[TopicSchema]] = None

    model_config = ConfigDict(from_attributes=True)


# ==============================================================================
# RAG Chat & Grounded Q&A Schemas
# ==============================================================================

class CitationSchema(BaseModel):
    """Verifiable source citation mapped to exact page and chunk."""

    citation_id: Optional[str] = Field(default=None)
    document_id: str
    page_number: int
    chunk_id: Optional[str] = None
    snippet: str
    relevance_score: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class ChatRequest(BaseModel):
    """Grounded RAG query request."""

    document_id: str = Field(..., description="Target document ID")
    query: Optional[str] = Field(default=None, description="Student question or prompt")
    message: Optional[str] = Field(default=None, description="Alternative key for student question")
    conversation_id: Optional[str] = Field(
        default=None, description="Optional conversation trace ID"
    )
    session_id: Optional[str] = Field(default=None, description="Alternative session ID")
    stream: bool = Field(default=False, description="Enable SSE token streaming")
    top_k: int = Field(default=4, ge=1, le=20, description="Number of chunks to retrieve")

    def get_query_text(self) -> str:
        return self.query or self.message or ""


class ChatResponse(BaseModel):
    """Synthesized grounded answer with verified citations."""

    conversation_id: str = "conv_default"
    session_id: Optional[str] = None
    message_id: str = "msg_default"
    response: str = ""
    answer: Optional[str] = None
    citations: List[CitationSchema] = Field(default_factory=list)
    grounded: bool = Field(default=True)
    is_grounded: Optional[bool] = None
    confidence: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class MessageSchema(BaseModel):
    """Single message in dialogue history."""

    role: str = Field(..., description="user | assistant | system")
    content: str
    citations: Optional[List[CitationSchema]] = None
    timestamp: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    model_config = ConfigDict(from_attributes=True)


# ==============================================================================
# Pedagogical Socratic Tutor Schemas
# ==============================================================================

class DiagnosticQuestionSchema(BaseModel):
    """Inquiry prompt formulated to test student mental model."""

    question_id: str
    question_type: str = Field(
        default="open_ended", description="open_ended | mcq | numeric"
    )
    prompt: str
    hints: List[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class TeachRequest(BaseModel):
    """Request to initiate or advance Socratic tutoring session."""

    document_id: str
    topic_id: Optional[str] = None
    topic: Optional[str] = None
    session_id: Optional[str] = None
    pedagogical_mode: Optional[str] = Field(
        default="socratic",
        description="socratic | first_principles | analogy | feynman",
    )
    student_level: Optional[str] = None
    preferred_difficulty: Optional[str] = Field(
        default="intermediate", description="beginner | intermediate | advanced"
    )

    def get_topic_name(self) -> str:
        return self.topic or self.topic_id or "Core Principles"


class TeachResponse(BaseModel):
    """Scaffolded instruction step with diagnostic inquiry."""

    session_id: str
    step_index: int = 1
    topic_name: str
    topic: Optional[str] = None
    pedagogical_mode: str = "socratic"
    scaffold_explanation: str
    intuition: Optional[str] = None
    technical_concept: Optional[str] = None
    analogy: Optional[str] = None
    real_world_example: Optional[str] = None
    diagnostic_question: Optional[DiagnosticQuestionSchema] = None
    citations: List[CitationSchema] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)

    def model_post_init(self, __context: Any) -> None:
        if self.topic is None:
            self.topic = self.topic_name
        if self.intuition is None:
            self.intuition = self.scaffold_explanation
        if self.technical_concept is None:
            self.technical_concept = self.scaffold_explanation


class ExplainAgainRequest(BaseModel):
    """Request for alternative explanation modality when student is stuck."""

    session_id: Optional[str] = None
    document_id: Optional[str] = None
    target_concept: Optional[str] = None
    topic: Optional[str] = None
    desired_modality: Optional[str] = Field(
        default="analogy",
        description="analogy | first_principles | step_by_step | intuitive",
    )
    strategy: Optional[str] = None
    current_obstacle: Optional[str] = None
    student_obstacle: Optional[str] = None

    def get_concept(self) -> str:
        return self.target_concept or self.topic or "Core Concept"

    def get_modality(self) -> str:
        return self.desired_modality or self.strategy or "analogy"


class FollowUpCheckSchema(BaseModel):
    """Quick comprehension probe."""

    prompt: str

    model_config = ConfigDict(from_attributes=True)


class ExplainAgainResponse(BaseModel):
    """Re-framed explanation with fresh metaphor or step-by-step logic."""

    session_id: str
    modality_used: str
    revised_explanation: str
    topic: Optional[str] = None
    key_takeaways: Optional[List[str]] = Field(default_factory=list)
    follow_up_check: Optional[FollowUpCheckSchema] = None
    check_question: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class MisconceptionSchema(BaseModel):
    """Diagnosed flaw in student understanding."""

    detected: bool = False
    category: Optional[str] = Field(
        default=None, description="CONCEPTUAL | PROCEDURAL | FACTUAL | TERMINOLOGICAL"
    )
    summary: Optional[str] = None
    explanation: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class EvaluateAnswerRequest(BaseModel):
    """Student response submitted for diagnostic evaluation."""

    session_id: Optional[str] = None
    document_id: Optional[str] = None
    topic: Optional[str] = None
    question: Optional[str] = None
    question_id: Optional[str] = None
    student_answer: str = Field(..., min_length=1)
    student_id: Optional[str] = None


class EvaluateAnswerResponse(BaseModel):
    """Pedagogical evaluation with misconception analysis and hint."""

    is_correct: bool
    score: Optional[float] = 0.85
    understanding_level: str = Field(
        default="PROFICIENT", description="COMPLETE | PARTIAL | INSUFFICIENT"
    )
    misconception: Optional[MisconceptionSchema] = None
    scaffolded_hint: Optional[str] = None
    hints: List[str] = Field(default_factory=list)
    mastery_delta: float = 0.10
    next_action: str = Field(
        default="ADVANCE_CONCEPT", description="PROCEED | PROVIDE_HINT | EXPLAIN_AGAIN"
    )

    model_config = ConfigDict(from_attributes=True)


# ==============================================================================
# Quiz & Formative Assessment Schemas
# ==============================================================================

class QuizOptionSchema(BaseModel):
    """Multiple choice question option."""

    key: str = Field(..., description="Option letter: A, B, C, D")
    text: str = Field(..., description="Option label content")

    model_config = ConfigDict(from_attributes=True)


class QuestionSchema(BaseModel):
    """Individual assessment item."""

    id: str
    type: str = Field(default="mcq", description="mcq | short_answer | problem_solving")
    topic_id: Optional[str] = None
    topic_name: Optional[str] = None
    prompt: str
    options: Optional[List[QuizOptionSchema]] = None
    correct_option: Optional[str] = None
    correct_answer: Optional[str] = None
    explanation: Optional[str] = None
    key_criteria: Optional[List[str]] = None

    model_config = ConfigDict(from_attributes=True)


class QuizGenerateRequest(BaseModel):
    """Request parameters for generating an assessment."""

    document_id: str
    topic: Optional[str] = None
    topic_id: Optional[str] = None
    topic_ids: Optional[List[str]] = None
    question_count: Optional[int] = Field(default=5, ge=1, le=25)
    num_questions: Optional[int] = None
    question_types: List[str] = Field(
        default_factory=lambda: ["mcq", "short_answer"]
    )
    difficulty: str = Field(
        default="medium", description="beginner | intermediate | advanced | adaptive"
    )

    def get_count(self) -> int:
        return self.num_questions or self.question_count or 5


class QuizResponse(BaseModel):
    """Generated quiz with questions."""

    quiz_id: Optional[str] = None
    id: Optional[str] = None
    document_id: str
    total_questions: Optional[int] = None
    title: Optional[str] = None
    topic: Optional[str] = None
    difficulty: Optional[str] = "medium"
    questions: List[QuestionSchema] = Field(default_factory=list)
    time_limit_minutes: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)

    def model_post_init(self, __context: Any) -> None:
        if self.id is None and self.quiz_id is not None:
            self.id = self.quiz_id
        elif self.quiz_id is None and self.id is not None:
            self.quiz_id = self.id
        if self.total_questions is None:
            self.total_questions = len(self.questions)


class QuestionEvaluationRequest(BaseModel):
    """Single question evaluation during active quiz."""

    quiz_id: Optional[str] = None
    question_id: Optional[str] = None
    question_prompt: Optional[str] = None
    student_answer: Optional[str] = None
    submitted_answer: Optional[str] = None
    correct_answer: Optional[str] = None
    topic: Optional[str] = None

    def get_answer(self) -> str:
        return self.student_answer or self.submitted_answer or ""


class QuestionEvaluationResponse(BaseModel):
    """Instant feedback on a single question."""

    question_id: Optional[str] = None
    is_correct: bool
    score: Optional[float] = 0.8
    correct_answer: Optional[str] = None
    feedback: Optional[str] = None
    explanation: Optional[str] = None
    misconception: Optional[MisconceptionSchema] = None
    hints: Optional[List[str]] = Field(default_factory=list)
    citation: Optional[CitationSchema] = None

    model_config = ConfigDict(from_attributes=True)


class QuizQuestionSubmission(BaseModel):
    """Submission for a single quiz item."""

    question_id: str
    submitted_answer: Optional[str] = None
    student_answer: Optional[str] = None
    correct_answer: Optional[str] = None
    question_prompt: Optional[str] = None
    topic_name: Optional[str] = None

    def get_answer(self) -> str:
        return self.submitted_answer or self.student_answer or ""


class QuizSubmitRequest(BaseModel):
    """Completed quiz submissions payload."""

    quiz_id: str
    document_id: Optional[str] = None
    student_id: Optional[str] = None
    time_spent_seconds: int = 0
    submissions: Optional[List[QuizQuestionSubmission]] = None
    answers: Optional[List[QuizQuestionSubmission]] = None

    def get_submissions(self) -> List[QuizQuestionSubmission]:
        return self.submissions or self.answers or []


class TopicBreakdownSchema(BaseModel):
    """Per-topic scoring and mastery change resulting from quiz."""

    topic_id: Optional[str] = None
    topic_name: str
    score: float = Field(..., ge=0.0, le=1.0)
    new_mastery_level: float = Field(..., ge=0.0, le=1.0)

    model_config = ConfigDict(from_attributes=True)


class QuizSubmitResponse(BaseModel):
    """Composite quiz evaluation and spaced repetition scheduling update."""

    attempt_id: str
    quiz_id: str
    score_percentage: float = Field(..., ge=0.0, le=100.0)
    total_questions: int
    correct_count: int
    time_spent_seconds: int
    passed: Optional[bool] = None
    topic_breakdown: List[TopicBreakdownSchema] = Field(default_factory=list)
    identified_misconceptions: List[str] = Field(default_factory=list)
    recommended_review_date: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

    def model_post_init(self, __context: Any) -> None:
        if self.passed is None:
            self.passed = self.score_percentage >= 70.0


# ==============================================================================
# Study Pack Schemas
# ==============================================================================

class FormulaItemSchema(BaseModel):
    """Key equation or law entry."""

    name: str
    formula: str
    variables: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class FlashcardItemSchema(BaseModel):
    """Front/back recall card."""

    id: str
    front: str
    back: str

    model_config = ConfigDict(from_attributes=True)


class PracticeProblemSchema(BaseModel):
    """Practice exercise with model solution."""

    question: str
    answer: str
    explanation: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class StudyPackSectionSchema(BaseModel):
    """Generic section container for study pack contents."""

    section_id: str
    title: str
    content: str
    type: str = Field(default="text", description="text | table | flashcards | problems")
    items: Optional[List[Dict[str, Any]]] = None

    model_config = ConfigDict(from_attributes=True)


class StudyPackGenerateRequest(BaseModel):
    """Study pack compilation request."""

    document_id: str
    title: Optional[str] = None
    pack_type: str = Field(
        default="comprehensive",
        description="comprehensive | formula_sheet | flashcards | practice_exam",
    )
    include_flashcards: bool = True
    include_cheat_sheet: bool = True
    include_practice_exam: bool = True


class StudyPackResponse(BaseModel):
    """Compiled study pack artifact representation."""

    id: str
    document_id: str
    title: str
    status: str = Field(
        default="GENERATING", description="GENERATING | READY | FAILED"
    )
    summary: Optional[str] = None
    formula_sheet: Optional[List[FormulaItemSchema]] = None
    flashcards: Optional[List[FlashcardItemSchema]] = None
    practice_problems: Optional[List[PracticeProblemSchema]] = None
    sections: Optional[List[StudyPackSectionSchema]] = None
    pdf_available: bool = False
    pdf_url: Optional[str] = None
    pdf_size_bytes: Optional[int] = 0
    created_at: Optional[datetime] = None
    generated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ==============================================================================
# Student Progress & Mastery Schemas
# ==============================================================================

class MasteryDistributionSchema(BaseModel):
    """Counts of concepts by mastery tier."""

    novice: int = 0
    learning: int = 0
    proficient: int = 0
    mastered: int = 0

    model_config = ConfigDict(from_attributes=True)


class StudentProgressResponse(BaseModel):
    """Cumulative learning metrics for student dashboard."""

    student_id: str
    total_documents_studied: int = 0
    total_learning_time_minutes: int = 0
    current_streak_days: int = 0
    total_quizzes_completed: int = 0
    total_topics_tracked: int = 10
    average_quiz_score: float = 0.0
    mastery_distribution: MasteryDistributionSchema = Field(
        default_factory=MasteryDistributionSchema
    )
    upcoming_reviews_count: int = 0

    model_config = ConfigDict(from_attributes=True)

    def model_post_init(self, __context: Any) -> None:
        if self.mastery_distribution and self.total_topics_tracked == 10:
            dist_sum = (
                self.mastery_distribution.novice
                + self.mastery_distribution.learning
                + self.mastery_distribution.proficient
                + self.mastery_distribution.mastered
            )
            if dist_sum > 0:
                self.total_topics_tracked = dist_sum


class TopicMasterySchema(BaseModel):
    """Granular concept mastery and spaced repetition tracking."""

    topic_id: str
    topic_name: str
    document_id: Optional[str] = None
    mastery_score: float = Field(default=0.1, ge=0.0, le=1.0)
    confidence_level: str = Field(
        default="LOW", description="LOW | MODERATE | HIGH"
    )
    attempts: int = 0
    weak_concepts: List[str] = Field(default_factory=list)
    last_practiced_at: Optional[datetime] = None
    spaced_repetition_interval_days: int = 1
    next_review_at: Optional[datetime] = None
    status: str = Field(
        default="LEARNING", description="NOVICE | LEARNING | PROFICIENT | MASTERED"
    )

    model_config = ConfigDict(from_attributes=True)


class StudentMasteryResponse(BaseModel):
    """Knowledge graph topic mastery list."""

    student_id: str
    topics: List[TopicMasterySchema]

    model_config = ConfigDict(from_attributes=True)
