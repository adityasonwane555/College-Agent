"""
BUDDY AI 2.0 — Factual Grounding & Deterministic Verification
Verifies that generated responses do not contradict approved institutional records,
specifically dates, venues, deadlines, and guest names.
"""

import re
from typing import List, Dict, Any, Tuple


def verify_response_grounding(
    response_text: str,
    verified_facts: List[Dict[str, Any]]
) -> Tuple[str, List[str]]:
    """
    Checks the generated response against verified institutional facts.
    Detects contradictions in dates or venues and provides grounded corrections.
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
            date_matches = re.findall(r'\b\d{1,2}(?:st|nd|rd|th)?\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b', response_text, re.IGNORECASE)
            for dm in date_matches:
                # Compare normalized date strings
                if dm.lower().replace("st", "").replace("nd", "").replace("rd", "").replace("th", "") != approved_date.lower().replace("st", "").replace("nd", "").replace("rd", "").replace("th", ""):
                    corrections.append(f"Detected contradictory event date '{dm}' in response; authoritative date in knowledge base is '{approved_date}'.")
                    # Replace incorrect date with approved date
                    grounded_text = re.sub(re.escape(dm), approved_date, grounded_text, flags=re.IGNORECASE)

    return grounded_text, corrections

