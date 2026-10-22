import re
from typing import Optional, Dict, Any, List
from ..database.repository import repo
from ..database.models import CitationModel


def resolve_fast_path(user_query: str) -> Optional[Dict[str, Any]]:
    """
    Evaluates incoming query for high-frequency reception desk intents at APCOER Pune.
    Returns immediate, human-sounding dialogue responses with citations in <10ms,
    avoiding robotic bullet points or chatbot data dumps.
    """
    q = user_query.strip().lower()
    clean = re.sub(r'[^a-z0-9\s]', '', q)

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
    if any(k in clean for k in ["hod", "head of department", "head of", "faculty", "professor", "cabin", "gaikwad", "rama", "kadam", "amit", "musale", "jitendra", "sorate", "raviraj", "amar", "selukar", "balaji", "newase", "atul", "totla", "kamble", "jagtap", "thakare"]):
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

        # Information Technology (IT)
        if "information technology" in clean or "it" in clean or "kadam" in clean or "amit" in clean:
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
        if "ai" in clean or "data science" in clean or "aids" in clean or "musale" in clean or "jitendra" in clean:
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
