from flask import Blueprint, request, jsonify
import io
import re
from typing import List, Dict, Any
import pdfplumber
import easyocr
from PIL import Image
import pypdfium2 as pdfium
import numpy as np
import os
from app.services.supabase_client import get_supabase_client

# Expose under /api/ocr-tor/*
bp = Blueprint('ocr_tor', __name__, url_prefix='/api/ocr-tor')

def extract_grades_from_tor(file_bytes: bytes, filename: str) -> Dict[str, Any]:
    """Extract text and clean grade list from a TOR PDF using EasyOCR."""
    full_text = ""

    try:
        print(f"[OCR_TOR] Starting EasyOCR extraction for {filename}")
        reader = easyocr.Reader(['en'])
        pdf = pdfium.PdfDocument(io.BytesIO(file_bytes))
        print(f"[OCR_TOR] PDF has {len(pdf)} pages")

        for i in range(len(pdf)):
            page = pdf[i]
            print(f"[OCR_TOR] Processing page {i+1}...")

            bmp = page.render(scale=2)
            try:
                pil_image = bmp.to_pil()
            finally:
                del bmp

            pil_image = pil_image.convert('RGB')
            image_array = np.array(pil_image)

            results = reader.readtext(image_array)
            page_text = " ".join(
                text for (_, text, conf) in results if conf > 0.5
            )
            full_text += " " + page_text
            print(f"[OCR_TOR] Page {i+1} extracted {len(page_text)} characters")

    except Exception as ocr_error:
        print(f"[OCR_TOR] EasyOCR failed: {ocr_error}")
        full_text = f"OCR Error: {str(ocr_error)}"

    # ----------------------------
    # 🔍 Parse Grades from Text
    # ----------------------------
    grades = []
    grade_values = []

    try:
        # Simple regex for grades 1.00–3.00 (exact matches)
        pattern = re.compile(r'\b[123]\.\d{2}\b')
        matches = pattern.findall(full_text)
        print(f"[OCR_TOR] Found {len(matches)} grade matches")

        for match in matches:
            grade_values.append(float(match))
            print(f"Found grade: {match}")

    except Exception as parse_error:
        print(f"[OCR_TOR] Grade parsing failed: {parse_error}")

    return {
        'grade_values': grade_values,
        'grades': grades,
        'full_text': full_text
    }

@bp.route('/process', methods=['POST', 'OPTIONS'])
def process_tor_extract_grades():
    """Endpoint to extract grades from uploaded TOR and return only the grade values array."""
    try:
        if request.method == 'OPTIONS':
            return ('', 204)

        # Get file from request
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not file.filename.lower().endswith('.pdf'):
            return jsonify({'error': 'File must be a PDF'}), 400
        
        # Read file bytes
        file_bytes = file.read()
        filename = file.filename
        
        print(f"[OCR_TOR] Processing file: {filename} ({len(file_bytes)} bytes)")
        
        # Extract text using OCR
        result = extract_grades_from_tor(file_bytes, filename)
        
        # Return the cleaned grade values array and full text for debugging
        return jsonify({
            'success': True,
            'grade_values': result['grade_values'],
            'full_text': result['full_text']
        }), 200
        
    except Exception as error:
        print(f"[OCR_TOR] Error: {error}")
        return jsonify({'error': str(error)}), 500

@bp.route('/get', methods=['GET'])
@bp.route('/get/<int:user_id>', methods=['GET'])
def get_grades(user_id=None):
    """Get stored grades for a user."""
    try:
        # Handle both email and user_id parameters
        email = request.args.get('email')
        if not email and not user_id:
            return jsonify({'error': 'Email or user_id is required'}), 400
        
        supabase = get_supabase_client()
        
        if user_id:
            # Query by user ID
            result = supabase.table('users').select('grades').eq('id', user_id).execute()
        else:
            # Query by email
            result = supabase.table('users').select('grades').eq('email', email).execute()
        
        if not result.data:
            return jsonify({'error': 'User not found'}), 404
        
        grades = result.data[0].get('grades', [])
        return jsonify({'grades': grades}), 200
        
    except Exception as error:
        return jsonify({'error': str(error)}), 500

@bp.route('/update', methods=['POST'])
def update_grades():
    """Update grades for a user."""
    try:
        data = request.get_json()
        email = data.get('email')
        grades = data.get('grades', [])
        
        if not email:
            return jsonify({'error': 'Email is required'}), 400

        supabase = get_supabase_client()
        result = supabase.table('users').update({'grades': grades}).eq('email', email).execute()
        
        if not result.data:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({'success': True, 'grades': grades}), 200
        
    except Exception as error:
        return jsonify({'error': str(error)}), 500

@bp.route('/update/<int:user_id>', methods=['POST'])
def update_grades_by_id(user_id):
    """Update grades for a user by ID."""
    try:
        data = request.get_json()
        grades = data.get('grades', [])
        
        if not grades:
            return jsonify({'error': 'Grades are required'}), 400

        supabase = get_supabase_client()
        result = supabase.table('users').update({'grades': grades}).eq('id', user_id).execute()
        
        if not result.data:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({'success': True, 'grades': grades}), 200
        
    except Exception as error:
        return jsonify({'error': str(error)}), 500

@bp.route('/add', methods=['POST'])
def add_grade():
    """Add a single grade to a user's grades."""
    try:
        data = request.get_json()
        email = data.get('email')
        grade = data.get('grade')
        
        if not email or not grade:
            return jsonify({'error': 'Email and grade are required'}), 400
            
        supabase = get_supabase_client()
        result = supabase.table('users').select('grades').eq('email', email).execute()
        
        if not result.data:
            return jsonify({'error': 'User not found'}), 404
        
        current_grades = result.data[0].get('grades', [])
        current_grades.append(grade)
        
        update_result = supabase.table('users').update({'grades': current_grades}).eq('email', email).execute()
        
        return jsonify({'success': True, 'grades': current_grades}), 200
        
    except Exception as error:
        return jsonify({'error': str(error)}), 500

@bp.route('/delete', methods=['DELETE'])
def delete_grade():
    """Delete a grade from a user's grades."""
    try:
        data = request.get_json()
        email = data.get('email')
        grade_id = data.get('grade_id')
        
        if not email or not grade_id:
            return jsonify({'error': 'Email and grade_id are required'}), 400
        
        supabase = get_supabase_client()
        result = supabase.table('users').select('grades').eq('email', email).execute()
        
        if not result.data:
            return jsonify({'error': 'User not found'}), 404
        
        current_grades = result.data[0].get('grades', [])
        updated_grades = [g for g in current_grades if g.get('id') != grade_id]
        
        update_result = supabase.table('users').update({'grades': updated_grades}).eq('email', email).execute()
        
        return jsonify({'success': True, 'grades': updated_grades}), 200
        
    except Exception as error:
        return jsonify({'error': str(error)}), 500