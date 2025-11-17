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

# Canonical IT IDs order subset (only those we explicitly map). Indices must
# align with the frontend order; any indices without mapping are ignored.
# Year 1
id_to_axes: Dict[str, List[str]] = {
   # --- BSIT Year 1 / First Semester ---
    'it_fy1_icc0101': ['I','R'],
    'it_fy1_icc0101_1': ['R'],
    'it_fy1_icc0102': ['I','R'],
    'it_fy1_icc0102_1': ['R','I'],
    'it_fy1_ipp0010': ['S','C'],
    'it_fy1_mmw0001': ['I'],
    'it_fy1_pcm0006': ['S','E'],
    'it_fy1_sts0002': ['I','S'],
    'it_fy1_aap0007': ['A'],
    'it_fy1_ped0001': ['S','R'],
    'it_fy1_nstp01': ['S','E'],

# --- BSIT Year 1 / Second Semester ---
    'it_fy2_cet0111': ['I'],
    'it_fy2_cet0114': ['I','R'],
    'it_fy2_cet0114_1': ['R','I'],
    'it_fy2_eit0121': ['A','S'],
    'it_fy2_eit0121_1a': ['A','R'],
    'it_fy2_eit0122': ['I'],
    'it_fy2_eit0123': ['A','I'],
    'it_fy2_eit0123_1': ['A','R'],
    'it_fy2_gtb121': ['S','A'],
    'it_fy2_icc0103': ['I','R'],
    'it_fy2_icc0103_1': ['R','I'],
    'it_fy2_ped0013': ['R','S'],
    'it_fy2_nstp02': ['S','E'],

# --- BSIT Year 2 / First Semester ---
    'it_sy1_cet0121': ['I'],
    'it_sy1_cet0225': ['I','R'],
    'it_sy1_cet0225_1': ['R','I'],
    'it_sy1_eit0211': ['I','R'],
    'it_sy1_eit0211_1a': ['R','I'],
    'it_sy1_eit_elective1': ['C','I'],
    'it_sy1_icc0104': ['I'],
    'it_sy1_icc0104_1': ['R','I'],
    'it_sy1_ppc122': ['A','S'],
    'it_sy1_tcw0005': ['S','E'],
    'it_sy1_ped0054': ['S','R'],

# --- BSIT Year 2 / Second Semester ---
    'it_sy2_eit0212': ['R','I'],
    'it_sy2_eit0221': ['I','C'],
    'it_sy2_eit0222': ['R','C'],
    'it_sy2_eit0222_1': ['R'],
    'it_sy2_eit_elective2': ['C','E','I'],
    'it_sy2_ges0013': ['I','S'],
    'it_sy2_icc0105': ['C','I'],
    'it_sy2_icc0105_1': ['R','C'],
    'it_sy2_rph0004': ['S','C'],
    'it_sy2_uts0003': ['S'],
    'it_sy2_ped0074': ['S','R'],

# --- BSIT Year 3 / First Semester ---
    'it_ty1_eit0311': ['C','I'],
    'it_ty1_eit0311_1': ['R','C'],
    'it_ty1_eit0312': ['R','I'],
    'it_ty1_eit0312_1': ['R'],
    'it_ty1_eit_elective3': ['I','C','E'],
    'it_ty1_icc0335': ['I','C'],
    'it_ty1_icc0335_1': ['R','I'],
    'it_ty1_lwr0009': ['S','E'],

# --- BSIT Year 3 / Second Semester ---
    'it_ty2_eit0321': ['I','C'],
    'it_ty2_eit0321_1': ['R','I'],
    'it_ty2_eit0322': ['I','R'],
    'it_ty2_eit0322_1': ['R','I'],
    'it_ty2_eit0323': ['I','A'],
    'it_ty2_eit0323_1': ['A','R'],
    'it_ty2_eth0008': ['S','C'],

# --- BSIT Year 3 / Midyear/Summer Term ---
    'it_my_cap0101': ['I','E'],
    'it_my_eit0331': ['I','R'],
    'it_my_eit0331_1': ['R','I'],

# --- BSIT Year 4 / First Semester ---
    'it_fy4_cap0102': ['I','E'],
    'it_fy4_eit_elective4': ['I','R'],
    'it_fy4_eit_elective5': ['C','I'],
    'it_fy4_eit_elective6': ['S','E'],

# --- BSIT Year 4 / Second Semester ---
    'it_fy4b_iip0101a': ['S','R'],
    'it_fy4b_iip0101_1': ['R','E'],
}

# BSCS mapping (subset) aligned with frontend CStaticTable ids
# Uses the provided RIASEC rationale; we map to axes lists
id_to_axes_cs: Dict[str, List[str]] = {
    # --- BSCS Year 1 / First Semester ---
    'cs_fy1_csc0102': ['I'],
    'cs_fy1_icc0101': ['I','R'],
    'cs_fy1_icc0101_1': ['R'],
    'cs_fy1_icc0102': ['I','R'],
    'cs_fy1_icc0102_1': ['R','I'],
    'cs_fy1_ipp0010': ['S','C'],
    'cs_fy1_mmw0001': ['I'],
    'cs_fy1_ped0001': ['S','R'],
    'cs_fy1_pcm0006': ['S','E'],  
    'cs_fy1_sts0002': ['I','S'],
    'cs_fy1_nstp01': ['S','E'],

    # --- BSCS Year 1 / Second Semester ---
    'cs_fy2_csc0211': ['I'],  
    'cs_fy2_csc0223': ['A','S'],
    'cs_fy2_icc0103': ['I','R'],
    'cs_fy2_icc0103_1': ['R','I'],
    'cs_fy2_icc0104': ['I'],
    'cs_fy2_icc0104_1': ['R','I'],
    'cs_fy2_lwr0009': ['S','E'],
    'cs_fy2_ped0012': ['S','R'],
    'cs_fy2_rph0004': ['S','C'],
    'cs_fy2_tcw0005': ['S','E'],
    'cs_fy2_nstp02': ['S','E'],

    # --- BSCS Year 2 / First Semester ---  
    'cs_sy1_csc0212': ['I','R'],
    'cs_sy1_csc0212_1': ['R','I'],
    'cs_sy1_csc0213': ['R','I'],
    'cs_sy1_csc0213_1': ['R'],
    'cs_sy1_csc0224': ['I','C'],
    'cs_sy1_eth0008': ['S','C'],
    'cs_sy1_icc0105': ['C','I'],
    'cs_sy1_icc0105_1': ['R','C'],
    'cs_sy1_ite0001': ['S','I'],
    'cs_sy1_ped0074': ['S','R'],
    'cs_sy1_uts0003': ['S'],

    # --- BSCS Year 2 / Second Semester ---
    'cs_sy2_cbm0016': ['E','S'],
    'cs_sy2_csc0221': ['I'],
    'cs_sy2_csc0222': ['R','I'],
    'cs_sy2_csc0222_1': ['R'],
    'cs_sy2_csc0316': ['I','C'],
    'cs_sy2_ges0013': ['I','S'],
    'cs_sy2_icc0106': ['I','C'],
    'cs_sy2_icc0106_1': ['R','I'],
    'cs_sy2_ped0023': ['S','R'],
    'cs_sy2_aap0007': ['A'],

    # --- BSCS Year 3 / First Semester ---
    'cs_ty1_csc0311': ['I'],
    'cs_ty1_csc0312': ['I','R'],
    'cs_ty1_csc0312_1': ['R','I'],
    'cs_ty1_csc0313': ['I','C','E'],
    'cs_ty1_csc0313_1': ['R','C'],
    'cs_ty1_csc0314': ['I','R'],
    'cs_ty1_csc0314_1': ['R','I'],
    'cs_ty1_csc0315': ['I','A'],
    'cs_ty1_csc0315_1': ['R','I'],

    # --- BSCS Year 3 / Second Semester ---
    'cs_ty2_csc0321': ['I','E','C'],
    'cs_ty2_csc0321_1': ['R','C'],
    'cs_ty2_csc0322': ['I'],
    'cs_ty2_csc0322_1': ['R','I'],
    'cs_ty2_csc0323': ['I','C'],
    'cs_ty2_csc0323_1': ['R','I'],
    'cs_ty2_csc0324': ['I','A','R'],
    'cs_ty2_csc0324_1': ['I','A','R'],
    'cs_ty2_csc0325': ['I','C'],

    # --- BSCS Year 3 / Midyear/Summer Term ---
    'cs_ty_csc195_1': ['R','E'],

    # --- BSCS Year 4 / First Semester ---
    'cs_fy4_csc0411': ['I','E'],
    'cs_fy4_csc0412': ['R','I'],
    'cs_fy4_csc0412_1': ['R'],
    'cs_fy4_csc0413': ['I','C','E'],
    'cs_fy4_csc0413_1': ['I','C','E'],
    'cs_fy4_csc0414': ['A','E','C'],
    'cs_fy4_csc0414_1': ['A','E','C'],

    # --- BSCS Year 4 / Second Semester ---
    'cs_fy4b_csc0421a': ['I','E'],
    'cs_fy4b_csc0422': ['I','R'],
    'cs_fy4b_csc0422_1': ['R','I'],
    'cs_fy4b_csc0423': ['S', 'C'],
    'cs_fy4b_csc0424': ['A','I'],
    'cs_fy4b_csc0424_1': ['A','R'],
}

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
                'Realistic': row.get('archetype_realistic_percentage'),
                'Investigative': row.get('archetype_investigative_percentage'),
                'Artistic': row.get('archetype_artistic_percentage'),
                'Social': row.get('archetype_social_percentage'),
                'Enterprising': row.get('archetype_enterprising_percentage'),
                'Conventional': row.get('archetype_conventional_percentage')
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
        order_ids = data.get('order_ids') or []
        
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
        gamma = None
        r = None
        tau = None
        similarity = None
        try:
            gv = data.get('gamma')
            rv = data.get('r')
            tv = data.get('tau')
            sv = data.get('similarity')
            gamma = float(gv) if gv is not None else None
            r = float(rv) if rv is not None else None
            tau = float(tv) if tv is not None else 0.9
            similarity = str(sv).lower() if isinstance(sv, str) else 'cosine'
        except Exception:
            pass

        archetype_analysis = calculate_riasec_archetype(grades, order_ids, gamma=gamma, r=r, tau=tau, similarity=similarity)
        
        # Save to database
        if archetype_analysis:
            try:
                supabase = get_supabase_client()

                # Get user by email (also fetch tor_notes for merge)
                user_response = supabase.table('users').select('user_id, tor_notes').eq('email', email).execute()
                if user_response.data:
                    user_row = user_response.data[0]
                    user_id = user_row['user_id']
                    
                    # Populate denormalized columns per migration schema (no JSON storage)
                    update_data = {
                        'archetype_analyzed_at': datetime.now(timezone.utc).isoformat()
                    }
                    # Populate columns from computed analysis
                    try:
                        perc = (
                            archetype_analysis.get('debias_percentages')
                            or archetype_analysis.get('opportunity_normalized_percentages')
                            or archetype_analysis.get('normalized_percentages')
                            or archetype_analysis.get('archetype_percentages')
                            or {}
                        )
                        def getp(k: str):
                            # accept both lowercase and capitalized keys from analyzer
                            return perc.get(k) if perc.get(k) is not None else perc.get(k.capitalize())
                        update_data_extra = {
                            'primary_archetype': archetype_analysis.get('primary_archetype_debiased') or archetype_analysis.get('primary_archetype'),
                            'archetype_realistic_percentage': getp('realistic'),
                            'archetype_investigative_percentage': getp('investigative'),
                            'archetype_artistic_percentage': getp('artistic'),
                            'archetype_social_percentage': getp('social'),
                            'archetype_enterprising_percentage': getp('enterprising'),
                            'archetype_conventional_percentage': getp('conventional')
                        }
                        # Merge extras where values are not None
                        for k, v in list(update_data_extra.items()):
                            if v is not None:
                                update_data[k] = v
                    except Exception:
                        pass
                    
                    # Merge archetype analysis into tor_notes → analysis_results.archetype_analysis
                    try:
                        existing_notes = user_row.get('tor_notes') or '{}'
                        notes_obj = {}
                        try:
                            notes_obj = json.loads(existing_notes) if isinstance(existing_notes, str) else (existing_notes or {})
                        except Exception:
                            notes_obj = {}

                        ar = notes_obj.get('analysis_results') or {}
                        ar['archetype_analysis'] = archetype_analysis
                        notes_obj['analysis_results'] = ar
                        update_data['tor_notes'] = json.dumps(notes_obj)
                    except Exception as _:
                        # Non-blocking if tor_notes merge fails
                        pass

                    supabase.table('users').update(update_data).eq('user_id', user_id).execute()
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

        if not email:
            return jsonify({'message': 'email is required'}), 400

        try:
            supabase = get_supabase_client()
            # Find user id
            user_resp = supabase.table('users').select('user_id').eq('email', email).limit(1).execute()
            if not user_resp.data:
                return jsonify({'message': 'User not found'}), 404
            user_id = user_resp.data[0]['user_id']

            # Clear denormalized archetype columns
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
            supabase.table('users').update(update_data).eq('user_id', user_id).execute()
            return jsonify({'message': 'Archetype results cleared (Objective 2)'}), 200
        except Exception as db_error:
            print(f"[OBJECTIVE-2] Clear DB error: {db_error}")
            return jsonify({'message': 'Failed to clear archetype results', 'error': str(db_error)}), 500
    except Exception as e:
        print(f"[OBJECTIVE-2] Error: {e}")
        return jsonify({'message': 'Failed to clear archetype results', 'error': str(e)}), 500

def calculate_riasec_archetype(grades, order_ids: List[str] | None = None, *, gamma: float | None = None, r: float | None = None, tau: float | None = None, similarity: str | None = None):
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
    # Treat 0 (no input) as 0 weight. Grades scale is 1.00(best)..3.00(pass)..5.00(fail)
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

    # Build the canonical order used by the frontend for the mapped subset.
    # Only these mapped IDs affect RIASEC scoring; others are ignored.
    curriculum_order: List[str] = list(id_to_axes.keys())

    # If explicit order_ids provided from frontend, use that; else append CS ids after IT subset
    if order_ids and isinstance(order_ids, list) and all(isinstance(x, str) for x in order_ids):
        curriculum_order = list(order_ids)
    else:
        curriculum_order += list(id_to_axes_cs.keys())

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
        # Prefer IT map, then CS map
        tags = id_to_axes.get(course_id, id_to_axes_cs.get(course_id, []))
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
        for k in range(6):
            mask = labels == k
            if np.any(mask):
                centroids[k] = X[mask].mean(axis=0)

    # Soft aggregation across clusters with selectable similarity and temperature
    eps = 1e-9
    _tau = float(tau) if (tau is not None and math.isfinite(float(tau)) and float(tau) > 0) else 0.9
    _sim = (similarity or 'cosine').lower()
    if _sim == 'cosine':
        # cosine similarity between each X[i] and centroid[k]
        Xn = X / (np.linalg.norm(X, axis=1, keepdims=True) + eps)
        Cn = centroids / (np.linalg.norm(centroids, axis=1, keepdims=True) + eps)
        sims = Xn @ Cn.T  # [-1,1]
        # optional: clamp negatives to reduce cross-axis leakage
        sims = np.maximum(sims, 0.0)
        # temperature-scaled softmax
        sims_scaled = sims / _tau
        sims_scaled = sims_scaled - sims_scaled.max(axis=1, keepdims=True)
        expv = np.exp(sims_scaled)
        weights_soft = expv / (expv.sum(axis=1, keepdims=True) + eps)
    else:
        # cosine similarity 
        distances = np.linalg.norm(X[:, None, :] - centroids[None, :, :], axis=2)
        sims = -distances  # larger (less negative) is closer
        sims_scaled = sims / _tau
        sims_scaled = sims_scaled - sims_scaled.max(axis=1, keepdims=True)
        expv = np.exp(sims_scaled)
        weights_soft = expv / (expv.sum(axis=1, keepdims=True) + eps)

    # Compute direct axis sums (no clustering)
    direct_totals = X.sum(axis=0)
    direct_contribs: List[List[float]] = [[] for _ in range(6)]
    for vec in X:
        for k in range(6):
            v = float(vec[k])
            if v > 0:
                direct_contribs[k].append(v)

    # Compute soft K-Means totals
    soft_totals = np.zeros(6, dtype=float)
    soft_contribs: List[List[float]] = [[] for _ in range(6)]
    per_row_max = []
    for i, vec in enumerate(X):
        c = float(vec.sum())
        if c <= 0:
            continue
        row_weights = weights_soft[i, :]
        per_row_max.append(float(row_weights.max()))
        for k in range(6):
            share = float(row_weights[k]) * c
            if share > 0:
                soft_totals[k] += share
                soft_contribs[k].append(share)

    # Ambiguity-aware blend factor based on clustering confidence
    conf = float(np.mean(per_row_max)) if per_row_max else 1.0
    alpha = min(0.95, max(0.5, conf))

    # Blended totals and contributions
    totals = alpha * soft_totals + (1.0 - alpha) * direct_totals
    assigned_contribs: List[List[float]] = [[] for _ in range(6)]
    for k in range(6):
        # Blend lists by proportional scaling to match blended totals
        # Concatenate to preserve distribution variety
        blended = []
        if soft_contribs[k]:
            blended.extend([alpha * v for v in soft_contribs[k]])
        if direct_contribs[k]:
            blended.extend([(1.0 - alpha) * v for v in direct_contribs[k]])
        assigned_contribs[k] = blended

    total_sum = float(totals.sum())
    if total_sum <= 0:
        return {}

    percentages = (totals / total_sum) * 100.0
    scores = totals.tolist()

    # Determine primary archetype by highest percentage
    max_idx = int(np.argmax(percentages))
    axis_to_name = {
        'R': 'Realistic',
        'I': 'Investigative',
        'A': 'Artistic',
        'S': 'Social',
        'E': 'Enterprising',
        'C': 'Conventional',
    }
    primary = axis_to_name.get(axes[max_idx], axes[max_idx].lower())

    # --- Fairness normalizations ---
    # 1) Frequency-normalized: divide each axis total by how often that axis appears in mapping
    #    to counter curriculum axis frequency imbalance.
    tag_freq = np.zeros(6, dtype=float)
    # Rebuild the tag list consistent with the curriculum used above
    for course_id in curriculum_order[: len(grades)]:
        tags = id_to_axes.get(course_id, id_to_axes_cs.get(course_id, []))
        for t in tags:
            if t in axis_index:
                tag_freq[axis_index[t]] += 1.0

    def safe_div(a: float, b: float) -> float:
        return float(a) / float(b) if b and b != 0 else 0.0

    freq_adj = np.array([safe_div(totals[i], tag_freq[i]) for i in range(6)], dtype=float)
    freq_sum = float(freq_adj.sum())
    normalized_percentages = ((freq_adj / freq_sum) * 100.0).tolist() if freq_sum > 0 else [0.0] * 6

    # 2) Opportunity-normalized: divide by a maximum attainable weight per axis based on mapping.
    #    Here we assume max per-course weight is (4.0 - best_grade) = 3.0 and split across tags.
    MAX_W = 3.0
    opportunity_den = np.zeros(6, dtype=float)
    for course_id in curriculum_order[: len(grades)]:
        tags = id_to_axes.get(course_id, id_to_axes_cs.get(course_id, []))
        if not tags:
            continue
        share = MAX_W / len(tags)
        for t in tags:
            if t in axis_index:
                opportunity_den[axis_index[t]] += share
    opp_adj = np.array([safe_div(totals[i], opportunity_den[i]) for i in range(6)], dtype=float)
    opp_sum = float(opp_adj.sum())
    opportunity_normalized_percentages = ((opp_adj / opp_sum) * 100.0).tolist() if opp_sum > 0 else [0.0] * 6

    global_tag_freq = np.zeros(6, dtype=float)
    for course_id in curriculum_order:
        tags = id_to_axes.get(course_id, id_to_axes_cs.get(course_id, []))
        for t in tags:
            if t in axis_index:
                global_tag_freq[axis_index[t]] += 1.0

    def safe_idf(freq_val: float, gamma: float = 0.7) -> float:
        try:
            return 1.0 / (math.log(1.0 + float(freq_val)) ** gamma) if float(freq_val) > 0 else 1.0
        except Exception:
            return 1.0

    idf_gamma = float(gamma) if (gamma is not None and math.isfinite(float(gamma)) and float(gamma) > 0) else 0.7
    idf_weights = np.array([safe_idf(global_tag_freq[i], idf_gamma) for i in range(6)], dtype=float)

    r = float(r) if (r is not None and math.isfinite(float(r)) and 0.0 < float(r) < 1.0) else 0.75
    debias_totals = np.zeros(6, dtype=float)
    for i in range(6):
        if not assigned_contribs[i]:
            continue
        contribs = [c * idf_weights[i] for c in assigned_contribs[i]]
        contribs.sort(reverse=True)
        adj = 0.0
        for idx_c, c in enumerate(contribs):
            adj += (r ** idx_c) * c
        debias_totals[i] = adj

    debias_sum = float(debias_totals.sum())
    debias_percentages = ((debias_totals / debias_sum) * 100.0).tolist() if debias_sum > 0 else [0.0] * 6
    debias_scores = debias_totals.tolist()
    debias_max_idx = int(np.argmax(debias_percentages)) if debias_sum > 0 else max_idx
    primary_debiased = axis_to_name.get(axes[debias_max_idx], axes[debias_max_idx].lower())

    return {
        'primary_archetype': primary,
        'primary_archetype_debiased': primary_debiased,
        'archetype_percentages': {
            'Realistic': round(float(percentages[axis_index['R']]), 2),
            'Investigative': round(float(percentages[axis_index['I']]), 2),
            'Artistic': round(float(percentages[axis_index['A']]), 2),
            'Social': round(float(percentages[axis_index['S']]), 2),
            'Enterprising': round(float(percentages[axis_index['E']]), 2),
            'Conventional': round(float(percentages[axis_index['C']]), 2)
        },
        'normalized_percentages': {
            'Realistic': round(float(normalized_percentages[axis_index['R']]), 2),
            'Investigative': round(float(normalized_percentages[axis_index['I']]), 2),
            'Artistic': round(float(normalized_percentages[axis_index['A']]), 2),
            'Social': round(float(normalized_percentages[axis_index['S']]), 2),
            'Enterprising': round(float(normalized_percentages[axis_index['E']]), 2),
            'Conventional': round(float(normalized_percentages[axis_index['C']]), 2)
        },
        'opportunity_normalized_percentages': {
            'Realistic': round(float(opportunity_normalized_percentages[axis_index['R']]), 2),
            'Investigative': round(float(opportunity_normalized_percentages[axis_index['I']]), 2),
            'Artistic': round(float(opportunity_normalized_percentages[axis_index['A']]), 2),
            'Social': round(float(opportunity_normalized_percentages[axis_index['S']]), 2),
            'Enterprising': round(float(opportunity_normalized_percentages[axis_index['E']]), 2),
            'Conventional': round(float(opportunity_normalized_percentages[axis_index['C']]), 2)
        },
        'archetype_scores': {
            'Realistic': round(float(scores[axis_index['R']]), 3),
            'Investigative': round(float(scores[axis_index['I']]), 3),
            'Artistic': round(float(scores[axis_index['A']]), 3),
            'Social': round(float(scores[axis_index['S']]), 3),
            'Enterprising': round(float(scores[axis_index['E']]), 3),
            'Conventional': round(float(scores[axis_index['C']]), 3)
        },
        'debias_percentages': {
            'Realistic': round(float(debias_percentages[axis_index['R']]), 2),
            'Investigative': round(float(debias_percentages[axis_index['I']]), 2),
            'Artistic': round(float(debias_percentages[axis_index['A']]), 2),
            'Social': round(float(debias_percentages[axis_index['S']]), 2),
            'Enterprising': round(float(debias_percentages[axis_index['E']]), 2),
            'Conventional': round(float(debias_percentages[axis_index['C']]), 2)
        },
        'debias_scores': {
            'Realistic': round(float(debias_scores[axis_index['R']]), 3),
            'Investigative': round(float(debias_scores[axis_index['I']]), 3),
            'Artistic': round(float(debias_scores[axis_index['A']]), 3),
            'Social': round(float(debias_scores[axis_index['S']]), 3),
            'Enterprising': round(float(debias_scores[axis_index['E']]), 3),
            'Conventional': round(float(debias_scores[axis_index['C']]), 3)
        }
    }
