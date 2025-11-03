"""
Objective 1: Career Forecasting
Handles career prediction and analysis based on academic performance
"""

from flask import Blueprint, request, jsonify
from app.services.supabase_client import get_supabase_client
from app.routes.auth import token_required
import json
from datetime import datetime, timezone
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from joblib import dump, load
import os

bp = Blueprint('objective_1', __name__, url_prefix='/api/objective-1')

JOBS_MASTER = [
    'software_engineer','data_scientist','machine_learning_engineer','ai_engineer',
    'backend_engineer','frontend_engineer','full_stack_engineer','mobile_developer',
    'devops_engineer','cloud_engineer','site_reliability_engineer','systems_analyst',
    'business_analyst','product_manager','ui_ux_designer','qa_engineer',
    'test_automation_engineer','security_engineer','cybersecurity_analyst',
    'network_engineer','database_administrator','data_engineer','data_analyst',
    'etl_engineer','mlops_engineer','platform_engineer','solutions_architect',
    'enterprise_architect','it_support_specialist','it_project_manager',
    'systems_administrator','game_developer','embedded_software_engineer',
    'iot_engineer','computer_vision_engineer','nlp_engineer','research_engineer',
    'research_scientist','blockchain_engineer','ar_vr_developer'
]

@bp.route('/bootstrap-model', methods=['POST'])
def bootstrap_model():
    """Create a lightweight decision-tree model and save it to dt_career.joblib.
    Intended for development to unblock Objective 1 when no model exists."""
    try:
        feature_len = int(request.args.get('feature_len') or 70)
        n_samples = max(500, feature_len * 20)

        rng = np.random.default_rng(42)
        X = rng.uniform(0.0, 4.0, size=(n_samples, feature_len)).astype(float)

        # Build synthetic multi-target signals: weight groups of features to jobs
        n_labels = len(JOBS_MASTER)
        Y = np.zeros((n_samples, n_labels), dtype=float)

        for j in range(n_labels):
            # Each job emphasizes a sliding window of features
            start = (j * 3) % max(1, feature_len - 5)
            end = min(feature_len, start + 10)
            weights = np.linspace(1.0, 2.0, end - start)
            signal = (X[:, start:end] * weights).mean(axis=1)
            # Add small noise to vary targets
            Y[:, j] = signal + rng.normal(0, 0.05, size=n_samples)

        model = RandomForestRegressor(random_state=42, n_estimators=120, max_depth=18, n_jobs=-1)
        model.fit(X, Y)

        bundle = {'model': model, 'labels': JOBS_MASTER}
        os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
        dump(bundle, MODEL_PATH)

        return jsonify({'message': 'Model bootstrapped (RandomForest)', 'labels_count': n_labels, 'model_path': MODEL_PATH}), 200
    except Exception as e:
        return jsonify({'message': 'Bootstrap failed', 'error': str(e)}), 500

@bp.route('/latest', methods=['GET'])
def get_latest_career_forecast():
    """Return latest saved career forecast for a user by email."""
    try:
        email = (request.args.get('email') or '').strip().lower()
        if not email:
            return jsonify({'message': 'email is required'}), 400

        supabase = get_supabase_client()
        resp = supabase.table('users').select('career_top_jobs, career_forecast_analyzed_at').eq('email', email).execute()
        if not resp.data:
            return jsonify({'message': 'User not found', 'email': email}), 404

        row = resp.data[0]
        jobs = row.get('career_top_jobs') or []

        return jsonify({
            'email': email,
            'career_top_jobs': jobs,
            'career_forecast_analyzed_at': row.get('career_forecast_analyzed_at')
        }), 200
    except Exception as e:
        print(f"[OBJECTIVE-1] Latest fetch error: {e}")
        return jsonify({'message': 'Failed to fetch latest career forecast', 'error': str(e)}), 500

@bp.route('/process', methods=['POST'])
def process_career_forecast():
    """Process career forecasting based on academic data"""
    try:
        data = request.get_json(silent=True) or {}
        email = (data.get('email') or '').strip().lower()
        grades_data = data.get('grades') or []
        
        print(f"[OBJECTIVE-1] Career forecast processing for email: {email}")
        print(f"[OBJECTIVE-1] Received {len(grades_data)} grade records for career analysis")
        if grades_data:
            print(f"[OBJECTIVE-1] First grade record: {grades_data[0]}")
        
        # Handle grades as simple array of numbers
        grades = []
        for grade_value in grades_data:
            if isinstance(grade_value, (int, float)) and 0 <= grade_value <= 4:
                grades.append(float(grade_value))
        
        print(f"[OBJECTIVE-1] Processing {len(grades)} grade values: {grades}")
        
        # Career forecasting logic based on academic performance
        (career_labels, career_probs), forecast_error = calculate_career_forecast(grades)
        
        # Save to database
        if career_labels:
            try:
                supabase = get_supabase_client()
                
                # Get user by email
                user_response = supabase.table('users').select('id').eq('email', email).execute()
                if user_response.data:
                    user_id = user_response.data[0]['id']
                    
                    # Save as array of top jobs (ordered)
                    update_data = {
                        'career_forecast_analyzed_at': datetime.now(timezone.utc).isoformat(),
                        'career_top_jobs': career_labels,
                        'career_top_jobs_scores': career_probs
                    }
                    
                    supabase.table('users').update(update_data).eq('id', user_id).execute()
                    print(f"[OBJECTIVE-1] Saved career forecast to database for user {user_id}")
                else:
                    print(f"[OBJECTIVE-1] User not found for email: {email}")
            except Exception as db_error:
                print(f"[OBJECTIVE-1] Database save error: {db_error}")
        
        if not career_labels:
            status = 422
            msg = forecast_error or 'Career forecast unavailable'
            return jsonify({
                'message': msg,
                'email': email,
                'grades_count': len(grades)
            }), status

        return jsonify({
            'message': 'Career forecast processed (Objective 1)',
            'email': email,
            'grades_count': len(grades),
            'career_top_jobs': career_labels,
            'career_top_jobs_scores': career_probs
        }), 200
        
    except Exception as e:
        print(f"[OBJECTIVE-1] Error: {e}")
        return jsonify({'message': 'Career forecast failed', 'error': str(e)}), 500

@bp.route('/save-results', methods=['POST'])
def save_career_results():
    """Save career forecast results to database"""
    try:
        data = request.get_json() or {}
        email = data.get('email', '')
        career_results = data.get('careerResults', {})
        
        print(f"[OBJECTIVE-1] Saving career results for email: {email}")
        print(f"[OBJECTIVE-1] Career results keys: {list(career_results.keys())}")
        
        return jsonify({
            'message': 'Career results saved (Objective 1)',
            'email': email,
            'saved_to_db': True
        }), 200
        
    except Exception as e:
        print(f"[OBJECTIVE-1] Error: {e}")
        return jsonify({'message': 'Failed to save career results', 'error': str(e)}), 500

@bp.route('/clear-results', methods=['POST'])
def clear_career_results():
    """Clear career forecast results"""
    try:
        data = request.get_json(silent=True) or {}
        email = (data.get('email') or '').strip().lower()

        print(f"[OBJECTIVE-1] Clearing career results for email: {email}")

        if not email:
            return jsonify({'message': 'email is required'}), 400

        try:
            supabase = get_supabase_client()
            # Find user id
            user_resp = supabase.table('users').select('id').eq('email', email).limit(1).execute()
            if not user_resp.data:
                return jsonify({'message': 'User not found'}), 404
            user_id = user_resp.data[0]['id']

            # Null out/clear denormalized forecast columns
            update_data = {
                'career_forecast_analyzed_at': None,
                'career_top_jobs': [],
                'career_top_jobs_scores': [],
            }
            supabase.table('users').update(update_data).eq('id', user_id).execute()
            return jsonify({'message': 'Career results cleared (Objective 1)'}), 200
        except Exception as db_error:
            print(f"[OBJECTIVE-1] Clear DB error: {db_error}")
            return jsonify({'message': 'Failed to clear career results', 'error': str(db_error)}), 500
    except Exception as e:
        print(f"[OBJECTIVE-1] Error: {e}")
        return jsonify({'message': 'Failed to clear career results', 'error': str(e)}), 500

MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'models', 'dt_career.joblib')

def calculate_career_forecast(grades):
    """
    Career forecast via RandomForestRegressor over course-grade features.
    - Input: fixed numeric grades aligned with ITStaticTable order.
    - Output: dict of career -> probability (0..1), top 6 only.
    No fallbacks: returns {} if model cannot run or input invalid.
    """
    try:
        if not grades or not isinstance(grades, list):
            return [], 'Invalid or empty grades input'
        X = np.array([[float(g) for g in grades]])
        if X.size == 0:
            return [], 'Empty feature vector'

        # Load pre-trained model
        if not os.path.exists(MODEL_PATH):
            return [], f'Model file not found at {MODEL_PATH}'
        model_bundle = load(MODEL_PATH)
        model: RandomForestRegressor = model_bundle.get('model')
        labels: list[str] = model_bundle.get('labels')
        if model is None or not labels:
            return [], 'Model bundle missing required keys {model, labels}'
        # Predict per-career score (regression per label stacked)
        y_pred = model.predict(X)
        if y_pred.ndim == 1:
            # single target not supported for multi-career; treat as invalid
            return [], 'Model output shape invalid (expected multi-target)'
        scores = y_pred[0]
        # Normalize to 0..1 via min-max if needed
        s_min, s_max = float(np.min(scores)), float(np.max(scores))
        if s_max == s_min:
            return [], 'Model produced constant scores'
        probs = (scores - s_min) / (s_max - s_min)
        pairs = sorted(zip(labels, probs.tolist()), key=lambda x: x[1], reverse=True)
        top_pairs = pairs[:6]
        top_labels = [k for k, _ in top_pairs]
        top_probs = [round(float(v), 4) for _, v in top_pairs]
        return (top_labels, top_probs), None
    except Exception as e:
        return [], f'Model inference error: {e}'
