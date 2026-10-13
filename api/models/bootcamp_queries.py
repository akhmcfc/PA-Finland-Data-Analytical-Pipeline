"""
Database query functions for bootcamp data
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import sqlite3
import json
from config.config import DATABASE_FILE
from api.utils.translations import translate_to_english, translate_list

def get_bootcamp_count():
    """Get total number of bootcampers"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM candidate_mapping_2026')
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_survey_1_summary():
    """Get Survey 1 data summary"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            COUNT(*) as total_responses,
            COUNT(DISTINCT candidate_id) as unique_candidates
        FROM pre_bootcamp_2026
    ''')
    
    result = cursor.fetchone()
    conn.close()
    
    return {
        "total_responses": result[0],
        "unique_candidates": result[1],
        "completion_rate": f"{(result[1] / get_bootcamp_count() * 100):.1f}%"
    }

def get_survey_2_summary():
    """Get Survey 2 data summary"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT 
        COUNT(*) as total_responses,
        COUNT(DISTINCT candidate_id) as unique_candidates
    FROM mid_bootcamp_2026
    WHERE candidate_id IS NOT NULL
''')
    
    result = cursor.fetchone()
    conn.close()
    
    total = get_bootcamp_count()
    responses = result[0] if result[0] else 0
    
    return {
        "total_responses": responses,
        "unique_candidates": result[1] if result[1] else 0,
        "completion_rate": f"{(responses / total * 100) if total > 0 else 0:.1f}%"
    }

def get_survey_3_summary():
    """Get Survey 3 data summary"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT 
        COUNT(*) as total_responses,
        COUNT(DISTINCT candidate_id) as unique_candidates
    FROM post_bootcamp_2026
    WHERE candidate_id IS NOT NULL
''')
    
    result = cursor.fetchone()
    conn.close()
    
    total = get_bootcamp_count()
    responses = result[0] if result[0] else 0
    
    return {
        "total_responses": responses,
        "unique_candidates": result[1] if result[1] else 0,
        "completion_rate": f"{(responses / total * 100) if total > 0 else 0:.1f}%"
    }

def get_dream_universities():
    """Get all dream universities mentioned in Survey 1"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    cursor.execute('SELECT dream_universities FROM pre_bootcamp_2026')
    results = cursor.fetchall()
    conn.close()
    
    # Count universities
    uni_count = {}
    for row in results:
        if row[0]:
            try:
                # Handle both string and JSON formats
                if isinstance(row[0], str) and row[0].startswith('['):
                    unis = json.loads(row[0])
                else:
                    unis = [u.strip() for u in row[0].split(',') if u.strip()]
                
                for uni in unis:
                    uni = uni.strip()
                    if uni and uni.lower() != 'other':
                        uni_count[uni] = uni_count.get(uni, 0) + 1
            except:
                pass
    
    # Sort by count
    sorted_unis = sorted(uni_count.items(), key=lambda x: x[1], reverse=True)
    return [{"university": translate_to_english(uni), "count": count} for uni, count in sorted_unis[:20]]

def get_field_distribution():
    """Get field of study distribution from pre-categorized data"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT category, COUNT(DISTINCT candidate_id) as count
        FROM field_categories_2026
        GROUP BY category
        ORDER BY count DESC
    ''')

    results = cursor.fetchall()
    conn.close()

    return [{"field": cat, "count": count} for cat, count in results]

DESTINATION_LABELS = {
    '*Manner-Eurooppa* / Mainland Europe (esim. Hollanti, Ranska, Saksa)': 'Mainland Europe',
    '*Oseania */ Oceania (Australia & Uusi-Seelanti)': 'Oceania',
    '*Iso-Britannia & Irlanti* / UK & Ireland': 'UK & Ireland',
    '*Pohjois-Amerikka* / USA & Kanada': 'USA & Canada',
    '*Aasia* / Asia (esim. Singapore, Japani, Etelä-Korea)': 'Asia',
    "*En ole vielä varma, haluan vain ulkomaille!* / I'm not sure yet, I just want to go abroad!)": 'Not sure yet',
    '*Muualla maailmassa* / Other (Etelä-Amerikka tai Afrikka)': 'Other',
}

def get_destination_distribution():
    """Get target destination distribution using known-option vocabulary matching"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    cursor.execute('SELECT target_destinations FROM pre_bootcamp_2026')
    results = cursor.fetchall()
    conn.close()

    dest_count = {}
    for row in results:
        raw = row[0]
        if not raw:
            continue
        for known_option, clean_label in DESTINATION_LABELS.items():
            if known_option in raw:
                dest_count[clean_label] = dest_count.get(clean_label, 0) + 1

    sorted_dests = sorted(dest_count.items(), key=lambda x: x[1], reverse=True)
    return [{"destination": label, "count": count} for label, count in sorted_dests]

def get_bootcamper_data(candidate_id):
    """Get all data for a specific bootcamper (PRIVATE - admin only)"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    # Get candidate info
    cursor.execute('''
        SELECT first_name, last_name, email, candidate_id
        FROM candidate_mapping_2026
        WHERE candidate_id = ?
    ''', (candidate_id,))
    
    candidate = cursor.fetchone()
    if not candidate:
        conn.close()
        return None
    
    # Get Survey 1
    cursor.execute('''
        SELECT dream_universities, field_of_study, target_destinations
        FROM pre_bootcamp_2026
        WHERE candidate_id = ?
    ''', (candidate_id,))
    survey_1 = cursor.fetchone()
    
    # Get Survey 2
    cursor.execute('''
        SELECT changed_universities, biggest_challenge, bootcamp_resources_used,
               support_needed, what_working_well, submitted_at
        FROM mid_bootcamp_2026
        WHERE candidate_id = ?
    ''', (candidate_id,))
    survey_2 = cursor.fetchone()
    
    # Get Survey 3
    cursor.execute('''
        SELECT heard_back_status, acceptances_received, final_choice,
               bootcamp_impact_final, most_valuable_element, resources_missing
        FROM post_bootcamp_2026
        WHERE candidate_id = ?
    ''', (candidate_id,))
    survey_3 = cursor.fetchone()
    
    conn.close()
    
    return {
        "candidate_id": candidate[3],
        "first_name": candidate[0],
        "last_name": candidate[1],
        "email": candidate[2],
        "survey_1": {
            "dream_universities": survey_1[0] if survey_1 else None,
            "field_of_study": survey_1[1] if survey_1 else None,
            "target_destinations": survey_1[2] if survey_1 else None
        } if survey_1 else None,
        "survey_2": {
            "changed_universities": survey_2[0] if survey_2 else None,
            "biggest_challenge": survey_2[1] if survey_2 else None,
            "resources_used": survey_2[2] if survey_2 else None,
            "support_needed": survey_2[3] if survey_2 else None,
            "what_working_well": survey_2[4] if survey_2 else None,
            "submitted_at": survey_2[5] if survey_2 else None
        } if survey_2 else None,
        "survey_3": {
            "heard_back": survey_3[0] if survey_3 else None,
            "acceptances": survey_3[1] if survey_3 else None,
            "final_choice": survey_3[2] if survey_3 else None,
            "bootcamp_impact": survey_3[3] if survey_3 else None,
            "most_valuable": survey_3[4] if survey_3 else None,
            "resources_missing": survey_3[5] if survey_3 else None
        } if survey_3 else None
    }



def get_dashboard_data():
    """Get complete dashboard data with all metrics"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    # Basic counts
    bootcamp_count = get_bootcamp_count()
    
    # Count applicants from Survey 1
    # Count applicants from Survey 1
    try:
        cursor.execute('SELECT COUNT(*) FROM applications_2026')
        applicants_count = cursor.fetchone()[0]
    except:
        applicants_count = bootcamp_count
    
    # Survey data
    survey_1 = get_survey_1_summary()
    survey_2 = get_survey_2_summary()
    survey_3 = get_survey_3_summary()
    
    # Universities and fields
    universities = get_dream_universities()
    fields = get_field_distribution()
    destinations = get_destination_distribution()
    
    # Geographic distribution
    try:
        cursor.execute('''
            SELECT city, COUNT(*) as count 
            FROM candidate_mapping_2026 
            WHERE city IS NOT NULL AND city != ''
            GROUP BY city 
            ORDER BY count DESC
        ''')
        geographic_list = [{'city': g[0], 'location': g[0], 'count': g[1]} for g in cursor.fetchall()]
    except:
        geographic_list = []
    
    # Schools
    try:
        cursor.execute('''
            SELECT high_school, COUNT(*) as count 
            FROM candidate_mapping_2026 
            WHERE high_school IS NOT NULL AND high_school != ''
            GROUP BY high_school 
            ORDER BY count DESC
        ''')
        schools_list = [{'school': s[0], 'count': s[1]} for s in cursor.fetchall()]
    except:
        schools_list = []
    
    # Acceptance rate
    acceptance_rate = None
    try:
        cursor.execute('SELECT COUNT(*) FROM post_bootcamp_2026')
        survey_3_total = cursor.fetchone()[0]
        if survey_3_total > 0:
            cursor.execute('SELECT COUNT(*) FROM post_bootcamp_2026 WHERE acceptances_received IS NOT NULL')
            acceptances = cursor.fetchone()[0]
            acceptance_rate = f"{(acceptances / survey_3_total * 100):.1f}%"
    except:
        acceptance_rate = None
    
    conn.close()
    
    return {
        'bootcamp_count': bootcamp_count,
        'applicants_count': applicants_count,
        'survey_1': survey_1,
        'survey_2': survey_2,
        'survey_3': survey_3,
        'dream_universities': universities,
        'field_distribution': fields,
        'destination_distribution': destinations,
        'geographic_distribution': geographic_list,
        'schools': schools_list,
        'acceptance_rate': acceptance_rate
    }

def get_geographic_distribution():
    """Get cities distribution"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT city, COUNT(*) as count 
        FROM applications_2026 
        WHERE city IS NOT NULL AND city != ''
        GROUP BY city 
        ORDER BY count DESC 
        LIMIT 20
    ''')
    
    results = cursor.fetchall()
    conn.close()
    
    return [{"city": city, "count": count} for city, count in results]

def get_schools_distribution():
    """Get schools distribution"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT high_school, COUNT(*) as count 
        FROM applications_2026 
        WHERE high_school IS NOT NULL AND high_school != ''
        GROUP BY high_school 
        ORDER BY count DESC 
        LIMIT 20
    ''')
    
    results = cursor.fetchall()
    conn.close()
    
    return [{"school": school, "count": count} for school, count in results]
def get_geographic_distribution():
    """Get cities distribution"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT city, COUNT(*) as count 
        FROM applications_2026 
        WHERE city IS NOT NULL AND city != ''
        GROUP BY city 
        ORDER BY count DESC 
        LIMIT 20
    ''')
    
    results = cursor.fetchall()
    conn.close()
    
    return [{"city": city, "count": count} for city, count in results]

def get_schools_distribution():
    """Get schools distribution"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT high_school, COUNT(*) as count 
        FROM applications_2026 
        WHERE high_school IS NOT NULL AND high_school != ''
        GROUP BY high_school 
        ORDER BY count DESC 
        LIMIT 20
    ''')
    
    results = cursor.fetchall()
    conn.close()
    
    return [{"school": school, "count": count} for school, count in results]
