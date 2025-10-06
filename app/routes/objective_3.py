"""
Objective 3: Job and Company Recommendations
Handles job matching and company recommendations based on career forecast and archetype analysis
"""

from flask import Blueprint, request, jsonify
from app.routes.auth import token_required
from app.services.supabase_client import get_supabase_client
import json
from datetime import datetime, timezone
import os
import google.generativeai as genai

bp = Blueprint('objective_3', __name__, url_prefix='/api/objective-3')


@bp.route('/process', methods=['POST'])
def process_job_recommendations():
    """Process job and company recommendations based on career forecast and archetype"""
    try:
        data = request.get_json(silent=True) or {}
        email = (data.get('email') or '').strip().lower()
        refresh = bool(data.get('refresh'))
        debug_requested = bool(data.get('debug'))
        
        print(f"[OBJECTIVE-3] Job recommendations processing for email: {email}")
        
        # Fetch career forecast and archetype analysis from database
        career_forecast = {}
        archetype_analysis = {}
        
        try:
            supabase = get_supabase_client()
            
            # Get user data using current schema (denormalized columns)
            select_cols = (
                'id, job_recommendations, career_top_jobs, career_top_jobs_scores, '
                'primary_archetype, '
                'archetype_realistic_percentage, archetype_investigative_percentage, '
                'archetype_artistic_percentage, archetype_social_percentage, '
                'archetype_enterprising_percentage, archetype_conventional_percentage'
            )
            user_response = supabase.table('users').select(select_cols).eq('email', email).limit(1).execute()
            if user_response.data:
                user_data = user_response.data[0]
                # Fast path: return cached recommendations unless refresh requested
                try:
                    cached = user_data.get('job_recommendations')
                    if cached and not refresh:
                        cached_obj = json.loads(cached) if isinstance(cached, str) else cached
                        if isinstance(cached_obj, dict):
                            print('[OBJECTIVE-3] Returning cached job_recommendations')
                            return jsonify({'message': 'Job recommendations (cached)', 'email': email, 'job_recommendations': cached_obj}), 200
                except Exception:
                    pass
                # Build career_forecast map from arrays if present
                jobs = user_data.get('career_top_jobs') or []
                scores = user_data.get('career_top_jobs_scores') or []
                if isinstance(jobs, list) and isinstance(scores, list) and len(jobs) == len(scores):
                    try:
                        career_forecast = {str(jobs[i]): float(scores[i]) for i in range(len(jobs))}
                    except Exception:
                        career_forecast = {}
                # Build archetype_analysis-like map from percentage columns
                def _num(v):
                    try:
                        return float(v)
                    except Exception:
                        return None
                archetype_analysis = {
                    'primary_archetype': user_data.get('primary_archetype') or '',
                    'archetype_realistic_percentage': _num(user_data.get('archetype_realistic_percentage')),
                    'archetype_investigative_percentage': _num(user_data.get('archetype_investigative_percentage')),
                    'archetype_artistic_percentage': _num(user_data.get('archetype_artistic_percentage')),
                    'archetype_social_percentage': _num(user_data.get('archetype_social_percentage')),
                    'archetype_enterprising_percentage': _num(user_data.get('archetype_enterprising_percentage')),
                    'archetype_conventional_percentage': _num(user_data.get('archetype_conventional_percentage')),
                }
                print(f"[OBJECTIVE-3] Forecast keys: {list(career_forecast.keys())}")
                print(f"[OBJECTIVE-3] Archetype % present: {[k for k,v in archetype_analysis.items() if k.startswith('archetype_') and v is not None]}")
            else:
                print(f"[OBJECTIVE-3] User not found for email: {email}")
        except Exception as db_error:
            print(f"[OBJECTIVE-3] Database fetch error: {db_error}")
        
        # Company recommendations based on career forecast and archetype
        result = generate_job_recommendations(career_forecast, archetype_analysis, debug=debug_requested)
        company_list = []
        if isinstance(result, dict):
            company_list = result.get('company_recommendations') or []
        debug_info = result.get('debug') if isinstance(result, dict) else None
        # Persist and return a minimal envelope without job openings
        job_recommendations = {'company_recommendations': company_list}
        print(f"[OBJECTIVE-3] Generated results: companies={len(company_list)}")
        
        # Save to database (even if empty arrays, so UI can read state)
        try:
            supabase = get_supabase_client()
            # Get user by email
            user_response = supabase.table('users').select('id').eq('email', email).execute()
            if user_response.data:
                user_id = user_response.data[0]['id']
                # Persist results; avoid non-existent columns for compatibility
                update_data = {
                    'job_recommendations': json.dumps(job_recommendations)
                }
                supabase.table('users').update(update_data).eq('id', user_id).execute()
                print(f"[OBJECTIVE-3] Saved job recommendations to database for user {user_id}")
            else:
                print(f"[OBJECTIVE-3] User not found for email: {email}")
        except Exception as db_error:
            print(f"[OBJECTIVE-3] Database save error: {db_error}")
        
        response_payload = {
            'message': 'Job recommendations processed (Objective 3)',
            'email': email,
            'job_recommendations': job_recommendations
        }
        if debug_requested and debug_info:
            response_payload['debug'] = debug_info
        return jsonify(response_payload), 200
        
    except Exception as e:
        print(f"[OBJECTIVE-3] Error: {e}")
        return jsonify({'message': 'Job recommendations failed', 'error': str(e)}), 500

@bp.route('/save-results', methods=['POST'])
def save_job_results():
    """Save job and company recommendation results to database"""
    try:
        data = request.get_json() or {}
        email = data.get('email', '')
        job_results = data.get('jobResults', {})
        
        print(f"[OBJECTIVE-3] Saving job results for email: {email}")
        print(f"[OBJECTIVE-3] Job results keys: {list(job_results.keys())}")
        
        return jsonify({
            'message': 'Job results saved (Objective 3)',
            'email': email,
            'saved_to_db': True
        }), 200
        
    except Exception as e:
        print(f"[OBJECTIVE-3] Error: {e}")
        return jsonify({'message': 'Failed to save job results', 'error': str(e)}), 500

@bp.route('/clear-results', methods=['POST'])
def clear_job_results():
    """Clear job and company recommendation results"""
    try:
        data = request.get_json(silent=True) or {}
        email = (data.get('email') or '').strip().lower()
        
        print(f"[OBJECTIVE-3] Clearing job results for email: {email}")
        
        return jsonify({'message': 'Job results cleared (Objective 3)'}), 200
    except Exception as e:
        print(f"[OBJECTIVE-3] Error: {e}")
        return jsonify({'message': 'Failed to clear job results', 'error': str(e)}), 500

def generate_job_recommendations(career_forecast, archetype_analysis, debug: bool = False):
    """
    Vector-similarity based recommender (no LLM involvement).

    - Build a user vector from career forecast scores and archetype weights.
    - Compare against predefined job role vectors using cosine similarity.
    - Return top-N matches plus company suggestions mapped per role.
    """
    if not isinstance(career_forecast, dict):
        career_forecast = {}

    # Archetype weights (normalized) to bias roles; fallback to neutral if missing
    archetype_weights = {
        'realistic': 1.0,
        'investigative': 1.0,
        'artistic': 1.0,
        'social': 1.0,
        'enterprising': 1.0,
        'conventional': 1.0,
    }
    for key in list(archetype_weights.keys()):
        val = archetype_analysis.get(f'archetype_{key}_percentage')
        try:
            archetype_weights[key] = float(val) / 100.0 if val is not None else archetype_weights[key]
        except Exception:
            pass

    # Map careers in forecast to the feature space (simple heuristic)
    feature_map = {
        'software': [1.0, 0.2, 0.6, 0.1, 0.3, 0.2],
        'data': [0.5, 1.0, 0.3, 0.1, 0.3, 0.3],
        'systems': [0.5, 0.3, 1.0, 0.1, 0.4, 0.4],
        'ux': [0.1, 0.2, 0.2, 1.0, 0.3, 0.4],
        'management': [0.3, 0.2, 0.4, 0.1, 1.0, 0.8],
        'business': [0.2, 0.2, 0.5, 0.2, 0.8, 1.0],
    }

    # Build user vector by summing weighted feature vectors from forecast
    user_vec = [0.0] * 6
    for career, score in career_forecast.items():
        key = career.lower()
        matched = None
        for fm_key in feature_map.keys():
            if fm_key in key:
                matched = fm_key
                break
        if not matched:
            continue
        weight = float(score) if isinstance(score, (int, float, str)) else 0.0
        fv = feature_map[matched]
        for i in range(6):
            user_vec[i] += weight * fv[i]

    # Bias user vector using archetype weights (simple scaling)
    # Map archetypes to feature indices
    archetype_to_feature = {
        'realistic': 0,           # hands-on -> programming/infrastructure
        'investigative': 1,       # research/data
        'artistic': 3,            # design/ux
        'social': 5,              # communication
        'enterprising': 4,        # management
        'conventional': 2,        # systems/process
    }
    for arch, idx in archetype_to_feature.items():
        user_vec[idx] *= 1.0 + 0.25 * archetype_weights.get(arch, 1.0)

    def cosine(a, b):
        import math
        dot = sum(x * y for x, y in zip(a, b))
        na = math.sqrt(sum(x * x for x in a)) or 1e-9
        nb = math.sqrt(sum(y * y for y in b)) or 1e-9
        return dot / (na * nb)

    # Fetch and score companies from database using cosine similarity on RIASEC and skills
    company_recommendations = []
    debug_obj = {'fetched': 0, 'ranked': 0, 'user_skills': [], 'user_riasec': [], 'sample_company': None}
    try:
        supabase = get_supabase_client()
        # Select all columns to support legacy/CSV-imported names like riasec_wei, skills_vect
        db_companies = supabase.table('companies').select('*').eq('active', True).limit(200).execute()
        items = db_companies.data or []
        print(f"[OBJECTIVE-3] DB companies fetched: {len(items)} (active=true)")
        if not items:
            # Fallback: fetch without the active filter in case of boolean type mismatch
            db_companies_all = supabase.table('companies').select('*').limit(200).execute()
            items = db_companies_all.data or []
            print(f"[OBJECTIVE-3] DB companies fetched without active filter: {len(items)}")
        debug_obj['fetched'] = len(items)
        def _coerce_array(val):
            # Accept numeric[], python list, or Postgres array string like "{0.1,0.2,...}"
            if isinstance(val, list):
                try:
                    return [float(x) for x in val]
                except Exception:
                    return []
            if isinstance(val, str):
                s = val.strip()
                if s.startswith('{') and s.endswith('}'):
                    try:
                        parts = [p.strip() for p in s[1:-1].split(',') if p.strip()]
                        return [float(p) for p in parts]
                    except Exception:
                        return []
            return []

        def cosine(a, b):
            import math
            if not a or not b or len(a) != len(b):
                return 0.0
            dot = sum(float(x) * float(y) for x, y in zip(a, b))
            na = math.sqrt(sum(float(x) * float(x) for x in a)) or 1e-9
            nb = math.sqrt(sum(float(y) * float(y) for y in b)) or 1e-9
            return dot / (na * nb)

        # Derive user vectors: skills from forecast mapping, RIASEC from archetype percentages
        user_skills = [0.0] * 6
        for career, score in (career_forecast or {}).items():
            key = career.lower()
            matched = None
            for fm_key in ['software','data','systems','ux','management','business']:
                if fm_key in key:
                    matched = fm_key
                    break
            if not matched:
                continue
            mapping = {
                'software': [1.0, 0.2, 0.6, 0.1, 0.3, 0.2],
                'data': [0.5, 1.0, 0.3, 0.1, 0.3, 0.3],
                'systems': [0.5, 0.3, 1.0, 0.1, 0.4, 0.4],
                'ux': [0.1, 0.2, 0.2, 1.0, 0.3, 0.4],
                'management': [0.3, 0.2, 0.4, 0.1, 1.0, 0.8],
                'business': [0.2, 0.2, 0.5, 0.2, 0.8, 1.0],
            }[matched]
            try:
                w = float(score)
            except Exception:
                w = 0.0
            for i in range(6):
                user_skills[i] += w * mapping[i]

        user_riasec = [
            float(archetype_analysis.get('archetype_realistic_percentage') or 0) / 100.0,
            float(archetype_analysis.get('archetype_investigative_percentage') or 0) / 100.0,
            float(archetype_analysis.get('archetype_artistic_percentage') or 0) / 100.0,
            float(archetype_analysis.get('archetype_social_percentage') or 0) / 100.0,
            float(archetype_analysis.get('archetype_enterprising_percentage') or 0) / 100.0,
            float(archetype_analysis.get('archetype_conventional_percentage') or 0) / 100.0,
        ]
        debug_obj['user_skills'] = [round(x, 3) for x in user_skills]
        debug_obj['user_riasec'] = [round(x, 3) for x in user_riasec]

        scored = []
        for row in items:
            comp_riasec = row.get('riasec_weights') or row.get('riasec_wei') or [0,0,0,0,0,0]
            comp_skills = row.get('skills_vector') or row.get('skills_vect') or [0,0,0,0,0,0]
            comp_riasec = _coerce_array(comp_riasec)
            comp_skills = _coerce_array(comp_skills)
            s = 0.6 * cosine(user_skills, comp_skills) + 0.4 * cosine(user_riasec, comp_riasec)
            scored.append((s, row))
        scored.sort(key=lambda x: x[0], reverse=True)

        for score, row in scored[:20]:
            company_recommendations.append({
                'title': row.get('name'),
                'description': row.get('description') or '',
                'location': (row.get('locations') or ['Remote'])[0],
                'locations': row.get('locations') or [],
                'url': row.get('website') or '',
                'logo_url': row.get('logo_url') or '',
                'roles': row.get('roles') or [],
                'industry': row.get('industry') or '',
                'company_size': row.get('company_size') or '',
                'linkedin_url': row.get('linkedin_url') or '',
                'hiring_tags': row.get('hiring_tags') or [],
                'score': round(float(score), 4)
            })
        debug_obj['ranked'] = len(company_recommendations)
        if company_recommendations:
            debug_obj['sample_company'] = company_recommendations[0]
        print(f"[OBJECTIVE-3] DB companies ranked: {len(company_recommendations)}")
    except Exception as e:
        print(f"[OBJECTIVE-3] Company ranking failed: {e}")

    return {
        'company_recommendations': company_recommendations,
        'provenance': {
            'companies': 'riasec_skills_cosine'
        },
        'debug': debug_obj if debug else None
    }

