"""
BUDDY AI 2.0 — College Document Retrieval & Citation Assembly Service

Architecture & Retrieval Ladder:
  - Hybrid Orchestration:
      - Dispatches queries to hybrid_search (combining SQLite FTS5 BM25 and dense vector dot-product scoring).
  - Keyword Filtering & Lexical Overlap:
      - Filters natural language stopwords while preserving essential institutional keywords (APCOER, ABMSP, Pune).
  - Resilient Fallback:
      - Falls back to raw SQL LIKE chunk matching when search indexes are cold or unpopulated.
  - Strict Attribution:
      - Enforces zero-hallucination citation formatting with document names, page indices, and relevance scores.
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
    """
    Extracts non-stopword alphanumeric search terms from a natural language query.

    Args:
        query: User's raw question string.

    Returns:
        List[str]: Filtered list of search terms.
    """
    words = re.findall(r"\b[a-zA-Z0-9_\-\.]{3,}\b", query.lower())
    filtered = [w for w in words if w not in STOP_WORDS]
    if not filtered:
        filtered = [w for w in words if w in {"college", "campus", "pune", "apcoer", "abmsp"}]
    return filtered


def calculate_score(query_terms: List[str], text: str) -> float:
    """
    Calculates normalized keyword term frequency relevance score.

    Args:
        query_terms: List of extracted keywords.
        text: Candidate passage text.

    Returns:
        float: Term frequency score.
    """
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


def is_search_query_relevant(query: str, min_term_length: int = 3) -> bool:
    """
    Checks if an input query contains at least one substantive, non-stopword keyword.

    Args:
        query: Raw user query string.
        min_term_length: Minimum character length for candidate keywords (default: 3).

    Returns:
        bool: True if query contains substantive search terms, False otherwise.
    """
    if not query or not isinstance(query, str):
        return False
    terms = extract_keywords(query)
    return any(len(t) >= min_term_length for t in terms)


def calculate_retrieval_metrics(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Computes statistical telemetry across a set of retrieved passage results.

    Args:
        results: List of result dictionaries with 'relevance_score' and 'source' keys.

    Returns:
        Dict[str, Any]: Summary metrics including result_count, max_score, average_score, and distinct_sources.
    """
    if not results:
        return {
            "result_count": 0,
            "max_score": 0.0,
            "average_score": 0.0,
            "distinct_sources": []
        }

    scores = [r.get("relevance_score", 0.0) for r in results]
    sources = sorted(list(set(r.get("source", "unknown") for r in results)))

    return {
        "result_count": len(results),
        "max_score": round(max(scores), 3) if scores else 0.0,
        "average_score": round(sum(scores) / len(scores), 3) if scores else 0.0,
        "distinct_sources": sources
    }

