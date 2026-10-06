# LEARNOVA — REST API Specification

> **Base URL:** `http://localhost:8000` (Local) / `https://api.learnova.ai` (Production)  
> **API Version:** `v1` (`/api/v1` or `/api`)  
> **Format:** Standard JSON (`application/json`) & Multipart Form Data (`multipart/form-data`)  
> **Specification Standard:** OpenAPI 3.1 compatible

---

## 1. Global Standards & Conventions

### 1.1 Headers
| Header | Type | Description | Required |
| :--- | :--- | :--- | :--- |
| `Content-Type` | `string` | `application/json` (or `multipart/form-data` for file uploads) | Yes |
| `X-Student-ID` | `string` | Unique identifier of the student (UUIDv4 or guest ID) | Optional (Defaults to default student) |
| `X-Session-ID` | `string` | Persistent dialogue session context ID | Optional |

### 1.2 Standard Success Envelope
For standard single resources and mutations:
```json
{
  "success": true,
  "data": { ... },
  "meta": {
    "timestamp": "2026-10-06T16:30:00Z",
    "request_id": "req_8f12a34b"
  }
}
```

### 1.3 Standard Error Envelope
All error responses return standard HTTP error status codes (4xx, 5xx) with the following JSON schema:
```json
{
  "success": false,
  "error": {
    "code": "DOCUMENT_NOT_FOUND",
    "message": "The requested document with ID 'doc_98b4f' could not be found.",
    "details": {
      "document_id": "doc_98b4f"
    }
  },
  "meta": {
    "timestamp": "2026-10-06T16:30:00Z",
    "request_id": "req_8f12a34b"
  }
}
```

#### Common Error Codes
- `INVALID_FILE_TYPE`: Uploaded file MIME type or magic bytes not supported.
- `FILE_SIZE_EXCEEDED`: Uploaded file exceeds maximum allowed limit (50 MB).
- `DOCUMENT_NOT_FOUND`: Referenced document ID does not exist.
- `TOPIC_NOT_FOUND`: Referenced topic ID does not exist.
- `SESSION_EXPIRED`: Interactive dialogue session timed out or invalid.
- `RAG_RETRIEVAL_FAILED`: Vector search or chunk retrieval encountered an error.
- `UNGROUNDED_RESPONSE`: Citation verification failed and generation was aborted.
- `RATE_LIMIT_EXCEEDED`: Client exceeded API rate limit quota.
- `INTERNAL_SERVER_ERROR`: Unhandled exception during backend processing.

---

## 2. Document Management Endpoints

### 2.1 Upload Document
Uploads a source document (PDF, DOCX, TXT, MD) for ingestion, chunking, and embedding.

- **Endpoint:** `POST /api/documents/upload`
- **Content-Type:** `multipart/form-data`
- **Request Parameters:**
  - `file`: Binary file stream (max 50 MB, allowed: `.pdf`, `.docx`, `.txt`, `.md`).
  - `title` (optional): `string` — Human-readable document title. If omitted, original filename is used.

**Response `202 Accepted`:**
```json
{
  "success": true,
  "data": {
    "id": "doc_a1b2c3d4",
    "filename": "quantum_mechanics_ch1.pdf",
    "title": "Quantum Mechanics - Principles & Wavefunctions",
    "file_size": 4194304,
    "mime_type": "application/pdf",
    "status": "PROCESSING",
    "total_pages": 38,
    "total_chunks": 0,
    "created_at": "2026-10-06T16:35:00Z"
  },
  "meta": {
    "timestamp": "2026-10-06T16:35:00Z",
    "request_id": "req_upload_001"
  }
}
```

---

### 2.2 List Documents
Retrieves a paginated list of ingested documents.

- **Endpoint:** `GET /api/documents`
- **Query Parameters:**
  - `page` (optional, default `1`): `integer`
  - `limit` (optional, default `20`, max `100`): `integer`
  - `status` (optional): `string` — Filter by `PROCESSING`, `READY`, `FAILED`
  - `search` (optional): `string` — Search by title or filename

**Response `200 OK`:**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "doc_a1b2c3d4",
        "title": "Quantum Mechanics - Principles & Wavefunctions",
        "filename": "quantum_mechanics_ch1.pdf",
        "file_size": 4194304,
        "mime_type": "application/pdf",
        "status": "READY",
        "total_pages": 38,
        "total_chunks": 142,
        "word_count": 28400,
        "topic_count": 6,
        "created_at": "2026-10-06T16:35:00Z",
        "updated_at": "2026-10-06T16:36:12Z"
      }
    ],
    "pagination": {
      "total_items": 1,
      "total_pages": 1,
      "current_page": 1,
      "page_size": 20
    }
  },
  "meta": {
    "timestamp": "2026-10-06T16:37:00Z",
    "request_id": "req_list_001"
  }
}
```

---

### 2.3 Get Document Details
Retrieves detailed metadata, parsed topic outlines, and ingestion statistics for a specific document.

- **Endpoint:** `GET /api/documents/{id}`
- **Path Parameters:**
  - `id`: `string` (UUID or slug)

**Response `200 OK`:**
```json
{
  "success": true,
  "data": {
    "id": "doc_a1b2c3d4",
    "title": "Quantum Mechanics - Principles & Wavefunctions",
    "filename": "quantum_mechanics_ch1.pdf",
    "file_size": 4194304,
    "mime_type": "application/pdf",
    "status": "READY",
    "total_pages": 38,
    "total_chunks": 142,
    "word_count": 28400,
    "summary": "Covers foundational wave mechanics, Schrödinger equation, wave packets, and Heisenberg uncertainty principle.",
    "topics": [
      {
        "id": "top_01",
        "name": "Wave-Particle Duality",
        "difficulty_level": "INTERMEDIATE",
        "chunk_count": 24,
        "mastery_score": 0.85
      },
      {
        "id": "top_02",
        "name": "Schrödinger Time-Dependent Equation",
        "difficulty_level": "ADVANCED",
        "chunk_count": 48,
        "mastery_score": 0.42
      }
    ],
    "created_at": "2026-10-06T16:35:00Z",
    "updated_at": "2026-10-06T16:36:12Z"
  },
  "meta": {
    "timestamp": "2026-10-06T16:38:00Z",
    "request_id": "req_get_001"
  }
}
```

---

### 2.4 Trigger Document Deep Analysis
Initiates or re-runs deep concept extraction, prerequisite graph building, and executive summary generation.

- **Endpoint:** `POST /api/documents/{id}/analyze`
- **Path Parameters:**
  - `id`: `string`
- **Request Body (optional):**
```json
{
  "force_recompute": false,
  "extract_formulas": true,
  "extract_flashcards": true
}
```

**Response `200 OK`:**
```json
{
  "success": true,
  "data": {
    "document_id": "doc_a1b2c3d4",
    "status": "ANALYZED",
    "executive_summary": "This document introduces modern quantum mechanics...",
    "topics_extracted": 6,
    "key_formulas_extracted": 14,
    "prerequisites_mapped": 8
  },
  "meta": {
    "timestamp": "2026-10-06T16:39:00Z",
    "request_id": "req_analyze_001"
  }
}
```

---

### 2.5 Delete Document
Permanently deletes a document, its disk file, database records, and vector embeddings.

- **Endpoint:** `DELETE /api/documents/{id}`
- **Path Parameters:**
  - `id`: `string`

**Response `200 OK`:**
```json
{
  "success": true,
  "data": {
    "document_id": "doc_a1b2c3d4",
    "deleted": true,
    "chunks_removed": 142
  },
  "meta": {
    "timestamp": "2026-10-06T16:40:00Z",
    "request_id": "req_del_001"
  }
}
```

---

## 3. RAG Chat & Grounded Q&A

### 3.1 Grounded Chat Query
Performs hybrid semantic and lexical retrieval against indexed document chunks and synthesizes an academic response with verified citations.

- **Endpoint:** `POST /api/chat`
- **Content-Type:** `application/json`
- **Request Body:**
```json
{
  "document_id": "doc_a1b2c3d4",
  "query": "What is the physical meaning of the wavefunction's probability density?",
  "conversation_id": "conv_998877",
  "stream": false,
  "top_k": 4
}
```

**Response `200 OK`:**
```json
{
  "success": true,
  "data": {
    "conversation_id": "conv_998877",
    "message_id": "msg_443322",
    "response": "According to the Born interpretation, the quantity $|\\psi(x,t)|^2$ represents the probability density of finding a particle at position $x$ at time $t$ [[Doc:doc_a1b2c3d4, Page:14, Chunk:chunk_42]]. The integral of this probability density over all space must equal 1, satisfying the normalization condition [[Doc:doc_a1b2c3d4, Page:15, Chunk:chunk_44]].",
    "citations": [
      {
        "citation_id": "cite_1",
        "document_id": "doc_a1b2c3d4",
        "page_number": 14,
        "chunk_id": "chunk_42",
        "snippet": "Max Born formulated that the square modulus of the wave function |psi(x)|^2 is proportional to the probability of finding the particle in an infinitesimal volume dx.",
        "relevance_score": 0.94
      },
      {
        "citation_id": "cite_2",
        "document_id": "doc_a1b2c3d4",
        "page_number": 15,
        "chunk_id": "chunk_44",
        "snippet": "Normalization requires that the total probability of finding the particle somewhere in space is unity: integral |psi|^2 dx = 1.",
        "relevance_score": 0.89
      }
    ],
    "grounded": true
  },
  "meta": {
    "timestamp": "2026-10-06T16:41:00Z",
    "request_id": "req_chat_001"
  }
}
```

*Note:* When `stream: true` is sent, the endpoint emits Server-Sent Events (`text/event-stream`) streaming token chunks followed by a final JSON payload containing the resolved citations array.

---

## 4. Pedagogical Socratic Tutor Endpoints

### 4.1 Teach Concept (Socratic / First Principles)
Initiates or continues an interactive teaching session on a specific topic. Instead of simply dictating content, it provides scaffolded explanations followed by a diagnostic question to test the student's reasoning.

- **Endpoint:** `POST /api/tutor/teach`
- **Request Body:**
```json
{
  "document_id": "doc_a1b2c3d4",
  "topic_id": "top_01",
  "session_id": "sess_55aa66",
  "pedagogical_mode": "socratic",
  "preferred_difficulty": "intermediate"
}
```
*Valid `pedagogical_mode` values:* `"socratic"`, `"first_principles"`, `"analogy"`, `"feynman"`

**Response `200 OK`:**
```json
{
  "success": true,
  "data": {
    "session_id": "sess_55aa66",
    "step_index": 1,
    "topic_name": "Wave-Particle Duality",
    "pedagogical_mode": "socratic",
    "scaffold_explanation": "Think of light not as a rigid particle or an endless wave, but as exhibiting properties of both depending on how we measure it. In the photoelectric effect, electrons are ejected only when light frequency exceeds a threshold, proving light carries discrete energy quanta ($E = h\\nu$).",
    "diagnostic_question": {
      "question_id": "q_diag_01",
      "question_type": "open_ended",
      "prompt": "If you double the intensity of light while keeping its frequency below the cutoff frequency, why are still no electrons emitted?",
      "hints": [
        "Recall what intensity represents vs what individual photon energy represents.",
        "Does electron ejection depend on the collective energy of many photons or single photon collisions?"
      ]
    },
    "citations": [
      {
        "document_id": "doc_a1b2c3d4",
        "page_number": 7,
        "chunk_id": "chunk_18",
        "snippet": "Einstein explained that light delivers energy in packets called photons. If an individual photon has energy below the work function phi, no electron can escape."
      }
    ]
  },
  "meta": {
    "timestamp": "2026-10-06T16:42:00Z",
    "request_id": "req_tutor_teach_001"
  }
}
```

---

### 4.2 Explain Again (Alternative Modality)
Invoked when a student indicates they do not understand or are stuck. The engine switches pedagogical modality (e.g., from formal math to intuitive mechanical analogy).

- **Endpoint:** `POST /api/tutor/explain-again`
- **Request Body:**
```json
{
  "session_id": "sess_55aa66",
  "target_concept": "Cutoff frequency in photoelectric effect",
  "desired_modality": "analogy",
  "current_obstacle": "I don't get why more light doesn't knock out electrons if total energy is higher."
}
```

**Response `200 OK`:**
```json
{
  "success": true,
  "data": {
    "session_id": "sess_55aa66",
    "modality_used": "analogy",
    "revised_explanation": "Imagine an arcade machine that only accepts 1-dollar tokens to dispense a prize. If you throw a thousand 10-cent dimes at the slot, none of them will activate the machine because each coin is individually too small. In the photoelectric effect, each electron is bound by a minimum 'toll' (the work function). Increasing intensity simply throws more dim coins, but none have the individual punch (frequency) to pay the toll.",
    "follow_up_check": {
      "prompt": "In this arcade analogy, what corresponds to the 'frequency' of light, and what corresponds to 'intensity'?"
    }
  },
  "meta": {
    "timestamp": "2026-10-06T16:43:00Z",
    "request_id": "req_tutor_again_001"
  }
}
```

---

### 4.3 Evaluate Student Answer
Evaluates a student's answer to a diagnostic or Socratic question, diagnoses potential misconceptions, and returns targeted feedback.

- **Endpoint:** `POST /api/tutor/evaluate-answer`
- **Request Body:**
```json
{
  "session_id": "sess_55aa66",
  "question_id": "q_diag_01",
  "student_answer": "Because more intensity just means more waves, but the speed of light stays the same so electrons don't move."
}
```

**Response `200 OK`:**
```json
{
  "success": true,
  "data": {
    "is_correct": false,
    "understanding_level": "PARTIAL",
    "misconception": {
      "detected": true,
      "category": "CONCEPTUAL",
      "summary": "Confusing wave speed with individual photon energy ($h\\nu$)",
      "explanation": "You correctly recognized that speed is invariant, but the constraint on electron ejection is photon energy (frequency), not wave propagation speed."
    },
    "scaffolded_hint": "Remember that energy of each individual photon is determined solely by $E = h\\nu$. What happens to each photon when you increase intensity?",
    "mastery_delta": -0.05,
    "next_action": "PROVIDE_HINT"
  },
  "meta": {
    "timestamp": "2026-10-06T16:44:00Z",
    "request_id": "req_eval_ans_001"
  }
}
```

---

## 5. Quiz & Formative Assessment Endpoints

### 5.1 Generate Quiz
Generates an assessment tailored to a document or specific topics, with questions adapted to the student's mastery profile.

- **Endpoint:** `POST /api/quiz/generate`
- **Request Body:**
```json
{
  "document_id": "doc_a1b2c3d4",
  "topic_ids": ["top_01", "top_02"],
  "question_count": 5,
  "question_types": ["mcq", "short_answer"],
  "difficulty": "adaptive"
}
```

**Response `200 OK`:**
```json
{
  "success": true,
  "data": {
    "quiz_id": "quiz_778899",
    "document_id": "doc_a1b2c3d4",
    "total_questions": 5,
    "questions": [
      {
        "id": "q_1",
        "type": "mcq",
        "topic_id": "top_01",
        "prompt": "What does the de Broglie relation $\\lambda = \\frac{h}{p}$ link together?",
        "options": [
          { "key": "A", "text": "Wave wavelength and particle linear momentum" },
          { "key": "B", "text": "Photon frequency and wave velocity" },
          { "key": "C", "text": "Angular momentum and electron orbital radius" },
          { "key": "D", "text": "Energy density and wave amplitude" }
        ]
      },
      {
        "id": "q_2",
        "type": "short_answer",
        "topic_id": "top_02",
        "prompt": "State the physical significance of the imaginary unit $i$ in the time-dependent Schrödinger equation."
      }
    ]
  },
  "meta": {
    "timestamp": "2026-10-06T16:45:00Z",
    "request_id": "req_quiz_gen_001"
  }
}
```

---

### 5.2 Evaluate Individual Question
Evaluates a single question submission in real-time during an active practice test, providing instant feedback without completing the entire quiz.

- **Endpoint:** `POST /api/quiz/evaluate`
- **Request Body:**
```json
{
  "quiz_id": "quiz_778899",
  "question_id": "q_1",
  "submitted_answer": "A"
}
```

**Response `200 OK`:**
```json
{
  "success": true,
  "data": {
    "question_id": "q_1",
    "is_correct": true,
    "correct_answer": "A",
    "explanation": "Correct. De Broglie proposed that matter possesses wave properties where wavelength $\\lambda$ is Planck's constant $h$ divided by momentum $p$.",
    "citation": {
      "document_id": "doc_a1b2c3d4",
      "page_number": 11,
      "chunk_id": "chunk_32"
    }
  },
  "meta": {
    "timestamp": "2026-10-06T16:46:00Z",
    "request_id": "req_quiz_eval_001"
  }
}
```

---

### 5.3 Submit Completed Quiz
Submits all answers for a full quiz session, computes the composite score, diagnoses recurring misconceptions, and records spaced repetition updates.

- **Endpoint:** `POST /api/quiz/submit`
- **Request Body:**
```json
{
  "quiz_id": "quiz_778899",
  "time_spent_seconds": 320,
  "submissions": [
    { "question_id": "q_1", "submitted_answer": "A" },
    { "question_id": "q_2", "submitted_answer": "It allows phase oscillation without decay." }
  ]
}
```

**Response `200 OK`:**
```json
{
  "success": true,
  "data": {
    "attempt_id": "att_112233",
    "quiz_id": "quiz_778899",
    "score_percentage": 90.0,
    "total_questions": 2,
    "correct_count": 2,
    "time_spent_seconds": 320,
    "topic_breakdown": [
      {
        "topic_id": "top_01",
        "topic_name": "Wave-Particle Duality",
        "score": 1.0,
        "new_mastery_level": 0.92
      },
      {
        "topic_id": "top_02",
        "topic_name": "Schrödinger Time-Dependent Equation",
        "score": 0.8,
        "new_mastery_level": 0.58
      }
    ],
    "identified_misconceptions": [],
    "recommended_review_date": "2026-10-09T16:47:00Z"
  },
  "meta": {
    "timestamp": "2026-10-06T16:47:00Z",
    "request_id": "req_quiz_sub_001"
  }
}
```

---

## 6. Study Pack & ReportLab PDF Endpoints

### 6.1 Generate Study Pack
Synthesizes a structured study pack comprising an executive conceptual summary, key formulas & laws table, common misconceptions list, flashcards, and practice problems.

- **Endpoint:** `POST /api/study-packs/generate`
- **Request Body:**
```json
{
  "document_id": "doc_a1b2c3d4",
  "title": "Quantum Mechanics Exam Mastery Pack",
  "include_flashcards": true,
  "include_cheat_sheet": true,
  "include_practice_exam": true
}
```

**Response `202 Accepted`:**
```json
{
  "success": true,
  "data": {
    "id": "pack_9900aa",
    "document_id": "doc_a1b2c3d4",
    "title": "Quantum Mechanics Exam Mastery Pack",
    "status": "GENERATING",
    "summary": null,
    "pdf_url": "/api/study-packs/pack_9900aa/pdf",
    "created_at": "2026-10-06T16:48:00Z"
  },
  "meta": {
    "timestamp": "2026-10-06T16:48:00Z",
    "request_id": "req_pack_gen_001"
  }
}
```

---

### 6.2 Get Study Pack Details
Retrieves the complete JSON representation of a generated Study Pack.

- **Endpoint:** `GET /api/study-packs/{id}`
- **Path Parameters:**
  - `id`: `string`

**Response `200 OK`:**
```json
{
  "success": true,
  "data": {
    "id": "pack_9900aa",
    "document_id": "doc_a1b2c3d4",
    "title": "Quantum Mechanics Exam Mastery Pack",
    "status": "READY",
    "summary": "### Core Concepts\nThis pack condenses the fundamental tenets of wave-particle duality...",
    "formula_sheet": [
      {
        "name": "de Broglie relation",
        "formula": "\\lambda = \\frac{h}{p}",
        "variables": "h: Planck constant, p: momentum"
      }
    ],
    "flashcards": [
      {
        "id": "fc_1",
        "front": "What is the physical meaning of |psi|^2?",
        "back": "Probability density of finding a particle at a given spatial coordinate."
      }
    ],
    "pdf_available": true,
    "pdf_size_bytes": 1048576,
    "generated_at": "2026-10-06T16:49:15Z"
  },
  "meta": {
    "timestamp": "2026-10-06T16:50:00Z",
    "request_id": "req_pack_get_001"
  }
}
```

---

### 6.3 Download Study Pack PDF
Streams the high-fidelity, FigureAI-styled ReportLab PDF document for direct viewing or printing.

- **Endpoint:** `GET /api/study-packs/{id}/pdf`
- **Path Parameters:**
  - `id`: `string`
- **Response Headers:**
  - `Content-Type`: `application/pdf`
  - `Content-Disposition`: `inline; filename="Learnova_StudyPack_pack_9900aa.pdf"`
- **Response:** Raw binary PDF stream (`200 OK`).

---

## 7. Student Mastery & Progress Endpoints

### 7.1 Get Overall Student Progress
Fetches cumulative student performance metrics, daily streaks, time invested, and broad mastery distributions.

- **Endpoint:** `GET /api/student/progress`
- **Headers:** `X-Student-ID` (optional)

**Response `200 OK`:**
```json
{
  "success": true,
  "data": {
    "student_id": "usr_default",
    "total_documents_studied": 4,
    "total_learning_time_minutes": 312,
    "current_streak_days": 5,
    "total_quizzes_completed": 18,
    "average_quiz_score": 88.4,
    "mastery_distribution": {
      "novice": 2,
      "learning": 5,
      "proficient": 7,
      "mastered": 4
    },
    "upcoming_reviews_count": 3
  },
  "meta": {
    "timestamp": "2026-10-06T16:51:00Z",
    "request_id": "req_prog_001"
  }
}
```

---

### 7.2 Get Granular Topic Mastery Graph
Returns the detailed concept mastery scores, Bayesian Knowledge Tracing probability estimates, retention decay status, and scheduled spaced repetition review timestamps.

- **Endpoint:** `GET /api/student/mastery`
- **Query Parameters:**
  - `document_id` (optional): `string` — Filter topics by specific document

**Response `200 OK`:**
```json
{
  "success": true,
  "data": {
    "student_id": "usr_default",
    "topics": [
      {
        "topic_id": "top_01",
        "topic_name": "Wave-Particle Duality",
        "document_id": "doc_a1b2c3d4",
        "mastery_score": 0.92,
        "confidence_level": "HIGH",
        "last_practiced_at": "2026-10-06T16:47:00Z",
        "spaced_repetition_interval_days": 3,
        "next_review_at": "2026-10-09T16:47:00Z",
        "status": "MASTERED"
      },
      {
        "topic_id": "top_02",
        "topic_name": "Schrödinger Time-Dependent Equation",
        "document_id": "doc_a1b2c3d4",
        "mastery_score": 0.58,
        "confidence_level": "MODERATE",
        "last_practiced_at": "2026-10-06T16:47:00Z",
        "spaced_repetition_interval_days": 1,
        "next_review_at": "2026-10-07T16:47:00Z",
        "status": "PRACTICING"
      }
    ]
  },
  "meta": {
    "timestamp": "2026-10-06T16:52:00Z",
    "request_id": "req_mast_001"
  }
}
```
