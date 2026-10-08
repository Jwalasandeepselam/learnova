"""Learnova application. Only authenticated, source-grounded v2 routes are served."""
from collections import defaultdict, deque
from contextlib import asynccontextmanager
import logging
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.config import settings
from backend.app.learning.router import router as learning_router
from backend.app.learning.service import initialize
from backend.app.voice.router import router as voice_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("learnova")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.ensure_directories()
    initialize()
    if settings.ENVIRONMENT == "production" and not settings.COOKIE_SECURE:
        raise RuntimeError("Production requires COOKIE_SECURE=true and HTTPS.")
    yield


app = FastAPI(title="Learnova", version="0.2.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware, allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True, allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type"],
)

# Single-process abuse protection. Multi-worker deployments need a shared limiter.
auth_attempts: dict[str, deque] = defaultdict(deque)


@app.middleware("http")
async def request_guards(request: Request, call_next):
    request_id = uuid.uuid4().hex
    if request.method in {"POST", "DELETE", "PATCH", "PUT"}:
        origin = request.headers.get("origin")
        if origin and origin not in settings.CORS_ORIGINS:
            return JSONResponse({"detail": "Request origin is not allowed."}, status_code=403)
        if request.headers.get("sec-fetch-site") == "cross-site" and not origin:
            return JSONResponse({"detail": "Cross-site request is not allowed."}, status_code=403)
    try:
        content_length = int(request.headers.get("content-length", "0"))
    except ValueError:
        return JSONResponse({"detail": "Invalid request size."}, status_code=400)
    if content_length > (settings.MAX_UPLOAD_MB * 10 + 1) * 1024 * 1024:
        return JSONResponse({"detail": "Upload is too large. Add fewer files at a time."}, status_code=413)
    if request.method == "POST" and request.url.path in {"/api/v2/auth/login", "/api/v2/auth/register"}:
        now = time.monotonic()
        client = request.client.host if request.client else "unknown"
        # Prune idle entries so a long-running process does not retain every client.
        for host in list(auth_attempts):
            if not auth_attempts[host] or auth_attempts[host][-1] < now - 60:
                del auth_attempts[host]
        attempts = auth_attempts[client]
        while attempts and attempts[0] < now - 60:
            attempts.popleft()
        if len(attempts) >= 20:
            return JSONResponse({"detail": "Too many sign-in attempts. Try again in a minute."}, status_code=429, headers={"Retry-After": "60"})
        attempts.append(now)
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "same-origin"
    response.headers["Cache-Control"] = "no-store"
    return response


@app.exception_handler(Exception)
async def unexpected_error(request: Request, exc: Exception):
    # Do not echo provider responses, request bodies, or secrets to the browser.
    logger.error("Unhandled request error: %s", type(exc).__name__)
    return JSONResponse({"detail": "The request could not be completed. Please retry."}, status_code=500)


@app.get("/api/health")
def health():
    return {"status": "healthy", "service": "learnova", "version": "0.2.0"}


app.include_router(learning_router)
app.include_router(voice_router)
