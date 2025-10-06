from flask import Blueprint, request, jsonify
import io
import re
from typing import List, Dict, Any
import pdfplumber
import pytesseract
from PIL import Image
import pypdfium2 as pdfium
from app.services.supabase_client import get_supabase_client

# Expose under /api/ocr-tor/*
bp = Blueprint('ocr_tor', __name__, url_prefix='/api/ocr-tor')

def extract_grades_from_tor(file_bytes: bytes, filename: str) -> Dict[str, Any]:
    """Extract grades from a TOR PDF file.

    Returns a dict with:
      - grade_values: List[float] extracted from the PDF (1.0..5.0, 0 allowed)
      - grades: List[dict] in the app's standard format. Since subject/units/semester
        cannot be reliably inferred without full OCR mapping, this function
        synthesizes lightweight items using the numeric grades only so the
        frontend can render immediately. You can later enrich these with
        subject metadata if available.
    """
    # Prefer table extraction from pdfplumber; fallback to text regex if needed
    grade_values: List[float] = []
    grades: List[Dict[str, Any]] = []

    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page_idx, page in enumerate(pdf.pages):
            try:
                table_settings = {
                    'vertical_strategy': 'lines',
                    'horizontal_strategy': 'lines',
                    'intersection_x_tolerance': 5,
                    'intersection_y_tolerance': 5,
                    'snap_tolerance': 3,
                    'join_tolerance': 3,
                    'edge_min_length': 3
                }
                tables = page.extract_tables(table_settings) or []
            except Exception:
                tables = []

            for table in tables:
                if not table or not any(table):
                    continue
                # Find header row by checking for keywords
                header_row_index = -1
                header_lower: List[str] = []
                for i, row in enumerate(table):
                    cells = [(c or '').strip() for c in row]
                    lower_cells = [c.lower() for c in cells]
                    if any(k in ' '.join(lower_cells) for k in ['grade', 'final']):
                        header_row_index = i
                        header_lower = lower_cells
                        break
                if header_row_index == -1:
                    continue

                # Map columns
                def find_col(*names):
                    for n in names:
                        if n in header_lower:
                            return header_lower.index(n)
                    # partial match
                    for idx, col in enumerate(header_lower):
                        for n in names:
                            if n in col:
                                return idx
                    return None

                col_subject = find_col('descriptive title', 'course title', 'subject')
                col_units = find_col('units', 'credit', 'credits')
                col_grade = find_col('grade', 'final')
                col_sem = find_col('semester', 'term')
                if col_grade is None:
                    continue

                # Consume following rows until next header/empty separation
                for r in table[header_row_index + 1:]:
                    cells = [(c or '').strip() for c in r]
                    if not any(cells):
                        continue
                    grade_txt = (cells[col_grade] if col_grade < len(cells) else '').strip()
                    # Extract numeric value from grade cell
                    m = re.search(r"(?:0|[1-5](?:\.0{1,2}|\.25|\.5|\.50|\.75)?)", grade_txt)
                    if not m:
                        continue
                    try:
                        value = float(m.group(0))
                    except Exception:
                        continue
                    if not (0.0 <= value <= 5.0):
                        continue
                    grade_values.append(value)
                    idx = len(grade_values)
                    subject = (cells[col_subject] if col_subject is not None and col_subject < len(cells) else f'Subject {idx}')
                    units_str = (cells[col_units] if col_units is not None and col_units < len(cells) else '0')
                    try:
                        units_val = int(re.sub(r"[^0-9]", "", units_str) or '0')
                    except Exception:
                        units_val = 0
                    semester = (cells[col_sem] if col_sem is not None and col_sem < len(cells) else '')
                    grades.append({
                        'id': f'G-{idx:03d}',
                        'subject': subject,
                        'units': units_val,
                        'grade': str(value),
                        'semester': semester
                    })

    # Fallback: regex over full text if no table produced anything
    if not grade_values:
        try:
            # OCR fallback: rasterize pages, run tesseract, parse numbers
            pdf = pdfium.PdfDocument(io.BytesIO(file_bytes))
            ocr_texts: List[str] = []
            for i in range(len(pdf)):
                page = pdf[i]
                # Render at higher scale for better OCR accuracy
                bmp = page.render(scale=2)
                try:
                    pil_image = bmp.to_pil()
                finally:
                    del bmp
                # Convert to grayscale to improve OCR in many cases
                pil_image = pil_image.convert('L')
                text = pytesseract.image_to_string(pil_image) or ''
                if text:
                    ocr_texts.append(text)
            full_text = "\n".join(ocr_texts)

            # Try to focus on the Grade column by filtering lines that contain patterns like
            # " 1.25  3" (grade then units) or isolated grades
            number_pattern = re.compile(r"\b(?:0|[1-5](?:\.0{1,2}|\.25|\.5|\.50|\.75)?)\b")
            tokens = number_pattern.findall(full_text)
            for token in tokens:
                try:
                    value = float(token)
                except ValueError:
                    continue
                if 0.0 <= value <= 5.0:
                    grade_values.append(value)
            grades = [{
                'id': f'G-{i+1:03d}',
                'subject': f'Subject {i+1}',
                'units': 0,
                'grade': str(v),
                'semester': ''
            } for i, v in enumerate(grade_values)]
        except Exception as ocr_error:
            print(f"[OCR_TOR] OCR fallback failed: {ocr_error}")

    return {'grade_values': grade_values, 'grades': grades}

@bp.route('/process', methods=['POST', 'OPTIONS'])
def process_tor_extract_grades():
    """Endpoint to extract grades from uploaded TOR and return the array."""
    try:
        if request.method == 'OPTIONS':
            return ('', 204)
        if 'file' not in request.files:
            return jsonify({'error': 'file is required'}), 400
        tor_file = request.files['file']
        filename = tor_file.filename or 'tor.pdf'
        file_bytes = tor_file.read()
        result = extract_grades_from_tor(file_bytes, filename)
        try:
            gv = result.get('grade_values') or []
            print(f"[OCR_TOR] Extracted grade_values count={len(gv)}: {gv}")
        except Exception:
            pass
        return jsonify({'success': True, **result}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/get/<int:user_id>', methods=['GET'])
def get_user_grades(user_id):
    """Get user grades array"""
    try:
        supabase = get_supabase_client()
        res = supabase.table('users').select('grades').eq('id', user_id).limit(1).execute()
        if not res.data:
            return jsonify({'error': 'User not found'}), 404
        row = res.data[0]
        grades = row.get('grades') or []
        return jsonify({
            'success': True,
            'grades': grades
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/update/<int:user_id>', methods=['POST'])
def update_user_grades(user_id):
    """Update user grades array"""
    try:
        data = request.get_json()
        grades = data.get('grades', [])
        # Basic validation
        for g in grades:
            for field in ['id','subject','units','grade','semester']:
                if field not in g:
                    return jsonify({'error': f'Missing required field: {field}'}), 400

        supabase = get_supabase_client()
        res = supabase.table('users').update({'grades': grades}).eq('id', user_id).execute()
        if not res.data:
            return jsonify({'error': 'User not found'}), 404
        return jsonify({
            'success': True,
            'message': 'Grades updated successfully',
            'grades': (res.data[0].get('grades') if res.data else grades) or grades
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/add/<int:user_id>', methods=['POST'])
def add_user_grade(user_id):
    """Add a single grade to user's grades array"""
    try:
        data = request.get_json()
        new_grade = data.get('grade')
        
        if not new_grade:
            return jsonify({'error': 'Grade data is required'}), 400
            
        # Validate required fields
        required_fields = ['id', 'subject', 'units', 'grade', 'semester']
        for field in required_fields:
            if field not in new_grade:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        supabase = get_supabase_client()
        # Fetch current grades
        res_get = supabase.table('users').select('grades').eq('id', user_id).limit(1).execute()
        if not res_get.data:
            return jsonify({'error': 'User not found'}), 404
        current_grades = res_get.data[0].get('grades') or []
        # Replace by id
        gid = new_grade['id']
        updated = [g for g in current_grades if (g or {}).get('id') != gid]
        updated.append(new_grade)
        # Save
        res_upd = supabase.table('users').update({'grades': updated}).eq('id', user_id).execute()
        return jsonify({
            'success': True,
            'message': 'Grade added successfully',
            'grades': (res_upd.data[0].get('grades') if res_upd.data else updated) or updated
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/delete/<int:user_id>', methods=['POST'])
def delete_user_grade(user_id):
    """Delete a grade from user's grades array"""
    try:
        data = request.get_json()
        grade_id = data.get('grade_id')
        
        if not grade_id:
            return jsonify({'error': 'Grade ID is required'}), 400
        supabase = get_supabase_client()
        res_get = supabase.table('users').select('grades').eq('id', user_id).limit(1).execute()
        if not res_get.data:
            return jsonify({'error': 'User not found'}), 404
        current = res_get.data[0].get('grades') or []
        updated = [g for g in current if (g or {}).get('id') != grade_id]
        res_upd = supabase.table('users').update({'grades': updated}).eq('id', user_id).execute()
        return jsonify({
            'success': True,
            'message': 'Grade deleted successfully',
            'grades': (res_upd.data[0].get('grades') if res_upd.data else updated) or updated
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
