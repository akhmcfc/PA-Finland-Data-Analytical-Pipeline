"""
Multi-year API routes for historical (2023-2025) and live (2026+) data
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from flask import Blueprint, jsonify, request
from api.models.multi_year_queries import (
    get_single_year_dashboard,
    get_multi_year_dashboard,
    get_applicants_count,
    get_bootcampers_count,
    get_high_schools_distribution,
    get_cities_distribution,
    get_bootcamper_dream_universities,
    get_bootcamper_fields_distribution,
    get_bootcamper_destinations_distribution,
    get_acceptance_rate,
    get_years_in_range
)

bp = Blueprint('multi_year', __name__, url_prefix='/api/multi-year')

@bp.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "OK", "service": "multi-year"})

@bp.route('/years/available', methods=['GET'])
def available_years():
    """Get available years"""
    return jsonify({"available_years": [2023, 2024, 2025, 2026]})

@bp.route('/year/<int:year>/dashboard', methods=['GET'])
def year_dashboard(year):
    """Get single year dashboard data"""
    if year not in [2023, 2024, 2025, 2026]:
        return jsonify({"error": "Year not available"}), 404
    
    data = get_single_year_dashboard(year)
    return jsonify(data)

@bp.route('/range/dashboard', methods=['GET'])
def range_dashboard():
    """Get multi-year range dashboard
    Query params: start_year=2023&end_year=2026
    """
    start_year = request.args.get('start_year', default=2023, type=int)
    end_year = request.args.get('end_year', default=2026, type=int)
    
    # Validate
    if start_year > end_year:
        return jsonify({"error": "start_year must be <= end_year"}), 400
    
    if start_year < 2023 or end_year > 2026:
        return jsonify({"error": "Year range must be 2023-2026"}), 400
    
    data = get_multi_year_dashboard(start_year, end_year)
    return jsonify(data)

@bp.route('/year/<int:year>/high-schools', methods=['GET'])
def year_high_schools(year):
    """Get high schools for single year (ALL applicants)"""
    years = [year]
    schools = get_high_schools_distribution(years)
    return jsonify({"year": year, "high_schools": schools})

@bp.route('/range/high-schools', methods=['GET'])
def range_high_schools():
    """Get high schools for year range (ALL applicants)"""
    start_year = request.args.get('start_year', default=2023, type=int)
    end_year = request.args.get('end_year', default=2026, type=int)
    
    years = get_years_in_range(start_year, end_year)
    schools = get_high_schools_distribution(years)
    return jsonify({"year_range": f"{start_year}-{end_year}", "high_schools": schools})

@bp.route('/year/<int:year>/cities', methods=['GET'])
def year_cities(year):
    """Get cities for single year (ALL applicants)"""
    years = [year]
    cities = get_cities_distribution(years)
    return jsonify({"year": year, "cities": cities})

@bp.route('/range/cities', methods=['GET'])
def range_cities():
    """Get cities for year range (ALL applicants)"""
    start_year = request.args.get('start_year', default=2023, type=int)
    end_year = request.args.get('end_year', default=2026, type=int)
    
    years = get_years_in_range(start_year, end_year)
    cities = get_cities_distribution(years)
    return jsonify({"year_range": f"{start_year}-{end_year}", "cities": cities})

@bp.route('/year/<int:year>/universities', methods=['GET'])
def year_universities(year):
    """Get dream universities for single year (BOOTCAMPERS ONLY)"""
    years = [year]
    unis = get_bootcamper_dream_universities(years)
    return jsonify({"year": year, "universities": unis})

@bp.route('/range/universities', methods=['GET'])
def range_universities():
    """Get dream universities for year range (BOOTCAMPERS ONLY)"""
    start_year = request.args.get('start_year', default=2023, type=int)
    end_year = request.args.get('end_year', default=2026, type=int)
    
    years = get_years_in_range(start_year, end_year)
    unis = get_bootcamper_dream_universities(years)
    return jsonify({"year_range": f"{start_year}-{end_year}", "universities": unis})

@bp.route('/year/<int:year>/fields', methods=['GET'])
def year_fields(year):
    """Get field distribution for single year (BOOTCAMPERS ONLY)"""
    years = [year]
    fields = get_bootcamper_fields_distribution(years)
    return jsonify({"year": year, "fields": fields})

@bp.route('/range/fields', methods=['GET'])
def range_fields():
    """Get field distribution for year range (BOOTCAMPERS ONLY)"""
    start_year = request.args.get('start_year', default=2023, type=int)
    end_year = request.args.get('end_year', default=2026, type=int)
    
    years = get_years_in_range(start_year, end_year)
    fields = get_bootcamper_fields_distribution(years)
    return jsonify({"year_range": f"{start_year}-{end_year}", "fields": fields})

@bp.route('/year/<int:year>/destinations', methods=['GET'])
def year_destinations(year):
    """Get target destinations for single year (BOOTCAMPERS ONLY)"""
    years = [year]
    dests = get_bootcamper_destinations_distribution(years)
    return jsonify({"year": year, "destinations": dests})

@bp.route('/range/destinations', methods=['GET'])
def range_destinations():
    """Get target destinations for year range (BOOTCAMPERS ONLY)"""
    start_year = request.args.get('start_year', default=2023, type=int)
    end_year = request.args.get('end_year', default=2026, type=int)
    
    years = get_years_in_range(start_year, end_year)
    dests = get_bootcamper_destinations_distribution(years)
    return jsonify({"year_range": f"{start_year}-{end_year}", "destinations": dests})

@bp.route('/year/<int:year>/acceptance-rate', methods=['GET'])
def year_acceptance_rate(year):
    """Get acceptance rate for single year (2026+ only)"""
    rate = get_acceptance_rate([year])
    return jsonify({"year": year, "acceptance_rate": rate, "note": "Only available for 2026+" if year < 2026 else None})

@bp.route('/range/acceptance-rate', methods=['GET'])
def range_acceptance_rate():
    """Get acceptance rate for year range (2026+ only in range)"""
    start_year = request.args.get('start_year', default=2023, type=int)
    end_year = request.args.get('end_year', default=2026, type=int)
    
    years = get_years_in_range(start_year, end_year)
    rate = get_acceptance_rate(years)
    
    note = None
    if not rate:
        note = "Acceptance rate only available for ranges including 2026+"
    else:
        note = "Tracked from bootcamper survey responses"
    
    return jsonify({"year_range": f"{start_year}-{end_year}", "acceptance_rate": rate, "note": note})
