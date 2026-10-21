import pytest
from app.security.url_validation import is_safe_url
from app.security.authentication import authenticate_admin, verify_admin_token, ACTIVE_ADMIN_TOKENS
from app.tools.web_tools import search_internet
from app.config import settings
from fastapi import HTTPException


@pytest.mark.asyncio
async def test_disabled_web_search():
    # settings.WEB_SEARCH_ENABLED is False by default
    res = await search_internet("latest AI research")
    assert res["status"] == "disabled"
    assert "disabled in configuration" in res["message"]


def test_ssrf_url_validation():
    # Localhost and loopback
    safe, msg = is_safe_url("http://localhost:8000/internal")
    assert not safe
    assert "prohibited" in msg

    safe, msg = is_safe_url("http://127.0.0.1:11434")
    assert not safe
    assert "loopback" in msg or "prohibited" in msg

    # AWS/GCP metadata IP
    safe, msg = is_safe_url("http://169.254.169.254/latest/meta-data/")
    assert not safe
    assert "metadata" in msg or "link-local" in msg

    # Invalid scheme
    safe, msg = is_safe_url("file:///etc/passwd")
    assert not safe
    assert "Unsupported scheme" in msg


def test_admin_authentication():
    # Valid login
    token = authenticate_admin(settings.ADMIN_USERNAME, settings.ADMIN_PASSWORD)
    assert token is not None
    assert token in ACTIVE_ADMIN_TOKENS

    # Token verification passes
    assert verify_admin_token(f"Bearer {token}") is True

    # Invalid credentials
    with pytest.raises(HTTPException) as exc:
        authenticate_admin("wrong_user", "wrong_pass")
    assert exc.value.status_code == 401

    # Fake token
    with pytest.raises(HTTPException) as exc_fake:
        verify_admin_token("Bearer bad-fake-token-xyz")
    assert exc_fake.value.status_code == 403
