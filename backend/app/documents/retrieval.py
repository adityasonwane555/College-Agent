"""
BUDDY AI 2.0 — College Document Retrieval Service
Provides keyword extraction, relevance scoring, and hybrid search integration.
"""

import re
from typing import List, Dict, Any, Optional
from ..database.repository import repo
from ..database.models import CitationModel
from .hybrid_retrieval import hybrid_search, build_citations


STOP_WORDS = {
    "a", "an", "the", "in", "on", "at", "to", "for", "of", "and", "or", "is",
    "are", "was", "were", "what", "where", "how", "who", "which", "do", "does",
    "can", "tell", "me", "about", "please", "college", "campus"
}


def extract_keywords(query: str) -> List[str]:
    """Extracts non-stopword alphanumeric search terms from query."""
    words = re.findall(r"\b[a-zA-Z0-9_\-\.]{3,}\b", query.lower())
    filtered = [w for w in words if w not in STOP_WORDS]
    if not filtered:
        filtered = [w for w in words if w in {"college", "campus", "pune", "apcoer", "abmsp"}]
    return filtered


def calculate_score(query_terms: List[str], text: str) -> float:
    """Calculates keyword overlap relevance score."""
    if not query_terms:
        return 0.0
    text_lower = text.lower()
    matches = 0
    for term in query_terms:
        if term in text_lower:
            matches += 1 + text_lower.count(term) * 0.2
    return round(matches / len(query_terms), 2)


def search_documents(query: str, top_k: int = 3, threshold: float = 0.25) -> List[Dict[str, Any]]:
    """
    Searches indexed college documents using hybrid retrieval (SQL + FTS5 + Vector).
    Falls back to keyword chunk search if hybrid results are empty.
    Returns ranked passages with citations and page numbers.
    Never invents citations if no relevant passage exists.
    """
    # Try hybrid search first
    hybrid_res = hybrid_search(query, top_k=top_k, use_sql=False, use_fts=True, use_vector=True)
    if hybrid_res:
        formatted_hybrid = []
        for r in hybrid_res:
            formatted_hybrid.append({
                "source": r["source"],
                "page": r.get("page", 1),
                "section": r.get("section", "General"),
                "relevance_score": r.get("relevance_score", 0.8),
                "content": r["content"]
            })
        return formatted_hybrid[:top_k]

    # Keyword fallback
    terms = extract_keywords(query)
    if not terms:
        return []

    candidate_chunks = repo.search_chunks(terms, limit=50)
    scored_results = []

    for chunk in candidate_chunks:
        score = calculate_score(terms, chunk["content"])
        if score >= threshold:
            scored_results.append({
                "source": chunk["document_name"],
                "page": chunk["page_number"],
                "section": chunk["section_title"],
                "relevance_score": score,
                "content": chunk["content"]
            })

    scored_results.sort(key=lambda x: x["relevance_score"], reverse=True)
    return scored_results[:top_k]


def format_citations(retrieval_results: List[Dict[str, Any]]) -> List[CitationModel]:
    """Converts retrieval results into CitationModel instances."""
    return build_citations(retrieval_results)
