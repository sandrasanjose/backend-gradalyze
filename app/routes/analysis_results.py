"""
Analysis Results Routes
API endpoints for managing career analysis results
"""

from flask import Blueprint, request, jsonify, current_app
from app.routes.auth import token_required
from app.models.analysis_results import AnalysisResult

bp = Blueprint('analysis_results', __name__, url_prefix='/api/analysis-results')


@bp.route('/', methods=['GET'])
@token_required
def get_analysis_result(current_user):
    """Get the latest analysis result for a user"""
    try:
        user_id = request.args.get('user_id', type=int)
        if not user_id:
            return jsonify({'message': 'user_id is required'}), 400
        
        result = AnalysisResult.get_by_user_id(user_id)
        if not result:
            return jsonify({'message': 'No analysis found'}), 404
        
        return jsonify(result), 200
    except Exception as e:
        current_app.logger.exception('Failed to fetch analysis result: %s', e)
        return jsonify({'message': 'Failed to fetch analysis', 'error': str(e)}), 500


@bp.route('/history', methods=['GET'])
@token_required
def get_analysis_history(current_user):
    """Get all analysis results for a user (historical)"""
    try:
        user_id = request.args.get('user_id', type=int)
        if not user_id:
            return jsonify({'message': 'user_id is required'}), 400
        
        results = AnalysisResult.get_all_by_user_id(user_id)
        return jsonify({'results': results}), 200
    except Exception as e:
        current_app.logger.exception('Failed to fetch analysis history: %s', e)
        return jsonify({'message': 'Failed to fetch history', 'error': str(e)}), 500


@bp.route('/<int:analysis_id>', methods=['GET'])
@token_required
def get_analysis_by_id(current_user, analysis_id):
    """Get a specific analysis result by ID"""
    try:
        result = AnalysisResult.get_by_id(analysis_id)
        if not result:
            return jsonify({'message': 'Analysis not found'}), 404
        return jsonify(result), 200
    except Exception as e:
        current_app.logger.exception('Failed to fetch analysis: %s', e)
        return jsonify({'message': 'Failed to fetch analysis', 'error': str(e)}), 500


@bp.route('/', methods=['POST'])
@token_required
def create_analysis_result(current_user):
    """Create a new analysis result"""
    try:
        data = request.get_json() or {}
        
        if 'user_id' not in data:
            return jsonify({'message': 'user_id is required'}), 400
        
        result = AnalysisResult.create(data)
        return jsonify({'message': 'Analysis created', 'result': result}), 201
    except Exception as e:
        current_app.logger.exception('Failed to create analysis: %s', e)
        return jsonify({'message': 'Failed to create analysis', 'error': str(e)}), 500


@bp.route('/upsert', methods=['POST'])
@token_required
def upsert_analysis_result(current_user):
    """Create or update analysis result for a user"""
    try:
        data = request.get_json() or {}
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({'message': 'user_id is required'}), 400
        
        # Remove user_id from update data to avoid conflicts
        update_data = {k: v for k, v in data.items() if k != 'user_id'}
        
        result = AnalysisResult.upsert_by_user_id(user_id, update_data)
        return jsonify({'message': 'Analysis saved', 'result': result}), 200
    except Exception as e:
        current_app.logger.exception('Failed to upsert analysis: %s', e)
        return jsonify({'message': 'Failed to save analysis', 'error': str(e)}), 500


@bp.route('/<int:analysis_id>', methods=['PUT'])
@token_required
def update_analysis_result(current_user, analysis_id):
    """Update an analysis result"""
    try:
        data = request.get_json() or {}
        if not data:
            return jsonify({'message': 'No data provided'}), 400
        
        # Remove fields that shouldn't be updated
        data.pop('analysis_id', None)
        data.pop('user_id', None)
        data.pop('created_at', None)
        
        updated = AnalysisResult.update(analysis_id, data)
        return jsonify({'message': 'Analysis updated', 'result': updated}), 200
    except Exception as e:
        current_app.logger.exception('Failed to update analysis: %s', e)
        return jsonify({'message': 'Failed to update analysis', 'error': str(e)}), 500


@bp.route('/<int:analysis_id>', methods=['DELETE'])
@token_required
def delete_analysis_result(current_user, analysis_id):
    """Delete an analysis result"""
    try:
        success = AnalysisResult.delete(analysis_id)
        if success:
            return jsonify({'message': 'Analysis deleted'}), 200
        return jsonify({'message': 'Analysis not found'}), 404
    except Exception as e:
        current_app.logger.exception('Failed to delete analysis: %s', e)
        return jsonify({'message': 'Failed to delete analysis', 'error': str(e)}), 500


@bp.route('/user/<int:user_id>', methods=['DELETE'])
@token_required
def delete_user_analysis_results(current_user, user_id):
    """Delete all analysis results for a user"""
    try:
        success = AnalysisResult.delete_by_user_id(user_id)
        if success:
            return jsonify({'message': 'All analyses deleted'}), 200
        return jsonify({'message': 'No analyses found'}), 404
    except Exception as e:
        current_app.logger.exception('Failed to delete user analyses: %s', e)
        return jsonify({'message': 'Failed to delete analyses', 'error': str(e)}), 500
