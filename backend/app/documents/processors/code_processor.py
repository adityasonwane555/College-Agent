"""
Processor for Source Code and Technical Files.
Treats code strictly as reference material; NEVER executes code.
Redacts credentials, parses docstrings and function/class signatures.
"""

import re
import time
from pathlib import Path
from typing import List, Dict, Any
from .base import BaseProcessor
from .text_processor import chunk_document_text
from ..common import ExtractedDocument, ExtractedChunk, DocumentType, IngestionStatus
from ...security.file_validation import calculate_file_hash, redact_secrets, check_prompt_injection


LANGUAGE_MAP = {
    "py": "python",
    "js": "javascript",
    "ts": "typescript",
    "tsx": "typescript_react",
    "jsx": "javascript_react",
    "java": "java",
    "cpp": "cpp",
    "c": "c",
    "h": "c_header",
    "ino": "arduino",
    "css": "css",
    "sql": "sql",
    "sh": "shell",
    "ps1": "powershell",
    "toml": "toml",
    "ini": "ini",
    "env.example": "config_example"
}


class CodeProcessor(BaseProcessor):
    @property
    def supported_extensions(self) -> List[str]:
        return list(LANGUAGE_MAP.keys())

    @property
    def document_type(self) -> DocumentType:
        return DocumentType.CODE

    def extract(self, filepath: Path, **kwargs) -> ExtractedDocument:
        start_t = time.time()
        file_hash = calculate_file_hash(filepath)
        filename = filepath.name
        ext = filepath.suffix.lower().lstrip(".")
        language = LANGUAGE_MAP.get(ext, "source_code")
        warnings: List[str] = []

        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            raw_code = f.read()

        redacted_code, sec_w = redact_secrets(raw_code)
        warnings.extend(sec_w)

        has_inj, inj_msg = check_prompt_injection(redacted_code)
        if has_inj and inj_msg:
            warnings.append(inj_msg)

        # Extract top-level symbols / definitions for quick reference
        symbols = []
        for line in redacted_code.splitlines():
            line_str = line.strip()
            if line_str.startswith("def ") or line_str.startswith("class ") or line_str.startswith("function ") or line_str.startswith("const "):
                symbols.append(line_str[:80])

        formatted_text = f"Language: {language}\nFilename: {filename}\n\n"
        if symbols:
            formatted_text += f"Key Symbols:\n" + "\n".join(symbols[:20]) + "\n\nSource Code:\n"
        formatted_text += redacted_code

        chunks = chunk_document_text(formatted_text, page_number=1, default_section=f"{language.capitalize()} Reference")
        for idx, ch in enumerate(chunks):
            ch.chunk_index = idx

        duration = time.time() - start_t

        return ExtractedDocument(
            filename=filename,
            file_hash=file_hash,
            detected_file_type=DocumentType.CODE,
            content_type=f"text/x-{language}",
            title=filename,
            extracted_text=redacted_code,
            structured_content={"language": language, "symbol_count": len(symbols), "key_symbols": symbols[:20]},
            chunks=chunks,
            source_metadata={"language": language, "file_size": filepath.stat().st_size, "line_count": len(redacted_code.splitlines())},
            extraction_method="source_code_reference_extractor",
            status=IngestionStatus.PROCESSING,
            warnings=list(set(warnings)),
            processing_duration_seconds=round(duration, 3)
        )

