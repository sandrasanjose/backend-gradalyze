from flask import Blueprint, request, jsonify
import io
import re
import json
import os
import time
from typing import Dict, Any

# OCR and PDF Processing Libraries
import pdfplumber
import easyocr
import pypdfium2 as pdfium
from PIL import Image, ImageOps, ImageEnhance
import numpy as np

# API Libraries
import google.generativeai as genai
from google.api_core import retry

# Flask and Project-Specific Imports
from flask_cors import CORS

# --- BLUEPRINT SETUP ---
bp = Blueprint('ocr_tor', __name__, url_prefix='/api/ocr-tor')
CORS(bp, resources={r"/api/ocr-tor/*": {"origins": "*"}}, supports_credentials=True)

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
        # User requested to focus on the best model for the system.
        # We found 'models/gemini-2.5-flash' in the list, which is the latest efficient model.
        # We also allow an override via environment variable.
        selected_model = os.getenv('GEMINI_MODEL_NAME', 'models/gemini-2.5-flash')
        
        genai.configure(api_key=GEMINI_API_KEY)
        gemini_model = genai.GenerativeModel(selected_model)
        
        print(f"[OCR_TOR] Gemini model initialized: {selected_model}")

except Exception as e:
    gemini_model = None
    print(f"[OCR_TOR] WARNING: Failed to initialize Gemini model: {e}")


def preprocess_image(pil_image):
    """
    Preprocesses the image for better OCR accuracy.
    - Converts to grayscale
    - Enhances contrast
    """
    try:
        # 1. Convert to Grayscale
        gray_image = ImageOps.grayscale(pil_image)
        
        # 2. Enhance Contrast (Factor 2.0 is usually good for text)
        enhancer = ImageEnhance.Contrast(gray_image)
        enhanced_image = enhancer.enhance(2.0)
        
        return enhanced_image
    except Exception as e:
        print(f"[OCR_TOR] Image preprocessing failed: {e}")
        return pil_image

def generate_with_retry(model, prompt, retries=3, initial_delay=60, **kwargs):
    """
    Wraps model.generate_content with retry logic for 429 Rate Limit errors.
    """
    import time
    if not model: return None
    
    current_delay = initial_delay
    
    for attempt in range(retries):
        try:
            # Add strict timeout to prevent hanging
            request_options = kwargs.pop('request_options', {"timeout": 600})
            return model.generate_content(prompt, request_options=request_options, **kwargs)
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "quota" in error_str.lower():
                print(f"[OCR_TOR] Rate Limit Hit (429). Waiting {current_delay}s before retry {attempt+1}/{retries}...")
                time.sleep(current_delay)
                current_delay *= 2 # Exponential backoff
            else:
                print(f"[OCR_TOR] Gemini Error (Non-Retryable): {e}")
                raise e
    
    print("[OCR_TOR] Max retries exceeded for Gemini API.")
    return None


def convert_percentage_to_grade(value: float, program: str = 'CS') -> float:
    """
    Converts a percentage grade (0-100) to a 1.0-5.0 scale.
    1.0 is highest, 5.0 is lowest/failing.
    """
    if value >= 97: return 1.00
    if value >= 94: return 1.25
    if value >= 91: return 1.50
    if value >= 88: return 1.75
    if value >= 85: return 2.00
    if value >= 82: return 2.25
    if value >= 79: return 2.50
    if value >= 76: return 2.75
    
    # Passing threshold check
    if program == 'IT':
        if value >= 70: return 3.00
    else:
        # CS or Default
        if value >= 75: return 3.00
        
    return 5.00

def refine_page_with_gemini(page_text_fragments, page_num):
    """
    Refines a SINGLE page of OCR data.
    """
    if not gemini_model: 
        return []

    # Format fragments
    # fragments is list of (bbox, text, prob)
    # text_block = "\n".join([f'text: "{t}", y: {int(b[0][1])}' for (b, t, p) in page_text_fragments[:300]])
    # SIMPLIFIED: Just send the text lines in order (EasyOCR usually sorts top-bottom)
    text_block = "\n".join([t for (b, t, p) in page_text_fragments])

    prompt = f"""
    You are an expert Transcript Digitizer.
    EXTRACT the table of academic grades from this OCR text (Page {page_num}).

    OCR TEXT:
    ---
    {text_block}
    ---

    CONTEXT (Common Subjects):
    [ICC 0101 Intro to Computing, CET 0111 Calculus, EIT 0121 HCI, etc.]

    RULES:
    1. Find rows with: Course Code (e.g., "ICC 0101"), Subject Title, and Grade.
    2. "Grade" is typically a number (1.00-5.00) or percentage (70-100).
    3. Ignore headers, footers, and signing blocks.
    4. If a row is "1st Semester" or "Year", ignore it (we handle semesters globally or you can tag it if attached to course).

    OUTPUT JSON (List of Objects):
    [
      {{
        "courseCode": "ICC 0101",
        "subject": "Introduction to Computing",
        "grade": 1.5,
        "units": 3.0,
        "semester": "Detected Semester"
      }}
    ]
    """

    try:
        # Use retry logic
        response = generate_with_retry(
            gemini_model, 
            prompt, 
            generation_config={"response_mime_type": "application/json"}
        )
        
        if not response: return []

        # Parse
        text = response.text.strip()
        data = json.loads(text)
        
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            return data.get('grades', []) or data.get('data', []) or []
        
        return []

    except Exception as e:
        print(f"[OCR_TOR] Page {page_num} refinement failed: {e}")
        return []

def extract_grades_from_tor(file_bytes: bytes, filename: str) -> Dict[str, Any]:
    full_text = ""
    
    if not EASYOCR_READER:
        return {'grades': [], 'grade_values': [], 'error': 'OCR Engine not initialized'}
    
    try:
        # Load PDF
        pdf = pdfium.PdfDocument(io.BytesIO(file_bytes))
        total_pages = len(pdf)
        print(f"[OCR_TOR] PDF loaded. Total pages: {total_pages}")

        final_grades = []

        # --- PROCESS PAGES SEQUENTIALLY ---
        for i, page in enumerate(pdf):
            page_num = i + 1
            print(f"[OCR_TOR] Processing Page {page_num} of {total_pages}...")
            
            # 1. OCR
            pil_image = page.render(scale=3).to_pil() 
            pil_image = preprocess_image(pil_image)
            raw_results = EASYOCR_READER.readtext(np.array(pil_image), detail=1)
            
            page_text = " ".join([r[1] for r in raw_results])
            full_text += page_text + "\n"

            if not raw_results:
                continue

            # 2. Gemini Refinement (Per Page)
            page_grades = refine_page_with_gemini(raw_results, page_num)
            
            # 3. Clean & Append
            for g in page_grades:
                try:
                    # Normalize keys
                    g['courseCode'] = g.get('courseCode') or g.get('course_code') or g.get('code') or ''
                    g['subject'] = g.get('subject') or g.get('title') or g.get('descriptive_title') or ''
                    
                    # Grade validation
                    raw_g = g.get('grade')
                    if raw_g is None: continue
                    g['grade'] = float(raw_g)
                    
                    # Units
                    g['units'] = float(g.get('units') or 3.0)
                    
                    # Semester fallback
                    if 'semester' not in g: g['semester'] = 'Detected Subjects'

                    final_grades.append(g)
                except Exception:
                    continue
            
            print(f"[OCR_TOR] Page {page_num} extracted {len(page_grades)} grades.")
            
            # PACING: Wait 2 seconds between pages to prevent 429
            if i < total_pages - 1:
                time.sleep(2.0)

    except Exception as e:
        print(f"[OCR_TOR] PDF Processing Error: {e}")
        return {'error': str(e)}

    # --- PHASE 3: POST-PROCESSING & CONVERSION ---
    # Determine Program (IT vs CS)
    program = 'CS'
    if 'information technology' in full_text.lower() or 'bsit' in full_text.lower():
        program = 'IT'
    print(f"[OCR_TOR] Detected Program: {program}")

    # Standardize Grades (Percentage -> 1.0-5.0)
    final_values = []
    for item in final_grades:
        g_val = item['grade']
        if g_val > 5.0:
            # Simple standard conversion (no custom scale extraction for now to keep it robust)
            # Or we could do a quick separate pass for scale if strictly needed, 
            # but user prioritized "working well" over "dynamic scale".
            converted = convert_percentage_to_grade(g_val, program)
            item['grade'] = converted
            g_val = converted
            
        final_values.append(g_val)

    print(f"[OCR_TOR] Total extracted grades: {len(final_grades)}")

    return {
        'grades': final_grades, 
        'grade_values': final_values, 
        'full_text': full_text
    }

@bp.route('/process', methods=['POST'])
def process_tor_endpoint():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'Invalid file type, please upload a PDF'}), 400

    try:
        print(f"[OCR_TOR] Received file: {file.filename}")
        file_bytes = file.read()
        result = extract_grades_from_tor(file_bytes, file.filename)
        return jsonify({'success': True, **result}), 200
    except Exception as e:
        print(f"[OCR_TOR] Unexpected error: {e}")
        return jsonify({'error': str(e)}), 500

# --- CRUD Endpoints (Preserved) ---
def get_supabase_client():
    # Placeholder: Ensure you have your actual supabase initialization here
    from supabase import create_client, Client
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY")
    
    if not url:
        raise ValueError("SUPABASE_URL is missing from environment variables")
    if not key:
        raise ValueError("SUPABASE_KEY (or SUPABASE_ANON_KEY) is missing from environment variables")
        
    return create_client(url, key)

@bp.route('/get/<int:user_id>', methods=['GET'])
def get_user_grades(user_id: int):
    try:
        supabase = get_supabase_client()
        resp = supabase.table('users').select('grades').eq('user_id', user_id).limit(1).execute()
        if not resp.data: return jsonify({'message': 'User not found'}), 404
        return jsonify({'grades': resp.data[0].get('grades') or []}), 200
    except Exception as e:
        return jsonify({'message': 'Failed to get grades', 'error': str(e)}), 500

@bp.route('/update/<int:user_id>', methods=['POST'])
def update_user_grades(user_id: int):
    try:
        payload = request.get_json(silent=True) or {}
        grades = payload.get('grades') or []
        print(f"[OCR_TOR] Updating grades for user {user_id}. Count: {len(grades)}")
        
        supabase = get_supabase_client()
        data = supabase.table('users').update({'grades': grades}).eq('user_id', user_id).execute()
        print(f"[OCR_TOR] Update result: {data}")
        
        return jsonify({'message': 'updated', 'grades': grades}), 200
    except Exception as e:
        # Import the debug logger dynamically to avoid circular imports if any
        try:
            from debug_logger import log_exception
            log_exception(e)
        except ImportError:
            print(f"[OCR_TOR] Could not import debug_logger: {e}")
            
        return jsonify({'message': 'Failed to update grades', 'error': str(e)}), 500