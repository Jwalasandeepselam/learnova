# Learnova

Learnova turns **your uploaded material** into a source-grounded teaching, practice, and revision space.

There are no built-in subjects, lessons, sample quizzes, or preset mastery scores. A learning session begins empty and activates only after the learner uploads material and Learnova completes analysis.

## What is implemented

- Private accounts and persisted learning sessions.
- Multi-file source upload for PDF, DOCX, PPTX, TXT, Markdown, PNG, JPEG, and WebP.
- Clear recovery states for unsupported, empty, corrupted, or low-confidence scanned material.
- Source analysis that creates an upload-specific concept map, source locations, and prerequisites.
- Grounded text tutoring with citations and session conversation context.
- Gemini Live voice teaching with interruption handling, streaming PCM audio, transcripts, and an explicit text fallback.
- Adaptive questions from active material, server-held answer keys, replay protection, difficulty adjustment, evidence-based mastery, final assessment, and downloadable reports.
- Responsive dark Learnova UI for laptops and mobile screens, with reduced-motion support.

## Quick start

Use Python 3.11+ and Node 20+.

```powershell
# Configure server secrets. Never put these in frontend/.env.local.
Copy-Item .env.example backend/.env
# Add GEMINI_API_KEY to backend/.env

python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000

# In another terminal
cd frontend
npm ci
npm run dev
```

Open `http://localhost:3000`. The frontend proxies `/api` to `http://127.0.0.1:8000` by default, so browser cookies stay same-origin. For a phone on the local network, set `API_INTERNAL_URL` to a reachable backend address and add that web origin to `CORS_ORIGINS` in `backend/.env` for direct voice WebSocket access.

## Configuration

Copy [`.env.example`](.env.example) to `backend/.env` and configure:

| Variable | Purpose |
| --- | --- |
| `GEMINI_API_KEY` | Required for analysis, tutoring, OCR, quizzes, and live voice. |
| `GEMINI_MODEL` | Text model; defaults to `gemini-2.5-flash`. |
| `GEMINI_EMBEDDING_MODEL` | Optional semantic retrieval; lexical source retrieval remains available during an embedding outage. |
| `GEMINI_LIVE_MODEL` | Live audio model; defaults to `gemini-3.8-live`. |
| `CORS_ORIGINS` | JSON list of frontend origins allowed to make credentialed requests. |
| `COOKIE_SECURE` | Set to `true` in production behind HTTPS. |
| `MAX_UPLOAD_MB` | Per-file upload limit; defaults to 20. |

Production must use HTTPS and `COOKIE_SECURE=true`. Do not commit `backend/.env`, frontend environment files containing private values, uploads, or SQLite databases.

## Source-grounding guarantees

Learnova stores source locations beside extracted chunks. Tutor and quiz calls retrieve only chunks belonging to the active account and session. A model output is rejected when it does not cite an actual retrieved chunk.

If the material does not support an answer, the interface says so. If Gemini or OCR is unavailable, the session enters a visible error state and keeps uploaded material intact; it never replaces failed work with demo content.

Generated analogies are labelled as additional help. DOCX locations are shown as text segments because word-processing page breaks are not stable outside their original renderer.

## Verification

```powershell
.\.venv\Scripts\python.exe -m pytest -q
cd frontend
npm run lint
npx tsc --noEmit
npm run build
```

The tests cover source-only ingestion, account isolation, answer-key secrecy, question replay rejection, finite final assessments, unsafe origins, parser handling, and live voice interruption transport guards. A real microphone and Gemini Live session still need browser/device verification with a valid live-capable provider model.
