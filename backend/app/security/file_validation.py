"""
BUDDY AI 2.0 — File Validation, Security Guardrails & Secret Redaction

Architecture & Security Layers:
  - Path Traversal & Filesystem Sanitization:
      - Strips directory traversal vectors (../, null bytes, backslashes, leading hidden dots) from filenames.
      - Enforces strict resolved path prefixes to protect against Zip-Slip attacks during archive extraction.
  - Resource Protection & DoS Prevention:
      - Enforces strict upper thresholds on standalone uploads (50MB) and uncompressed archive expansion (100MB).
      - Computes streaming chunked SHA-256 hashes to verify document deduplication without unbounded memory usage.
  - Automated Secret Redaction:
      - Scans file contents and source code for credential leaks (Google Gemini keys, Groq API keys, OpenAI keys,
        generic bearer tokens, passwords, and RSA/EC private keys) and masks them before storage or indexing.
  - Anti-Prompt-Injection Safeguards:
      - Scans untrusted uploaded documents and user inputs for instruction override patterns (e.g. 'ignore previous instructions',
        'system override', 'disregard system prompt') to prevent indirect prompt injection vulnerabilities.
"""

import os
import re
import hashlib
from pathlib import Path
from typing import Tuple, List, Optional
from fastapi import HTTPException


# Maximum file size (50MB default)
MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024
# Maximum decompressed archive size (100MB)
MAX_ARCHIVE_EXPAND_BYTES = 100 * 1024 * 1024
# Maximum files inside archive
MAX_ARCHIVE_FILE_COUNT = 100


SECRET_PATTERNS = [
    (re.compile(r'(?i)(api[_-]?key|apikey|secret[_-]?key|access[_-]?key)\s*[:=]\s*["\']?([a-zA-Z0-9_\-\.]{16,})["\']?'), r'\1="[REDACTED_SECRET]"'),
    (re.compile(r'(?i)(bearer\s+)([a-zA-Z0-9_\-\.]{20,})'), r'\1[REDACTED_TOKEN]'),
    (re.compile(r'(?i)(password|passwd|pwd)\s*[:=]\s*["\']?([^\s"\']{6,})["\']?'), r'\1="[REDACTED_PASSWORD]"'),
    (re.compile(r'(AIzaSy[a-zA-Z0-9_\-]{33})'), r'[REDACTED_GOOGLE_API_KEY]'),
    (re.compile(r'(gsk_[a-zA-Z0-9]{32,})'), r'[REDACTED_GROQ_KEY]'),
    (re.compile(r'(sk-[a-zA-Z0-9]{32,})'), r'[REDACTED_API_KEY]'),
    (re.compile(r'-----BEGIN (?:RSA |EC )?PRIVATE KEY-----[\s\S]*?-----END (?:RSA |EC )?PRIVATE KEY-----'), r'[REDACTED_PRIVATE_KEY]'),
]

INJECTION_PATTERNS = [
    re.compile(r'(?i)ignore\s+(all\s+)?(previous|prior|above)\s+instructions'),
    re.compile(r'(?i)you\s+are\s+now\s+a(n)?\s+(unrestricted|different|new)\s+ai'),
    re.compile(r'(?i)disregard\s+(the\s+)?system\s+prompt'),
    re.compile(r'(?i)system\s+override\s*:\s*execute'),
]


def calculate_file_hash(data_or_path: bytes | Path | str) -> str:
    """
    Computes a deterministic SHA-256 cryptographic hash of a file path or raw bytes buffer.

    Args:
        data_or_path: File path on disk or raw bytes payload.

    Returns:
        str: Lowercase 64-character hexadecimal SHA-256 digest string.
    """
    sha256 = hashlib.sha256()
    if isinstance(data_or_path, (Path, str)):
        with open(data_or_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                sha256.update(chunk)
    else:
        sha256.update(data_or_path)
    return sha256.hexdigest()


def sanitize_filename(filename: str) -> str:
    """
    Sanitizes and normalizes an uploaded file's basename to prevent directory traversal
    and filesystem exploits. Strips null bytes, backslashes, path delimiters, and leading dots.

    Args:
        filename: Untrusted original filename from client upload headers.

    Returns:
        str: Cleaned, filesystem-safe alphanumeric filename.
    """
    base = os.path.basename(filename).strip()
    safe_name = re.sub(r'[^a-zA-Z0-9_\.\-]', '_', base)
    if not safe_name or safe_name.startswith('.'):
        safe_name = f"upload_{safe_name.lstrip('.')}"
    return safe_name


def validate_file_size(filepath: Path, max_size_bytes: int = MAX_FILE_SIZE_BYTES):
    """
    Enforces maximum allowed file size on disk to protect against denial-of-service storage exhaustion.

    Args:
        filepath: Target file on disk to evaluate.
        max_size_bytes: Maximum allowed size in bytes (default: 50MB).

    Raises:
        HTTPException(400): If the file does not exist on disk.
        HTTPException(413): If file size exceeds the configured ceiling.
    """
    if not filepath.exists():
        raise HTTPException(status_code=400, detail="Uploaded file does not exist.")
    size = filepath.stat().st_size
    if size > max_size_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File size ({round(size / (1024*1024), 2)}MB) exceeds maximum limit of {max_size_bytes // (1024*1024)}MB."
        )


def is_safe_archive_path(base_dir: Path, target_path: Path) -> bool:
    """
    Protects against Zip-Slip vulnerabilities by verifying that the resolved target extraction
    path resides strictly inside the intended destination directory.

    Args:
        base_dir: Intended extraction root directory.
        target_path: Proposed destination path for an extracted archive entry.

    Returns:
        bool: True if safe, False if traversal outside base_dir is attempted.
    """
    try:
        resolved_base = base_dir.resolve()
        resolved_target = target_path.resolve()
        return str(resolved_target).startswith(str(resolved_base))
    except Exception:
        return False


def redact_secrets(text: str) -> Tuple[str, List[str]]:
    """
    Scans plain text or code passages for credential patterns (API keys, bearer tokens, passwords)
    and replaces matching sensitive fragments with redacted placeholders.

    Args:
        text: Raw textual passage or document snippet.

    Returns:
        Tuple[str, List[str]]: Tuple of (redacted_text, list_of_warning_messages).
    """
    warnings: List[str] = []
    redacted_text = text
    for pattern, replacement in SECRET_PATTERNS:
        if pattern.search(redacted_text):
            warnings.append(f"Potential secret detected and redacted matching {pattern.pattern[:30]}...")
            redacted_text = pattern.sub(replacement, redacted_text)
    return redacted_text, warnings


def check_prompt_injection(text: str) -> Tuple[bool, Optional[str]]:
    """
    Inspects document text or user input for adversarial prompt-override patterns.

    Args:
        text: Untrusted plain text passage.

    Returns:
        Tuple[bool, Optional[str]]: Tuple of (is_injection_detected, reason_message_or_None).
    """
    for pattern in INJECTION_PATTERNS:
        match = pattern.search(text)
        if match:
            return True, f"Suspicious prompt-override instruction detected: '{match.group(0)}'"
    return False, None

