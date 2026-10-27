"""Regression coverage for the password policy shared by the auth form and API."""
from pathlib import Path

import pytest
from pydantic import ValidationError

from backend.app.learning.router import Credentials


def test_browser_password_requirement_matches_api_policy():
    """The browser must not accept a password the registration endpoint rejects."""
    source = (Path(__file__).parents[2] / 'frontend' / 'lib' / 'auth.ts').read_text(encoding='utf-8')
    assert 'PASSWORD_MIN_LENGTH = 10' in source

    with pytest.raises(ValidationError):
        Credentials(email='short-password@example.test', password='ninechars')
