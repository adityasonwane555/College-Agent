import re
from typing import Optional, Dict, Any, List
from ..database.repository import repo
from ..database.models import CitationModel


def resolve_fast_path(user_query: str) -> Optional[Dict[str, Any]]:
    """
    Evaluates incoming query for high-frequency reception desk intents.
    Returns immediate, human-sounding dialogue responses with citations in <10ms,
    avoiding robotic bullet points or chatbot data dumps.
    """
    q = user_query.strip().lower()
    clean = re.sub(r'[^a-z0-9\s]', '', q)

    # 1. Greetings & Persona identity
    greeting_tokens = ["hi", "hello", "hey", "greetings", "good morning", "good afternoon", "good evening"]
    if clean in greeting_tokens or clean in ["who are you", "what is your name", "what are you", "tell me about yourself", "what can you do"]:
        return {
            "response": (
                "Hello there! I'm Buddy, your campus reception assistant. "
                "I'm here to help you find faculty offices, classrooms, check college timings, "
                "or look up admissions and events. How can I help you today?"
            ),
            "citations": []
        }

    # 2. Faculty / HOD queries
    if any(k in clean for k in ["hod", "head of department", "head of", "faculty", "professor", "cabin", "arvind", "patil", "nair", "deshmukh", "kapoor"]):
        # Computer Science
        if "computer" in clean or "cs" in clean or "arvind" in clean:
            fac_list = repo.get_faculty("Arvind Sharma")
            faculty = fac_list[0] if fac_list else None
            dept = repo.get_department("Computer Science")
            if faculty and dept:
                citations = [
                    CitationModel(source="Faculty Directory", page=1, section="Computer Science", snippet=f"Dr. Arvind Sharma - HOD, Cabin {faculty.get('cabin', 'N/A')}")
                ]
                text = (
                    f"The Head of Computer Science is Dr. Arvind Sharma! "
                    f"His office is in Cabin {faculty.get('cabin', '301')}, up on the {dept.get('floor', 'third floor').lower()} of the {dept.get('block', 'Academic Block')}. "
                    f"He usually holds office hours from 10:00 AM to noon on weekdays, or you can drop him an email at {faculty.get('email', '')}. "
                    "Would you like me to point you toward the elevators?"
                )
                return {"response": text, "citations": citations}

        # Mechanical
        if "mechanical" in clean or "patil" in clean:
            fac_list = repo.get_faculty("Sneha Patil")
            faculty = fac_list[0] if fac_list else None
            dept = repo.get_department("Mechanical Engineering")
            if faculty and dept:
                citations = [
                    CitationModel(source="Faculty Directory", page=2, section="Mechanical Engineering", snippet=f"Dr. Sneha Patil - HOD, Cabin {faculty.get('cabin', 'N/A')}")
                ]
                text = (
                    f"The Head of Mechanical Engineering is Dr. Sneha Patil! "
                    f"Her office is in Cabin {faculty.get('cabin', '202')}, located on the {dept.get('floor', 'second floor').lower()} of the {dept.get('block', 'Workshop Block')}. "
                    f"She is available for student consultations from 2:00 PM to 4:00 PM, or you can reach her by email at {faculty.get('email', '')}. "
                    "Let me know if you need directions to the workshop area!"
                )
                return {"response": text, "citations": citations}

        # Electronics
        if "electronics" in clean or "nair" in clean:
            fac_list = repo.get_faculty("Rajeshwari Nair")
            faculty = fac_list[0] if fac_list else None
            dept = repo.get_department("Electronics & Telecommunication")
            if faculty and dept:
                citations = [
                    CitationModel(source="Faculty Directory", page=3, section="ENTC", snippet=f"Dr. Rajeshwari Nair - HOD, Cabin {faculty.get('cabin', 'N/A')}")
                ]
                text = (
                    f"The Head of Electronics and Telecommunication is Dr. Rajeshwari Nair. "
                    f"You can find her in Cabin {faculty.get('cabin', '204')}, on the {dept.get('floor', 'second floor').lower()} of the {dept.get('block', 'ENTC Block')}. "
                    f"Her office hours are from 11:00 AM to 1:00 PM, or you can reach her at {faculty.get('email', '')}. "
                    "Feel free to ask if you'd like directions!"
                )
                return {"response": text, "citations": citations}

    # 3. College Hours / Timing queries
    if any(k in clean for k in ["hours", "timings", "timing", "open", "close", "when does", "what time"]):
        hours_list = repo.get_college_hours()
        if hours_list:
            citations = [
                CitationModel(source="Campus Facilities Guide", page=1, section="Operating Hours", snippet="Central College & Facility Hours")
            ]
            text = (
                "Our college campus is open Monday through Saturday from 8:00 AM to 6:00 PM. "
                "If you're visiting the Central Library, it stays open late until 8:00 PM for study sessions, "
                "and the Administrative and Registrar offices are open from 9:30 AM to 5:00 PM. "
                "Is there a specific office or facility you're planning to visit today?"
            )
            return {"response": text, "citations": citations}

    # 4. Room / Location queries
    if any(k in clean for k in ["where is", "room", "lab", "auditorium", "library", "locate", "directions"]):
        if "auditorium" in clean:
            room = repo.get_room("Main Auditorium") or repo.get_room("Auditorium")
            if room:
                return {
                    "response": (
                        f"The {room.get('name')} is located on the {room.get('floor', 'ground floor').lower()} of the {room.get('building', 'Central Auditorium Building')}, "
                        "just past the central campus courtyard. It's where all our university seminars, workshops, and guest lectures take place!"
                    ),
                    "citations": [CitationModel(source="Campus Map", page=1, section="Venues", snippet=f"{room.get('name')}: {room.get('building')}, {room.get('floor')}")]
                }
        if "library" in clean:
            room = repo.get_room("Central Library")
            if room:
                return {
                    "response": (
                        f"The Central Library is on the {room.get('floor', 'second floor').lower()} of the {room.get('building', 'Library Building')}. "
                        "It has spacious quiet reading halls, digital catalog terminals, and borrowing desks open until 8:00 PM on weekdays."
                    ),
                    "citations": [CitationModel(source="Campus Map", page=1, section="Library", snippet=f"{room.get('name')}: {room.get('building')}, {room.get('floor')}")]
                }
        if "102" in clean or "registrar" in clean:
            room = repo.get_room("Registrar Office") or repo.get_room("102")
            if room:
                return {
                    "response": (
                        f"Room 102 is the Registrar and Admissions Office, right on the {room.get('floor', 'first floor').lower()} of the {room.get('building', 'Administrative Block')}. "
                        "That is where staff can help you with student registrations, document verifications, and fee payments."
                    ),
                    "citations": [CitationModel(source="Campus Map", page=1, section="Administration", snippet=f"{room.get('name')}: {room.get('building')}, {room.get('floor')}")]
                }
        if "204" in clean or "robotics" in clean:
            room = repo.get_room("Advanced Robotics & AI Lab") or repo.get_room("Lab-204")
            if room:
                return {
                    "response": (
                        f"The Advanced Robotics and AI Lab is Lab 204, on the {room.get('floor', 'second floor').lower()} of the {room.get('building', 'Technology Wing')}. "
                        "It is fully equipped for robotics research and hardware prototyping. Feel free to stop by if you're working on a project!"
                    ),
                    "citations": [CitationModel(source="Campus Map", page=2, section="Laboratories", snippet=f"{room.get('name')}: {room.get('building')}, {room.get('floor')}")]
                }

    return None
