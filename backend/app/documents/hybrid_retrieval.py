"""
BUDDY AI 2.0 — Persistent Hybrid Retrieval Engine

Architecture & Retrieval Pipeline:
  - 3-Way Tri-Brid Retrieval Engine:
      1. Authoritative Structured SQL: Direct parameterized queries against SQLite tables
         (approved events, faculty directories, engineering branches, and institutional heritage).
      2. SQLite FTS5 Keyword Search: BM25-ranked full-text search indexing ingested documents and prospectus chunks.
      3. Dense Semantic Vector Search: ChromaDB vector store matching embeddings for contextual paraphrasing.
  - Reciprocal Rank Fusion (RRF) & Scoring:
      - Combines rank signals using standard RRF formula `score = 1.0 / (60 + rank)`.
      - Applies an authoritative priority boost (+2.0) to relational facts to ensure official college
        records supersede fuzzy document extracts and eliminate hallucinations.
  - Multi-Turn Deduplication & Citation Grounding:
      - Collates and deduplicates evidence passages across retrieval sources, packaging structured
        citations (`CitationModel`) for transparent UI verification.
"""

from typing import List, Dict, Any, Optional
from ..database.repository import repo
from ..database.models import CitationModel
from .vector_store import vector_store


def retrieve_structured_facts(query: str) -> List[Dict[str, Any]]:
    """
    Extracts authoritative verified records directly from SQLite tables based on query intent.

    Evaluation Categories:
      - College Events: Dates, venues, schedules, chief guests, and registration rules.
      - Faculty & Leadership: Names, designations, cabins, office hours, and fuzzy spelling matching.
      - Institutional Heritage: APCOER founding history, ABMSP parent trust (1907), motto, and DTE Code 6794.
      - Academic Branches: Engineering departments, HODs, floor locations, and course offerings.

    Args:
        query: Raw user utterance string.

    Returns:
        List[Dict[str, Any]]: List of authoritative fact passages formatted for RAG evidence synthesis.
    """
    facts = []
    q_lower = query.lower().strip()

    # Events check
    if any(k in q_lower for k in ["event", "robotics", "symposium", "gathering", "innovation"]):
        events = repo.get_upcoming_events()
        for e in events:
            if any(term in e["title"].lower() for term in q_lower.split() if len(term) > 3) or "event" in q_lower or "robotics" in q_lower:
                act_str = f" Activities: {e['activities']}." if e.get('activities') else ""
                guest_str = f" Chief Guest: {e['guests']}." if e.get('guests') else ""
                reg_str = f" Registration: {'Required' if e.get('registration_required') else 'Open'}."
                if e.get('registration_deadline'):
                    reg_str += f" Deadline: {e['registration_deadline']}."

                fact_text = (
                    f"Event '{e['title']}' is scheduled on {e['date']} at {e['venue']} (time: {e['time']}). "
                    f"Organizer: {e['organizer']}.{guest_str}{act_str}{reg_str} Description: {e['description']}"
                )
                facts.append({
                    "source": f"Database: Event '{e['title']}'",
                    "page": 1,
                    "section": "Approved College Events",
                    "content": fact_text,
                    "relevance_score": 1.0,
                    "is_authoritative": True,
                    "metadata": e
                })

    # Faculty check
    faculty_indicators = ["faculty", "professor", "professors", "principal", "vice principal", "director", "hod", "teacher", "teachers", "cabin", "dr.", "prof."]
    has_faculty_kw = any(k in q_lower for k in faculty_indicators)
    if has_faculty_kw or (("who is" in q_lower or "about" in q_lower or "tell me" in q_lower) and any(title in q_lower for title in ["prof", "dr", "mr", "mrs"])):
        import re
        import difflib
        FACULTY_STOPWORDS = {
            "who", "is", "the", "are", "tell", "about", "what", "where", "which",
            "professor", "professors", "faculty", "teacher", "teachers", "cabin", "cabins",
            "email", "emails", "contact", "phone", "office", "hours", "department", "dept",
            "apcoer", "college", "please", "know", "does", "belong", "to", "at", "in",
            "dr", "prof", "mr", "mrs", "miss", "and", "or", "for", "a", "an", "he", "she",
            "his", "her", "him", "principal", "director"
        }
        raw_tokens = [re.sub(r'[^a-zA-Z]', '', t).lower() for t in q_lower.split()]
        name_tokens = [t for t in raw_tokens if len(t) >= 3 and t not in FACULTY_STOPWORDS]

        all_faculty = repo.list_faculty()
        matched_faculty_ids = set()
        matched_faculty = []

        # 0. Check specific leadership roles (Principal, Vice Principal)
        if "principal" in q_lower and "vice" not in q_lower:
            for f in repo.get_faculty("principal"):
                if f["id"] not in matched_faculty_ids and "principal" in f["designation"].lower() and "vice" not in f["designation"].lower():
                    matched_faculty_ids.add(f["id"])
                    matched_faculty.append(f)
        elif "vice principal" in q_lower or "vice-principal" in q_lower:
            for f in repo.get_faculty("vice principal"):
                if f["id"] not in matched_faculty_ids:
                    matched_faculty_ids.add(f["id"])
                    matched_faculty.append(f)

        # 1. Direct matching on name or email
        for token in name_tokens:
            direct_matches = repo.get_faculty(token)
            for f in direct_matches:
                if f["id"] not in matched_faculty_ids:
                    if token in f["name"].lower() or token in f["email"].lower():
                        matched_faculty_ids.add(f["id"])
                        matched_faculty.append(f)

        # 2. Spelling variation & close-match fallback (e.g. 'Dorke' -> 'Dodke')
        if not matched_faculty and name_tokens:
            for f in all_faculty:
                full_name = f["name"].lower()
                surname = full_name.split()[-1] if full_name.split() else ""
                email_handle = f["email"].split("@")[0].lower() if f.get("email") else ""

                for token in name_tokens:
                    if surname and difflib.get_close_matches(token, [surname], cutoff=0.7):
                        if f["id"] not in matched_faculty_ids:
                            matched_faculty_ids.add(f["id"])
                            matched_faculty.append(f)
                    elif email_handle and difflib.get_close_matches(token, email_handle.split("."), cutoff=0.7):
                        if f["id"] not in matched_faculty_ids:
                            matched_faculty_ids.add(f["id"])
                            matched_faculty.append(f)

        if matched_faculty:
            for f in matched_faculty:
                fac_text = (
                    f"{f['name']} is {f['designation']} in the Department of {f['department']} at APCOER. "
                    f"Cabin location: {f['cabin']}. Email: {f['email']}. Office hours: {f['office_hours']}."
                )
                facts.append({
                    "source": f"Database: Faculty Directory ({f['name']})",
                    "page": 1,
                    "section": f"{f['department']} Faculty",
                    "content": fac_text,
                    "relevance_score": 1.0,
                    "is_authoritative": True
                })
        elif name_tokens and any(k in q_lower for k in ["professor", "prof", "dr", "faculty"]):
            search_name = " ".join([t.capitalize() for t in name_tokens])
            not_found_text = (
                f"No faculty member named '{search_name}' is found in the available APCOER faculty records. "
                f"If you know their department, please specify it to narrow the search."
            )
            facts.append({
                "source": "Database: APCOER Faculty Directory",
                "page": 1,
                "section": "Faculty Directory Verification",
                "content": not_found_text,
                "relevance_score": 1.0,
                "is_authoritative": True
            })

    # College Name, Founding Trust & Heritage check
    if any(k in q_lower for k in ["heritage", "founded", "founder", "trust", "abmsp", "motto", "history", "about college", "college name", "our college", "who established"]):
        heritage_text = (
            "Our college is Anantrao Pawar College of Engineering & Research (APCOER), Pune, established in 2012 by the "
            "Akhil Bharatiya Maratha Shikshan Parishad (A.B.M.S. Parishad). A.B.M.S. Parishad is an illustrious educational trust founded in 1907 "
            "with the guiding motto 'Bahujan Hitay, Bahujan Sukhaya' (For the welfare and happiness of the masses), carrying an enduring 117+ year "
            "heritage inspired by social reformers Rajarshi Chhatrapati Shahu Maharaj, Mahatma Jyotirao Phule, and Dr. Babasaheb Ambedkar. "
            "APCOER's 10-acre green campus is located at Parvati Hills, Pune - 411009, affiliated with Savitribai Phule Pune University (SPPU) and approved by AICTE (DTE Code: 6794)."
        )
        facts.append({
            "source": "Database: Institutional Heritage & College Profile",
            "page": 1,
            "section": "Founding Heritage & ABMSP Trust",
            "content": heritage_text,
            "relevance_score": 1.0,
            "is_authoritative": True
        })

    # Department and Branches check
    if any(k in q_lower for k in ["branch", "branches", "department", "departments", "course", "courses", "comp", "mech", "civil", "e&tc", "it", "aids", "mca", "fe"]):
        depts = repo.list_departments()
        # If user asks for all branches / departments offered
        if any(w in q_lower for w in ["which", "what", "all", "list", "how many", "offered", "available"]) and any(w in q_lower for w in ["branch", "branches", "department", "departments", "course", "courses", "engineering"]):
            dept_lines = [f"• {d['name']} ({d['code']}) - Headed by {d['hod']}" for d in depts]
            all_depts_text = (
                "Anantrao Pawar College of Engineering & Research (APCOER), Pune offers the following engineering and academic branches:\n"
                + "\n".join(dept_lines)
            )
            facts.append({
                "source": "Database: Official Engineering Branches & Academic Programs Directory",
                "page": 1,
                "section": "Approved Academic Branches",
                "content": all_depts_text,
                "relevance_score": 1.0,
                "is_authoritative": True
            })

        for d in depts:
            if d["name"].lower() in q_lower or d["code"].lower() in q_lower:
                dept_text = (
                    f"The {d['name']} ({d['code']}) is in {d['block']}, {d['floor']}. "
                    f"HOD is {d['hod']} ({d['contact_email']}). {d['description']}"
                )
                facts.append({
                    "source": f"Database: Department of {d['name']}",
                    "page": 1,
                    "section": "Departments",
                    "content": dept_text,
                    "relevance_score": 0.95,
                    "is_authoritative": True
                })

    return facts


def hybrid_search(
    query: str,
    top_k: int = 4,
    use_sql: bool = True,
    use_fts: bool = True,
    use_vector: bool = True
) -> List[Dict[str, Any]]:
    """
    Executes three-way hybrid retrieval combining structured SQL facts, FTS5 BM25 text rank,
    and ChromaDB vector embeddings using Reciprocal Rank Fusion (RRF).

    Scoring Logic:
      - SQL Structured Facts: Seed score `1.0 / (idx + 1) + 2.0` (authoritative boost).
      - SQLite FTS5 Keyword Hits: Increments fusion score by `(1.0 / (60 + idx)) * 1.5`.
      - Dense Semantic Vector Hits: Increments fusion score by `(1.0 / (60 + idx)) * 1.2`.

    Args:
        query: Search prompt or user question.
        top_k: Maximum number of ranked passages to return (default: 4).
        use_sql: Whether to query authoritative relational SQLite tables.
        use_fts: Whether to query SQLite FTS5 full-text index.
        use_vector: Whether to query ChromaDB dense vector store.

    Returns:
        List[Dict[str, Any]]: Top-K ranked passages sorted by descending fusion score.
    """
    candidates: Dict[str, Dict[str, Any]] = {}

    # 1. SQL Structured Query (Weight: highest for direct factual questions)
    if use_sql:
        sql_facts = retrieve_structured_facts(query)
        for idx, item in enumerate(sql_facts):
            key = f"sql_{item['source']}_{item['content'][:40]}"
            score = 1.0 / (idx + 1) + 2.0  # High authoritative boost
            candidates[key] = {**item, "fusion_score": score, "retrieval_method": "sql_structured"}

    # 2. SQLite FTS5 Keyword Search
    if use_fts:
        try:
            fts_results = repo.search_chunks_fts(query, limit=top_k * 2)
            for idx, r in enumerate(fts_results):
                key = f"chunk_{r.get('chunk_id') or r['document_name']}_{r['content'][:40]}"
                rrf_score = 1.0 / (60 + idx)
                if key in candidates:
                    candidates[key]["fusion_score"] += rrf_score * 1.5
                    candidates[key]["retrieval_method"] += "+fts5"
                else:
                    candidates[key] = {
                        "source": r["document_name"],
                        "page": r.get("page_number", 1),
                        "section": r.get("section_title", "General"),
                        "content": r["content"],
                        "relevance_score": round(abs(r.get("rank", 1.0)), 2),
                        "fusion_score": rrf_score,
                        "retrieval_method": "fts5"
                    }
        except Exception:
            pass

    # 3. Vector Similarity Search
    if use_vector:
        try:
            vector_results = vector_store.search(query, top_k=top_k * 2)
            for idx, vr in enumerate(vector_results):
                key = f"chunk_{vr.get('chunk_id') or vr['source']}_{vr['content'][:40]}"
                rrf_score = 1.0 / (60 + idx)
                if key in candidates:
                    candidates[key]["fusion_score"] += rrf_score * 1.2
                    candidates[key]["retrieval_method"] += "+vector"
                else:
                    candidates[key] = {
                        "source": vr["source"],
                        "page": vr.get("page", 1),
                        "section": vr.get("section", "General"),
                        "content": vr["content"],
                        "relevance_score": vr.get("similarity_score", 0.5),
                        "fusion_score": rrf_score,
                        "retrieval_method": "vector"
                    }
        except Exception:
            pass

    ranked = list(candidates.values())
    ranked.sort(key=lambda x: x["fusion_score"], reverse=True)
    return ranked[:top_k]


def build_citations(retrieval_results: List[Dict[str, Any]]) -> List[CitationModel]:
    """
    Constructs deduplicated structured citation instances from retrieved passages.
    Extracts document names, page numbers, sections, relevance scores, and concise text snippets.

    Args:
        retrieval_results: List of ranked candidate passages from hybrid search.

    Returns:
        List[CitationModel]: List of unique citation objects for UI display and audit verification.
    """
    citations: List[CitationModel] = []
    seen_sources = set()
    for res in retrieval_results:
        src = res["source"]
        if src in seen_sources:
            continue
        seen_sources.add(src)
        snippet = res["content"].strip()
        if len(snippet) > 180:
            snippet = snippet[:177] + "..."
        citations.append(CitationModel(
            source=src,
            page=res.get("page", 1),
            section=res.get("section"),
            relevance_score=res.get("relevance_score"),
            snippet=snippet
        ))
    return citations

