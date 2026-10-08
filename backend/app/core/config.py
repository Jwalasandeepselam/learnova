"""Compatibility import for existing extraction and retrieval modules."""
from backend.app.config import BACKEND_DIR, ROOT_DIR, Settings, get_settings, settings

__all__ = ["BACKEND_DIR", "ROOT_DIR", "Settings", "get_settings", "settings"]
