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
    allow_headers=["Content-Type", "Authorization"],
)

# Single-process abuse protection. Multi-worker deployments need a shared limiter.
# Keep the map bounded so abusive traffic cannot turn the limiter into a memory sink.
rate_buckets: dict[tuple[str, str], deque] = defaultdict(deque)
RATE_LIMITS = {
    "/api/v2/auth/login": (10, 60),
    "/api/v2/auth/register": (6, 60),
    "/api/v2/sessions": (30, 60),
}


def request_limit(path: str):
    if path in RATE_LIMITS:
        return RATE_LIMITS[path]
    if path.endswith("/files"):
        return (12, 60)
    if path.endswith(("/analyze", "/chat", "/quiz", "/answers")):
        return (45, 60)
    return None


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
    limit = request_limit(request.url.path) if request.method == "POST" else None
    if limit:
        now = time.monotonic()
        client = request.client.host if request.client else "unknown"
        maximum, window = limit
        key = (request.url.path, client)
        # Prune idle entries so a long-running process does not retain every client.
        for stale_key in list(rate_buckets):
            if not rate_buckets[stale_key] or rate_buckets[stale_key][-1] < now - 60:
                del rate_buckets[stale_key]
        if len(rate_buckets) > 10_000:
            return JSONResponse({"detail": "Service is busy. Please retry shortly."}, status_code=503)
        attempts = rate_buckets[key]
        while attempts and attempts[0] < now - window:
            attempts.popleft()
        if len(attempts) >= maximum:
            return JSONResponse({"detail": "Too many requests. Try again shortly."}, status_code=429, headers={"Retry-After": str(window)})
        attempts.append(now)
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "same-origin"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'"
    response.headers["Permissions-Policy"] = "camera=(), geolocation=(), microphone=()"
    response.headers["Cache-Control"] = "no-store"
    if settings.ENVIRONMENT == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
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
