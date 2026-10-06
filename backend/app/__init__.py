"""
Learnova Backend Application Core
AI Personal Teaching Assistant
"""

import sys
from pathlib import Path

# Ensure both backend root and project root are in sys.path
_backend_dir = Path(__file__).resolve().parent.parent
_project_root = _backend_dir.parent

for _p in [str(_backend_dir), str(_project_root)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

__version__ = "1.0.0"
