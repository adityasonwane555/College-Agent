"""
BUDDY AI 2.0 — College Knowledge & Directory Toolset

Architecture & Orchestration:
  - Tool Invocation Dispatcher:
      - Provides structured tool execution functions invoked by the Agent Orchestrator and Unified Provider
        when answering student, visitor, and administrative campus queries.
  - Authoritative Relational Grounding:
      - Directly queries SQLite tables for deterministic entity data (departments, rooms, faculty, events,
        announcements, campus hours, and FAQs), eliminating hallucination on verified college facts.
  - Structured Retrieval & Attribution:
      - Integrates hybrid semantic document search with verified source attribution, page references, and section metadata.
  - Human-Readable & LLM-Friendly Formatting:
      - Serializes query results into conversational strings optimized for direct model synthesis and speech output.
"""

from typing import Dict, Any, List
from ..database.repository import repo
from ..documents.retrieval import search_documents


def search_faq(query: str) -> str:
    """
    Searches curated, official college frequently asked questions in the database.

    Args:
        query: Search keywords or question phrase from the user.

    Returns:
        str: Formatted list of matching Q&A entries, or a fallback notice if none found.
    """
    results = repo.search_faq(query)
    if not results:
        return f"No official FAQs found matching query: '{query}'."
    formatted = []
    for r in results:
        formatted.append(f"Q: {r['question']}\nA: {r['answer']}\nCategory: {r['category']}")
    return "\n\n".join(formatted)


def get_department(name: str) -> str:
    """
    Retrieves detailed directory information for an academic or administrative department by name or code.

    Args:
        name: Name (e.g. 'Computer Engineering') or short code (e.g. 'COMP').

    Returns:
        str: Department location, block, floor, HOD name, contact email, and academic overview.
    """
    dept = repo.get_department(name)
    if not dept:
        return f"Department '{name}' was not found in the official college directory."
    return (
        f"The {dept['name']} (code {dept['code']}) is located on the {dept['floor']} of {dept['block']}. "
        f"The Head of Department is {dept['hod']}, and can be contacted at {dept['contact_email']}. "
        f"Department overview: {dept['description']}"
    )


def get_room(room_name: str) -> str:
    """
    Finds physical location, building block, floor, and purpose for a classroom, lab, auditorium, or office.

    Args:
        room_name: Name or room number (e.g. 'Lab 301', 'Auditorium', 'Principal Office').

    Returns:
        str: Room title, room number, building, floor, and operational purpose.
    """
    room = repo.get_room(room_name)
    if not room:
        return f"Room or facility '{room_name}' was not found in the campus location directory."
    return (
        f"{room['name']} (room number {room['room_number']}) is located on the {room['floor']} of {room['building']}. "
        f"Purpose and activities: {room['purpose']}."
    )


def get_faculty(name: str) -> str:
    """
    Looks up faculty profiles including designation, department, cabin location, qualifications,
    teaching experience, research interests, and office consultation hours.

    Args:
        name: Full or partial name of the faculty member or department role.

    Returns:
        str: Comprehensive biography, academic credentials, office hours, and contact details.
    """
    members = repo.get_faculty(name)
    if not members:
        return f"No faculty member matching '{name}' was found in the official faculty directory."
    formatted = []
    for f in members:
        details = [f"{f['name']} serves as {f['designation']} in {f['department']}."]
        if f.get('qualification'):
            details.append(f"Qualification: {f['qualification']}.")
        if f.get('experience'):
            details.append(f"Teaching/Experience: {f['experience']}.")
        if f.get('area_of_interest'):
            details.append(f"Area of Interest: {f['area_of_interest']}.")
        details.append(f"Their office or lab is located in {f['cabin']}.")
        details.append(f"Office consulting hours are {f['office_hours']}, and email ID is {f['email']}.")
        if f.get('research_profile'):
            details.append(f"Research profile: {f['research_profile']}.")
        formatted.append(" ".join(details))
    return " ".join(formatted)


def get_college_hours() -> str:
    """
    Retrieves official operating hours and weekly schedules for campus facilities, libraries,
    administrative offices, and laboratories.

    Returns:
        str: Formatted facility schedules with opening times, closing times, and operational days.
    """
    hours = repo.get_college_hours()
    if not hours:
        return "Operating hours are not currently recorded in the college database."
    formatted = []
    for h in hours:
        note_str = f" ({h['notes']})" if h.get('notes') else ""
        formatted.append(
            f"{h['facility_name']} is open from {h['open_time']} to {h['close_time']} on {h['days']}{note_str}."
        )
    return " ".join(formatted)


def get_upcoming_events() -> str:
    """
    Retrieves the verified calendar of upcoming college seminars, workshops, technical symposiums,
    cultural fests, and campus placement drives.

    Returns:
        str: Formatted event summaries with dates, venues, organizers, guest speakers, and registration details.
    """
    events = repo.get_upcoming_events()
    if not events:
        return "There are no upcoming college events scheduled at this moment."
    formatted = []
    for e in events:
        details_list = [f"The event '{e['title']}' organized by {e['organizer']} takes place on {e['date']} at {e['time']} in {e['venue']}."]
        if e.get("guests"):
            details_list.append(f"Chief Guest / Speakers: {e['guests']}.")
        if e.get("activities"):
            details_list.append(f"Scheduled activities: {e['activities']}.")
        if e.get("registration_required"):
            reg_text = "Registration is required."
            if e.get("registration_deadline"):
                reg_text += f" Registration deadline: {e['registration_deadline']}."
            details_list.append(reg_text)
        details_list.append(f"Description: {e['description']}.")
        formatted.append(" ".join(details_list))
    return " ".join(formatted)


def get_announcements() -> str:
    """
    Retrieves the latest official administrative circulars, examination notices, and campus broadcasts.

    Returns:
        str: Chronologically sorted notices with title, posting date, priority level, and body content.
    """
    notices = repo.get_announcements()
    if not notices:
        return "There are no new college announcements posted right now."
    formatted = []
    for n in notices:
        formatted.append(
            f"Notice titled '{n['title']}' posted on {n['date_posted']} with priority {n['priority']}: {n['content']}."
        )
    return " ".join(formatted)


def search_college_documents(query: str) -> Dict[str, Any]:
    """
    Searches indexed college documents (prospectus, syllabi, student guides, academic handbooks)
    using hybrid search and generates verifiable citation passages.

    Args:
        query: Search query or topic keywords.

    Returns:
        Dict[str, Any]: Search outcome dictionary containing formatted passages and citation objects.
    """
    results = search_documents(query, top_k=3)
    if not results:
        return {
            "status": "not_found",
            "message": f"Could not find a reliable answer for '{query}' in the indexed college documents.",
            "citations": []
        }
    
    formatted_texts = []
    citations = []
    for r in results:
        citations.append({
            "source": r["source"],
            "page": r["page"],
            "section": r["section"],
            "snippet": r["content"][:200]
        })
        formatted_texts.append(
            f"[Source: {r['source']} | Page {r['page']} | Section: {r['section']}]\n{r['content']}"
        )

    return {
        "status": "found",
        "passages": "\n\n".join(formatted_texts),
        "citations": citations
    }
