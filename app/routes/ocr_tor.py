from flask import Blueprint, request, jsonify
import io
import re
import json
import os
from typing import Dict, Any

# OCR and PDF Processing Libraries
import pdfplumber
import easyocr
import pypdfium2 as pdfium
import numpy as np

# Text Matching and API Libraries
import google.generativeai as genai

# Flask and Project-Specific Imports
from flask_cors import CORS
from app.services.supabase_client import get_supabase_client

# --- BLUEPRINT SETUP ---
bp = Blueprint('ocr_tor', __name__, url_prefix='/api/ocr-tor')
CORS(bp, resources={r"/api/ocr-tor/*": {"origins": "http://localhost:5173"}}, supports_credentials=True)

# --- INITIALIZE OCR ENGINE ---
try:
    EASYOCR_READER = easyocr.Reader(['en'], gpu=False)
    print("[OCR_TOR] EasyOCR reader initialized successfully.")
except Exception as e:
    EASYOCR_READER = None
    print(f"[OCR_TOR] WARNING: Failed to initialize EasyOCR reader: {e}")

# --- INITIALIZE GEMINI API ---
try:
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    if not GEMINI_API_KEY:
        gemini_model = None
        print("[OCR_TOR] WARNING: GEMINI_API_KEY not found. Gemini refinement is disabled.")
    else:
        genai.configure(api_key=GEMINI_API_KEY)
        # This model name is correct and will work with the updated library
        gemini_model = genai.GenerativeModel('models/gemini-pro-latest')
        print("[OCR_TOR] Gemini model initialized successfully.")
except Exception as e:
    gemini_model = None
    print(f"[OCR_TOR] WARNING: Failed to initialize Gemini model: {e}")

def refine_with_gemini_layout_aware(ocr_results: list) -> Dict[str, Any]:
    """Uses Gemini to parse structured OCR data and extract course information directly from TOR."""
    if not gemini_model:
        return {}

    print("[OCR_TOR] Attempting layout-aware refinement with Gemini...")
    ocr_data_for_prompt = [f'text: "{text}", position: ({int(bbox[0][0])}, {int(bbox[0][1])})' for (bbox, text, prob) in ocr_results]

    prompt = f"""
        You are an expert at reading academic transcripts (Transcript of Records). Below is OCR data with text and (x, y) coordinates.
        
        Extract all courses from this transcript. For each course, identify:
        1. Course code/number (e.g., "CS101", "IT-101", "MATH 101")
        2. Descriptive title (the full course name)
        3. Units (credit hours/units for the course)
        4. Grade (the final grade received, usually a number like 1.0, 2.5, 3.0, etc.)

        OCR Data:
        ---
        {chr(10).join(ocr_data_for_prompt)}
        ---

        Return a clean JSON array of objects, where each object has:
        - "course_code": the course code/number (string)
        - "title": the descriptive course title (string)
        - "units": the number of units/credits (number)
        - "grade": the final grade (number)

        Extract ALL courses you can find in the transcript. Do not filter or match to any reference list - just extract what is actually in the document.
        Return only the JSON array.
        """
    try:
        request_options = {"timeout": 100}
        response = gemini_model.generate_content(prompt, request_options=request_options)
        
        cleaned_json_text = response.text.strip().replace("```json", "").replace("```", "")
        extracted_data = json.loads(cleaned_json_text)

        courses = []
        grade_values = []
        if isinstance(extracted_data, list):
            for item in extracted_data:
                if isinstance(item, dict):
                    try:
                        course_code = str(item.get('course_code', item.get('code', ''))).strip()
                        title = str(item.get('title', item.get('subject', ''))).strip()
                        units = float(item.get('units', item.get('unit', 0)))
                        grade = float(item.get('grade', 0))
                        
                        if course_code and title and grade > 0:
                            course_data = {
                                'course_code': course_code,
                                'title': title,
                                'units': units,
                                'grade': grade
                            }
                            courses.append(course_data)
                            grade_values.append(grade)
                    except (ValueError, TypeError) as e:
                        print(f"[OCR_TOR] Skipping invalid course entry: {item}, error: {e}")
                        continue
        print(f"[OCR_TOR] Gemini refinement successful. Extracted {len(courses)} courses.")
        return {'courses': courses, 'grade_values': grade_values}
    except Exception as e:
        print(f"[OCR_TOR] Gemini refinement failed: {e}")
        return {}


def extract_course_from_line(line_text: str) -> Dict[str, Any] | None:
    """Extract course information from a line of text using regex patterns."""
    if not line_text or len(line_text.strip()) < 3:
        return None
    
    # Pattern for course code (alphanumeric with possible dashes/spaces)
    course_code_pattern = re.compile(r'\b([A-Z]{2,4}[\s\-]?\d{3,4})\b', re.IGNORECASE)
    # Pattern for grade (1.0 to 5.0 scale)
    grade_pattern = re.compile(r'\b([1-5]\.\d{1,2})\b')
    # Pattern for units (usually 1-6 digits, sometimes with decimals)
    units_pattern = re.compile(r'\b(\d{1,2}(?:\.\d+)?)\s*(?:units?|credits?|hrs?)?\b', re.IGNORECASE)
    
    course_code_match = course_code_pattern.search(line_text)
    grade_match = grade_pattern.search(line_text)
    units_match = units_pattern.search(line_text)
    
    if not grade_match:
        return None
    
    course_code = course_code_match.group(1) if course_code_match else ""
    grade = float(grade_match.group(1))
    units = float(units_match.group(1)) if units_match else 0.0
    
    # Extract title (everything except course code, grade, and units)
    title = line_text.strip()
    if course_code_match:
        title = title.replace(course_code_match.group(1), "").strip()
    if grade_match:
        title = title.replace(grade_match.group(1), "").strip()
    if units_match:
        title = title.replace(units_match.group(1), "").strip()
    # Clean up common words
    title = re.sub(r'\b(units?|credits?|hrs?)\b', '', title, flags=re.IGNORECASE).strip()
    title = re.sub(r'\s+', ' ', title).strip()
    
    if not title:
        return None
    
    return {
        'course_code': course_code,
        'title': title,
        'units': units,
        'grade': grade
    }

def has_meaningful_text(text: str) -> bool:
    if not text or len(text.strip()) < 50: return False
    return any(char.isdigit() for char in text)

def extract_grades_from_tor(file_bytes: bytes, filename: str) -> Dict[str, Any]:
    full_text = ""
    raw_ocr_results = []

    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            temp_text = "".join(page.extract_text() or "" for page in pdf.pages)
        if has_meaningful_text(temp_text):
            full_text = temp_text
            print(f"[OCR_TOR] Text extracted using pdfplumber for {filename}.")
    except Exception:
        print(f"[OCR_TOR] Not a text-based PDF. Defaulting to EasyOCR.")

    if not full_text:
        if not EASYOCR_READER:
            return {'full_text': "OCR Error: EasyOCR is not initialized.", 'grades': [], 'grade_values': [], 'subject_pairs': []}
        try:
            print(f"[OCR_TOR] Starting EasyOCR extraction for {filename}")
            pdf = pdfium.PdfDocument(io.BytesIO(file_bytes))
            for i, page in enumerate(pdf):
                print(f"[OCR_TOR] Processing page {i+1}/{len(pdf)} with EasyOCR...")
                # Reduced scale for much faster processing
                pil_image = page.render(scale=2).to_pil()
                image_np = np.array(pil_image)
                
                results = EASYOCR_READER.readtext(image_np, detail=1)
                raw_ocr_results.extend(results)
                full_text += " ".join([res[1] for res in results]) + "\n"
        except Exception as ocr_error:
            full_text = f"OCR Error: {str(ocr_error)}"
            print(f"[OCR_TOR] EasyOCR extraction failed: {ocr_error}")

    if raw_ocr_results and gemini_model:
        gemini_results = refine_with_gemini_layout_aware(raw_ocr_results)
        if gemini_results.get('courses'):
            courses = gemini_results['courses']
            return {
                'grade_values': gemini_results.get('grade_values', [g['grade'] for g in courses]),
                'grades': courses,
                'subject_pairs': courses,  # For backward compatibility
                'courses': courses,  # Main data structure
                'full_text': full_text
            }

    print("[OCR_TOR] Gemini failed or was not used. Falling back to regex extraction method.")
    courses = []
    grade_values = []
    
    if full_text and "OCR Error" not in full_text:
        for line in full_text.split('\n'):
            course_data = extract_course_from_line(line)
            if course_data:
                courses.append(course_data)
                grade_values.append(course_data['grade'])

    return {
        'grade_values': grade_values,
        'grades': courses,
        'subject_pairs': courses,  # For backward compatibility
        'courses': courses,  # Main data structure
        'full_text': full_text
    }


@bp.route('/process', methods=['POST'])
def process_tor_endpoint():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected for uploading'}), 400
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'Invalid file type, please upload a PDF'}), 400

    try:
        file_bytes = file.read()
        filename = file.filename
        print(f"[OCR_TOR] Received file for processing: {filename}")
        result = extract_grades_from_tor(file_bytes, filename)
        return jsonify({'success': True, **result}), 200
    except Exception as e:
        print(f"[OCR_TOR] An unexpected error occurred: {e}")
        return jsonify({'error': f'An internal error occurred: {e}'}), 500

# --- Grades CRUD over users.grades ---
@bp.route('/get/<int:user_id>', methods=['GET'])
def get_user_grades(user_id: int):
    try:
        supabase = get_supabase_client()
        resp = supabase.table('users').select('grades').eq('user_id', user_id).limit(1).execute()
        if not resp.data:
            return jsonify({'message': 'User not found'}), 404
        grades = resp.data[0].get('grades') or []
        return jsonify({'grades': grades}), 200
    except Exception as e:
        return jsonify({'message': 'Failed to get grades', 'error': str(e)}), 500

@bp.route('/update/<int:user_id>', methods=['POST'])
def update_user_grades(user_id: int):
    try:
        payload = request.get_json(silent=True) or {}
        grades = payload.get('grades') or []
        supabase = get_supabase_client()
        upd = supabase.table('users').update({'grades': grades}).eq('user_id', user_id).execute()
        saved = (upd.data[0].get('grades') if upd.data else grades) or grades
        return jsonify({'message': 'updated', 'grades': saved}), 200
    except Exception as e:
        return jsonify({'message': 'Failed to update grades', 'error': str(e)}), 500

@bp.route('/add/<int:user_id>', methods=['POST'])
def add_user_grade(user_id: int):
    try:
        payload = request.get_json(silent=True) or {}
        grade = payload.get('grade') or None
        if grade is None:
            return jsonify({'message': 'grade is required'}), 400
        supabase = get_supabase_client()
        resp = supabase.table('users').select('grades').eq('user_id', user_id).limit(1).execute()
        if not resp.data:
            return jsonify({'message': 'User not found'}), 404
        grades = resp.data[0].get('grades') or []
        grades.append(grade)
        upd = supabase.table('users').update({'grades': grades}).eq('user_id', user_id).execute()
        saved = (upd.data[0].get('grades') if upd.data else grades) or grades
        return jsonify({'message': 'added', 'grades': saved}), 200
    except Exception as e:
        return jsonify({'message': 'Failed to add grade', 'error': str(e)}), 500

@bp.route('/delete/<int:user_id>', methods=['POST'])
def delete_user_grade(user_id: int):
    try:
        payload = request.get_json(silent=True) or {}
        grade_id = payload.get('grade_id')
        if not grade_id:
            return jsonify({'message': 'grade_id is required'}), 400
        supabase = get_supabase_client()
        resp = supabase.table('users').select('grades').eq('user_id', user_id).limit(1).execute()
        if not resp.data:
            return jsonify({'message': 'User not found'}), 404
        grades = resp.data[0].get('grades') or []
        new_grades = [g for g in grades if (g or {}).get('id') != grade_id]
        upd = supabase.table('users').update({'grades': new_grades}).eq('user_id', user_id).execute()
        saved = (upd.data[0].get('grades') if upd.data else new_grades) or new_grades
        return jsonify({'message': 'deleted', 'grades': saved}), 200
    except Exception as e:
        return jsonify({'message': 'Failed to delete grade', 'error': str(e)}), 500