# LEARNOVA — Developer Onboarding & Local Setup Guide

> **Production-Grade AI Personal Teaching Assistant**  
> Complete local development guide for the FastAPI backend, Next.js frontend, ReportLab engine, and vector store.

---

## 1. Prerequisites & System Requirements

Before starting local development, ensure the following toolchains are installed on your workstation:

| Requirement | Minimum Version | Recommended Version | Verification Command |
| :--- | :--- | :--- | :--- |
| **Python** | `3.11.0` | `3.11.9+` or `3.12+` | `python --version` |
| **Node.js** | `20.0.0` (LTS) | `22.x` (LTS) | `node --version` |
| **npm** | `10.0.0` | `10.8+` | `npm --version` |
| **Git** | `2.40.0` | Latest | `git --version` |
| **Operating System**| Windows 10/11, macOS 13+, or Ubuntu 22.04+ LTS | — | — |

---

## 2. Repository Architecture & Layout

```
Learnova/
├── backend/                      # FastAPI Python Application
│   ├── app/
│   │   ├── api/                  # REST API Route Handlers
│   │   │   ├── v1/
│   │   │   │   ├── documents.py  # Ingestion, parsing, chunking
│   │   │   │   ├── chat.py       # Grounded RAG conversational queries
│   │   │   │   ├── tutor.py      # Socratic dialogue & explanations
│   │   │   │   ├── quiz.py       # Quiz generation, evaluation & submissions
│   │   │   │   ├── study_packs.py# Study pack compilation & PDF download
│   │   │   │   └── student.py    # Progress & BKT mastery analytics
│   │   │   └── router.py         # Top-level API router aggregation
│   │   ├── core/                 # Core utilities
│   │   │   ├── config.py         # Pydantic BaseSettings & env configs
│   │   │   ├── database.py       # Async SQLAlchemy session factory
│   │   │   └── security.py       # File validator, MIME check, rate limiter
│   │   ├── models/               # SQLAlchemy 2.0 ORM Models
│   │   │   ├── document.py       # Document & DocumentChunk entities
│   │   │   ├── topic.py          # Topic & prerequisite graph
│   │   │   ├── session.py        # Dialogue session state
│   │   │   ├── quiz.py           # Quiz & QuizAttempt entities
│   │   │   ├── mastery.py        # StudentMastery entity
│   │   │   └── study_pack.py     # StudyPack entity
│   │   ├── schemas/              # Pydantic v2 Request/Response Schemas
│   │   │   ├── documents.py
│   │   │   ├── chat.py
│   │   │   ├── tutor.py
│   │   │   ├── quiz.py
│   │   │   └── study_packs.py
│   │   ├── services/             # Core Business Logic & Algorithms
│   │   │   ├── rag/              # Ingestion, chunking, BM25 + Vector search
│   │   │   ├── llm/              # OpenAI, Claude, Gemini, Ollama adapters
│   │   │   ├── tutor/            # Socratic state machine & misconception detector
│   │   │   ├── mastery/          # Bayesian Knowledge Tracing & SM-2 algorithms
│   │   │   └── pdf/              # ReportLab FigureAI Study Pack builder
│   │   └── main.py               # FastAPI ASGI entrypoint & middleware setup
│   ├── tests/                    # Pytest test suite
│   │   ├── test_documents.py
│   │   ├── test_rag.py
│   │   ├── test_tutor.py
│   │   └── test_pdf_engine.py
│   ├── requirements.txt          # Python dependencies
│   └── pyproject.toml            # Build metadata & linter configurations
│
├── frontend/                     # Next.js 16 Application
│   ├── app/                      # Next.js App Router
│   │   ├── layout.tsx            # Global Root Layout (Fonts, FigureAI theme)
│   │   ├── page.tsx              # Home / Dashboard
│   │   ├── documents/            # Document management & file explorer
│   │   ├── tutor/                # Socratic split-screen teaching workspace
│   │   ├── quiz/                 # Formative assessment arena
│   │   ├── study-packs/          # Study Pack viewer & PDF viewer
│   │   └── mastery/              # Mastery knowledge graph & analytics
│   ├── components/               # Modular UI Components (FigureAI design)
│   │   ├── ui/                   # Pill buttons, hairlines, badges, modals
│   │   ├── tutor/                # Chat bubbles, citation drawer, hints
│   │   └── quiz/                 # MCQ cards, progress meter, feedback card
│   ├── lib/                      # Shared Frontend Utilities
│   │   ├── api.ts                # Type-safe Fetch / Axios client
│   │   └── types.ts              # TypeScript interface definitions
│   ├── public/                   # Static assets & brand graphics
│   ├── package.json              # Frontend npm dependencies
│   └── tsconfig.json             # TypeScript configuration
│
├── storage/                      # Local Persistent Storage (Git-ignored)
│   ├── uploads/                  # Ingested PDF and source files
│   ├── study_packs/              # Generated ReportLab PDF files
│   └── vector_store/             # ChromaDB persistent directory
│
├── ARCHITECTURE.md               # System Architecture Blueprint
├── API.md                        # REST API Specification
├── DATABASE.md                   # Relational & Vector DB Schemas
├── AI.md                         # LLM Providers & Pedagogical Algorithms
├── DEVELOPMENT.md                # Local Setup & Developer Guide
└── README.md                     # Project Overview & Quick Start
```

---

## 3. Backend Setup (FastAPI)

### 3.1 Step 1: Create Virtual Environment
Open PowerShell (or your terminal) and navigate to the project root:

```powershell
cd c:\Users\sande\OneDrive\Documents\Learnova
python -m venv venv
```

Activate the virtual environment:
- **Windows (PowerShell):**
  ```powershell
  .\venv\Scripts\Activate.ps1
  ```
- **macOS / Linux:**
  ```bash
  source venv/bin/activate
  ```

### 3.2 Step 2: Install Dependencies
```powershell
cd backend
pip install --upgrade pip
pip install -r requirements.txt
```

#### Core Python Packages Installed:
- `fastapi>=0.115.0`, `uvicorn[standard]>=0.30.0`
- `pydantic>=2.8.0`, `pydantic-settings>=2.4.0`
- `sqlalchemy>=2.0.32`, `aiosqlite>=0.20.0`
- `chromadb>=0.5.5`
- `pymupdf>=1.24.9`, `pdfplumber>=0.11.4`, `python-docx>=1.1.2`
- `reportlab>=4.2.2`
- `openai>=1.42.0`, `anthropic>=0.34.0`, `google-genai>=0.1.1`
- `pytest>=8.3.0`, `pytest-asyncio>=0.24.0`, `httpx>=0.27.0`

### 3.3 Step 3: Configure Environment Variables
Create a `.env` file inside the `backend/` directory:

```env
# Application Settings
ENVIRONMENT=development
DEBUG=true
PORT=8000
CORS_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000"]

# Storage Paths (relative to backend or absolute)
STORAGE_DIR=../storage
UPLOAD_DIR=../storage/uploads
STUDY_PACK_DIR=../storage/study_packs
VECTOR_STORE_DIR=../storage/vector_store

# Relational Database
DATABASE_URL=sqlite+aiosqlite:///../storage/learnova.db

# AI Provider Configuration
AI_PROVIDER=openai
AI_MODEL=gpt-4o-mini
AI_EMBEDDING_PROVIDER=openai
AI_EMBEDDING_MODEL=text-embedding-3-small

# API Keys (Provide your active key)
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
OLLAMA_BASE_URL=http://localhost:11434
```

### 3.4 Step 4: Run the Backend Development Server
```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Verify backend health:
- Interactive API Docs (Swagger UI): **`http://localhost:8000/docs`**
- Alternative OpenAPI Redoc: **`http://localhost:8000/redoc`**
- Health Probe: `GET http://localhost:8000/health`

---

## 4. Frontend Setup (Next.js 16)

### 4.1 Step 1: Install Dependencies
Open a second terminal window:

```powershell
cd c:\Users\sande\OneDrive\Documents\Learnova\frontend
npm install
```

### 4.2 Step 2: Configure Environment Variables
Create a `.env.local` file inside `frontend/`:

```env
# URL pointing to the FastAPI Backend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 4.3 Step 3: Run the Next.js Development Server
```powershell
npm run dev
```

The Next.js client is now running at **`http://localhost:3000`**.

---

## 5. End-to-End Local Testing Flow

Follow these verification steps to test the entire stack locally:

### 5.1 Step 1: Upload a Source Document
Upload a sample PDF (e.g., lecture notes or textbook excerpt) through the Web UI at `http://localhost:3000` or via cURL:
```powershell
curl -X POST "http://localhost:8000/api/documents/upload" `
  -F "file=@sample_physics.pdf"
```
The backend extracts text with PyMuPDF, chunks the document into 600-token blocks, generates dense embeddings, and stores them in ChromaDB.

### 5.2 Step 2: Test Grounded Chat with Citations
```powershell
curl -X POST "http://localhost:8000/api/chat" `
  -H "Content-Type: application/json" `
  -d '{"document_id": "doc_xxxx", "query": "Explain the uncertainty principle."}'
```
Inspect the response payload for verified citations `[[Doc:..., Page:..., Chunk:...]]`.

### 5.3 Step 3: Launch Socratic Tutor Session
Navigate to the Socratic Workspace in the UI. Choose a topic and submit an initial hypothesis. The AI tutor evaluates your response, flags any misconceptions, and poses a guided diagnostic question.

### 5.4 Step 4: Compile & Download FigureAI Study Pack PDF
Trigger study pack compilation:
```powershell
curl -X POST "http://localhost:8000/api/study-packs/generate" `
  -H "Content-Type: application/json" `
  -d '{"document_id": "doc_xxxx", "title": "Physics Exam Mastery"}'
```
Open `http://localhost:8000/api/study-packs/{pack_id}/pdf` in your browser to view the rendered ReportLab publication PDF.

---

## 6. Testing & Quality Assurance

### 6.1 Backend Tests (Pytest)
Run the automated test suite with coverage:
```powershell
cd backend
pytest -v --cov=app --cov-report=term-missing
```

Run specific test modules:
```powershell
pytest tests/test_rag.py -v
pytest tests/test_tutor.py -v
pytest tests/test_pdf_engine.py -v
```

### 6.2 Frontend Code Quality (ESLint & TypeCheck)
```powershell
cd frontend
npm run lint
npx tsc --noEmit
```

### 6.3 Code Formatting & Style Standards
- **Python:** Strict adherence to `ruff` or `black` formatting:
  ```powershell
  ruff check backend/app --fix
  ruff format backend/app
  ```
- **TypeScript:** Strict adherence to Prettier and Tailwind CSS v4 class order.

---

## 7. Troubleshooting & FAQ

#### Q1: "CORS error when frontend queries `localhost:8000`"
**Resolution:** Ensure `CORS_ORIGINS` in `backend/.env` contains `"http://localhost:3000"`. Restart the FastAPI server after modifying `.env`.

#### Q2: "ReportLab font rendering error or missing Helvetica / Space Grotesk"
**Resolution:** By default, ReportLab falls back to standard Core PostScript fonts (`Helvetica`, `Helvetica-Bold`, `Courier`). If custom TrueType fonts (`SpaceGrotesk-Medium.ttf`) are configured, ensure they exist in `backend/app/services/pdf/fonts/` or allow the fallback to `Helvetica`.

#### Q3: "ChromaDB database lock error on Windows"
**Resolution:** Make sure only one uvicorn worker is accessing the SQLite/Chroma file simultaneously. In local development, avoid setting `--workers > 1` when using SQLite or ChromaDB local persistence.

#### Q4: "I want to run 100% offline without API keys"
**Resolution:** Install [Ollama](https://ollama.ai/), pull a model (`ollama pull llama3.2`), and set `AI_PROVIDER=ollama` in `backend/.env`. Embeddings will automatically use local HuggingFace `all-MiniLM-L6-v2` or `nomic-embed-text`.
