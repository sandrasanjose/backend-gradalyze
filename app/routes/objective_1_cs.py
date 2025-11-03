"""
Objective 1 (CS): Career Forecasting for BSCS program

Uses the same model interface as Objective 1, but exposes a separate endpoint
namespace so the frontend can call program-specific routes if desired.
"""

from flask import Blueprint, request, jsonify
from app.services.supabase_client import get_supabase_client
from datetime import datetime, timezone
from joblib import load, dump
from app.routes.objective_1 import JOBS_MASTER
import numpy as np
import os

bp = Blueprint('objective_1_cs', __name__, url_prefix='/api/objective-1-cs')

# CS-specific model path
MODEL_PATH_CS = os.path.join(os.path.dirname(__file__), '..', '..', 'models', 'dt_career_cs.joblib')

@bp.route('/process', methods=['POST'])
def process_career_forecast_cs():
    try:
        data = request.get_json(silent=True) or {}
        email = (data.get('email') or '').strip().lower()
        grades_data = data.get('grades') or []

        # Coerce numeric grades (0..4)
        grades = []
        for g in grades_data:
            try:
                x = float(g)
            except Exception:
                continue
            if 0 <= x <= 4:
                grades.append(x)

        # Inference identical to IT variant for now
        (career_labels, career_probs), forecast_error = _run_model(grades)

        if not career_labels:
            return jsonify({'message': forecast_error or 'Career forecast unavailable', 'email': email, 'grades_count': len(grades)}), 422

        # Persist denormalized result
        try:
            supabase = get_supabase_client()
            user_resp = supabase.table('users').select('id').eq('email', email).limit(1).execute()
            if user_resp.data:
                user_id = user_resp.data[0]['id']
                supabase.table('users').update({
                    'career_forecast_analyzed_at': datetime.now(timezone.utc).isoformat(),
                    'career_top_jobs': career_labels,
                    'career_top_jobs_scores': career_probs
                }).eq('id', user_id).execute()
        except Exception:
            pass

        return jsonify({
            'message': 'Career forecast processed (Objective 1 - CS)',
            'email': email,
            'grades_count': len(grades),
            'career_top_jobs': career_labels,
            'career_top_jobs_scores': career_probs
        }), 200
    except Exception as e:
        return jsonify({'message': 'Career forecast failed', 'error': str(e)}), 500

@bp.route('/clear-results', methods=['POST'])
def clear_career_results_cs():
    try:
        data = request.get_json(silent=True) or {}
        email = (data.get('email') or '').strip().lower()
        if not email:
            return jsonify({'message': 'email is required'}), 400
        supabase = get_supabase_client()
        user_resp = supabase.table('users').select('id').eq('email', email).limit(1).execute()
        if not user_resp.data:
            return jsonify({'message': 'User not found'}), 404
        user_id = user_resp.data[0]['id']
        supabase.table('users').update({
            'career_forecast_analyzed_at': None,
            'career_top_jobs': [],
            'career_top_jobs_scores': [],
        }).eq('id', user_id).execute()
        return jsonify({'message': 'Career results cleared (Objective 1 - CS)'}), 200
    except Exception as e:
        return jsonify({'message': 'Failed to clear career results', 'error': str(e)}), 500

@bp.route('/train', methods=['POST'])
def train_career_model_cs():
    """
    Train a CS-specific career forecasting model from labeled data.

    Expected JSON body:
    {
      "samples": [
        { "grades": [..number..], "labels": {"software_engineer": 0.92, ...} },
        ...
      ]
    }
    - grades: numeric vector aligned with the CS table order you use in the frontend
    - labels: dict of job -> score (0..1). Jobs not present default to 0.
    """
    try:
        data = request.get_json(silent=True) or {}
        samples = data.get('samples') or []
        if not isinstance(samples, list) or not samples:
            return jsonify({'message': 'samples array required'}), 400

        # Use shared JOBS_MASTER for consistent label space with IT
        labels = list(JOBS_MASTER)

        # Build X, Y
        X_rows = []
        Y_rows = []
        for s in samples:
            g = s.get('grades') or []
            try:
                vec = [float(x) for x in g]
            except Exception:
                vec = []
            if not vec:
                continue
            # normalize invalid values
            vec = [min(4.0, max(0.0, x)) for x in vec]
            X_rows.append(vec)
            lbs = s.get('labels') or {}
            target = []
            for name in labels:
                try:
                    v = float(lbs.get(name, 0.0))
                except Exception:
                    v = 0.0
                target.append(min(1.0, max(0.0, v)))
            Y_rows.append(target)

        if not X_rows:
            return jsonify({'message': 'no valid samples with grades found'}), 400

        # Pad/truncate feature vectors to the same length
        feat_len = max(len(r) for r in X_rows)
        X = []
        for r in X_rows:
            if len(r) < feat_len:
                X.append(r + [0.0] * (feat_len - len(r)))
            else:
                X.append(r[:feat_len])
        X = np.array(X, dtype=float)
        Y = np.array(Y_rows, dtype=float)

        # Train multi-output regressor
        from sklearn.ensemble import RandomForestRegressor
        model = RandomForestRegressor(random_state=42, n_estimators=180, max_depth=22, n_jobs=-1)
        model.fit(X, Y)

        bundle = {'model': model, 'labels': labels}
        os.makedirs(os.path.dirname(MODEL_PATH_CS), exist_ok=True)
        from joblib import dump
        dump(bundle, MODEL_PATH_CS)

        return jsonify({'message': 'CS model trained', 'labels_count': len(labels), 'feature_len': int(feat_len), 'model_path': MODEL_PATH_CS}), 200
    except Exception as e:
        return jsonify({'message': 'Training failed', 'error': str(e)}), 500

def _run_model(grades):
    try:
        if not grades or not isinstance(grades, list):
            return ([], []), 'Invalid or empty grades input'
        X = np.array([[float(g) for g in grades]])
        if X.size == 0:
            return ([], []), 'Empty feature vector'
        # Ensure a CS model exists; if not, bootstrap a fresh CS model tuned to input length
        _ensure_model(len(grades))
        model_path = MODEL_PATH_CS
        if not os.path.exists(model_path):
            return ([], []), f'Model file not found at {model_path}'
        model_bundle = load(model_path)
        model = model_bundle.get('model')
        labels = model_bundle.get('labels')
        if model is None or not labels:
            return ([], []), 'Model bundle missing required keys {model, labels}'
        y_pred = model.predict(X)
        if y_pred.ndim == 1:
            return ([], []), 'Model output shape invalid (expected multi-target)'
        scores = y_pred[0]
        s_min, s_max = float(np.min(scores)), float(np.max(scores))
        if s_max == s_min:
            return ([], []), 'Model produced constant scores'
        probs = (scores - s_min) / (s_max - s_min)
        pairs = sorted(zip(labels, probs.tolist()), key=lambda x: x[1], reverse=True)
        top_pairs = pairs[:6]
        top_labels = [k for k, _ in top_pairs]
        top_probs = [round(float(v), 4) for _, v in top_pairs]
        return (top_labels, top_probs), None
    except Exception as e:
        return ([], []), f'Model inference error: {e}'

# Default fallback feature length if no hint provided
TARGET_FEATURE_LEN = 75

def _ensure_model(feature_len_hint: int | None = None):
    """Guarantee a CS model file exists.
    If missing, bootstrap a small CS bundle with default labels.
    """
    try:
        # Determine desired feature length (prefer runtime hint)
        desired_len = int(feature_len_hint) if feature_len_hint and feature_len_hint > 0 else TARGET_FEATURE_LEN

        # Case 1: CS model exists and matches desired feature length
        if os.path.exists(MODEL_PATH_CS):
            try:
                bundle = load(MODEL_PATH_CS)
                model = bundle.get('model')
                n_in = getattr(model, 'n_features_in_', None)
                if n_in == desired_len:
                    return
                # else retrain/refresh to desired length
            except Exception:
                pass
        # Case 2: bootstrap lightweight CS model
        from sklearn.ensemble import RandomForestRegressor
        seed = 42
        feature_len = desired_len
        n_samples = max(800, feature_len * 30)
        rng = np.random.default_rng(seed)
        X = rng.uniform(0.0, 4.0, size=(n_samples, feature_len)).astype(float)
        labels = list(JOBS_MASTER)
        Y = np.zeros((n_samples, len(labels)), dtype=float)
        for j, _ in enumerate(labels):
            start = (j * 3) % max(1, feature_len - 8)
            end = min(feature_len, start + 12)
            weights = np.linspace(0.6, 1.8, end - start)
            base = (X[:, start:end] * weights).mean(axis=1)
            noise = rng.normal(0, 0.05, size=n_samples)
            Y[:, j] = np.tanh(base / 3.0) + noise
        model = RandomForestRegressor(random_state=seed, n_estimators=160, max_depth=20, n_jobs=-1)
        model.fit(X, Y)
        bundle = {'model': model, 'labels': labels}
        os.makedirs(os.path.dirname(MODEL_PATH_CS), exist_ok=True)
        dump(bundle, MODEL_PATH_CS)
    except Exception:
        # Best-effort; processing will surface errors if still missing
        pass


