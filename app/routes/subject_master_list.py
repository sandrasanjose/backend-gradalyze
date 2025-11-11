from typing import Dict, Any

SUBJECT_MASTER_DICT: Dict[str, Dict[str, Any]] = {
    # --- BSIT Year 1 / First Semester ---
    'it_fy1_icc0101': {'title': 'Introduction to Computing (Lecture)', 'units': 3.0},
    'it_fy1_icc0101_1': {'title': 'Introduction to Computing (Laboratory)', 'units': 1.0},
    'it_fy1_icc0102': {'title': 'Fundamentals of Programming (Lecture)', 'units': 3.0},
    'it_fy1_icc0102_1': {'title': 'Fundamentals of Programming (Laboratory)', 'units': 1.0},
    'it_fy1_ipp0010': {'title': 'Interdisiplinaryong Pagbasa at Pagsulat Tungo sa Mabisang Pagpapahayag', 'units': 3.0},
    'it_fy1_mmw0001': {'title': 'Mathematics in the Modern World', 'units': 3.0},
    'it_fy1_pcm0006': {'title': 'Purposive Communication', 'units': 3.0},
    'it_fy1_sts0002': {'title': 'Science, Technology and Society', 'units': 3.0},
    'it_fy1_aap0007': {'title': 'Art Appreciation', 'units': 3.0},
    'it_fy1_ped0001': {'title': 'Foundation of Physical Activities', 'units': 1.0},
    'it_fy1_nstp01': {'title': 'National Service Training Program 1', 'units': 1.5},

    # --- BSIT Year 1 / Second Semester ---
    'it_fy2_cet0111': {'title': 'Calculus 1', 'units': 3.0},
    'it_fy2_cet0114': {'title': 'General Chemistry (Lecture)', 'units': 3.0},
    'it_fy2_cet0114_1': {'title': 'General Chemistry (Laboratory)', 'units': 1.0},
    'it_fy2_eit0121': {'title': 'Introduction to Computer Human Interaction (Lecture)', 'units': 2.0},
    'it_fy2_eit0121_1a': {'title': 'Introduction to Computer Human Interaction (Laboratory)', 'units': 1.0},
    'it_fy2_eit0122': {'title': 'Discrete Mathematics', 'units': 3.0},
    'it_fy2_eit0123': {'title': 'Web Systems Technology (Lecture)', 'units': 2.0},
    'it_fy2_eit0123_1': {'title': 'Web Systems Technology (Laboratory)', 'units': 1.0},
    'it_fy2_gtb121': {'title': 'Great Books', 'units': 3.0},
    'it_fy2_icc0103': {'title': 'Intermediate Programming (Lecture)', 'units': 3.0},
    'it_fy2_icc0103_1': {'title': 'Intermediate Programming (Laboratory)', 'units': 1.0},
    'it_fy2_ped0013': {'title': 'Philippine Folk Dance', 'units': 1.0},
    'it_fy2_nstp02': {'title': 'National Service Training Program 2', 'units': 1.5},

    # --- BSIT Year 2 / First Semester ---
    'it_sy1_cet0121': {'title': 'Calculus 2', 'units': 3.0},
    'it_sy1_cet0225': {'title': 'Physics for IT (Lecture)', 'units': 3.0},
    'it_sy1_cet0225_1': {'title': 'Physics for IT (Laboratory)', 'units': 1.0},
    'it_sy1_eit0211': {'title': 'Object Oriented Programming (Lecture)', 'units': 2.0},
    'it_sy1_eit0211_1a': {'title': 'Object Oriented Programming (Laboratory)', 'units': 1.0},
    'it_sy1_eit_elective1': {'title': 'Professional Elective 1 - Software Quality Assurance', 'units': 3.0},
    'it_sy1_icc0104': {'title': 'Data Structures and Algorithms (Lecture)', 'units': 2.0},
    'it_sy1_icc0104_1': {'title': 'Data Structures and Algorithms (Laboratory)', 'units': 1.0},
    'it_sy1_ppc122': {'title': 'Philippine Popular Culture', 'units': 3.0},
    'it_sy1_tcw0005': {'title': 'The Contemporary World', 'units': 3.0},
    'it_sy1_ped0054': {'title': 'Soccer', 'units': 1.0},

    # --- BSIT Year 2 / Second Semester ---
    'it_sy2_eit0212': {'title': 'Platform Technology', 'units': 3.0},
    'it_sy2_eit0221': {'title': 'Quantitative Methods', 'units': 3.0},
    'it_sy2_eit0222': {'title': 'Networking 1 (Lecture)', 'units': 2.0},
    'it_sy2_eit0222_1': {'title': 'Networking 1 (Laboratory)', 'units': 1.0},
    'it_sy2_eit_elective2': {'title': 'Professional Elective 2 - System Analysis and Design', 'units': 3.0},
    'it_sy2_ges0013': {'title': 'Environmental Science', 'units': 3.0},
    'it_sy2_icc0105': {'title': 'Information Management (Lecture)', 'units': 2.0},
    'it_sy2_icc0105_1': {'title': 'Information Management (Laboratory)', 'units': 1.0},
    'it_sy2_rph0004': {'title': 'Readings in Philippine History', 'units': 3.0},
    'it_sy2_uts0003': {'title': 'Understanding the Self', 'units': 3.0},
    'it_sy2_ped0074': {'title': 'PE Elective', 'units': 1.0},

    # --- BSIT Year 3 / First Semester ---
    'it_ty1_eit0311': {'title': 'Advanced Database Systems (Lecture)', 'units': 2.0},
    'it_ty1_eit0311_1': {'title': 'Advanced Database Systems (Laboratory)', 'units': 1.0},
    'it_ty1_eit0312': {'title': 'Networking 2 (Lecture)', 'units': 2.0},
    'it_ty1_eit0312_1': {'title': 'Networking 2 (Laboratory)', 'units': 1.0},
    'it_ty1_eit_elective3': {'title': 'Professional Elective 3 - Software Engineering', 'units': 3.0},
    'it_ty1_icc0335': {'title': 'Application and Emerging Technologies (Lecture)', 'units': 2.0},
    'it_ty1_icc0335_1': {'title': 'Application and Emerging Technologies (Laboratory)', 'units': 1.0},
    'it_ty1_lwr0009': {'title': 'Life and Works of Rizal', 'units': 3.0},

    # --- BSIT Year 3 / Second Semester ---
    'it_ty2_eit0321': {'title': 'Information Assurance and Security 1 (Lecture)', 'units': 2.0},
    'it_ty2_eit0321_1': {'title': 'Information Assurance and Security 1 (Laboratory)', 'units': 1.0},
    'it_ty2_eit0322': {'title': 'System Integration and Architecture 1 (Lecture)', 'units': 2.0},
    'it_ty2_eit0322_1': {'title': 'System Integration and Architecture 1 (Laboratory)', 'units': 1.0},
    'it_ty2_eit0323': {'title': 'Integrative Programming and Technologies (Lecture)', 'units': 2.0},
    'it_ty2_eit0323_1': {'title': 'Integrative Programming and Technologies (Laboratory)', 'units': 1.0},
    'it_ty2_eth0008': {'title': 'Ethics', 'units': 3.0},

    # --- BSIT Year 3 / Midyear/Summer Term ---
    'it_my_cap0101': {'title': 'Capstone Project 1', 'units': 3.0},
    'it_my_eit0331': {'title': 'System Integration and Architecture 2 (Lecture)', 'units': 2.0},
    'it_my_eit0331_1': {'title': 'System Integration and Architecture 2 (Laboratory)', 'units': 1.0},

    # --- BSIT Year 4 / First Semester ---
    'it_fy4_cap0102': {'title': 'Capstone Project 2', 'units': 3.0},
    'it_fy4_eit_elective4': {'title': 'Professional Elective 4', 'units': 3.0},
    'it_fy4_eit_elective5': {'title': 'Professional Elective 5 - Software Testing', 'units': 3.0},
    'it_fy4_eit_elective6': {'title': 'Professional Elective 6 - Seminar and Field Trip', 'units': 3.0},

    # --- BSIT Year 4 / Second Semester ---
    'it_fy4b_iip0101a': {'title': 'Practicum Lecture', 'units': 2.0},
    'it_fy4b_iip0101_1': {'title': 'Practicum Immersion', 'units': 4.0},

    # --- BSCS Year 1 / First Semester ---
    'cs_fy1_csc0102': {'title': 'Discrete Structures 1', 'units': 3.0},
    'cs_fy1_icc0101': {'title': 'Introduction to Computing (Lecture)', 'units': 2.0},
    'cs_fy1_icc0101_1': {'title': 'Introduction to Computing (Laboratory)', 'units': 1.0},
    'cs_fy1_icc0102': {'title': 'Fundamentals of Programming (Lecture)', 'units': 2.0},
    'cs_fy1_icc0102_1': {'title': 'Fundamentals of Programming (Laboratory)', 'units': 1.0},
    'cs_fy1_ipp0010': {'title': 'Interdisiplinaryong Pagbasa at Pagsulat Tungo sa Mabisang Pagpapahayag', 'units': 3.0},
    'cs_fy1_mmw0001': {'title': 'Mathematics in the Modern World', 'units': 3.0},
    'cs_fy1_ped0001': {'title': 'Foundation of Physical Activities', 'units': 2.0},
    'cs_fy1_pcm0006': {'title': 'Purposive Communication', 'units': 3.0},  
    'cs_fy1_sts0002': {'title': 'Science, Technology and Society', 'units': 3.0},
    'cs_fy1_nstp01': {'title': 'National Service Training Program 1', 'units': 3.0},

    # --- BSCS Year 1 / Second Semester ---
    'cs_fy2_csc0211': {'title': 'Discrete Structures 2', 'units': 3.0},  
    'cs_fy2_csc0223': {'title': 'Human Computer Interaction', 'units': 3.0},
    'cs_fy2_icc0103': {'title': 'Intermediate Programming (Lecture)', 'units': 2.0},
    'cs_fy2_icc0103_1': {'title': 'Intermediate Programming (Laboratory)', 'units': 1.0},
    'cs_fy2_icc0104': {'title': 'Data Structures & Algorithms (Lecture)', 'units': 2.0},
    'cs_fy2_icc0104_1': {'title': 'Data Structures & Algorithms (Laboratory)', 'units': 1.0},
    'cs_fy2_lwr0009': {'title': 'Life and Works of Rizal', 'units': 3.0},
    'cs_fy2_ped0012': {'title': 'Group Exercise', 'units': 2.0},
    'cs_fy2_rph0004': {'title': 'Readings in Philippine History', 'units': 3.0},
    'cs_fy2_tcw0005': {'title': 'The Contemporary World', 'units': 3.0},
    'cs_fy2_nstp02': {'title': 'National Service Training Program 2', 'units': 3.0},

    # --- BSCS Year 2 / First Semester ---  
    'cs_sy1_csc0212': {'title': 'Object Oriented Programming (Lecture)', 'units': 2.0},
    'cs_sy1_csc0212_1': {'title': 'Object Oriented Programming (Laboratory)', 'units': 1.0},
    'cs_sy1_csc0213': {'title': 'Logic Design and Digital Computer Circuits (Lecture)', 'units': 2.0},
    'cs_sy1_csc0213_1': {'title': 'Logic Design and Digital Computer Circuits (Laboratory)', 'units': 1.0},
    'cs_sy1_csc0224': {'title': 'Operation Research', 'units': 3.0},
    'cs_sy1_eth0008': {'title': 'Ethics', 'units': 3.0},
    'cs_sy1_icc0105': {'title': 'Information Management (Lecture)', 'units': 2.0},
    'cs_sy1_icc0105_1': {'title': 'Information Management (Laboratory)', 'units': 1.0},
    'cs_sy1_ite0001': {'title': 'Living in the IT Era', 'units': 3.0},
    'cs_sy1_ped0074': {'title': 'PE Elective', 'units': 2.0},
    'cs_sy1_uts0003': {'title': 'Understanding the Self', 'units': 3.0},

    # --- BSCS Year 2 / Second Semester ---
    'cs_sy2_cbm0016': {'title': 'The Entrepreneurial Mind', 'units': 3.0},
    'cs_sy2_csc0221': {'title': 'Algorithm and Complexity', 'units': 3.0},
    'cs_sy2_csc0222': {'title': 'Architecture and Organization (Lecture)', 'units': 2.0},
    'cs_sy2_csc0222_1': {'title': 'Architecture and Organization (Laboratory)', 'units': 1.0},
    'cs_sy2_csc0316': {'title': 'Information Assurance and Security', 'units': 3.0},
    'cs_sy2_ges0013': {'title': 'Environmental Science', 'units': 3.0},
    'cs_sy2_icc0106': {'title': 'Application Dev & Emerging Technologies (Lecture)', 'units': 2.0},
    'cs_sy2_icc0106_1': {'title': 'Application Dev & Emerging Technologies (Laboratory)', 'units': 1.0},
    'cs_sy2_ped0023': {'title': 'PE Elective 2', 'units': 2.0},
    'cs_sy2_aap0007': {'title': 'Art Appreciation', 'units': 3.0},

    # --- BSCS Year 3 / First Semester ---
    'cs_ty1_csc0311': {'title': 'Automata Theory and Formal Languages', 'units': 3.0},
    'cs_ty1_csc0312': {'title': 'Programming Languages (Lecture)', 'units': 2.0},
    'cs_ty1_csc0312_1': {'title': 'Programming Languages (Laboratory)', 'units': 1.0},
    'cs_ty1_csc0313': {'title': 'Software Engineering (Lecture)', 'units': 2.0},
    'cs_ty1_csc0313_1': {'title': 'Software Engineering (Laboratory)', 'units': 1.0},
    'cs_ty1_csc0314': {'title': 'Operating System (Lecture)', 'units': 2.0},
    'cs_ty1_csc0314_1': {'title': 'Operating System (Laboratory)', 'units': 1.0},
    'cs_ty1_csc0315': {'title': 'Intelligent System (Lecture)', 'units': 2.0},
    'cs_ty1_csc0315_1': {'title': 'Intelligent System (Laboratory)', 'units': 1.0},

    # --- BSCS Year 3 / Second Semester ---
    'cs_ty2_csc0321': {'title': 'Software Engineering 2 (Lecture)', 'units': 2.0},
    'cs_ty2_csc0321_1': {'title': 'Software Engineering 2 (Laboratory)', 'units': 1.0},
    'cs_ty2_csc0322': {'title': 'Compiler Design (Lecture)', 'units': 2.0},
    'cs_ty2_csc0322_1': {'title': 'Compiler Design (Laboratory)', 'units': 1.0},
    'cs_ty2_csc0323': {'title': 'Computational Science (Lecture)', 'units': 2.0},
    'cs_ty2_csc0323_1': {'title': 'Computational Science (Laboratory)', 'units': 1.0},
    'cs_ty2_csc0324': {'title': 'CS Elective 1 (Lecture)', 'units': 2.0},
    'cs_ty2_csc0324_1': {'title': 'CS Elective 1 (Laboratory)', 'units': 1.0},
    'cs_ty2_csc0325': {'title': 'Research Writing', 'units': 3.0},

    # --- BSCS Year 3 / Midyear/Summer Term ---
    'cs_ty_csc195_1': {'title': 'Practicum (240 hrs)', 'units': 2.0},

    # --- BSCS Year 4 / First Semester ---
    'cs_fy4_csc0411': {'title': 'CS Thesis Writing 1', 'units': 3.0},
    'cs_fy4_csc0412': {'title': 'Networks and Communication (Lecture)', 'units': 2.0},
    'cs_fy4_csc0412_1': {'title': 'Networks and Communication (Laboratory)', 'units': 1.0},
    'cs_fy4_csc0413': {'title': 'CS Elective 2 (Lecture)', 'units': 2.0},
    'cs_fy4_csc0413_1': {'title': 'CS Elective 2 (Laboratory)', 'units': 1.0},
    'cs_fy4_csc0414': {'title': 'CS Elective 3 (Lecture)', 'units': 2.0},
    'cs_fy4_csc0414_1': {'title': 'CS Elective 3 (Laboratory)', 'units': 1.0},

    # --- BSCS Year 4 / Second Semester ---
    'cs_fy4b_csc0421a': {'title': 'CS Thesis Writing 2', 'units': 3.0},
    'cs_fy4b_csc0422': {'title': 'Parallel and Distributing Computing (Lecture)', 'units': 2.0},
    'cs_fy4b_csc0422_1': {'title': 'Parallel and Distributed Computing (Laboratory)', 'units': 1.0},
    'cs_fy4b_csc0423': {'title': 'Social Issues and Professional Practice', 'units': 3.0},
    'cs_fy4b_csc0424': {'title': 'Graphics and Visual Computing (Lecture)', 'units': 2.0},
    'cs_fy4b_csc0424_1': {'title': 'Graphics and Visual Computing (Laboratory)', 'units': 1.0},
}

MASTER_SUBJECT_CODES = list(SUBJECT_MASTER_DICT.keys())
