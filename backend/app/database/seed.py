from .repository import repo
from .models import (
    FAQModel, DepartmentModel, RoomModel, FacultyModel,
    CollegeHoursModel, EventModel, AnnouncementModel
)


DEMO_DISCLAIMER = "[DEMO DATA]"


def seed_database():
    """Seeds the SQLite database with structured sample college data labeled as DEMO DATA."""
    # Check if already seeded
    existing_depts = repo.list_departments()
    if existing_depts:
        return

    # Seed FAQs
    faqs = [
        FAQModel(
            question="What are the college admission requirements?",
            answer=f"{DEMO_DISCLAIMER} For undergraduate B.Tech programs, candidates must have passed 10+2 with Physics, Mathematics, and Chemistry with a minimum aggregate of 60%. Admission is based on State/National entrance exam counseling.",
            category="Admissions"
        ),
        FAQModel(
            question="Where can I pay my semester fees?",
            answer=f"{DEMO_DISCLAIMER} Semester fees can be paid online via the Student Portal (portal.college.edu) or in person at the Accounts Section, Ground Floor, Admin Block (Counter 3 & 4).",
            category="Finance"
        ),
        FAQModel(
            question="How do I get a library card / access digital journals?",
            answer=f"{DEMO_DISCLAIMER} Every student receives an activated RFID library card during orientation. For digital journal access (IEEE, Springer, ScienceDirect), visit the Central Library 1st Floor Digital Hub to activate your campus credentials.",
            category="Library"
        ),
        FAQModel(
            question="Is there a hostel facility on campus?",
            answer=f"{DEMO_DISCLAIMER} Yes, the campus has separate hostels for boys (Aryabhatta & Ramanujan Halls) and girls (Gargi & Kalpana Halls) with Wi-Fi, mess, and 24/7 security.",
            category="Campus Life"
        ),
        FAQModel(
            question="What is the procedure for issuing a Bonafide Certificate?",
            answer=f"{DEMO_DISCLAIMER} Apply via the College ERP portal under 'Student Services -> Certificates', or submit a handwritten application to the Academic Registrar office (Admin Block, Room 102). Processing takes 24 hours.",
            category="Academics"
        ),
        FAQModel(
            question="Where is the medical room / health center?",
            answer=f"{DEMO_DISCLAIMER} The Campus Health Centre is located adjacent to the Sports Complex, Ground Floor. A resident doctor and nurse are available from 8:00 AM to 8:00 PM.",
            category="Facilities"
        ),
    ]
    for f in faqs:
        repo.add_faq(f)

    # Seed Departments
    departments = [
        DepartmentModel(
            name="Computer Science and Engineering",
            code="CSE",
            block="Main Academic Block",
            floor="2nd Floor, Wing A",
            hod="Dr. Arvind Sharma",
            contact_email="hod.cse@college.edu",
            description=f"{DEMO_DISCLAIMER} Offers B.Tech, M.Tech, and Ph.D. with specializations in AI, Cybersecurity, and Cloud Systems."
        ),
        DepartmentModel(
            name="Mechanical Engineering",
            code="MECH",
            block="Engineering Workshop Block",
            floor="1st Floor",
            hod="Dr. Rajeshwari Nair",
            contact_email="hod.mech@college.edu",
            description=f"{DEMO_DISCLAIMER} Specializes in Robotics, Thermal Engineering, CAD/CAM, and Advanced Manufacturing."
        ),
        DepartmentModel(
            name="Electronics and Communication Engineering",
            code="ECE",
            block="Science & Tech Annex",
            floor="3rd Floor",
            hod="Dr. Vikram Deshmukh",
            contact_email="hod.ece@college.edu",
            description=f"{DEMO_DISCLAIMER} Focuses on VLSI Design, Embedded Systems, IoT, and Wireless Communications."
        ),
        DepartmentModel(
            name="Civil Engineering",
            code="CIVIL",
            block="Main Academic Block",
            floor="1st Floor, Wing B",
            hod="Dr. Meenakshi Sundaram",
            contact_email="hod.civil@college.edu",
            description=f"{DEMO_DISCLAIMER} Covers Structural Engineering, Environmental Systems, Geotech, and Surveying."
        ),
        DepartmentModel(
            name="Management Studies (MBA)",
            code="DOMS",
            block="Management Tower",
            floor="4th Floor",
            hod="Prof. Sunita Kapoor",
            contact_email="hod.mba@college.edu",
            description=f"{DEMO_DISCLAIMER} Offers MBA programs in Tech Management, Marketing, Human Resources, and Finance."
        ),
    ]
    for d in departments:
        repo.add_department(d)

    # Seed Rooms
    rooms = [
        RoomModel(
            room_number="101",
            name="Principal Office & Directorate",
            building="Admin Block",
            floor="Ground Floor",
            purpose="Principal, Director, and Executive Secretary offices."
        ),
        RoomModel(
            room_number="102",
            name="Academic Registrar Office",
            building="Admin Block",
            floor="Ground Floor",
            purpose="Student admissions, bonafide verification, marksheets, and transcripts."
        ),
        RoomModel(
            room_number="Auditorium-1",
            name="Dr. APJ Abdul Kalam Auditorium",
            building="Convention Center",
            floor="Ground Floor",
            purpose="Major college symposiums, guest lectures, convocations, and cultural fests. Seats 800 people."
        ),
        RoomModel(
            room_number="Lab-204",
            name="Advanced AI & Robotics Laboratory",
            building="Main Academic Block",
            floor="2nd Floor",
            purpose="Hands-on lab for Machine Learning, computer vision, and autonomous robotics projects."
        ),
        RoomModel(
            room_number="Seminar-301",
            name="ECE Department Seminar Hall",
            building="Science & Tech Annex",
            floor="3rd Floor",
            purpose="Departmental seminars, viva voce presentations, and faculty meetings."
        ),
        RoomModel(
            room_number="LIB-01",
            name="Central Library Reading Room & Digital Hub",
            building="Central Library",
            floor="1st Floor",
            purpose="Quiet study area, journal archives, reference books, and e-learning terminals."
        ),
    ]
    for r in rooms:
        repo.add_room(r)

    # Seed Faculty
    faculty = [
        FacultyModel(
            name="Dr. Arvind Sharma",
            department="Computer Science and Engineering",
            designation="Professor & Head of Department",
            cabin="Room 210, Main Academic Block",
            email="arvind.sharma@college.edu",
            office_hours="Mon, Wed, Fri: 2:00 PM - 4:00 PM"
        ),
        FacultyModel(
            name="Dr. Sneha Patil",
            department="Computer Science and Engineering",
            designation="Associate Professor (AI / Data Science)",
            cabin="Room 214, Main Academic Block",
            email="sneha.patil@college.edu",
            office_hours="Tue, Thu: 10:00 AM - 12:30 PM"
        ),
        FacultyModel(
            name="Dr. Rajeshwari Nair",
            department="Mechanical Engineering",
            designation="Professor & Head of Department",
            cabin="Room 105, Workshop Block",
            email="rajeshwari.nair@college.edu",
            office_hours="Mon - Thu: 3:00 PM - 5:00 PM"
        ),
        FacultyModel(
            name="Dr. Vikram Deshmukh",
            department="Electronics and Communication Engineering",
            designation="Professor & Head of Department",
            cabin="Room 312, Science Annex",
            email="vikram.deshmukh@college.edu",
            office_hours="Mon, Wed: 11:00 AM - 1:00 PM"
        ),
        FacultyModel(
            name="Prof. Sunita Kapoor",
            department="Management Studies (MBA)",
            designation="Dean & HOD Management",
            cabin="Room 401, Management Tower",
            email="sunita.kapoor@college.edu",
            office_hours="Tue, Fri: 2:30 PM - 4:30 PM"
        ),
    ]
    for fac in faculty:
        repo.add_faculty(fac)

    # Seed College Hours
    hours = [
        CollegeHoursModel(
            facility_name="Main Campus & Academic Gates",
            open_time="07:30 AM",
            close_time="08:00 PM",
            days="Monday to Saturday",
            notes=f"{DEMO_DISCLAIMER} Student ID cards required for entry after 6:00 PM."
        ),
        CollegeHoursModel(
            facility_name="Central Library",
            open_time="08:30 AM",
            close_time="09:00 PM",
            days="Monday to Saturday (10:00 AM - 05:00 PM on Sundays)",
            notes="Digital Hub closes at 8:00 PM."
        ),
        CollegeHoursModel(
            facility_name="Administrative Office / Accounts Counter",
            open_time="09:30 AM",
            close_time="04:30 PM",
            days="Monday to Friday (Lunch break: 1:00 PM - 1:45 PM)",
            notes="Closed on Second Saturdays and public holidays."
        ),
        CollegeHoursModel(
            facility_name="Student Cafeteria & Food Court",
            open_time="08:00 AM",
            close_time="07:30 PM",
            days="All Days",
            notes="Breakfast served 8:00 AM - 10:30 AM, Lunch 12:00 PM - 2:30 PM."
        ),
        CollegeHoursModel(
            facility_name="Health Centre / Dispensary",
            open_time="08:00 AM",
            close_time="08:00 PM",
            days="All Days (Emergency on call 24x7)",
            notes="Resident doctor available."
        ),
    ]
    for h in hours:
        repo.add_college_hours(h)

    # Seed Events
    events = [
        EventModel(
            title="Annual Tech Symposium — InnovateX 2026",
            date="2026-11-15",
            time="09:30 AM - 05:30 PM",
            venue="Auditorium-1 & Lab Complex",
            description=f"{DEMO_DISCLAIMER} 48-hour hackathon, robotics maze solver competition, AI paper presentations, and venture pitch challenge.",
            organizer="CSE & ECE Student Councils"
        ),
        EventModel(
            title="Campus Placement Drive — Tier-1 Tech Companies",
            date="2026-11-22",
            time="08:30 AM - 06:00 PM",
            venue="Convention Center Hall 2",
            description=f"{DEMO_DISCLAIMER} Pre-placement talks, coding round, and technical interviews for final year students.",
            organizer="Training and Placement Cell (T&P)"
        ),
        EventModel(
            title="Alumni Homecoming & Mentorship Summit",
            date="2026-12-05",
            time="10:00 AM - 04:00 PM",
            venue="Central Amphitheatre",
            description=f"{DEMO_DISCLAIMER} Alumni meet and career guidance session across industry sectors.",
            organizer="Alumni Affairs Office"
        ),
    ]
    for e in events:
        repo.add_event(e)

    # Seed Announcements
    announcements = [
        AnnouncementModel(
            title="Mid-Term Semester Examination Schedule Released",
            content=f"{DEMO_DISCLAIMER} The timetable for mid-semester assessments for all UG and PG batches is now published on the notice board and college website.",
            date_posted="2026-10-18",
            priority="Urgent"
        ),
        AnnouncementModel(
            title="National Science & Technology Day Project Registrations",
            content=f"{DEMO_DISCLAIMER} Project abstracts for the Science Exhibition must be submitted to the respective faculty coordinators by November 5.",
            date_posted="2026-10-15",
            priority="High"
        ),
        AnnouncementModel(
            title="Hostel Wi-Fi Upgrades Completed",
            content=f"{DEMO_DISCLAIMER} High-speed optical fiber backbone has been commissioned in Aryabhatta and Gargi halls.",
            date_posted="2026-10-10",
            priority="Normal"
        ),
    ]
    for a in announcements:
        repo.add_announcement(a)


if __name__ == "__main__":
    seed_database()
    print("Database seeded with labeled DEMO DATA successfully.")
