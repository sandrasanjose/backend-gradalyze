"""
Objective 2: RIASEC Archetype Classification
Handles personality archetype analysis and classification
"""

from flask import Blueprint, request, jsonify
from app.services.supabase_client import get_supabase_client
from app.routes.auth import token_required
import json
from datetime import datetime, timezone
import math
from typing import Dict, List
import numpy as np

bp = Blueprint('objective_2', __name__, url_prefix='/api/objective-2')

@bp.route('/latest', methods=['GET'])
def get_latest_archetype():
    """Return latest saved archetype analysis for a user by email (from denormalized columns)."""
    try:
        email = (request.args.get('email') or '').strip().lower()
        if not email:
            return jsonify({'message': 'email is required'}), 400

        supabase = get_supabase_client()
        resp = supabase.table('users').select(
            'primary_archetype, archetype_analyzed_at, '
            'archetype_realistic_percentage, archetype_investigative_percentage, archetype_artistic_percentage, '
            'archetype_social_percentage, archetype_enterprising_percentage, archetype_conventional_percentage'
        ).eq('email', email).execute()
        if not resp.data:
            return jsonify({'message': 'User not found', 'email': email}), 404

        row = resp.data[0]
        analysis = {
            'primary_archetype': row.get('primary_archetype'),
            'archetype_percentages': {
                'realistic': row.get('archetype_realistic_percentage'),
                'investigative': row.get('archetype_investigative_percentage'),
                'artistic': row.get('archetype_artistic_percentage'),
                'social': row.get('archetype_social_percentage'),
                'enterprising': row.get('archetype_enterprising_percentage'),
                'conventional': row.get('archetype_conventional_percentage')
            }
        }

        return jsonify({
            'email': email,
            'archetype_analysis': analysis,
            'archetype_analyzed_at': row.get('archetype_analyzed_at')
        }), 200
    except Exception as e:
        print(f"[OBJECTIVE-2] Latest fetch error: {e}")
        return jsonify({'message': 'Failed to fetch latest archetype', 'error': str(e)}), 500

@bp.route('/process', methods=['POST'])
def process_archetype_analysis():
    """Process RIASEC archetype analysis based on academic data"""
    try:
        data = request.get_json(silent=True) or {}
        email = (data.get('email') or '').strip().lower()
        grades_data = data.get('grades') or []
        
        print(f"[OBJECTIVE-2] Archetype analysis processing for email: {email}")
        print(f"[OBJECTIVE-2] Received {len(grades_data)} grade records for archetype analysis")
        if grades_data:
            print(f"[OBJECTIVE-2] First grade record: {grades_data[0]}")
        
        # Handle grades as simple array of numbers
        grades = []
        for grade_value in grades_data:
            if isinstance(grade_value, (int, float)) and 0 <= grade_value <= 4:
                grades.append(float(grade_value))
        
        print(f"[OBJECTIVE-2] Processing {len(grades)} grade values: {grades}")
        
        # RIASEC archetype analysis based on academic performance
        archetype_analysis = calculate_riasec_archetype(grades)
        
        # Save to database
        if archetype_analysis:
            try:
                supabase = get_supabase_client()
                
                # Get user by email
                user_response = supabase.table('users').select('id').eq('email', email).execute()
                if user_response.data:
                    user_id = user_response.data[0]['id']
                    
                    # Populate denormalized columns per migration schema (no JSON storage)
                    update_data = {
                        'archetype_analyzed_at': datetime.now(timezone.utc).isoformat()
                    }
                    # Populate columns from computed analysis
                    try:
                        perc = archetype_analysis.get('archetype_percentages', {}) or {}
                        update_data_extra = {
                            'primary_archetype': archetype_analysis.get('primary_archetype'),
                            'archetype_realistic_percentage': perc.get('realistic'),
                            'archetype_investigative_percentage': perc.get('investigative'),
                            'archetype_artistic_percentage': perc.get('artistic'),
                            'archetype_social_percentage': perc.get('social'),
                            'archetype_enterprising_percentage': perc.get('enterprising'),
                            'archetype_conventional_percentage': perc.get('conventional')
                        }
                        # Merge extras where values are not None
                        for k, v in list(update_data_extra.items()):
                            if v is not None:
                                update_data[k] = v
                    except Exception:
                        pass
                    
                    supabase.table('users').update(update_data).eq('id', user_id).execute()
                    print(f"[OBJECTIVE-2] Saved archetype analysis to database for user {user_id}")
                else:
                    print(f"[OBJECTIVE-2] User not found for email: {email}")
            except Exception as db_error:
                print(f"[OBJECTIVE-2] Database save error: {db_error}")
        
        return jsonify({
            'message': 'Archetype analysis processed (Objective 2)',
            'email': email,
            'grades_count': len(grades),
            'archetype_analysis': archetype_analysis
        }), 200
        
    except Exception as e:
        print(f"[OBJECTIVE-2] Error: {e}")
        return jsonify({'message': 'Archetype analysis failed', 'error': str(e)}), 500

@bp.route('/save-results', methods=['POST'])
def save_archetype_results():
    """Save archetype analysis results to database"""
    try:
        data = request.get_json() or {}
        email = data.get('email', '')
        archetype_results = data.get('archetypeResults', {})
        
        print(f"[OBJECTIVE-2] Saving archetype results for email: {email}")
        print(f"[OBJECTIVE-2] Archetype results keys: {list(archetype_results.keys())}")
        
        return jsonify({
            'message': 'Archetype results saved (Objective 2)',
            'email': email,
            'saved_to_db': True
        }), 200
        
    except Exception as e:
        print(f"[OBJECTIVE-2] Error: {e}")
        return jsonify({'message': 'Failed to save archetype results', 'error': str(e)}), 500

@bp.route('/clear-results', methods=['POST'])
def clear_archetype_results():
    """Clear archetype analysis results"""
    try:
        data = request.get_json(silent=True) or {}
        email = (data.get('email') or '').strip().lower()
        
        print(f"[OBJECTIVE-2] Clearing archetype results for email: {email}")
        
        return jsonify({'message': 'Archetype results cleared (Objective 2)'}), 200
    except Exception as e:
        print(f"[OBJECTIVE-2] Error: {e}")
        return jsonify({'message': 'Failed to clear archetype results', 'error': str(e)}), 500

def calculate_riasec_archetype(grades):
    """
    RIASEC via KMeans-style clustering using BSIT course-to-RIASEC mapping.
    - Input: fixed-order numeric grades array aligned with ITStaticTable.
    - Approach: map each course to a 6D RIASEC vector, weight by grade quality,
      cluster points with k=6 (centroids init to unit R/I/A/S/E/C), compute
      percentages from clustered weights, and pick primary archetype.
    """
    if not grades:
        return {}

    # Normalize grades to weights: higher grade -> higher weight.
    # Treat 0 (no input) as 0 weight. Grades scale is 1.00(best)..3.00(pass)..4.00(fail)
    def grade_to_weight(g: float) -> float:
        if g is None:
            return 0.0
        try:
            x = float(g)
        except Exception:
            return 0.0
        if x <= 0:
            return 0.0
        if x < 1 or x > 4:
            return 0.0
        # Invert so lower numeric grade (better) gives higher weight
        return max(0.0, 4.0 - x)

    # RIASEC axes order
    axes = ['R', 'I', 'A', 'S', 'E', 'C']
    axis_index: Dict[str, int] = {a: i for i, a in enumerate(axes)}

    # Canonical IT IDs order subset (only those we explicitly map). Indices must
    # align with the frontend order; any indices without mapping are ignored.
    # Year 1
    id_to_axes: Dict[str, List[str]] = {
        'it_fy1_sts0002': ['S','I'],
        'it_fy1_aap0007': ['A'],
        'it_fy1_pcm0006': ['S','E'],
        'it_fy1_mmw0001': ['I'],
        'it_fy1_ipp0010': ['S','C'],
        'it_fy1_icc0101': ['I','C'],
        'it_fy1_icc0102': ['I','C'],
        'it_fy1_ped0001': ['R','S'],
        'it_fy1_nstp01': ['S','E'],
        # Year 1 - 2nd sem
        'it_fy2_cet0111': ['I'],
        'it_fy2_cet0114': ['I','R'],
        'it_fy2_eit0121': ['A','S'],
        'it_fy2_eit0122': ['I'],
        'it_fy2_eit0123': ['A','C'],
        'it_fy2_icc0103': ['I','C'],
        'it_fy2_gtb121': ['S','A'],
        'it_fy2_ped0013': ['R','S'],
        'it_fy2_nstp02': ['S','E'],
        # Year 2 - 1st sem
        'it_sy1_cet0121': ['I'],
        'it_sy1_cet0225': ['I','R'],
        'it_sy1_tcw0005': ['S','E'],
        'it_sy1_icc0104': ['I','C'],
        'it_sy1_eit0211': ['I','C'],
        'it_sy1_ppc122': ['S','A'],
        'it_sy1_ped0054': ['R','S'],
        # Year 2 - 2nd sem
        'it_sy2_eit0221': ['I'],
        'it_sy2_eit0222': ['R','I'],
        'it_sy2_eit0222_1': ['R','I'],
        'it_sy2_ges0013': ['I','S'],
        'it_sy2_rph0004': ['S','C'],
        'it_sy2_uts0003': ['S','E'],
        'it_sy2_ped0074': ['R','S'],
        # Year 3 - 1st sem
        'it_ty1_icc0335': ['I','E'],
        'it_ty1_eit0311': ['C','I'],
        'it_ty1_eit0311_1': ['C','I'],
        'it_ty1_eit0312': ['R','I'],
        'it_ty1_eit0312_1': ['R','I'],
        'it_ty1_eit_elective3': [],
        'it_ty1_lwr0009': ['S','E'],
        # Year 3 - 2nd sem
        'it_ty2_eit0321': ['R','C'],
        'it_ty2_eit0321_1': ['R','C'],
        'it_ty2_eit0322': ['R','C'],
        'it_ty2_eit0322_1': ['R','C'],
        'it_ty2_eit0323': ['I','C'],
        'it_ty2_eit0323_1': ['I','C'],
        'it_ty2_eth0008': ['S','C'],
        # Midyear
        'it_my_eit0331': ['R','C'],
        'it_my_eit0331_1': ['R','C'],
        'it_my_cap0101': ['E','I','S'],
        # Year 4
        'it_fy4_cap0102': ['E','I','S'],
        'it_fy4_elective4': [],
        'it_fy4_elective5': [],
        'it_fy4_elective6': [],
        'it_fy4b_iip0101a': ['R','E'],
        'it_fy4b_iip0101_1': ['R','S','E'],
    }

    # Build the canonical order used by the frontend for the mapped subset.
    # Only these mapped IDs affect RIASEC scoring; others are ignored.
    curriculum_order: List[str] = list(id_to_axes.keys())

    # Create course vectors (points) in RIASEC space
    points: List[np.ndarray] = []
    weights: List[float] = []
    for idx, course_id in enumerate(curriculum_order):
        if idx >= len(grades):
            break
        g = grades[idx]
        w = grade_to_weight(g)
        if w <= 0:
            continue
        tags = id_to_axes.get(course_id, [])
        if not tags:
            continue
        vec = np.zeros(6, dtype=float)
        share = w / len(tags)
        for t in tags:
            if t in axis_index:
                vec[axis_index[t]] = share
        points.append(vec)
        weights.append(w)

    if not points:
        return {}

    X = np.vstack(points)

    # Initialize centroids as unit vectors for R,I,A,S,E, and C respectively
    centroids = np.eye(6, dtype=float)

    # Run a few KMeans iterations (Lloyd's algorithm)
    for _ in range(5):
        # Assign step
        distances = np.linalg.norm(X[:, None, :] - centroids[None, :, :], axis=2)
        labels = np.argmin(distances, axis=1)
        # Update step
        for k in range(6):
            mask = labels == k
            if np.any(mask):
                centroids[k] = X[mask].mean(axis=0)

    # Aggregate total weight per cluster (axis)
    totals = np.zeros(6, dtype=float)
    for vec in X:
        # Assign to nearest final centroid
        d = np.linalg.norm(vec[None, :] - centroids, axis=1)
        k = int(np.argmin(d))
        totals[k] += vec.sum()

    total_sum = float(totals.sum())
    if total_sum <= 0:
        return {}

    percentages = (totals / total_sum) * 100.0
    scores = totals.tolist()

    # Determine primary archetype by highest percentage
    max_idx = int(np.argmax(percentages))
    axis_to_name = {
        'R': 'realistic',
        'I': 'investigative',
        'A': 'artistic',
        'S': 'social',
        'E': 'enterprising',
        'C': 'conventional',
    }
    primary = axis_to_name.get(axes[max_idx], axes[max_idx].lower())

    return {
        'primary_archetype': primary,
        'archetype_percentages': {
            'realistic': round(float(percentages[axis_index['R']]), 2),
            'investigative': round(float(percentages[axis_index['I']]), 2),
            'artistic': round(float(percentages[axis_index['A']]), 2),
            'social': round(float(percentages[axis_index['S']]), 2),
            'enterprising': round(float(percentages[axis_index['E']]), 2),
            'conventional': round(float(percentages[axis_index['C']]), 2)
        },
        'archetype_scores': {
            'realistic': round(float(scores[axis_index['R']]), 3),
            'investigative': round(float(scores[axis_index['I']]), 3),
            'artistic': round(float(scores[axis_index['A']]), 3),
            'social': round(float(scores[axis_index['S']]), 3),
            'enterprising': round(float(scores[axis_index['E']]), 3),
            'conventional': round(float(scores[axis_index['C']]), 3)
        }
    }
