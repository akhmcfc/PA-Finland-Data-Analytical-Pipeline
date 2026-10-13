"""
Multi-year database query functions for historical + live bootcamp data
Follows logic: High schools/cities from ALL applicants, Universities/fields from BOOTCAMPERS ONLY
"""

import sqlite3
from config.config import DATABASE_FILE

def get_years_in_range(start_year, end_year):
    """Get list of years in range that have data"""
    available_years = [2023, 2024, 2025, 2026]
    return [y for y in available_years if start_year <= y <= end_year]

def get_applicants_count(years):
    """Get total applicants for given years (ALL applicants for high school/city analysis)"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    total = 0
    
    for year in years:
        try:
            cursor.execute(f'SELECT COUNT(*) FROM applications_{year}')
            total += cursor.fetchone()[0]
        except:
            pass
    
    conn.close()
    return total

def get_bootcampers_count(years):
    """Get total bootcampers selected for given years"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    total = 0
    
    for year in years:
        try:
            cursor.execute(f'SELECT COUNT(*) FROM bootcampers_{year}')
            total += cursor.fetchone()[0]
        except:
            pass
    
    conn.close()
    return total

def get_high_schools_distribution(years):
    """Get high schools from ALL applicants across years"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    school_count = {}
    
    for year in years:
        try:
            cursor.execute(f'''
                SELECT high_school, COUNT(*) as count
                FROM applications_{year}
                WHERE high_school IS NOT NULL AND high_school != ''
                GROUP BY high_school
            ''')
            
            for school, count in cursor.fetchall():
                school_count[school] = school_count.get(school, 0) + count
        except:
            pass
    
    conn.close()
    
    sorted_schools = sorted(school_count.items(), key=lambda x: x[1], reverse=True)
    return [{"school": school, "count": count} for school, count in sorted_schools[:20]]

def get_cities_distribution(years):
    """Get cities from ALL applicants across years"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    city_count = {}
    
    for year in years:
        try:
            cursor.execute(f'''
                SELECT city, COUNT(*) as count
                FROM applications_{year}
                WHERE city IS NOT NULL AND city != ''
                GROUP BY city
            ''')
            
            for city, count in cursor.fetchall():
                city_count[city] = city_count.get(city, 0) + count
        except:
            pass
    
    conn.close()
    
    sorted_cities = sorted(city_count.items(), key=lambda x: x[1], reverse=True)
    return [{"city": city, "count": count} for city, count in sorted_cities[:15]]

def get_bootcamper_dream_universities(years):
    """Get dream universities from BOOTCAMPERS ONLY"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    uni_count = {}
    
    for year in years:
        try:
            cursor.execute(f'SELECT dream_universities FROM applications_{year} WHERE was_selected = 1')
            
            for row in cursor.fetchall():
                if row[0]:
                    unis = [u.strip() for u in row[0].split(',') if u.strip()]
                    for uni in unis:
                        if uni and uni.lower() != 'other':
                            uni_count[uni] = uni_count.get(uni, 0) + 1
        except:
            pass
    
    conn.close()
    
    sorted_unis = sorted(uni_count.items(), key=lambda x: x[1], reverse=True)
    return [{"university": uni, "count": count} for uni, count in sorted_unis[:20]]

def get_bootcamper_fields_distribution(years):
    """Get field distribution from BOOTCAMPERS ONLY"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    field_count = {}
    
    for year in years:
        try:
            cursor.execute(f'''
                SELECT field_of_study, COUNT(*) as count
                FROM applications_{year}
                WHERE was_selected = 1 AND field_of_study IS NOT NULL AND field_of_study != ''
                GROUP BY field_of_study
            ''')
            
            for field, count in cursor.fetchall():
                field_count[field] = field_count.get(field, 0) + count
        except:
            pass
    
    conn.close()
    
    sorted_fields = sorted(field_count.items(), key=lambda x: x[1], reverse=True)
    return [{"field": field, "count": count} for field, count in sorted_fields]

def get_bootcamper_destinations_distribution(years):
    """Get target destinations from BOOTCAMPERS ONLY"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    dest_count = {}
    
    for year in years:
        try:
            cursor.execute(f'''
                SELECT target_destinations
                FROM applications_{year}
                WHERE was_selected = 1
            ''')
            
            for row in cursor.fetchall():
                if row[0]:
                    # Parse destinations
                    dests = [d.strip() for d in row[0].split(',') if d.strip()]
                    for dest in dests:
                        dest_count[dest] = dest_count.get(dest, 0) + 1
        except:
            pass
    
    conn.close()
    
    sorted_dests = sorted(dest_count.items(), key=lambda x: x[1], reverse=True)
    return [{"destination": dest, "count": count} for dest, count in sorted_dests]

def get_acceptance_rate(years):
    """Get acceptance rate for bootcampers (2026+ only with tracking)
    Returns None if years don't include 2026+"""
    
    # Check if any year is 2026+
    if not any(y >= 2026 for y in years):
        return None
    
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    total_with_offers = 0
    
    # Only calculate from outcomes_all_years if it has data
    try:
        cursor.execute('''
            SELECT COUNT(*) FROM outcomes_all_years
            WHERE offers_from_universities IS NOT NULL AND offers_from_universities != ''
        ''')
        total_with_offers = cursor.fetchone()[0]
    except:
        pass
    
    total_bootcampers = get_bootcampers_count(years)
    
    conn.close()
    
    if total_bootcampers == 0:
        return None
    
    rate = (total_with_offers / total_bootcampers) * 100
    return f"{rate:.1f}%"

def get_multi_year_dashboard(start_year, end_year):
    """Get complete dashboard for year range"""
    years = get_years_in_range(start_year, end_year)
    
    applicants = get_applicants_count(years)
    bootcampers = get_bootcampers_count(years)
    
    # Acceptance rate only for ranges including 2026+
    acceptance_rate = get_acceptance_rate(years)
    acceptance_note = None
    if acceptance_rate:
        acceptance_note = "Tracked from bootcamper survey responses (2026+)"
    
    return {
        "year_range": f"{start_year}-{end_year}",
        "years_included": years,
        "applicants_count": applicants,
        "bootcampers_count": bootcampers,
        "high_schools": get_high_schools_distribution(years),
        "cities": get_cities_distribution(years),
        "dream_universities": get_bootcamper_dream_universities(years),
        "field_distribution": get_bootcamper_fields_distribution(years),
        "destination_distribution": get_bootcamper_destinations_distribution(years),
        "acceptance_rate": acceptance_rate,
        "acceptance_rate_note": acceptance_note
    }

def get_single_year_dashboard(year):
    """Get dashboard for single year"""
    return get_multi_year_dashboard(year, year)
