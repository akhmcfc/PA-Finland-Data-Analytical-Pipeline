"""
Multi-year database query functions for historical + live bootcamp data
Follows logic: High schools/cities from ALL applicants, Universities/fields from BOOTCAMPERS ONLY
"""

import sqlite3
from config.config import DATABASE_FILE
from api.utils.translations import translate_to_english

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
            # 2026 uses candidate_mapping_2026, others use bootcampers_{year}
            table = 'candidate_mapping_2026' if year == 2026 else f'bootcampers_{year}'
            cursor.execute(f'SELECT COUNT(*) FROM {table}')
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
    """Dream universities from BOOTCAMPERS ONLY. Names are normalised with the university_aliases table; each bootcamper counts once per university."""
    import re
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    try:
        aliases = [(re.compile(pat, re.I), canon) for pat, canon in cursor.execute("SELECT pattern, canonical FROM university_aliases")]
    except Exception:
        aliases = []
    uni_count = {}
    for year in years:
        try:
            cursor.execute(f'SELECT dream_universities FROM applications_{year} WHERE was_selected = 1')
            rows = cursor.fetchall()
        except Exception:
            continue
        for (text,) in rows:
            if not text:
                continue
            found = set()
            for part in re.split(r"[,;/\n]+|\s+(?:and|or|ja|tai)\s+", text, flags=re.I):
                part = part.strip(" .")
                if not part or part.lower() in ("other", "not listed here"):
                    continue
                hit = {canon for rx, canon in aliases if rx.search(part)}
                if hit:
                    found |= hit
                elif len(part.split()) <= 5 and not (len(part.split()) > 2 and re.search(r'[\u00e4\u00f6\u00e5]', part, re.I)):
                    found.add(part)
            for uni in found:
                uni_count[uni] = uni_count.get(uni, 0) + 1
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





# ---- Finnish/free-text normalization overrides (appended; later defs win) ----
import re as _re

_DEST_RULES = [
    ("Mainland Europe", r"manner-?eurooppa|mainland europe|continental europe|hollanti|netherlands|ranska|france|saksa|germany|scandinavia|\beu\b|europe"),
    ("UK & Ireland", r"iso-britannia|\buk\b|ireland|irlanti|britain|england"),
    ("USA & Canada", r"pohjois-amerikka|north america|\busa\b|kanada|canada"),
    ("Asia", r"aasia|\basia\b|singapore|japani|japan|etel\u00e4-korea|south korea|china|hong kong"),
    ("Oceania", r"oseania|oceania|australia|uusi-seelanti|new zealand"),
    ("Africa", r"muualla maailmassa|etel\u00e4-amerikka|south america|afrikka|africa"),
    ("Not sure / Anywhere abroad", r"en ole viel\u00e4 varma|not sure|haluan vain ulkomaille|anywhere|everywhere|just want to go abroad|unsure"),
]

_FIELD_RULES = [
    ("Law", r"\blaw|oikeus|\blak(i|ia|itiet)"),
    ("Business/Economics", r"econ|business|financ|accounting|kauppa|bisnes|rahoitus|management|commerce|liike"),
    ("Medicine/Health", r"medic|l\u00e4\u00e4k|veterin|nursing|health|dent|pharma"),
    ("STEM/Engineering", r"engineer|insin\u00f6\u00f6|robotic|architect|arkki|rakennus|computer|\bict\b|\bit\b|informatiikka|data|software|math|matem|physic|fysiik|quantum|chem|kemi|biolog|neuroscien|astronom|geolog|environment|\bstem\b"),
    ("Social Sciences", r"politic|international relations|\bir\b|\bppe\b|sociolog|psycholog|global affairs|european studies|anthropolog|kansainv|yhteiskunt|social"),
    ("Humanities", r"literature|linguist|translation|histor|philosoph|language|humanit|kirjall"),
    ("Arts/Media", r"\bart\b|\barts\b|design|music|film|kuvataide|media"),
    ("Undecided/Exploring", r"exploring|not sure|undecided|en ole|ei viel\u00e4|unsure"),
]

_FIELD_RULES.append(("STEM/Engineering", r"natural science|luonnontiet"))

def _labels(text, rules):
    t = (text or "").lower()
    out = []
    for name, pat in rules:
        if _re.search(pat, t) and name not in out:
            out.append(name)
    return out

def _cols(cur, table):
    return [r[1] for r in cur.execute('PRAGMA table_info("%s")' % table)]

def _fetch_raw(cur, year, names):
    rows = []
    for table, extra in (("pre_bootcamp_%d" % year, ""), ("applications_%d" % year, " AND was_selected = 1")):
        cols = _cols(cur, table)
        col = next((n for n in names if n in cols), None)
        if not cols or not col:
            continue
        idc = "candidate_id" if "candidate_id" in cols else "rowid"
        q = 'SELECT %s, "%s" FROM "%s" WHERE "%s" IS NOT NULL AND "%s" != ""%s' % (idc, col, table, col, col, extra)
        try:
            rows = cur.execute(q).fetchall()
            break
        except Exception:
            continue
    return rows

def get_bootcamper_destinations_distribution(years):
    conn = sqlite3.connect(DATABASE_FILE)
    cur = conn.cursor()
    counts = {}
    for y in years:
        for _id, raw in _fetch_raw(cur, y, ["target_destinations", "study_destination"]):
            for l in (_labels(raw, _DEST_RULES) or ["Not sure / Anywhere abroad"]):
                counts[l] = counts.get(l, 0) + 1
    conn.close()
    return [{"destination": k, "count": v} for k, v in sorted(counts.items(), key=lambda x: -x[1])]

def get_bootcamper_fields_distribution(years):
    conn = sqlite3.connect(DATABASE_FILE)
    cur = conn.cursor()
    counts = {}
    for y in years:
        claude = {}
        if y == 2026:
            try:
                for cid, cat in cur.execute("SELECT candidate_id, category FROM field_categories_2026"):
                    claude.setdefault(cid, []).append(cat)
            except Exception:
                pass
        for cid, raw in _fetch_raw(cur, y, ["field_of_study", "intended_field"]):
            if cid in claude:
                labs = claude[cid]
            else:
                labs = _labels(raw, _FIELD_RULES)
                if len(labs) > 1:
                    labs = [l for l in labs if l != "Undecided/Exploring"]
                labs = labs or ["Other"]
            for l in labs:
                counts[l] = counts.get(l, 0) + 1
    conn.close()
    return [{"field": k, "count": v} for k, v in sorted(counts.items(), key=lambda x: -x[1])]

