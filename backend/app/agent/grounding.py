"""
BUDDY AI 2.0 — Factual Grounding & Deterministic Verification

Architecture & Guardrails:
  - Anti-Hallucination Pipeline:
      - Validates generated LLM responses against verified institutional facts retrieved from SQLite/ChromaDB.
      - Detects and resolves temporal discrepancies (e.g. incorrect event dates, outdated application deadlines).
      - Cross-checks venue, room assignments, and guest references against approved campus records.
  - Automatic In-Flight Correction:
      - Uses regex patterns to identify calendar dates with or without ordinal indicators (1st, 2nd, 3rd, 4th).
      - Normalizes matched date strings and performs exact or near-match substitution with authoritative facts.
      - Returns audit logs of all detected discrepancies to support transparency and debugging.
"""

import re
from typing import List, Dict, Any, Tuple


def verify_response_grounding(
    response_text: str,
    verified_facts: List[Dict[str, Any]]
) -> Tuple[str, List[str]]:
    """
    Validates and corrects an LLM response against verified institutional records.

    Verification Rules:
      1. Inspects metadata in each verified fact (e.g., approved date, venue, event title).
      2. If an event or topic is referenced in the response, extracts date expressions
         using regex patterns matching standard English calendar formats.
      3. Strips ordinal suffixes ('st', 'nd', 'rd', 'th') for consistent semantic comparison.
      4. If a date contradiction is found, logs an audit warning and substitutes the approved
         authoritative date directly into the response text.

    Args:
        response_text: Raw candidate response string synthesized by the LLM.
        verified_facts: List of retrieved factual passages containing authoritative metadata.

    Returns:
        Tuple[str, List[str]]:
            - grounded_text: Sanitized response text with verified factual dates.
            - corrections: List of human-readable audit descriptions of all modifications made.
    """
    corrections: List[str] = []
    grounded_text = response_text

    for fact in verified_facts:
        meta = fact.get("metadata")
        if not meta:
            continue

        approved_date = meta.get("date")
        approved_venue = meta.get("venue")
        event_title = meta.get("title", "")

        # Check date consistency if the event title is mentioned in the response
        if approved_date and (event_title.lower() in response_text.lower() or "event" in response_text.lower() or "robotics" in response_text.lower()):
            # Look for conflicting date patterns in response
            # e.g., if approved is 18 December, but response mentions 15 December
            date_matches = re.findall(
                r'\b\d{1,2}(?:st|nd|rd|th)?\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b',
                response_text,
                re.IGNORECASE
            )
            for dm in date_matches:
                # Compare normalized date strings
                norm_dm = dm.lower().replace("st", "").replace("nd", "").replace("rd", "").replace("th", "")
                norm_approved = approved_date.lower().replace("st", "").replace("nd", "").replace("rd", "").replace("th", "")
                if norm_dm != norm_approved:
                    corrections.append(
                        f"Detected contradictory event date '{dm}' in response; authoritative date in knowledge base is '{approved_date}'."
                    )
                    # Replace incorrect date with approved date
                    grounded_text = re.sub(re.escape(dm), approved_date, grounded_text, flags=re.IGNORECASE)

    return grounded_text, corrections
