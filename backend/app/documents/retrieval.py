import re
from typing import List, Dict, Any, Optional
from ..database.repository import repo
from ..database.models import CitationModel


STOP_WORDS = {
    "a", "an", "the", "in", "on", "at", "to", "for", "of", "and", "or", "is",
    "are", "was", "were", "what", "where", "how", "who", "which", "do", "does",
    "can", "tell", "me", "about", "please", "college", "campus"
}


def extract_keywords(query: str) -> List[str]:
    """Extracts non-stopword alphanumeric search terms from query."""
    words = re.findall(r"\b[a-zA-Z0-9_\-\.]{3,}\b", query.lower())
    return [w for w in words if w not in STOP_WORDS]


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


def search_documents(query: str, top_k: int = 3, threshold: float = 0.3) -> List[Dict[str, Any]]:
    """
    Searches indexed college documents.
    Returns ranked passages with citations and page numbers.
    Never invents citations if no relevant passage exists.
    """
    terms = extract_keywords(query)
    if not terms:
        return []

    candidate_chunks = repo.search_chunks(terms, limit=15)
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

    # Sort descending by relevance score
    scored_results.sort(key=lambda x: x["relevance_score"], reverse=True)
    return scored_results[:top_k]


def format_citations(retrieval_results: List[Dict[str, Any]]) -> List[CitationModel]:
    """Converts retrieval results into CitationModel instances."""
    citations = []
    for res in retrieval_results:
        snippet = res["content"]
        if len(snippet) > 200:
            snippet = snippet[:197] + "..."
        citations.append(CitationModel(
            source=res["source"],
            page=res.get("page"),
            section=res.get("section"),
            relevance_score=res.get("relevance_score"),
            snippet=snippet
        ))
    return citations
