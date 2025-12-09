
# [UPDATE] app/routes/objective_2.py

from flask import Blueprint, request, jsonify
from app.services.supabase_client import get_supabase_client
import json
from datetime import datetime, timezone
import os
import google.generativeai as genai

bp = Blueprint('objective_2', __name__, url_prefix='/api/objective-2')

# --- INITIALIZE GEMINI ---
try:
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
        # Use the same model logic as ocr_tor.py (User preference)
        selected_model = os.getenv('GEMINI_MODEL_NAME', 'models/gemini-2.5-flash')
        gemini_model = genai.GenerativeModel(selected_model)
        print(f"[OBJECTIVE-2] Gemini model initialized: {selected_model}")
    else:
        gemini_model = None
except Exception as e:
    gemini_model = None
    print(f"[OBJECTIVE-2] Failed to init Gemini: {e}")

@bp.route('/process', methods=['POST'])
def process_archetype_analysis():
    """Process RIASEC archetype analysis (UNIVERSAL)"""
    try:
        data = request.get_json(silent=True) or {}
        email = (data.get('email') or '').strip().lower()
        grades_data = data.get('grades') or []
        
        # 1. Format Data
        transcript_text = ""
        if grades_data and isinstance(grades_data[0], dict):
            lines = []
            for item in grades_data:
                subject = item.get('subject', 'Unknown')
                grade = item.get('grade', 'N/A')
                lines.append(f"- {subject}: {grade}")
            transcript_text = "\n".join(lines)
        else:
            transcript_text = f"{grades_data}"

        # 2. Ask Gemini
        archetype_analysis = calculate_riasec_with_gemini(transcript_text)
        
        # 3. Get Population Stats
        population_counts = {}
        try:
            supabase = get_supabase_client()
            # Group by primary_archetype and count
            # Note: Supabase-py might not support complex group_by easily without rpc, 
            # so we might need to fetch all or use a known rpc if available.
            # For now, let's try a simple select of primary_archetype and aggregate in python 
            # if the dataset is small, OR separate counts. 
            # Optimized way: use .select('primary_archetype', count='exact') with .eq? No.
            # Let's just fetch all primary_archetypes for now (assuming < 10k users).
            # If scaling is needed, we should create a Postgres View or RPC.
            
            # Fetching all primary archetypes to count
            rows = supabase.table('users').select('primary_archetype').execute()
            print(f"[OBJECTIVE-2] Population Stats - Rows found: {len(rows.data) if rows.data else 0}")
            if rows.data:
                counts = {}
                for r in rows.data:
                    pa = r.get('primary_archetype')
                    if pa:
                        # Normalize to Title Case
                        pa = pa.capitalize()
                        counts[pa] = counts.get(pa, 0) + 1
                population_counts = counts
                print(f"[OBJECTIVE-2] Population Counts: {population_counts}")
        except Exception as e:
            print(f"[OBJECTIVE-2] Stats Error: {e}")

        # 4. Save to Database (Existing Logic)
        if archetype_analysis:
            try:
                supabase = get_supabase_client()
                user_resp = supabase.table('users').select('user_id, tor_notes').eq('email', email).execute()
                if user_resp.data:
                    user_row = user_resp.data[0]
                    user_id = user_row['user_id']
                    
                    update_data = {
                        'archetype_analyzed_at': datetime.now(timezone.utc).isoformat(),
                        'primary_archetype': archetype_analysis.get('primary_archetype', 'Unknown'),
                        'archetype_realistic_percentage': archetype_analysis['archetype_percentages'].get('Realistic', 0),
                        'archetype_investigative_percentage': archetype_analysis['archetype_percentages'].get('Investigative', 0),
                        'archetype_artistic_percentage': archetype_analysis['archetype_percentages'].get('Artistic', 0),
                        'archetype_social_percentage': archetype_analysis['archetype_percentages'].get('Social', 0),
                        'archetype_enterprising_percentage': archetype_analysis['archetype_percentages'].get('Enterprising', 0),
                        'archetype_conventional_percentage': archetype_analysis['archetype_percentages'].get('Conventional', 0),
                        'archetype_social_percentage': archetype_analysis['archetype_percentages'].get('Social', 0),
                        'archetype_enterprising_percentage': archetype_analysis['archetype_percentages'].get('Enterprising', 0),
                        'archetype_conventional_percentage': archetype_analysis['archetype_percentages'].get('Conventional', 0),
                        # Note: We don't have specific columns for skills/cross-disciplinary yet, 
                        # so they will live in tor_notes['analysis_results']['archetype_analysis']
                    }
                    
                    # Merge into JSON (tor_notes) for full object storage
                    try:
                        existing_notes = user_row.get('tor_notes') or '{}'
                        notes_obj = json.loads(existing_notes) if isinstance(existing_notes, str) else (existing_notes or {})
                        ar = notes_obj.get('analysis_results') or {}
                        
                        # Inject population stats into the saved object? Maybe not strictly necessary to save stats 
                        # as they change, but we definitely save the contributing subjects.
                        ar['archetype_analysis'] = archetype_analysis
                        notes_obj['analysis_results'] = ar
                        update_data['tor_notes'] = json.dumps(notes_obj)
                    except:
                        pass

                    supabase.table('users').update(update_data).eq('user_id', user_id).execute()
            except Exception as e:
                print(f"[OBJECTIVE-2] DB Save Error: {e}")

        return jsonify({
            'message': 'Archetype analysis processed (Universal AI)',
            'email': email,
            'archetype_analysis': archetype_analysis,
            'population_counts': population_counts
        }), 200

    except Exception as e:
        return jsonify({'message': 'Analysis failed', 'error': str(e)}), 500


def generate_with_retry(model, prompt, retries=3, initial_delay=60):
    """
    Wraps model.generate_content with retry logic for 429 Rate Limit errors.
    """
    import time
    if not model: return None
    
    current_delay = initial_delay
    
    for attempt in range(retries):
        try:
            # Add strict timeout
            return model.generate_content(prompt, request_options={"timeout": 600})
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "quota" in error_str.lower():
                print(f"[OBJECTIVE-2] Rate Limit Hit (429). Waiting {current_delay}s before retry {attempt+1}/{retries}...")
                time.sleep(current_delay)
                current_delay *= 2 # Exponential backoff
            else:
                print(f"[OBJECTIVE-2] Gemini Error (Non-Retryable): {e}")
                raise e
    
    print("[OBJECTIVE-2] Max retries exceeded for Gemini API.")
    return None

def calculate_riasec_with_gemini(transcript_text):
    if not gemini_model:
        return {}
        
    prompt = f"""
    You are an expert Psychologist specializing in RIASEC (Holland Codes). 
    Perform a purely objective, UNBIASED analysis of this student's transcript.

    Transcript:
    ---
    {transcript_text}
    ---
    
    CRITICAL INSTRUCTIONS FOR BIAS ELIMINATION:
    1. **Content-Only Analysis**: Evaluate ONLY the subject matter (e.g., "Math" -> Investigative) and the grade (performance).
    2. **Zero Assumptions**: Do NOT infer gender, age, socioeconomic status, or cultural background. Do NOT use stereotypes (e.g., do not assume "Nursing" implies female or "Engineering" implies male).
    3. **Universal Standardization**: Treat all subjects with equal weight regarding their potential career implications, derived solely from the syllabus implications of the title.
    
    Task:
    1. Analyze the subjects and weigh them by grades (Higher grades = stronger affinity).
    2. Calculate the percentage (0-100) for each RIASEC category.
    3. Determine the Primary Archetype.
    4. Identify top 5 "Contributing Subjects".
    5. Extract "Transferable Skills".
    6. Suggest 3-5 "Cross-Disciplinary Careers".
    
    Return ONLY a raw JSON object:
    {{
      "primary_archetype": "Social",
      "archetype_percentages": {{
        "Realistic": 10.5,
        "Investigative": 20.0,
        "Artistic": 5.0,
        "Social": 40.0,
        "Enterprising": 15.0,
        "Conventional": 9.5
      }},
      "contributing_subjects": {{
        "Realistic": ["Hardware Lab"],
        "Investigative": ["Calculus"],
        "Artistic": ["Multimedia"],
        "Social": ["Ethics"],
        "Enterprising": ["Management"],
        "Conventional": ["Database"]
      }},
      "transferable_skills": ["Critical Analysis", "Problem Solving"],
      "cross_disciplinary_careers": ["Product Manager", "UI Researcher"]
    }}
    """
    
    try:
        response = generate_with_retry(gemini_model, prompt)
        if not response:
             return {}

        text = response.text.replace('```json', '').replace('```', '').strip()
        data = json.loads(text)
        
        # Normalize to ensure keys exist
        defaults = {"Realistic":0,"Investigative":0,"Artistic":0,"Social":0,"Enterprising":0,"Conventional":0}
        data['archetype_percentages'] = {**defaults, **data.get('archetype_percentages', {})}
        
        # Ensure contributing_subjects exists
        data['contributing_subjects'] = data.get('contributing_subjects', {})
        
        # Ensure new fields exist
        data['transferable_skills'] = data.get('transferable_skills', [])
        data['cross_disciplinary_careers'] = data.get('cross_disciplinary_careers', [])
        
        # Add "debiased" aliases for frontend compatibility if needed
        data['debias_percentages'] = data['archetype_percentages']
        data['primary_archetype_debiased'] = data['primary_archetype']
        
        return data
    except Exception as e:
        print(f"[OBJECTIVE-2] AI Analysis Failed: {e}")
        return {}

@bp.route('/clear-results', methods=['POST'])
def clear_archetype_results():
    """Clear archetype analysis results"""
    try:
        data = request.get_json(silent=True) or {}
        email = (data.get('email') or '').strip().lower()

        print(f"[OBJECTIVE-2] Clearing archetype results for email: {email}")

        if not email:
            return jsonify({'message': 'email is required'}), 400

        try:
            supabase = get_supabase_client()
            # Find user id
            user_resp = supabase.table('users').select('user_id, tor_notes').eq('email', email).limit(1).execute()
            if not user_resp.data:
                return jsonify({'message': 'User not found'}), 404
            
            user_row = user_resp.data[0]
            user_id = user_row['user_id']

            # 1. Clear columns
            update_data = {
                'archetype_analyzed_at': None,
                'primary_archetype': None,
                'archetype_realistic_percentage': None,
                'archetype_investigative_percentage': None,
                'archetype_artistic_percentage': None,
                'archetype_social_percentage': None,
                'archetype_enterprising_percentage': None,
                'archetype_conventional_percentage': None,
            }

            # 2. Clear from tor_notes JSON
            try:
                existing_notes = user_row.get('tor_notes') or '{}'
                notes_obj = json.loads(existing_notes) if isinstance(existing_notes, str) else (existing_notes or {})
                if 'analysis_results' in notes_obj:
                    if 'archetype_analysis' in notes_obj['analysis_results']:
                        del notes_obj['analysis_results']['archetype_analysis']
                    # If analysis_results is empty, maybe keep it or remove it? keeping it is safer.
                update_data['tor_notes'] = json.dumps(notes_obj)
            except Exception as json_err:
                print(f"[OBJECTIVE-2] Error clearing JSON notes: {json_err}")

            supabase.table('users').update(update_data).eq('user_id', user_id).execute()
            return jsonify({'message': 'Archetype results cleared (Objective 2)'}), 200
        except Exception as db_error:
            print(f"[OBJECTIVE-2] Clear DB error: {db_error}")
            return jsonify({'message': 'Failed to clear archetype results', 'error': str(db_error)}), 500
    except Exception as e:
        print(f"[OBJECTIVE-2] Error: {e}")
        return jsonify({'message': 'Failed to clear archetype results', 'error': str(e)}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500
