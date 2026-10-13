"""
Set up the 2026 bootcamp database with tables per security config.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
from config.config import DATABASE_FILE, DATABASE_DIR

def setup_database():
    print(f"\n{'='*70}")
    print(f"SETTING UP 2026 BOOTCAMP DATABASE")
    print(f"{'='*70}\n")

    os.makedirs(DATABASE_DIR, exist_ok=True)

    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS candidate_mapping_2026 (
            candidate_id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            first_name TEXT,
            last_name TEXT
        )
    ''')
    print(f"Created: candidate_mapping_2026")

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pre_bootcamp_2026 (
            candidate_id TEXT PRIMARY KEY,
            dream_universities TEXT,
            target_destinations TEXT,
            field_of_study TEXT,
            confidence_level TEXT,
            FOREIGN KEY (candidate_id) REFERENCES candidate_mapping_2026(candidate_id)
        )
    ''')
    print(f"Created: pre_bootcamp_2026")

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mid_bootcamp_2026 (
            candidate_id TEXT PRIMARY KEY,
            changed_universities TEXT,
            changed_destination TEXT,
            changed_major TEXT,
            application_progress TEXT,
            biggest_challenge TEXT,
            acceptances TEXT,
            rejections TEXT,
            bootcamp_impact TEXT,
            updated_confidence TEXT,
            whats_working TEXT,
            FOREIGN KEY (candidate_id) REFERENCES candidate_mapping_2026(candidate_id)
        )
    ''')
    print(f"Created: mid_bootcamp_2026")

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS post_bootcamp_2026 (
            candidate_id TEXT PRIMARY KEY,
            universities_applied TEXT,
            universities_accepted TEXT,
            universities_rejected TEXT,
            final_choice TEXT,
            why_chose TEXT,
            achieved_predicted_grades TEXT,
            bootcamp_impact_final TEXT,
            most_valuable_element TEXT,
            plans_changed TEXT,
            biggest_surprise TEXT,
            advice_for_future TEXT,
            current_activity TEXT,
            FOREIGN KEY (candidate_id) REFERENCES candidate_mapping_2026(candidate_id)
        )
    ''')
    print(f"Created: post_bootcamp_2026")

    conn.commit()
    conn.close()

    print(f"\n{'='*70}")
    print(f"DATABASE SETUP COMPLETE")
    print(f"Location: {DATABASE_FILE}")
    print(f"{'='*70}\n")

if __name__ == '__main__':
    setup_database()
