"""
Load Survey 1 (pre-bootcamp) data into pre_bootcamp_2026.
Survey 1 was already completed before candidate IDs existed, so this
maps the existing merged CSV columns directly -- no Typeform pull needed.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import sqlite3
from config.config import BOOTCAMPERS_FILE, DATABASE_FILE

DREAM_DESTINATIONS_COL = 'Missä unelmoit opiskelevasi? (Valitse kaikki sopivat vaihtoehdot) 🤩'
DREAM_UNIVERSITIES_COL = 'Mitkä yliopistot ovat toivelistallasi? (Valitse kaikki sopivat vaihtoehdot) 🏛️'
FIELD_OF_STUDY_COL = 'Mitä alaa aiot hakea opiskelemaan?📚'

def load_pre_bootcamp_data():
    print(f"\n{'='*70}")
    print(f"LOADING PRE-BOOTCAMP DATA")
    print(f"{'='*70}\n")

    df = pd.read_csv(BOOTCAMPERS_FILE, encoding='utf-8')
    df = df.dropna(how='all')

    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    loaded = 0
    errors = 0

    for idx, row in df.iterrows():
        email = row['Email']

        cursor.execute('SELECT candidate_id FROM candidate_mapping_2026 WHERE email = ?', (email,))
        result = cursor.fetchone()

        if not result:
            print(f"No candidate_id found for {email} -- skipping")
            errors += 1
            continue

        candidate_id = result[0]

        dream_universities = row.get(DREAM_UNIVERSITIES_COL, None)
        target_destinations = row.get(DREAM_DESTINATIONS_COL, None)
        field_of_study = row.get(FIELD_OF_STUDY_COL, None)

        cursor.execute('''
            INSERT OR REPLACE INTO pre_bootcamp_2026
            (candidate_id, dream_universities, target_destinations, field_of_study, confidence_level)
            VALUES (?, ?, ?, ?, ?)
        ''', (candidate_id, dream_universities, target_destinations, field_of_study, None))

        loaded += 1

    conn.commit()
    conn.close()

    print(f"LOADED {loaded} BOOTCAMPER RECORDS")
    print(f"Errors: {errors}")
    print(f"\n{'='*70}\n")

if __name__ == '__main__':
    load_pre_bootcamp_data()
