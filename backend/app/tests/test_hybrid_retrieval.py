"""
BUDDY AI 2.0 — Hybrid Retrieval & Fusion Tests
Verifies that SQL structured queries, FTS5 full-text keyword search,
and local vector similarity combine effectively via Reciprocal Rank Fusion.
"""

from app.documents.hybrid_retrieval import retrieve_structured_facts, hybrid_search, build_citations
from app.documents.vector_store import LocalMultilingualVectorizer
import numpy as np


def test_structured_facts_retrieval():
    facts = retrieve_structured_facts("When is the robotics event?")
    assert len(facts) >= 1
    assert "APCOER Robotics Innovation Day 2026" in facts[0]["content"]
    assert facts[0]["is_authoritative"] is True


def test_multilingual_vectorizer_similarity():
    vectorizer = LocalMultilingualVectorizer()

    # English semantic proximity
    v_comp1 = np.array(vectorizer.embed_text("Computer Engineering Department Labs"), dtype=np.float32)
    v_comp2 = np.array(vectorizer.embed_text("Computers and coding laboratory in college"), dtype=np.float32)
    v_food = np.array(vectorizer.embed_text("Cafeteria food menu snacks"), dtype=np.float32)

    sim_comp = float(np.dot(v_comp1, v_comp2))
    sim_food = float(np.dot(v_comp1, v_food))
    assert sim_comp > sim_food

    # Marathi (Devanagari) vectorization
    v_marathi1 = np.array(vectorizer.embed_text("अभियांत्रिकी महाविद्यालय प्रवेश"), dtype=np.float32)
    v_marathi2 = np.array(vectorizer.embed_text("महाविद्यालयीन शिक्षण"), dtype=np.float32)
    assert np.linalg.norm(v_marathi1) > 0.99
    assert float(np.dot(v_marathi1, v_marathi2)) > 0.0


def test_hybrid_search_fusion():
    results = hybrid_search("Robotics Innovation Day Main Auditorium", top_k=3)
    assert len(results) >= 1
    citations = build_citations(results)
    assert len(citations) >= 1
    assert citations[0].source is not None
    assert citations[0].snippet is not None

