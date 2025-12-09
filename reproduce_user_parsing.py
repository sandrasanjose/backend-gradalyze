import json
import re

# The user provided this text
ocr_text = """
[OCR] Complete text: PAMANTASAN NG LUNGSOD NG MAYNILA (Univcrsity of thc City of Manila) Office of the University Registrar Manila, Philippines OFFICIAL TRANSCRIPT OF RECORDS Abesamis; Aiver Sanliago ADESAMIS, AIVER SANTIAGO Address: 623 Corcuera Tondo, Manila Date Admitted: Ist Semester, 2020-2021 Entrance Data: Senior High School Graduate Arellano University Unils Gradcs Course No_ Descriplive Titlc Final Complction Credit COLLEGE QFENGINEERING AND TECHNOLOGY Ist Semester 2020-2021 ICC 0101 Introduction to Computing (Lecture) 1.50 ICC 0101.1 Introduction to Computing (Laboratory) 1.25 ICC 0102 Fundamentals of Programming (Lecture) 1.75 ICC 0102.1 Fundamentals of Programming (Laboratory) 1.75 IPP 0010 Interdisiplinaryong Pagbasa at Pagsulat Tungo sa Mabisang Pagpapahayag| 1.75 MMW 0001 Mathematics in the Modern World 1.50 PCM 00o6 Purposive Communicatinn 1.25 STS 0002 Science Technology and Society 1.00 AAP 0007 Art Appreciation 1.25 PED 0001 Foundation of Physical Activities 1.00 NSTP 01 National Service Training Program 1 (ROTCICWTS) 1.50 2nd Semester, 2020-2021 CET 0111 Calculus 1.75 CET 0114 General Chemistry (Lecture) 1.25 CET 0114.1 General Chemistry (Laboratory) 1.25 EIT 0121 Introduction to Computer Human Interaction (Lecture) 1.00 EIT 0121.1A Introduction to Computer Human Interaction (Laboratory) 1.00 EIT 0122 Discrete Mathematics 1.U0 EIT 0123 Web Systems Technology (Lecture) 1.75 EIT 0123.1 Web Systems Technology (Laboratory) 1.50 GTB 121 Great Books 1.00 ICC 0103 Intermediate Programming (Lecture) 1.50 ICC U1UJ.1 Intermedlate Programming (Laburalury) 1.75 PED 0013 Philippine Folk Dance 1.00 NSTP 02 National Service Training Program 2 (ROTCICWTS) 1.25 Lst Semester_2021-2022 CET 0121 Calculus 2.75 CET 0225 Physics for IT (Lecture) 2.75 CET 0225.1 Physics for [T (Laboratory) 2.00 EIT 0211 Object Oriented Programming (Lecture) 1.00 EIT 0211.1A Object Oriented Programming (Laboratory) 1.25 EIT ELECTIVE 1 Professional Elective 1.25 ICC 0104 Data Structures and Algorithms (Lecture) 1.00 ICC 0104.1 Data Structures dr Alyorithms (Laboratory) 1.25 PPC 122 Philippine Popular Culture 1.0U TCW 0005 The Contemporary World 1.25 PED 0054 Soccer 1.00 2nd Semester_2021-2022 EIT 0212 Platform Technology 1.50 XVXVXVXVXVXVXVXVXVXVXVXVXVXVXVXVXVXVXVXVXV  TURN TO NEXT PAGE XVXVXVXVXVXVXV XVXVXVXVXVXVXVXVXVXVXVXVXVX Remarks: Grading Sysleu; 1.00-1.25 Exccllent; 1.5-1.75, Good; 2.00 2.25, Cood; 2.5-2.75_ Satisfactory 3.00, Passed; 5.00, Failed; (5.00) , Dropped Unofficially (DU); Inc JINCO, Incomplete; DO, Dropped Officially: Credits: One unit of credit is one hour lecture or recilalion_ or three hours of laboralory, drafting, or shopwork, cach week for Ihe period of complete semesler_ This transcript is valid only when it bears the University seal and the original signature Of the Registrar: crasure Or alteration made on this documcnt rendersit void unless initialcd by the foregoing official Prepared by: Released: Lee BENEDICTO DBA_REB_REA 0n FEB 2 5 2025 Checked by: M.A Mundo Univcrsity Registrar by: Reviseal Oclolwr; 1979 Name: st , Very Any Acting Del
PAMANTASAN NG LUNGSOD NG MAYNILA (University of the City of Manila) Office of the University Registrar Page 2 of 2 Manila, Philippines OFFICIAL TRANSCRIPT OF RECORDS Name: ABESAMIS, AIVER SANTIAGO Units Grades Course No. Descriplive Title Final Completion Credit Znd Semester_ 2021-2022 EIT 0221 Quantitative Methods 1.00 EIT 0222 Networking (Lecture) 1.00 ET 0222.1 Networking (Laboratory) 1.00 EIT ELECTIVE 2 Professional Elective 2 1.00 GES 0013 Environmental Science 1.25 ICC 0105 Information Management (Lecture) 1.00 ICC 0105.1 Information Management (Laboratory) 1.00 RPH 0004 Readings in Philippine History 1.50 UTS 0003 Understanding the Self 1.00 PED 0074 Volleyball 1.00 Ist Semesters 2022-2022 EIT 0311 Advanced Database Systems (Lecture) 1.UU EIT 0311.1 Advanced Database Systems (Laboratory) 1.75 EIT 0312 Networking 2 (Lecture) 1.00 EIT 0312.1 Networking 2 (Laboratory) 1.00 EIT ELECTIVE 3 Professional Elective 3 1.00 ICC 0335 Application and Emerging Technologies (Lecture) 1.00 ICC 0335 Application and Emerging Technologies (Laboratory) 1.25 LWR 0009 Life and Works of Rizal 1.25 2nd Semester_2022-2023 EIT 0321 IInformation Assurance and Security (Lecture) 1.00 EIT 0321.1 Information Assurance and Security (Laboratory) 1.00 EIT 0322 System Intcgration Architccturc (Lecturc) 2.00 EIT 0322.1 System Integration Architecture 1 (Laboratory) 2.00 EIT 0323 Integrative Programming and Technologies (Lecture) 1.00 EIT 0323.1 Integrative Prograrming Technologies (Laboratory) 1.00 ETH 0008 Ethics 1.25 MiuxedTew2022-2022 CAP 0101 Capstone Project 1 1.00 EIT 0331 System Integration and Architecture 2 (Lecture) 2.25 EIT 0331.1 System Integration and Architecture 2 (Laboratory) 2.25 Lst Semester_ 2023-2024 CAP 0102 Capstone Project 2 1.00 EIT ELECTTVE 4 Professional Elective 1.25 EIT ELECTIVE 5 Professional Elective 5 1.00 EIT ELECTIVE 6 Professional Elective 6 1.UU College of Information System and Technology Management 2nd Semester_2023-2024 IIP 01014 Practicum (Lecture) 1.25 IIP 0101,1 Practicum (Immersion) 1.,25 Graduated with the degree of BACHELOR OF SCIENCE IN INFORMATION TECHNOLOGY, Magna Cum Laude on Septernber 5, 2024 a5 approved by the Pamantasan Univcrsity Council and by virtuc of Rcsolution No. 5321 of thc Board of Regents dated August 2,2024 Remarks: Grading System: 1.00-1.25, Excellent; 1.5-1.75_ Good; 2.00-2.25_ 3.UU, Passed; 5.00 , Falled; (5.00)_ Drupped Unufficially (DU); Ine fINCO, Inumple Credits; One unit of crcdit is one hour lecture or recitation, lhree hours of laboratory, draftin each week for the complele semester: This transcript is valid only when it bears the University seal and the original signaturd Any erasure 0r alteration made on this document renders # void unless initialed by thel Abesamis Aiver Santiago Prepared By: Released: Lee BENEDICTQ DBAREB_REA 0n FEB 2 5 2025 Checked by: M.Af Ybel Mundo Acting University Registrar by: Rcviscd Oclober, 1979 and and ard Very period
"""

# Simulate what the current logic might be doing or failing to do.
# The current logic likely sends this text to Gemini.
# We will try to simulate a regex extraction to see if we can parse it manually first,
# which helps in crafting the Gemini prompt.

# Pattern to find semesters
semester_pattern = re.compile(r'(1st|2nd|Summer|Mid|Ist|Znd|Lst)\s*Semester[s_,\s]*(\d{4}-\d{4})', re.IGNORECASE)

# Pattern to find course lines: Course Code (e.g., ICC 0101) + Title + Grade
# Note: The text has "Course No_ Descriplive Titlc Final Complction Credit" header
# Example line: ICC 0101 Introduction to Computing (Lecture) 1.50
course_pattern = re.compile(r'([A-Z]{2,4}\s*\d{3,4}(?:\.\d{1,2}[A-Z]?)?)\s+(.+?)\s+(\d\.\d{2}|1\.U0|1\.,25)', re.IGNORECASE)

print("--- Simulating Parsing ---")

current_semester = "Unknown Semester"
parsed_data = []

lines = ocr_text.split('\n')
for line in lines:
    line = line.strip()
    if not line: continue
    
    # Check for semester header
    sem_match = semester_pattern.search(line)
    if sem_match:
        current_semester = f"{sem_match.group(1)} Semester {sem_match.group(2)}"
        print(f"Found Semester: {current_semester}")
        continue
        
    # Check for course line
    course_match = course_pattern.search(line)
    if course_match:
        code = course_match.group(1)
        title = course_match.group(2)
        grade_str = course_match.group(3).replace('U', '0').replace(',', '.') # Fix OCR errors like 1.U0 -> 1.00
        
        print(f"  Found Course: {code} | {title} | {grade_str}")
        parsed_data.append({
            "semester": current_semester,
            "course_code": code,
            "subject": title,
            "grade": float(grade_str),
            "units": 3.0 # Defaulting units as they are not clearly aligned in text sometimes
        })

print(f"\nTotal Parsed: {len(parsed_data)}")
