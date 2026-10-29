"""
Processor for Tabular Data: CSV, TSV, and XLSX workbooks.
Preserves header-to-value relationships and sheet metadata.
"""

import csv
import time
from pathlib import Path
from typing import List, Dict, Any
from .base import BaseProcessor
from ..common import ExtractedDocument, ExtractedChunk, DocumentType, IngestionStatus
from ...security.file_validation import calculate_file_hash, redact_secrets, check_prompt_injection

try:
    import openpyxl
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False


class SpreadsheetProcessor(BaseProcessor):
    @property
    def supported_extensions(self) -> List[str]:
        return ["csv", "tsv", "xlsx", "xls"]

    @property
    def document_type(self) -> DocumentType:
        return DocumentType.CSV

    def _extract_csv(self, filepath: Path, delimiter: str = ",") -> tuple[str, List[Dict[str, Any]], List[ExtractedChunk]]:
        sheets_data: Dict[str, Any] = {}
        rows_list: List[Dict[str, Any]] = []
        chunks: List[ExtractedChunk] = []
        text_lines: List[str] = []

        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.reader(f, delimiter=delimiter)
            all_rows = [row for row in reader if any(cell.strip() for cell in row)]

        if not all_rows:
            return "", [], []

        headers = [h.strip() for h in all_rows[0]]
        text_lines.append(f"Headers: {', '.join(headers)}")

        for row_idx, row in enumerate(all_rows[1:], start=1):
            row_dict: Dict[str, Any] = {}
            row_desc_parts: List[str] = []
            for col_idx, cell in enumerate(row):
                header = headers[col_idx] if col_idx < len(headers) and headers[col_idx] else f"Column_{col_idx+1}"
                val = cell.strip()
                row_dict[header] = val
                if val:
                    row_desc_parts.append(f"{header}: {val}")

            rows_list.append(row_dict)
            if row_desc_parts:
                row_text = f"Record #{row_idx}: " + "; ".join(row_desc_parts)
                text_lines.append(row_text)
                chunks.append(ExtractedChunk(
                    chunk_index=row_idx - 1,
                    page_number=1,
                    section_title=f"Record {row_idx}",
                    content=row_text,
                    metadata={"row_index": row_idx, "headers": headers}
                ))

        full_text = "\n".join(text_lines)
        return full_text, rows_list, chunks

    def _extract_xlsx(self, filepath: Path) -> tuple[str, Dict[str, List[Dict[str, Any]]], List[ExtractedChunk]]:
        if not OPENPYXL_AVAILABLE:
            raise RuntimeError("openpyxl is not installed for Excel workbook extraction.")

        wb = openpyxl.load_workbook(str(filepath), data_only=True)
        sheets_dict: Dict[str, List[Dict[str, Any]]] = {}
        chunks: List[ExtractedChunk] = []
        full_text_parts: List[str] = []
        chunk_idx = 0

        for sheet_idx, sheet_name in enumerate(wb.sheetnames, start=1):
            ws = wb[sheet_name]
            all_rows = list(ws.iter_rows(values_only=True))
            if not all_rows:
                continue

            # Find first non-empty row as header
            header_row_idx = 0
            headers = []
            for r_i, r in enumerate(all_rows):
                if any(c is not None and str(c).strip() for c in r):
                    header_row_idx = r_i
                    headers = [str(c).strip() if c is not None else f"Column_{c_i+1}" for c_i, c in enumerate(r)]
                    break

            if not headers:
                continue

            sheet_records: List[Dict[str, Any]] = []
            sheet_text_lines = [f"=== Sheet: {sheet_name} ===", f"Headers: {', '.join(headers)}"]

            for r_idx, r in enumerate(all_rows[header_row_idx + 1:], start=1):
                if not any(c is not None and str(c).strip() for c in r):
                    continue
                record: Dict[str, Any] = {}
                record_parts: List[str] = []
                for c_idx, cell in enumerate(r):
                    h = headers[c_idx] if c_idx < len(headers) else f"Column_{c_idx+1}"
                    val = str(cell).strip() if cell is not None else ""
                    record[h] = val
                    if val:
                        record_parts.append(f"{h}: {val}")

                sheet_records.append(record)
                if record_parts:
                    line = f"[{sheet_name} Row {r_idx}] " + "; ".join(record_parts)
                    sheet_text_lines.append(line)
                    chunks.append(ExtractedChunk(
                        chunk_index=chunk_idx,
                        page_number=sheet_idx,
                        section_title=f"{sheet_name} Row {r_idx}",
                        content=line,
                        metadata={"sheet_name": sheet_name, "row_index": r_idx}
                    ))
                    chunk_idx += 1

            sheets_dict[sheet_name] = sheet_records
            full_text_parts.append("\n".join(sheet_text_lines))

        return "\n\n".join(full_text_parts), sheets_dict, chunks

    def extract(self, filepath: Path, **kwargs) -> ExtractedDocument:
        start_t = time.time()
        file_hash = calculate_file_hash(filepath)
        filename = filepath.name
        ext = filepath.suffix.lower().lstrip(".")
        warnings: List[str] = []

        is_xlsx = ext in ["xlsx", "xls"]
        doc_type = DocumentType.XLSX if is_xlsx else DocumentType.CSV

        if is_xlsx:
            if not OPENPYXL_AVAILABLE:
                return ExtractedDocument(
                    filename=filename,
                    file_hash=file_hash,
                    detected_file_type=DocumentType.XLSX,
                    content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    title=filename,
                    status=IngestionStatus.FAILED,
                    warnings=["openpyxl library is not installed"],
                    processing_duration_seconds=round(time.time() - start_t, 3)
                )
            full_text, structured_tables, chunks = self._extract_xlsx(filepath)
            structured_content = {"sheets": structured_tables}
        else:
            delim = "\t" if ext == "tsv" else ","
            full_text, rows_list, chunks = self._extract_csv(filepath, delimiter=delim)
            structured_content = {"records": rows_list}

        redacted_text, sec_w = redact_secrets(full_text)
        warnings.extend(sec_w)

        duration = time.time() - start_t
        title = filename.replace("_", " ").rsplit(".", 1)[0]

        return ExtractedDocument(
            filename=filename,
            file_hash=file_hash,
            detected_file_type=doc_type,
            content_type="text/csv" if not is_xlsx else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            title=title,
            extracted_text=redacted_text,
            structured_content=structured_content,
            chunks=chunks,
            source_metadata={"file_size": filepath.stat().st_size, "record_count": len(chunks)},
            extraction_method="spreadsheet_extractor",
            status=IngestionStatus.PROCESSING,
            warnings=list(set(warnings)),
            processing_duration_seconds=round(duration, 3)
        )

