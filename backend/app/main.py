"""Learnova FastAPI Application Entrypoint.

Initializes configuration, database schema, CORS policies, standard error envelopes,
and modular REST API routers according to ARCHITECTURE.md and API.md.
"""

from contextlib import asynccontextmanager
from datetime import datetime, timezone
import logging
import uuid
import sys
from pathlib import Path

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

try:
    from backend.app.config import get_settings
    from backend.app.models.database import init_db
    from backend.app.models.schemas import ErrorDetail, ErrorResponse, MetaSchema
except ImportError:
    from app.config import get_settings
    from app.models.database import init_db
    from app.models.schemas import ErrorDetail, ErrorResponse, MetaSchema

settings = get_settings()

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("learnova")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager to initialize storage and database tables on startup."""
    logger.info("Initializing Learnova storage and database schema...")
    settings.ensure_directories()
    init_db()
    logger.info("Learnova backend initialized successfully.")
    yield
    logger.info("Learnova backend shutting down.")


app = FastAPI(
    title="Learnova API",
    description="AI Personal Teaching Assistant REST API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware
origins = settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else [settings.CORS_ORIGINS]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==============================================================================
# Standard Exception Handlers adhering to API.md
# ==============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Normalize HTTPExceptions into standard ErrorResponse schema."""
    req_id = getattr(request.state, "request_id", f"req_{uuid.uuid4().hex[:8]}")
    error_payload = ErrorResponse(
        success=False,
        error=ErrorDetail(
            code=f"HTTP_{exc.status_code}",
            message=str(exc.detail),
            details={"status_code": exc.status_code},
        ),
        meta=MetaSchema(
            timestamp=datetime.now(timezone.utc),
            request_id=req_id,
        ),
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=error_payload.model_dump(mode="json"),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Normalize Pydantic request validation errors."""
    req_id = getattr(request.state, "request_id", f"req_{uuid.uuid4().hex[:8]}")
    error_payload = ErrorResponse(
        success=False,
        error=ErrorDetail(
            code="VALIDATION_ERROR",
            message="The request payload failed schema validation.",
            details={"errors": exc.errors()},
        ),
        meta=MetaSchema(
            timestamp=datetime.now(timezone.utc),
            request_id=req_id,
        ),
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_payload.model_dump(mode="json"),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Normalize unhandled internal errors."""
    req_id = getattr(request.state, "request_id", f"req_{uuid.uuid4().hex[:8]}")
    logger.exception(f"Unhandled exception on request {req_id}: {exc}")
    error_payload = ErrorResponse(
        success=False,
        error=ErrorDetail(
            code="INTERNAL_SERVER_ERROR",
            message="An unexpected server error occurred.",
            details={"type": type(exc).__name__},
        ),
        meta=MetaSchema(
            timestamp=datetime.now(timezone.utc),
            request_id=req_id,
        ),
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_payload.model_dump(mode="json"),
    )


# ==============================================================================
# Health & Status Routes
# ==============================================================================

@app.get("/api/health", tags=["System"])
async def health_check():
    """System health check endpoint."""
    return {
        "success": True,
        "status": "healthy",
        "service": "learnova-backend",
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/", tags=["System"])
async def root():
    """Root redirect / information endpoint."""
    return {
        "service": "Learnova AI Teaching Assistant API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "active",
    }


# ==============================================================================
# Mount API Routers
# ==============================================================================
from backend.app.api.documents import router as documents_router
from backend.app.api.chat import router as chat_router
from backend.app.api.tutor import router as tutor_router
from backend.app.api.quiz import router as quiz_router
from backend.app.api.study_packs import router as study_packs_router
from backend.app.api.student import router as student_router

app.include_router(documents_router, prefix="/api")
app.include_router(chat_router, prefix="/api")
app.include_router(tutor_router, prefix="/api")
app.include_router(quiz_router, prefix="/api")
app.include_router(study_packs_router, prefix="/api")
app.include_router(student_router, prefix="/api")

