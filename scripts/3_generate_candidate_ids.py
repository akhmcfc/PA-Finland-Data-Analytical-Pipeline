"""
Generate unique candidate IDs for all 36 confirmed 2026 bootcampers.
Inserts ID-to-identity mapping into candidate_mapping_2026 (private table).
Saves a CSV backup of the mapping.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import sqlite3
import secrets
import string
from config.config import BOOTCAMPERS_FILE, DATABASE_FILE, DATA_DIR, CANDIDATE_ID_PREFIX

OUTPUT_FILE = os.path.join(DATA_DIR, 'processed', '2026_candidate_ids.csv')

def generate_id(existing_ids):
    chars = string.ascii_uppercase + string.digits
    while True:
        suffix = ''.join(secrets.choice(chars) for _ in range(8))
        candidate_id = f"{CANDIDATE_ID_PREFIX}-{suffix}"
        if candidate_id not in existing_ids:
            return candidate_id

def generate_candidate_ids():
    print(f"\n{'='*70}")
    print(f"GENERATING CANDIDATE IDs FOR 2026 BOOTCAMP")
    print(f"{'='*70}\n")

    df = pd.read_csv(BOOTCAMPERS_FILE, encoding='utf-8')
    df = df.dropna(how='all')

    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    existing_ids = set()
    mapping_rows = []

    for idx, row in df.iterrows():
        first_name = row['First name']
        last_name = row['Last Name']
        email = row['Email']

        candidate_id = generate_id(existing_ids)
        existing_ids.add(candidate_id)

        cursor.execute('''
            INSERT OR REPLACE INTO candidate_mapping_2026
            (candidate_id, email, first_name, last_name)
            VALUES (?, ?, ?, ?)
        ''', (candidate_id, email, first_name, last_name))

        mapping_rows.append({
            'candidate_id': candidate_id,
            'first_name': first_name,
            'last_name': last_name,
            'email': email
        })

        print(f"{first_name} {last_name} ({email}) -> {candidate_id}")

    conn.commit()
    conn.close()

    os.makedirs(os.path.join(DATA_DIR, 'processed'), exist_ok=True)
    mapping_df = pd.DataFrame(mapping_rows)
    mapping_df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8')

    print(f"\n{'='*70}")
    print(f"GENERATED {len(mapping_rows)} CANDIDATE IDs")
    print(f"{'='*70}\n")
    print(f"Saved mapping to: {OUTPUT_FILE}\n")

if __name__ == '__main__':
    generate_candidate_ids()
