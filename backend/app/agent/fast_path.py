import re
from typing import Optional, Dict, Any, List
from ..database.repository import repo
from ..database.models import CitationModel


def _word_in_clean(word: str, clean_text: str) -> bool:
    """Checks if a whole word exists in clean text with word boundaries."""
    return bool(re.search(r'\b' + re.escape(word) + r'\b', clean_text))


def resolve_fast_path(user_query: str) -> Optional[Dict[str, Any]]:
    """
    Evaluates incoming query for high-frequency reception desk intents at APCOER Pune.
    Returns immediate, human-sounding dialogue responses with citations in <10ms,
    avoiding robotic bullet points or chatbot data dumps.
    """
    q = user_query.strip().lower()
    clean = re.sub(r'[^a-z0-9\s]', '', q)

    # Never intercept personal introductions or self-identifications (let LLM converse naturally)
    if re.search(r'\b(?:my name is|i am|im|this is|call me)\b', clean):
        return None

    # 1. Greetings, College Name & Persona Identity
    college_tokens = [
        "who are you", "what is your name", "what are you", "tell me about yourself",
        "what can you do", "which college", "what college", "what is this college", "college name",
        "name of college", "what is the college name", "where am i", "about college",
        "about apcoer", "apcoer", "our college", "name of our college", "our college name",
        "what is our college name", "what is the name of our college", "know our college",
        "college info", "information about college"
    ]
    greeting_tokens = ["hi", "hello", "hey", "greetings", "good morning", "good afternoon", "good evening"]

    is_identity_query = (
        clean in greeting_tokens or
        any(t in clean for t in college_tokens) or
        ("name" in clean and "college" in clean) or
        ("which" in clean and "college" in clean)
    )

    if is_identity_query and not any(k in clean for k in ["branch", "branches", "course", "courses", "department", "admission", "principal", "hod", "fee", "fees", "timing", "placement", "recruit", "history", "trust", "abmsp", "founder", "motto"]):
        return {
            "response": (
                "Hello and welcome! I am Buddy, the official AI Receptionist at Anantrao Pawar College of Engineering & Research (APCOER), Pune. "
                "Our prestigious institution is run by the Akhil Bharatiya Maratha Shikshan Parishad (A.B.M.S. Parishad, founded in 1907 with the guiding motto 'Bahujan Hitay, Bahujan Sukhaya') and is affiliated with Savitribai Phule Pune University (DTE Code: 6794). "
                "I am delighted to assist you with academic departments, admissions under DTE Code 6794, faculty cabins, campus navigation, placements, and facilities. How can I assist you today?"
            ),
            "citations": [
                CitationModel(
                    source="APCOER: Institutional Overview (College Overview)",
                    page=1,
                    section="College Identity",
                    snippet="Anantrao Pawar College of Engineering & Research (APCOER), Parvati, Pune - 411009, run by ABMSP (Estd. 1907, 'Bahujan Hitay, Bahujan Sukhaya'), affiliated to SPPU (DTE Code: 6794)."
                )
            ]
        }

    # 1b. Institutional History, ABMSP Trust, Motto & Heritage
    if any(k in clean for k in ["history", "founded", "founder", "founders", "abmsp", "parishad", "trust", "bahujan", "motto", "origin", "heritage", "who started", "who founded", "background of college", "about the trust"]):
        return {
            "response": (
                "Akhil Bharatiya Maratha Shikshan Parishad (A.B.M.S. Parishad), our parent educational trust, was founded in 1907 by a team of renowned educationists and social reformers with the noble thought 'Bahujan Hitay, Bahujan Sukhaya'—for the welfare and happiness of the masses. "
                "In the first half of the 20th century, A.B.M.S. Parishad made a commendable contribution of awakening and inspiring the masses who were deprived of education for generations, establishing educational institutions throughout Maharashtra and beyond. "
                "The Parishad draws its enduring inspiration from Mahatma Jyotirao Phule, Rajarshi Chhatrapati Shahu Maharaj (the Ruler of Kolhapur), and Dr. Babasaheb Ambedkar, who fought for economic, social, and political justice and advocated the empowerment of disadvantaged sections of society. "
                "To carry forward this great legacy, Anantrao Pawar College of Engineering & Research (APCOER) was established in 2012 on a lush 10-acre campus near Parvati Hills. Would you like to know more about our academic departments or trust leadership?"
            ),
            "citations": [
                CitationModel(
                    source="APCOER: Institutional History (About A.B.M.S. Parishad)",
                    page=1,
                    section="Trust Heritage & Motto",
                    snippet="A.B.M.S. Parishad was established in 1907 with the thought 'Bahujan Hitay, Bahujan Sukhaya' by a team of renowned educationists and social reformers, drawing inspiration from Mahatma Phule, Rajarshi Shahu Maharaj, and Dr. Babasaheb Ambedkar."
                )
            ]
        }

    # 2. Principal / Vice Principal / College Leadership
    if any(k in clean for k in ["principal", "director", "sunil thakare", "thakare", "vice principal", "jagtap"]):
        fac_list = repo.get_faculty("Sunil B. Thakare")
        principal = fac_list[0] if fac_list else None
        if "vice" in clean or "jagtap" in clean:
            vp_list = repo.get_faculty("Shrikant B. Jagtap")
            vp = vp_list[0] if vp_list else None
            return {
                "response": (
                    "Our Vice Principal is Prof. Shrikant B. Jagtap from the Department of Mechanical Engineering. "
                    "His office is in Room 103 on the Ground Floor of the Main Academic Building, and you can contact him at viceprincipal@abmspcoerpune.org. "
                    "Would you like directions to the administrative wing?"
                ),
                "citations": [CitationModel(source="APCOER Faculty Directory", page=1, section="Administration", snippet="Prof. Shrikant B. Jagtap - Vice Principal")]
            }
        return {
            "response": (
                "The Principal of APCOER is Dr. Sunil B. Thakare, an eminent academician and Professor in Civil Engineering. "
                "His office is located in Room 101 on the Ground Floor of the Main Academic Building, right past the reception foyer. "
                "He is generally available for appointments on weekday mornings between 11:00 AM and 1:00 PM, or you can email principal@abmspcoerpune.org. "
                "Would you like me to guide you to Room 101?"
            ),
            "citations": [CitationModel(source="APCOER Faculty Directory", page=1, section="Directorate", snippet="Dr. Sunil B. Thakare - Principal & Professor")]
        }

    # 3. Faculty / HOD queries (Verified Current Leadership)
    if any(k in clean for k in [
        "hod", "head of department", "head of", "faculty", "professor", "professors", "teacher", "teachers", "staff", "cabin",
        "gaikwad", "rama", "kadam", "amit", "musale", "jitendra", "sorate", "raviraj", "amar", "selukar", "balaji", "newase", "atul", "totla", "kamble", "jagtap", "thakare",
        "rankhambe", "devika", "lavhe", "ramesh", "kokane", "sayali", "kalal", "ashok", "nikam", "rajshri", "dodke", "akash", "dipalee", "shah", "khaire", "prajakta", "khote", "shital", "ajinkya", "patil"
    ]):
        # Computer Engineering
        if "computer" in clean or "cs" in clean or "comp" in clean or "gaikwad" in clean or "rama" in clean:
            return {
                "response": (
                    "The Head of the Computer Engineering Department is Dr. Rama B. Gaikwad! "
                    "Her cabin is located on the second floor of the Main Academic Building in the Computer Engineering Wing. "
                    "She is available for student consultations from 10:30 AM to 12:30 PM on weekdays, and you can reach her at rama.gaikwad@abmspcoerpune.org. "
                    "Would you like directions to the Computer Engineering department?"
                ),
                "citations": [CitationModel(source="APCOER Faculty Directory", page=1, section="Computer Engineering", snippet="Dr. Rama B. Gaikwad - Professor & Head of Department")]
            }

        # Information Technology (IT) Faculty Specific Queries
        if any(f in clean for f in ["rankhambe", "devika"]):
            return {
                "response": (
                    "Prof. D. P. Rankhambe is an Assistant Professor in the Information Technology Department. "
                    "She holds an M.E. in CSE with over 11 years of teaching experience. "
                    "Her areas of interest include HCI, Big Data, Cloud Computing, DBMS, and STQA. "
                    "Her lab is Room 327 (Operating System Lab) on the third floor, with consulting hours Monday through Friday from 11:00 AM to 1:00 PM. "
                    "You can reach her at rankhambedevika@gmail.com. Would you like directions to Room 327?"
                ),
                "citations": [CitationModel(source="APCOER Faculty Directory", page=1, section="Information Technology", snippet="Prof. D. P. Rankhambe - Assistant Professor, IT (Room 327, Operating System Lab)")]
            }

        if any(f in clean for f in ["lavhe", "ramesh"]):
            return {
                "response": (
                    "Prof. R. S. Lavhe serves as Assistant Professor in the Information Technology Department. "
                    "He holds an M.E. in Information Technology with over 11.5 years of teaching experience, specializing in Information Security. "
                    "His office is in the IT Faculty Room on the third floor, and he is available from 11:00 AM to 1:00 PM on weekdays. "
                    "His email is ramesh.lavhe@abmspcoerpune.org. Would you like directions to the third floor IT faculty room?"
                ),
                "citations": [CitationModel(source="APCOER Faculty Directory", page=1, section="Information Technology", snippet="Prof. R. S. Lavhe - Assistant Professor, IT (IT Faculty Room, 3rd Floor)")]
            }

        if any(f in clean for f in ["kokane", "sayali"]):
            return {
                "response": (
                    "Prof. S. R. Kokane is an Assistant Professor in the Information Technology Department. "
                    "She holds an M.E. in CE and is pursuing her PhD, with over 11 years of teaching experience in IoT and AI. "
                    "She oversees Room 303 (Software Design & Testing Lab) on the third floor, and her office hours are from 2:00 PM to 4:00 PM on weekdays. "
                    "You can contact her at sayali.kokane@abmspcoerpune.org. May I guide you to Room 303?"
                ),
                "citations": [CitationModel(source="APCOER Faculty Directory", page=1, section="Information Technology", snippet="Prof. S. R. Kokane - Assistant Professor, IT (Room 303, Software Design & Testing Lab)")]
            }

        if any(f in clean for f in ["kalal", "ashok"]):
            return {
                "response": (
                    "Prof. A. N. Kalal is an Assistant Professor in the Information Technology Department. "
                    "He holds an M.Tech in Computer Science with over 12 years of experience. His domains include Database, Data Mining, Cloud Computing, and Machine Learning. "
                    "His lab is Room 332 (Multimedia Lab) on the third floor, with consulting hours between 11:00 AM and 1:00 PM on weekdays. "
                    "His email is ashok.kalal@abmspcoerpune.org. Would you like directions to Room 332?"
                ),
                "citations": [CitationModel(source="APCOER Faculty Directory", page=1, section="Information Technology", snippet="Prof. A. N. Kalal - Assistant Professor, IT (Room 332, Multimedia Lab)")]
            }

        if any(f in clean for f in ["nikam", "rajshri"]):
            return {
                "response": (
                    "Prof. Rajshri Nikam is an Assistant Professor in the Information Technology Department. "
                    "She holds a B.E. and M.E. in IT with 11.5 years of teaching experience, specializing in Data Mining. "
                    "Her lab is Room 331 (Network Lab) on the third floor, with consulting hours Monday through Friday from 11:00 AM to 1:00 PM. "
                    "You can reach her at rajshri.nikam@abmspcoerpune.org. Let me know if you would like directions to Room 331!"
                ),
                "citations": [CitationModel(source="APCOER Faculty Directory", page=1, section="Information Technology", snippet="Prof. Rajshri Nikam - Assistant Professor, IT (Room 331, Network Lab)")]
            }

        if any(f in clean for f in ["dodke", "akash"]):
            return {
                "response": (
                    "Prof. A. R. Dodke is an Assistant Professor in Information Technology. "
                    "He holds an M.E. in Computer Engineering with 9 years of teaching experience, specializing in Software Quality Assurance. "
                    "He manages Room 328 (Web Engineering Technology Lab) on the third floor, available from 10:00 AM to 12:00 PM on weekdays. "
                    "His email is akash.dodke@abmspcoerpune.org. Would you like directions to Room 328?"
                ),
                "citations": [CitationModel(source="APCOER Faculty Directory", page=1, section="Information Technology", snippet="Prof. A. R. Dodke - Assistant Professor, IT (Room 328, Web Engineering Lab)")]
            }

        if any(f in clean for f in ["dipalee", "shah"]):
            return {
                "response": (
                    "Prof. Dipalee Shah serves as Assistant Professor in the Information Technology Department. "
                    "She holds a B.E. in IT and M.E. in Computer Engineering, bringing 1.3 years of teaching and 5 years 4 months of industry experience in Data Structures, DBMS, and Data Engineering. "
                    "Her office is in the IT Faculty Room on the third floor. You can reach her at dipalee.shah@abmspcoerpune.org. "
                    "Would you like directions to the IT department?"
                ),
                "citations": [CitationModel(source="APCOER Faculty Directory", page=1, section="Information Technology", snippet="Prof. Dipalee Shah - Assistant Professor, IT (3rd Floor)")]
            }

        if any(f in clean for f in ["khaire", "prajakta"]):
            return {
                "response": (
                    "Prof. Prajakta G. Khaire is an Assistant Professor in the Information Technology Department. "
                    "She holds an M.Tech in Computer Engineering with research interests in Machine Learning, Data Analytics, and DBMS. "
                    "She is in charge of Room 301 (Microprocessor Lab) on the third floor, available from 10:30 AM to 12:30 PM on weekdays. "
                    "Her email is prajakta.khaire@abmspcoerpune.org. May I guide you to Room 301?"
                ),
                "citations": [CitationModel(source="APCOER Faculty Directory", page=1, section="Information Technology", snippet="Prof. Prajakta G. Khaire - Assistant Professor, IT (Room 301, Microprocessor Lab)")]
            }

        if any(f in clean for f in ["khote", "shital"]):
            return {
                "response": (
                    "Prof. Shital S. Khote is an Assistant Professor in the Information Technology Department. "
                    "She holds an M.E. in Computer Engineering with teaching experience in DBMS and Machine Learning. "
                    "She is in charge of Room 330 (Distributed System Lab) on the third floor, available between 2:00 PM and 4:00 PM on weekdays. "
                    "Her email is shital.khote@abmspcoerpune.org. Would you like directions to Room 330?"
                ),
                "citations": [CitationModel(source="APCOER Faculty Directory", page=1, section="Information Technology", snippet="Prof. Shital S. Khote - Assistant Professor, IT (Room 330, Distributed System Lab)")]
            }

        if any(f in clean for f in ["ajinkya", "patil"]):
            return {
                "response": (
                    "Mr. Ajinkya Patil is the Lab Assistant in the Information Technology Department. "
                    "He holds an MCA degree with 4 years of technical experience in laboratory administration. "
                    "His office is in the IT Department Laboratories on the third floor, and his email is ajinkya.patil@abmspcoerpune.org. "
                    "Feel free to ask if you need help finding any of the IT computer labs!"
                ),
                "citations": [CitationModel(source="APCOER Faculty Directory", page=1, section="Information Technology", snippet="Mr. Ajinkya Patil - Lab Assistant, IT (3rd Floor Labs)")]
            }

        # Information Technology (IT) Roster or HOD
        if ("information technology" in clean or (_word_in_clean("it", clean) and any(_word_in_clean(w, clean) for w in ["dept", "department", "branch", "engineering", "course", "lab", "faculty", "hod"]))) and any(_word_in_clean(term, clean) for term in ["faculty", "professor", "professors", "teachers", "staff", "members", "team", "roster", "list"]):
            return {
                "response": (
                    "The Information Technology (IT) Department is headed by Dr. Amit Ashokrao Kadam (Head & Associate Professor, Room 304). "
                    "The department's teaching and technical team includes Prof. D. P. Rankhambe (Assistant Professor, Operating System Lab Room 327), "
                    "Prof. R. S. Lavhe (Assistant Professor, Information Security), "
                    "Prof. S. R. Kokane (Assistant Professor, Software Design & Testing Lab Room 303), "
                    "Prof. A. N. Kalal (Assistant Professor, Multimedia Lab Room 332), "
                    "Prof. Rajshri Nikam (Assistant Professor, Network Lab Room 331), "
                    "Prof. A. R. Dodke (Assistant Professor, Web Engineering Lab Room 328), "
                    "Prof. Dipalee Shah (Assistant Professor, Data Structures & Data Engineering), "
                    "Prof. Prajakta G. Khaire (Assistant Professor, Microprocessor Lab Room 301), "
                    "Prof. Shital S. Khote (Assistant Professor, Distributed System Lab Room 330), "
                    "and Mr. Ajinkya Patil (Lab Assistant). "
                    "All IT faculty cabins and specialized computing laboratories are situated on the 3rd floor of the Main Academic Building. "
                    "Would you like details on any particular faculty member or directions to their lab?"
                ),
                "citations": [CitationModel(source="APCOER Faculty Directory", page=1, section="Information Technology", snippet="IT Department Faculty Roster: Dr. Amit Ashokrao Kadam (HOD), Prof. D. P. Rankhambe, Prof. R. S. Lavhe, Prof. S. R. Kokane, Prof. A. N. Kalal, Prof. Rajshri Nikam, Prof. A. R. Dodke, Prof. Dipalee Shah, Prof. Prajakta G. Khaire, Prof. Shital S. Khote, Mr. Ajinkya Patil (3rd Floor)")]
            }

        if "information technology" in clean or (_word_in_clean("it", clean) and any(_word_in_clean(w, clean) for w in ["dept", "department", "branch", "engineering", "course", "lab", "hod", "cabin"])) or _word_in_clean("kadam", clean) or ("amit" in clean and "kadam" in clean):
            return {
                "response": (
                    "The Head of the Information Technology (IT) Department is Dr. Amit Ashokrao Kadam! "
                    "His office is situated in Room 304 (IT HOD Cabin) on the third floor of the Main Academic Building. "
                    "His research areas include Blockchain Technology, IoT, and Cyber Security. You can contact him at amit.kadam@abmspcoerpune.org. "
                    "Would you like directions to the IT department on the third floor?"
                ),
                "citations": [CitationModel(source="APCOER Faculty Directory", page=1, section="Information Technology", snippet="Dr. Amit Ashokrao Kadam - Associate Professor & Head of Department (Room 304)")]
            }

        # Artificial Intelligence & Data Science (AI & DS)
        if "data science" in clean or _word_in_clean("aids", clean) or (_word_in_clean("ai", clean) and any(_word_in_clean(w, clean) for w in ["dept", "department", "branch", "engineering", "course", "ds", "hod", "cabin"])) or _word_in_clean("musale", clean) or _word_in_clean("jitendra", clean):
            return {
                "response": (
                    "The Head of the Artificial Intelligence and Data Science (AI & DS) Department is Dr. Jitendra Musale! "
                    "His cabin is located on the second floor of the Main Academic Building. "
                    "His consultation hours are from 10:00 AM to 12:00 PM, and you can reach him at jitendra.musale@abmspcoerpune.org. "
                    "Would you like more information about the AI & DS program or labs?"
                ),
                "citations": [CitationModel(source="APCOER Faculty Directory", page=1, section="AI & DS", snippet="Dr. Jitendra Musale - Associate Professor & Head of Department")]
            }

        # Electronics & Telecommunication (E&TC)
        if "electronics" in clean or "entc" in clean or "etc" in clean or "telecommunication" in clean or "amar" in clean or ("deshmukh" in clean and "amar" in clean):
            return {
                "response": (
                    "The Head of Electronics & Telecommunication Engineering (E&TC) is Dr. Amar Deshmukh! "
                    "His office is located in Room 323 (E&TC HOD Cabin) on the third floor of the Main Academic Building. "
                    "His consulting hours are 11:30 AM to 1:30 PM on weekdays, and his email is amar.deshmukh@abmspcoerpune.org. "
                    "Would you like directions to the E&TC department?"
                ),
                "citations": [CitationModel(source="APCOER Faculty Directory", page=1, section="E&TC", snippet="Dr. Amar Deshmukh - Associate Professor & Head of Department (Room 323)")]
            }

        # Civil Engineering
        if "civil" in clean or "sorate" in clean or "raviraj" in clean:
            return {
                "response": (
                    "The Head of Civil Engineering is Dr. Raviraj Ramesh Sorate, who also serves as the Institute NBA Coordinator! "
                    "His cabin is located in Room 224 on the second floor of the Civil Engineering Wing. "
                    "His consultation hours are 11:00 AM to 1:00 PM, and you can contact him at raviraj.sorate@abmspcoerpune.org. "
                    "Feel free to ask if you would like directions to Room 224!"
                ),
                "citations": [CitationModel(source="APCOER Faculty Directory", page=1, section="Civil Engineering", snippet="Dr. Raviraj Ramesh Sorate - Associate Professor & HOD (Room 224)")]
            }

        # Mechanical Engineering
        if "mechanical" in clean or "mech" in clean or ("kamble" in clean and ("mech" in clean or "dattatray" in clean)):
            return {
                "response": (
                    "The Head of Mechanical Engineering is Dr. Dattatray P. Kamble (Dr. D. P. Kamble)! "
                    "His office is situated in the Mechanical HOD Cabin inside the Engineering Workshop Complex on the Ground Floor. "
                    "His consultation hours are from 2:30 PM to 4:30 PM, and you can reach him at dattatray.kamble@abmspcoerpune.org. "
                    "Let me know if you need directions to the workshop complex!"
                ),
                "citations": [CitationModel(source="APCOER Faculty Directory", page=1, section="Mechanical Engineering", snippet="Dr. Dattatray P. Kamble - Associate Professor & HOD")]
            }

        # First Year Engineering (FE)
        if "first year" in clean or "fe" in clean or "selukar" in clean or "balaji" in clean:
            return {
                "response": (
                    "The Head of the First Year Engineering (Applied Science) Department is Dr. Balaji S. Selukar! "
                    "His cabin is on the Ground Floor of the Main Academic Building. "
                    "His office hours are from 10:00 AM to 12:00 PM, and you can reach him at balaji.selukar@abmspcoerpune.org. "
                    "Would you like details on First Year induction or academics?"
                ),
                "citations": [CitationModel(source="APCOER Faculty Directory", page=1, section="First Year", snippet="Dr. Balaji S. Selukar - Assistant Professor & HOD")]
            }

        # Master of Computer Applications (MCA)
        if "mca" in clean or "newase" in clean or "atul" in clean:
            return {
                "response": (
                    "The Head of the Master of Computer Applications (MCA) Department is Dr. Atul D. Newase! "
                    "His cabin is located on the 4th floor of the Main Academic Building, and his email is atul.newase.mca@abmspcoerpune.org. "
                    "Let me know if you would like information on MCA admission eligibility or curriculum!"
                ),
                "citations": [CitationModel(source="APCOER Faculty Directory", page=1, section="MCA", snippet="Dr. Atul D. Newase - Assistant Professor & HOD")]
            }

        # Training & Placement Officer (TPO)
        if "placement" in clean or "tpo" in clean or "totla" in clean or "nilesh" in clean:
            return {
                "response": (
                    "Our Training and Placement Cell is headed by Prof. Nilesh S. Totla. "
                    "The TPO office is located in Room TPO-01 on the first floor of the Main Academic Building. "
                    "He coordinates campus recruitment with top recruiters like TCS, Infosys, Capgemini, and L&T. You can reach the cell at tpo@abmspcoerpune.org. "
                    "Are you looking for placement reports or campus drive details?"
                ),
                "citations": [CitationModel(source="APCOER T&P Cell", page=1, section="Placements", snippet="Prof. Nilesh S. Totla - Training & Placement Officer (Room TPO-01)")]
            }

    # 4. Admissions, DTE Code & Eligibility
    if any(k in clean for k in ["admission", "admissions", "dte code", "dte", "code", "eligibility", "cap round", "cap"]):
        return {
            "response": (
                "Admissions to Anantrao Pawar College of Engineering & Research (APCOER), Pune are conducted through the Maharashtra State CET Cell CAP rounds under DTE Institute Code 6794. "
                "For First Year B.Tech, candidates require valid MHT-CET or JEE Main scores, while Direct Second Year admissions are based on Diploma or B.Sc. merit. "
                "Our document verification and admission counseling desk is active in Room 102 on the Ground Floor. Would you like directions to the admission desk?"
            ),
            "citations": [
                CitationModel(source="APCOER Admission Directorate", page=1, section="Admissions", snippet="DTE Code: 6794 | CAP Round Admissions for B.Tech & MCA")
            ]
        }

    # 5. College Hours & Timings
    if any(k in clean for k in ["hours", "timings", "timing", "open", "close", "when does", "what time"]):
        return {
            "response": (
                "APCOER college campus and academic departments are open Monday through Saturday from 8:30 AM to 5:00 PM. "
                "The Central Library and Digital Reading Hall stay open late from 8:00 AM to 8:00 PM for student study, "
                "and the Student Section & Accounts Counter (Room 102) operates from 9:30 AM to 4:30 PM. "
                "Is there a specific department or facility you are planning to visit today?"
            ),
            "citations": [CitationModel(source="APCOER Campus Timings", page=1, section="Operating Hours", snippet="Academic Hours: 8:30 AM - 5:00 PM | Library: 8:00 AM - 8:00 PM")]
        }

    # 6. Room & Location queries
    if any(k in clean for k in ["where is", "room", "lab", "auditorium", "library", "locate", "directions"]):
        if "auditorium" in clean or "seminar" in clean:
            return {
                "response": (
                    "The College Auditorium is located on the Ground Floor of the Main Academic Building, right opposite the central reception lobby. "
                    "It is where all our major symposiums like SPARKTECH, student orientations, and cultural functions take place. Would you like me to point you toward the entrance?"
                ),
                "citations": [CitationModel(source="APCOER Campus Map", page=1, section="Auditorium", snippet="Auditorium-01: Ground Floor, Main Building")]
            }
        if "library" in clean:
            return {
                "response": (
                    "The Central Library and Reading Hall is located on the Ground and First Floor of the Library Wing. "
                    "It features over 25,000 engineering volumes, DelNet digital access, and spacious study halls open until 8:00 PM. Would you like directions to the library?"
                ),
                "citations": [CitationModel(source="APCOER Campus Map", page=1, section="Library", snippet="Central Library: Ground & 1st Floor")]
            }
        if "102" in clean or "student section" in clean or "registrar" in clean:
            return {
                "response": (
                    "Room 102 is the Student Administrative Section and Admission Counter, located on the Ground Floor of the Main Building. "
                    "That is where staff assist students with admission verification, scholarships, fee receipts, and bonafide certificates. Would you like directions to Room 102?"
                ),
                "citations": [CitationModel(source="APCOER Campus Map", page=1, section="Administration", snippet="Room 102: Student Section & Registrar")]
            }
        if "tbi" in clean or "incubation" in clean:
            return {
                "response": (
                    "The APCOER Technology Business Incubator (TBI) is on the Ground Floor near the Innovation Complex. "
                    "It supports student startups, patent applications, and hardware prototyping. Would you like to visit the TBI center?"
                ),
                "citations": [CitationModel(source="APCOER Campus Map", page=1, section="TBI", snippet="APCOER TBI Innovation Center: Ground Floor")]
            }

    # 7. Courses, Programs & Branches offered
    if any(k in clean for k in ["which branch", "branches", "courses", "programs", "departments", "degrees", "what branch", "engineering branches"]):
        return {
            "response": (
                "APCOER Pune offers 6 core undergraduate B.Tech engineering branches affiliated with Savitribai Phule Pune University: "
                "Computer Engineering, Artificial Intelligence & Data Science (AI & DS), Information Technology, "
                "Electronics & Telecommunication (E&TC), Civil Engineering, and Mechanical Engineering. "
                "We also offer Master of Computer Applications (MCA) and postgraduate M.E. programs. "
                "Which specific branch are you interested in exploring?"
            ),
            "citations": [CitationModel(source="APCOER Academic Programs", page=1, section="Courses Offered", snippet="UG: Computer, AI&DS, IT, E&TC, Civil, Mech | PG: MCA, M.E.")]
        }

    # 8. Fees & Scholarships
    if any(k in clean for k in ["fee", "fees", "scholarship", "cost", "freeship", "ebc", "tfws", "mahadbt"]):
        return {
            "response": (
                "College fees at APCOER are determined as per the Maharashtra Fee Regulating Authority (FRA) guidelines. "
                "Eligible students can benefit from comprehensive Government scholarship schemes processed via the MahaDBT portal, "
                "including EBC (50% tuition waiver for eligible open category), TFWS (100% tuition waiver), and SC/ST/OBC/VJNT government concessions. "
                "Our dedicated Scholarship Helpdesk is available at the Accounts Counter on the Ground Floor to help with applications!"
            ),
            "citations": [CitationModel(source="APCOER Accounts & Scholarships", page=1, section="Fee Structure & Financial Aid", snippet="FRA Approved Fees | MahaDBT EBC, TFWS & Category Scholarships")]
        }

    # 9. Campus Location & Address
    if any(k in clean for k in ["where is apcoer", "address", "location", "how to reach", "where is it located", "where is the campus"]):
        return {
            "response": (
                "APCOER is located at Survey No. 83/2/E, Laxminagar, Parvati, Pune - 411009, Maharashtra, right at the foot of the scenic Parvati Hills. "
                "It is conveniently accessible from Swargate Bus Station (around 3 km) and Pune Railway Station (around 6 km). "
                "Are you traveling to campus by public transit or your own vehicle?"
            ),
            "citations": [CitationModel(source="APCOER Campus Guide", page=1, section="Location & Connectivity", snippet="S. No. 83/2/E, Laxminagar, Parvati, Pune - 411009")]
        }

    return None
