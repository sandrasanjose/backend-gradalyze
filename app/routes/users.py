from flask import Blueprint, jsonify, request
import os
from app.routes.auth import token_required
from app.services.supabase_client import get_supabase_client

bp = Blueprint("users", __name__, url_prefix="/api/users")

@bp.route("/", methods=["GET"])
@token_required
def list_users(current_user):
    try:
        supabase = get_supabase_client()
        response = supabase.table("users").select("*").execute()
        return jsonify(response.data), 200
    except Exception as error:
        return jsonify({"error": str(error)}), 500

@bp.route("/", methods=["POST"])
@token_required
def add_user(current_user):
    try:
        payload = request.get_json(silent=True) or {}
        if not payload:
            return jsonify({"error": "No data provided"}), 400
        supabase = get_supabase_client()
        response = supabase.table("users").insert(payload).execute()
        return jsonify(response.data), 201
    except Exception as error:
        return jsonify({"error": str(error)}), 500

@bp.route("/<int:user_id>", methods=["GET"])
@token_required
def get_user(current_user, user_id):
    try:
        supabase = get_supabase_client()
        response = supabase.table("users").select("*").eq("id", user_id).execute()
        if not response.data:
            return jsonify({"error": "User not found"}), 404
        return jsonify(response.data[0]), 200
    except Exception as error:
        return jsonify({"error": str(error)}), 500

@bp.route("/<int:user_id>", methods=["PUT"])
@token_required
def update_user(current_user, user_id):
    try:
        payload = request.get_json(silent=True) or {}
        if not payload:
            return jsonify({"error": "No data provided"}), 400
        supabase = get_supabase_client()
        response = supabase.table("users").update(payload).eq("id", user_id).execute()
        return jsonify(response.data), 200
    except Exception as error:
        return jsonify({"error": str(error)}), 500

@bp.route("/<int:user_id>", methods=["DELETE"])
@token_required
def delete_user(current_user, user_id):
    try:
        supabase = get_supabase_client()
        response = supabase.table("users").delete().eq("id", user_id).execute()
        return jsonify({"message": "User deleted successfully"}), 200
    except Exception as error:
        return jsonify({"error": str(error)}), 500

@bp.route("/profile-summary", methods=["GET"])
def profile_summary():
    try:
        email = (request.args.get('email') or '').strip().lower()
        if not email:
            return jsonify({'message': 'email is required'}), 400
        supabase = get_supabase_client()
        cols = (
            'id, name, email, course, student_number, '
            'tor_storage_path, tor_url, '
            'certificate_paths, certificate_urls, latest_certificate_path, latest_certificate_url, '
            'primary_archetype, archetype_analyzed_at, '
            'archetype_realistic_percentage, archetype_investigative_percentage, archetype_artistic_percentage, '
            'archetype_social_percentage, archetype_enterprising_percentage, archetype_conventional_percentage, '
            'career_top_jobs, career_top_jobs_scores, career_forecast_analyzed_at, '
            'job_recommendations'
        )
        resp = supabase.table('users').select(cols).eq('email', email).execute()
        if not resp.data:
            return jsonify({'message': 'User not found', 'email': email}), 404
        return jsonify(resp.data[0]), 200
    except Exception as error:
        return jsonify({'message': 'Profile summary failed', 'error': str(error)}), 500

@bp.route('/upload-tor', methods=['POST'])
def upload_tor_v2():
    """Upload TOR file to Supabase storage and persist path/URL to users table."""
    try:
        supabase = get_supabase_client()
        if 'file' not in request.files:
            return jsonify({'message': 'file is required'}), 400
        email = (request.form.get('email') or '').strip().lower()
        if not email:
            return jsonify({'message': 'email is required'}), 400

        file = request.files['file']
        bucket = os.getenv('SUPABASE_TOR_BUCKET', 'transcripts')
        filename = file.filename or 'tor.pdf'
        storage_path = f"{email}/{filename}"

        # Upload
        file_bytes = file.read()
        upload_result = supabase.storage.from_(bucket).upload(
            storage_path,
            file_bytes,
            {'content-type': file.mimetype or 'application/pdf', 'upsert': 'true'}
        )
        # If the client returns a dict with an error field, bubble it up
        if isinstance(upload_result, dict):
            possible_error = upload_result.get('error') or upload_result.get('Error')
            if possible_error:
                return jsonify({'message': 'Upload failed', 'error': str(possible_error)}), 500
        # Get public URL
        public_url_resp = supabase.storage.from_(bucket).get_public_url(storage_path)
        public_url = None
        if isinstance(public_url_resp, dict):
            data_obj = public_url_resp.get('data') or public_url_resp
            public_url = (
                data_obj.get('publicUrl')
                or data_obj.get('public_url')
                or data_obj.get('publicURL')
            )
        if not public_url:
            public_url = str(public_url_resp)

        # Save to users table
        user = supabase.table('users').select('id:user_id').eq('email', email).execute()
        if not user.data:
            return jsonify({'message': 'User not found'}), 404
        supabase.table('users').update({
            'tor_storage_path': storage_path,
            'tor_url': public_url,
            'tor_uploaded_at': supabase.rpc if False else None
        }).eq('user_id', user.data[0]['user_id']).execute()

        return jsonify({'message': 'uploaded', 'storage_path': storage_path, 'url': public_url}), 200
    except Exception as error:
        return jsonify({'message': 'Upload failed', 'error': str(error)}), 500

@bp.route('/delete-tor', methods=['DELETE', 'OPTIONS'])
def delete_tor():
    """Delete a user's TOR from Supabase storage and clear fields in users table.

    Query params:
      - email: user email (required)
    """
    try:
        if request.method == 'OPTIONS':
            return ('', 204)

        email = (request.args.get('email') or '').strip().lower()
        if not email:
            return jsonify({'message': 'email is required'}), 400

        supabase = get_supabase_client()
        # Fetch user and current tor path
        user_resp = supabase.table('users').select('user_id, tor_storage_path').eq('email', email).limit(1).execute()
        if not user_resp.data:
            return jsonify({'message': 'User not found'}), 404
        user_row = user_resp.data[0]
        storage_path = user_row.get('tor_storage_path')

        # Remove from storage if path exists
        if storage_path:
            bucket = os.getenv('SUPABASE_TOR_BUCKET', 'transcripts')
            try:
                remove_result = supabase.storage.from_(bucket).remove([storage_path])
                # If API returns error-like dict, surface it
                if isinstance(remove_result, dict) and (remove_result.get('error') or remove_result.get('Error')):
                    return jsonify({'message': 'Delete failed', 'error': str(remove_result.get('error') or remove_result.get('Error'))}), 500
            except Exception as err:
                # Continue to clear DB even if object missing
                pass

        # Clear fields in users table
        supabase.table('users').update({
            'tor_storage_path': None,
            'tor_url': None,
            'tor_uploaded_at': None
        }).eq('user_id', user_row['user_id']).execute()

        return jsonify({'message': 'deleted'}), 200
    except Exception as error:
        return jsonify({'message': 'Delete failed', 'error': str(error)}), 500

@bp.route('/upload-certificates', methods=['POST'])
def upload_certificates_v2():
    """Upload one or more certificates to Supabase storage and persist paths/URLs."""
    try:
        supabase = get_supabase_client()
        if 'files' not in request.files:
            return jsonify({'message': 'files[] is required'}), 400
        email = (request.form.get('email') or '').strip().lower()
        if not email:
            return jsonify({'message': 'email is required'}), 400

        files = request.files.getlist('files')
        bucket = os.getenv('SUPABASE_CERT_BUCKET', 'certificates')
        paths, urls = [], []
        for f in files:
            filename = f.filename or 'certificate.pdf'
            storage_path = f"{email}/{filename}"
            f_bytes = f.read()
            cert_upload_result = supabase.storage.from_(bucket).upload(
                storage_path,
                f_bytes,
                {'content-type': f.mimetype or 'application/pdf', 'upsert': 'true'}
            )
            if isinstance(cert_upload_result, dict):
                cert_error = cert_upload_result.get('error') or cert_upload_result.get('Error')
                if cert_error:
                    return jsonify({'message': 'Upload failed', 'error': str(cert_error)}), 500
            public_url_resp = supabase.storage.from_(bucket).get_public_url(storage_path)
            public_url = None
            if isinstance(public_url_resp, dict):
                data_obj = public_url_resp.get('data') or public_url_resp
                public_url = (
                    data_obj.get('publicUrl')
                    or data_obj.get('public_url')
                    or data_obj.get('publicURL')
                )
            if not public_url:
                public_url = str(public_url_resp)
            paths.append(storage_path)
            urls.append(public_url)

        user = supabase.table('users').select('id, certificate_paths, certificate_urls').eq('email', email).execute()
        if not user.data:
            return jsonify({'message': 'User not found'}), 404
        prev_paths = user.data[0].get('certificate_paths') or []
        prev_urls = user.data[0].get('certificate_urls') or []
        supabase.table('users').update({
            'certificate_paths': prev_paths + paths,
            'certificate_urls': prev_urls + urls,
            'latest_certificate_path': paths[-1] if paths else None,
            'latest_certificate_url': urls[-1] if urls else None
        }).eq('user_id', user.data[0]['user_id']).execute()

        return jsonify({'message': 'uploaded', 'paths': paths, 'urls': urls}), 200
    except Exception as error:
        return jsonify({'message': 'Upload failed', 'error': str(error)}), 500

@bp.route('/delete-certificate', methods=['DELETE', 'OPTIONS'])
def delete_certificate_v2():
    """Delete a single certificate by path or url and update user arrays.

    Body JSON:
      - email: user email (required)
      - certificate_path: storage path within cert bucket (preferred)
      - certificate_url: public URL (alternative)
    """
    try:
        if request.method == 'OPTIONS':
            return ('', 204)

        data = request.get_json(silent=True) or {}
        email = (data.get('email') or '').strip().lower()
        cert_path = (data.get('certificate_path') or '').strip()
        cert_url = (data.get('certificate_url') or '').strip()
        if not email:
            return jsonify({'message': 'email is required'}), 400
        if not cert_path and not cert_url:
            return jsonify({'message': 'certificate_path or certificate_url is required'}), 400

        supabase = get_supabase_client()
        user_resp = supabase.table('users').select('id, certificate_paths, certificate_urls, latest_certificate_path, latest_certificate_url').eq('email', email).limit(1).execute()
        if not user_resp.data:
            return jsonify({'message': 'User not found'}), 404
        user_row = user_resp.data[0]
        user_id = user_row['user_id']

        bucket = os.getenv('SUPABASE_CERT_BUCKET', 'certificates')

        # Determine storage path if only URL provided
        if not cert_path and cert_url:
            try:
                marker = f"/{bucket}/"
                idx = cert_url.find(marker)
                if idx != -1:
                    cert_path = cert_url[idx + len(marker):]
            except Exception:
                cert_path = ''

        # Attempt storage removal when path known
        if cert_path:
            try:
                remove_result = supabase.storage.from_(bucket).remove([cert_path])
                if isinstance(remove_result, dict) and (remove_result.get('error') or remove_result.get('Error')):
                    # Proceed to update DB arrays even if storage deletion reports error (object may be gone)
                    pass
            except Exception:
                pass

        # Update arrays in DB
        prev_paths = (user_row.get('certificate_paths') or [])[:]
        prev_urls = (user_row.get('certificate_urls') or [])[:]
        # Also derive the counterpart URL from the path to remove matching entry in urls
        derived_url = None
        if cert_path:
            try:
                public_url_resp = supabase.storage.from_(bucket).get_public_url(cert_path)
                if isinstance(public_url_resp, dict):
                    data_obj = public_url_resp.get('data') or public_url_resp
                    derived_url = (
                        data_obj.get('publicUrl')
                        or data_obj.get('public_url')
                        or data_obj.get('publicURL')
                    )
                else:
                    derived_url = str(public_url_resp)
            except Exception:
                derived_url = None

        # Normalize empties
        target_path = cert_path or ''
        target_url = cert_url or derived_url or ''

        new_paths = [p for p in prev_paths if p and p != target_path]
        # Remove both provided URL and derived public URL if present
        new_urls = [u for u in prev_urls if u and u != target_url]

        # Recompute latest fields
        new_latest_path = new_paths[-1] if new_paths else None
        new_latest_url = new_urls[-1] if new_urls else None

        update_payload = {
            'certificate_paths': new_paths,
            'certificate_urls': new_urls,
            'latest_certificate_path': new_latest_path,
            'latest_certificate_url': new_latest_url
        }
        supabase.table('users').update(update_payload).eq('user_id', user_id).execute()

        return jsonify({'message': 'deleted', 'certificate_paths': new_paths, 'certificate_urls': new_urls}), 200
    except Exception as error:
        return jsonify({'message': 'Delete failed', 'error': str(error)}), 500

@bp.route('/extract-grades', methods=['POST', 'OPTIONS'])
def extract_grades():
    """Accept a TOR upload, OCR it via ocr_tor, persist grades to the user, and return them.

    Accepts multipart/form-data:
      - file: TOR file (required)
      - email: user email (required)
    """
    try:
        if request.method == 'OPTIONS':
            return ('', 204)

        supabase = get_supabase_client()

        file_bytes = None
        filename = 'tor.pdf'
        email = ''

        # Case 1: multipart upload (file + email)
        if 'file' in request.files:
            email = (request.form.get('email') or '').strip().lower()
            if not email:
                return jsonify({'error': 'email is required'}), 400
            tor_file = request.files['file']
            filename = tor_file.filename or 'tor.pdf'
            file_bytes = tor_file.read()
        else:
            # Case 2: JSON body with storage_path + email
            data = request.get_json(silent=True) or {}
            email = (data.get('email') or '').strip().lower()
            storage_path = (data.get('storage_path') or '').strip()
            if not email:
                return jsonify({'error': 'email is required'}), 400
            if not storage_path:
                return jsonify({'error': 'file or storage_path is required'}), 400
            bucket = os.getenv('SUPABASE_TOR_BUCKET', 'transcripts')
            try:
                downloaded = supabase.storage.from_(bucket).download(storage_path)
                # Some clients return bytes; others may return dict with data
                if isinstance(downloaded, (bytes, bytearray)):
                    file_bytes = bytes(downloaded)
                elif isinstance(downloaded, dict):
                    file_bytes = downloaded.get('data')
                else:
                    file_bytes = None
                filename = storage_path.split('/')[-1] or 'tor.pdf'
            except Exception as dl_err:
                return jsonify({'error': f'Failed to download file: {str(dl_err)}'}), 400
        if not file_bytes:
            return jsonify({'error': 'Unable to read TOR file'}), 400

        # Call OCR processor
        from app.routes.ocr_tor import extract_grades_from_tor
        ocr_result = extract_grades_from_tor(file_bytes, filename) or {}
        grades = ocr_result.get('grades') or []
        grade_values = ocr_result.get('grade_values') or []
        full_text = ocr_result.get('full_text') or ""

        # Validate minimal structure if any grades are returned
        for g in grades:
            for field in ['id', 'subject', 'units', 'grade', 'semester']:
                if field not in (g or {}):
                    return jsonify({'error': f'Missing required field: {field}'}), 400

        # Resolve user by email
        res_user = supabase.table('users').select('id:user_id').eq('email', email).limit(1).execute()
        if not res_user.data:
            return jsonify({'error': 'User not found'}), 404
        user_id = res_user.data[0]['user_id']

        # Save extracted grades
        res_upd = supabase.table('users').update({'grades': grades}).eq('user_id', user_id).execute()
        saved = (res_upd.data[0].get('grades') if res_upd.data else grades) or grades

        return jsonify({'success': True, 'grades': saved, 'grade_values': grade_values, 'full_text': full_text}), 200
    except Exception as error:
        return jsonify({'message': 'Extract grades failed', 'error': str(error)}), 500

