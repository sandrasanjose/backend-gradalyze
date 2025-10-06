from flask import Blueprint, request, jsonify, current_app
import os
from app.services.supabase_client import get_supabase_client
# Certificate analyzer functions inlined below

bp = Blueprint('ocr_cert', __name__, url_prefix='/api/ocr-cert')

@bp.route('/extract-text', methods=['POST'])
def extract_certificate_text():
    """Extract text from certificate documents using OCR"""
    try:
        data = request.get_json(silent=True) or {}
        email = (data.get('email') or '').strip().lower()
        certificate_path = data.get('certificate_path')
        
        if not email or not certificate_path:
            return jsonify({'message': 'email and certificate_path are required'}), 400
        
        supabase = get_supabase_client()
        
        # Verify user exists
        res_user = supabase.table('users').select('id').eq('email', email).limit(1).execute()
        if not res_user.data:
            return jsonify({'message': 'User not found'}), 404
        
        # Use TOR bucket for certificate extraction (fallback to legacy var or default)
        bucket = os.getenv('SUPABASE_TOR_BUCKET') or os.getenv('SUPABASE_BUCKET') or 'tor'
        
        # Download and extract text from certificate
        try:
            file_bytes = supabase.storage.from_(bucket).download(certificate_path)
            import io
            import pdfplumber
            
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                pages_text = [page.extract_text() or '' for page in pdf.pages]
            full_text = '\n'.join(pages_text)
            
            current_app.logger.info(f'Extracted {len(full_text)} characters from certificate')
            current_app.logger.info(f'First 200 characters: {full_text[:200]}')
            
        except Exception as e:
            current_app.logger.error(f'Certificate extraction failed: {e}')
            return jsonify({'message': 'Failed to extract text from certificate', 'error': str(e)}), 500
        
        # Analyze the extracted text
        analyzer = CertificateAnalyzer()
        analysis = analyzer.analyze_certificate(full_text)
        
        return jsonify({
            'message': 'Certificate text extracted and analyzed successfully',
            'extracted_text': full_text,
            'analysis': analysis,
            'text_length': len(full_text),
            'debug_info': {
                'text_preview': full_text[:200] + '...' if len(full_text) > 200 else full_text,
                'keywords_found': len(analysis.get('extracted_keywords', [])),
                'confidence_score': analysis.get('confidence_score', 0)
            }
        }), 200
        
    except Exception as error:
        current_app.logger.exception('Certificate extraction failed: %s', error)
        return jsonify({'message': 'Certificate extraction failed', 'error': str(error)}), 500


@bp.route('/analyze', methods=['POST'])
def analyze_certificate():
    """Analyze certificate text for career and archetype enhancements"""
    try:
        data = request.get_json(silent=True) or {}
        certificate_text = data.get('certificate_text', '')
        
        if not certificate_text:
            return jsonify({'message': 'certificate_text is required'}), 400
        
        # Analyze the certificate text
        analysis = analyze_certificate_text(certificate_text)
        
        return jsonify({
            'message': 'Certificate analysis completed',
            'analysis': analysis
        }), 200
        
    except Exception as error:
        current_app.logger.exception('Certificate analysis failed: %s', error)
        return jsonify({'message': 'Certificate analysis failed', 'error': str(error)}), 500


@bp.route('/enhance-analysis', methods=['POST'])
def enhance_analysis_with_certificates():
    """Enhance existing TOR analysis with certificate data"""
    try:
        data = request.get_json(silent=True) or {}
        email = (data.get('email') or '').strip().lower()
        certificate_analyses = data.get('certificate_analyses', [])
        
        if not email:
            return jsonify({'message': 'email is required'}), 400
        
        if not certificate_analyses:
            return jsonify({'message': 'certificate_analyses is required'}), 400
        
        supabase = get_supabase_client()
        
        # Get user's current TOR analysis
        res_user = supabase.table('users').select('id, tor_notes').eq('email', email).limit(1).execute()
        if not res_user.data:
            return jsonify({'message': 'User not found'}), 404
        
        user = res_user.data[0]
        
        # Parse existing TOR analysis
        try:
            tor_notes = user.get('tor_notes') or '{}'
            if isinstance(tor_notes, str):
                tor_analysis = json.loads(tor_notes)
            else:
                tor_analysis = tor_notes
        except Exception as e:
            current_app.logger.error(f'Failed to parse TOR notes: {e}')
            return jsonify({'message': 'Failed to parse existing analysis'}), 400
        
        # Enhance analysis with certificate data (inlined function)
        def enhance_analysis_with_certificates(tor_analysis: dict, certificate_analyses: list) -> dict:
            """Enhance TOR analysis with certificate data"""
            # Simple enhancement - just merge the certificate analyses
            enhanced = tor_analysis.copy()
            
            # Add certificate keywords
            all_keywords = []
            for cert_analysis in certificate_analyses:
                all_keywords.extend(cert_analysis.get('extracted_keywords', []))
            
            if all_keywords:
                enhanced['certificate_keywords'] = list(set(all_keywords))
            
            return enhanced
        
        enhanced_analysis = enhance_analysis_with_certificates(tor_analysis, certificate_analyses)
        
        # Update user's TOR notes with enhanced analysis
        import json as _json
        from datetime import datetime, timezone
        
        update_data = {
            'tor_notes': _json.dumps(enhanced_analysis),
            'archetype_analyzed_at': datetime.now(timezone.utc).isoformat()
        }
        
        # Certificate enhancement only - no archetype logic here
        # Archetype analysis should be handled by objective_2
        
        supabase.table('users').update(update_data).eq('id', user['id']).execute()
        
        return jsonify({
            'message': 'Analysis enhanced with certificate data',
            'enhanced_analysis': enhanced_analysis,
            'certificate_count': len(certificate_analyses)
        }), 200
        
    except Exception as error:
        current_app.logger.exception('Certificate enhancement failed: %s', error)
        return jsonify({'message': 'Certificate enhancement failed', 'error': str(error)}), 500
