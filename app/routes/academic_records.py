"""
Academic Records Routes
API endpoints for managing student academic records
"""

from flask import Blueprint, request, jsonify, current_app
from app.routes.auth import token_required
from app.models.academic_records import AcademicRecord

bp = Blueprint('academic_records', __name__, url_prefix='/api/academic-records')


@bp.route('/', methods=['GET'])
@token_required
def get_academic_records(current_user):
    """Get all academic records for the authenticated user"""
    try:
        user_id = request.args.get('user_id', type=int)
        if not user_id:
            return jsonify({'message': 'user_id is required'}), 400
        
        records = AcademicRecord.get_by_user_id(user_id)
        return jsonify({'records': records}), 200
    except Exception as e:
        current_app.logger.exception('Failed to fetch academic records: %s', e)
        return jsonify({'message': 'Failed to fetch records', 'error': str(e)}), 500


@bp.route('/<int:record_id>', methods=['GET'])
@token_required
def get_academic_record(current_user, record_id):
    """Get a specific academic record by ID"""
    try:
        record = AcademicRecord.get_by_id(record_id)
        if not record:
            return jsonify({'message': 'Record not found'}), 404
        return jsonify(record), 200
    except Exception as e:
        current_app.logger.exception('Failed to fetch academic record: %s', e)
        return jsonify({'message': 'Failed to fetch record', 'error': str(e)}), 500


@bp.route('/', methods=['POST'])
@token_required
def create_academic_record(current_user):
    """Create a new academic record"""
    try:
        data = request.get_json() or {}
        
        # Validate required fields
        required = ['user_id', 'sub_name', 'units', 'grades']
        missing = [f for f in required if f not in data]
        if missing:
            return jsonify({'message': 'Missing required fields', 'missing': missing}), 400
        
        record = AcademicRecord.create(data)
        return jsonify({'message': 'Record created', 'record': record}), 201
    except Exception as e:
        current_app.logger.exception('Failed to create academic record: %s', e)
        return jsonify({'message': 'Failed to create record', 'error': str(e)}), 500


@bp.route('/bulk', methods=['POST'])
@token_required
def create_academic_records_bulk(current_user):
    """Create multiple academic records at once"""
    try:
        data = request.get_json() or {}
        records = data.get('records', [])
        
        if not records or not isinstance(records, list):
            return jsonify({'message': 'records array is required'}), 400
        
        created = AcademicRecord.create_bulk(records)
        return jsonify({'message': f'{len(created)} records created', 'records': created}), 201
    except Exception as e:
        current_app.logger.exception('Failed to create academic records: %s', e)
        return jsonify({'message': 'Failed to create records', 'error': str(e)}), 500


@bp.route('/<int:record_id>', methods=['PUT'])
@token_required
def update_academic_record(current_user, record_id):
    """Update an academic record"""
    try:
        data = request.get_json() or {}
        if not data:
            return jsonify({'message': 'No data provided'}), 400
        
        # Remove fields that shouldn't be updated
        data.pop('record_id', None)
        data.pop('created_at', None)
        
        updated = AcademicRecord.update(record_id, data)
        return jsonify({'message': 'Record updated', 'record': updated}), 200
    except Exception as e:
        current_app.logger.exception('Failed to update academic record: %s', e)
        return jsonify({'message': 'Failed to update record', 'error': str(e)}), 500


@bp.route('/<int:record_id>', methods=['DELETE'])
@token_required
def delete_academic_record(current_user, record_id):
    """Delete an academic record"""
    try:
        success = AcademicRecord.delete(record_id)
        if success:
            return jsonify({'message': 'Record deleted'}), 200
        return jsonify({'message': 'Record not found'}), 404
    except Exception as e:
        current_app.logger.exception('Failed to delete academic record: %s', e)
        return jsonify({'message': 'Failed to delete record', 'error': str(e)}), 500


@bp.route('/user/<int:user_id>', methods=['DELETE'])
@token_required
def delete_user_academic_records(current_user, user_id):
    """Delete all academic records for a user"""
    try:
        success = AcademicRecord.delete_by_user_id(user_id)
        if success:
            return jsonify({'message': 'All records deleted'}), 200
        return jsonify({'message': 'No records found'}), 404
    except Exception as e:
        current_app.logger.exception('Failed to delete user academic records: %s', e)
        return jsonify({'message': 'Failed to delete records', 'error': str(e)}), 500


@bp.route('/semester', methods=['GET'])
@token_required
def get_semester_records(current_user):
    """Get academic records for a specific semester"""
    try:
        user_id = request.args.get('user_id', type=int)
        year = request.args.get('year', type=int)
        semester = request.args.get('semester')
        
        if not all([user_id, year, semester]):
            return jsonify({'message': 'user_id, year, and semester are required'}), 400
        
        records = AcademicRecord.get_by_semester(user_id, year, semester)
        return jsonify({'records': records}), 200
    except Exception as e:
        current_app.logger.exception('Failed to fetch semester records: %s', e)
        return jsonify({'message': 'Failed to fetch records', 'error': str(e)}), 500
