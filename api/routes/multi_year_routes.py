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


# ---- Survey tabs (added) ----
from flask import jsonify as _jsonify
from api.models.survey_queries import get_survey_data as _get_survey_data

@bp.route("/survey/<int:n>")
def survey_tab_data(n):
    if n not in (1, 2, 3):
        return _jsonify({"error": "survey must be 1, 2 or 3"}), 404
    return _jsonify(_get_survey_data(n))


# ---- Survey tab fixes (added) ----
import json as _sj, re as _sre
from flask import request as _sreq
from api.models.survey_fix import fix_survey as _fix_survey

@bp.after_app_request
def _survey_fix(resp):
    try:
        if not _sre.search(r"/survey/\d+/?$", _sreq.path) or resp.status_code != 200 or resp.mimetype != "application/json":
            return resp
        data = _sj.loads(resp.get_data(as_text=True))
        n = int(_sre.search(r"/(\d+)/?$", _sreq.path).group(1))
        resp.set_data(_sj.dumps(_fix_survey(data, n)))
    except Exception:
        pass
    return resp



# ---- Acceptance rate rules (added) ----
import json as _json
from flask import request as _request, jsonify as _jsonify
from api.models.acceptance import live_years_summary as _lys, outcomes_by_year as _oby, year_config as _year_config, span as _span

@bp.route("/config")
def _year_config_endpoint():
    c = _year_config()
    return _jsonify({"live_years": c["live"], "tracked_years": c["live"], "historical_years": c["historical"],
                     "live_start_year": (c["live"][0] if c["live"] else None), "years": c["years"]})

@bp.after_request
def _acceptance_fix(resp):
    try:
        if "/dashboard" not in _request.path or resp.status_code != 200 or resp.mimetype != "application/json":
            return resp
        data = _json.loads(resp.get_data(as_text=True))
        cfg = _year_config()
        yrs = sorted(set(data.get("years_included") or []))
        live = [y for y in yrs if y in cfg["live"]]
        hist = [y for y in yrs if y in cfg["historical"]]
        data["acceptance_rate"] = None
        data["acceptance_rate_note"] = ""
        if live:
            S = _lys(live)
            data["acceptance_by_year"] = [{
                "year": x["year"], "status": x["status"], "detail": x["detail"], "bootcampers": x["bootcampers"],
                "responses": x["responses"], "with_offer": x["with_offer"], "counted_bootcampers": x["counted_bootcampers"],
                "rate": ("%.1f%%" % (100.0 * x["counted_offers"] / x["counted_bootcampers"])) if x["counted_bootcampers"] else None
            } for x in S]
            counted = [x for x in S if x["counted_bootcampers"] > 0]
            total_sel = sum(x["bootcampers"] for x in S)
            if not counted:
                data["acceptance_rate"] = "TBD"
                data["acceptance_rate_note"] = "%s bootcampers only - awaiting Survey 3" % _span(live)
            else:
                cb = sum(x["counted_bootcampers"] for x in counted)
                co = sum(x["counted_offers"] for x in counted)
                data["acceptance_rate"] = "%.1f%%" % (100.0 * co / cb)
                yc = _span([x["year"] for x in counted])
                if cb == total_sel:
                    data["acceptance_rate_note"] = "%s bootcampers only - full cohort (%d of %d)" % (yc, cb, total_sel)
                else:
                    cl, pl = [], []
                    for x in S:
                        cl += x["counted_labels"]; pl += x["pending"]
                    data["acceptance_rate_note"] = "%s bootcampers only - %d of %d bootcampers counted so far (%s); pending: %s" % (yc, cb, total_sel, ", ".join(cl), ", ".join(pl))
        if hist:
            H = _oby(hist)
            data["historical_outcomes"] = H
            if H and not live and set(hist) == set(cfg["historical"]) and H["bootcampers"]:
                data["acceptance_rate"] = "%.1f%%" % (100.0 * H["with_offer"] / H["bootcampers"])
                data["acceptance_rate_note"] = "Retro data: %d outcome responses from %d bootcampers (%s)" % (H["responses"], H["bootcampers"], _span(hist))
        resp.set_data(_json.dumps(data))
    except Exception:
        pass
    return resp
