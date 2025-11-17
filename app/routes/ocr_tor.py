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
from PIL import Image
import numpy as np
import cv2

# Text Matching and API Libraries
from difflib import get_close_matches
import google.generativeai as genai

# Flask and Project-Specific Imports
from flask_cors import CORS
from app.routes.objective_2 import id_to_axes as IT_SUBJECT_CODES, id_to_axes_cs as CS_SUBJECT_CODES
from app.routes.subject_master_list import SUBJECT_MASTER_DICT
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

# --- MASTER SUBJECT LIST ---
MASTER_SUBJECT_INFO = {code: info['title'].strip() for code, info in SUBJECT_MASTER_DICT.items()}
OFFICIAL_SUBJECTS = list(MASTER_SUBJECT_INFO.values())

def refine_with_gemini_layout_aware(ocr_results: list) -> Dict[str, Any]:
    """Uses Gemini to parse structured OCR data for better accuracy."""
    if not gemini_model:
        return {}

    print("[OCR_TOR] Attempting layout-aware refinement with Gemini...")
    ocr_data_for_prompt = [f'text: "{text}", position: ({int(bbox[0][0])}, {int(bbox[0][1])})' for (bbox, text, prob) in ocr_results]

    prompt = f"""
        You are an expert at reading academic transcripts. Below is OCR data with text and (x, y) coordinates.
        Accurately match each subject title with its final grade. The grade is usually in a column to the right.

        Reference Subject List:
        {json.dumps(OFFICIAL_SUBJECTS, indent=2)}

        OCR Data:
        ---
        {chr(10).join(ocr_data_for_prompt)}
        ---

        Return a clean JSON array of objects, where each object has a "subject" and a "grade" key. Match subjects to the reference list and ensure grades are numbers.
        Return only the JSON array.
        """
    try:
        request_options = {"timeout": 100}
        response = gemini_model.generate_content(prompt, request_options=request_options)
        
        cleaned_json_text = response.text.strip().replace("```json", "").replace("```", "")
        extracted_data = json.loads(cleaned_json_text)

        grades, grade_values, subject_pairs = [], [], []
        if isinstance(extracted_data, list):
            for item in extracted_data:
                if isinstance(item, dict) and 'subject' in item and 'grade' in item:
                    try:
                        grade_value = float(item['grade'])
                        subject = str(item['subject'])
                        grades.append({'subject': subject, 'grade': grade_value})
                        grade_values.append(grade_value)
                        subject_pairs.append({'subject': subject, 'grade': grade_value})
                    except (ValueError, TypeError):
                        continue
        print(f"[OCR_TOR] Gemini refinement successful. Extracted {len(grades)} pairs.")
        return {'grade_values': grade_values, 'grades': grades, 'subject_pairs': subject_pairs}
    except Exception as e:
        print(f"[OCR_TOR] Gemini refinement failed: {e}")
        return {}


def fuzzy_subject_match(line_text: str) -> str | None:
    line_lower = line_text.lower()
    for subject in OFFICIAL_SUBJECTS:
        if subject.lower() in line_lower:
            return subject
    matches = get_close_matches(line_lower, OFFICIAL_SUBJECTS, n=1, cutoff=0.7)
    return matches[0] if matches else None

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
        if gemini_results.get('grades'):
            final_grades = gemini_results['grades']
            it_course_ids = [grade['subject'] for grade in final_grades if grade['subject'] in IT_SUBJECT_CODES]
            cs_course_ids = [grade['subject'] for grade in final_grades if grade['subject'] in CS_SUBJECT_CODES]
            all_course_ids = it_course_ids + cs_course_ids
            return {
                'grade_values': [g['grade'] for g in final_grades],
                'grades': final_grades,
                'subject_pairs': [g['subject'] for g in final_grades],
                'full_text': full_text,
                'metadata': [{
                    'id': course_id,
                    'title': SUBJECT_MASTER_DICT[course_id]['title'],
                    'units': SUBJECT_MASTER_DICT[course_id]['units'],
                    'description': SUBJECT_MASTER_DICT[course_id]['description']
                } for course_id in all_course_ids]
            }

    print("[OCR_TOR] Gemini failed or was not used. Falling back to simple regex method.")
    grades, grade_values, subject_pairs = [], [], []
    grade_pattern = re.compile(r'\b[1-5]\.\d{2}\b')
    if full_text and "OCR Error" not in full_text:
        for line in full_text.split('\n'):
            found_grades = grade_pattern.findall(line)
            if not found_grades: continue
            subject_match = fuzzy_subject_match(line)
            if subject_match:
                for g in found_grades:
                    grade = float(g)
                    grades.append({'subject': subject_match, 'grade': grade})
                    subject_pairs.append({'subject': subject_match, 'grade': grade})
                    grade_values.append(grade)

    return {
        'grade_values': grade_values, 'grades': grades,
        'subject_pairs': subject_pairs, 'full_text': full_text
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