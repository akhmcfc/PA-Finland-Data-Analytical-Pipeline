"""
Admin API routes (password protected)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from flask import Blueprint, jsonify
from api.models.bootcamp_queries import get_bootcamper_data
from api.utils.security import require_admin_password, log_admin_access

bp = Blueprint('admin', __name__, url_prefix='/api/2026/admin')

@bp.route('/bootcamper/<candidate_id>', methods=['GET'])
@require_admin_password
def get_bootcamper(candidate_id):
    """Get complete bootcamper data (private - includes email)"""
    try:
        data = get_bootcamper_data(candidate_id)
        
        if not data:
            return jsonify({"error": "Bootcamper not found"}), 404
        
        # Log access
        log_admin_access("GET_BOOTCAMPER", candidate_id)
        
        return jsonify(data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/health', methods=['GET'])
@require_admin_password
def admin_health():
    """Admin health check (password protected)"""
    return jsonify({"status": "Admin panel healthy"}), 200
