"""
Public API routes (no authentication required)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from flask import Blueprint, jsonify
from api.models.bootcamp_queries import (
    get_dashboard_data, 
    get_dream_universities, 
    get_field_distribution, 
    get_destination_distribution,
    get_geographic_distribution,
    get_schools_distribution,
    get_bootcamp_count, 
    get_survey_1_summary, 
    get_survey_2_summary,
    get_survey_3_summary
)

bp = Blueprint('public', __name__, url_prefix='/api/2026')

@bp.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "OK"})

@bp.route('/bootcamp/count', methods=['GET'])
def bootcamp_count():
    """Get bootcamp count"""
    count = get_bootcamp_count()
    return jsonify({"count": count})

@bp.route('/survey/1/summary', methods=['GET'])
def survey_1_summary():
    """Get survey 1 summary"""
    data = get_survey_1_summary()
    return jsonify(data)

@bp.route('/survey/2/summary', methods=['GET'])
def survey_2_summary():
    """Get survey 2 summary"""
    data = get_survey_2_summary()
    return jsonify(data)

@bp.route('/survey/3/summary', methods=['GET'])
def survey_3_summary():
    """Get survey 3 summary"""
    data = get_survey_3_summary()
    return jsonify(data)

@bp.route('/universities/dream', methods=['GET'])
def dream_universities():
    """Get dream universities"""
    data = get_dream_universities()
    return jsonify(data)

@bp.route('/fields/distribution', methods=['GET'])
def fields_distribution():
    """Get field distribution"""
    data = get_field_distribution()
    return jsonify({"count": len(data), "fields": data})

@bp.route('/destinations/distribution', methods=['GET'])
def destinations_distribution():
    """Get destination distribution"""
    data = get_destination_distribution()
    return jsonify(data)

@bp.route('/geographic-distribution', methods=['GET'])
def geographic_distribution():
    """Get geographic distribution"""
    data = get_geographic_distribution()
    return jsonify({"count": len(data), "cities": data})

@bp.route('/schools', methods=['GET'])
def schools_distribution():
    """Get schools distribution"""
    data = get_schools_distribution()
    return jsonify({"count": len(data), "schools": data})

@bp.route('/dashboard', methods=['GET'])
def dashboard():
    """Get full dashboard data"""
    data = get_dashboard_data()
    return jsonify(data)
