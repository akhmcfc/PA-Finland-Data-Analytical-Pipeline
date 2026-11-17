"""
Set up the bootcamp database for the year in PA_YEAR with tables per security config.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
from config.config import DATABASE_FILE, DATABASE_DIR, BOOTCAMP_YEAR, require_year

def setup_database():
    print(f"\n{'='*70}")
    print(f"SETTING UP {BOOTCAMP_YEAR} BOOTCAMP DATABASE")
    print(f"{'='*70}\n")

    require_year()
    os.makedirs(DATABASE_DIR, exist_ok=True)

    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS candidate_mapping_{BOOTCAMP_YEAR} (
            candidate_id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            first_name TEXT,
            last_name TEXT,
            expected_uni_start_year INTEGER,
            survey_2_send_start TEXT,
            survey_2_send_end TEXT,
            survey_3_send_start TEXT,
            survey_3_send_end TEXT,
            survey_2_sent_date TEXT,
            survey_3_sent_date TEXT
        )
    ''')
    print(f"Created: candidate_mapping_{BOOTCAMP_YEAR}")

    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS pre_bootcamp_{BOOTCAMP_YEAR} (
            candidate_id TEXT PRIMARY KEY,
            dream_universities TEXT,
            target_destinations TEXT,
            field_of_study TEXT,
            confidence_level TEXT,
            FOREIGN KEY (candidate_id) REFERENCES candidate_mapping_{BOOTCAMP_YEAR}(candidate_id)
        )
    ''')
    print(f"Created: pre_bootcamp_{BOOTCAMP_YEAR}")

    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS mid_bootcamp_{BOOTCAMP_YEAR} (
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
            FOREIGN KEY (candidate_id) REFERENCES candidate_mapping_{BOOTCAMP_YEAR}(candidate_id)
        )
    ''')
    print(f"Created: mid_bootcamp_{BOOTCAMP_YEAR}")

    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS post_bootcamp_{BOOTCAMP_YEAR} (
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
            FOREIGN KEY (candidate_id) REFERENCES candidate_mapping_{BOOTCAMP_YEAR}(candidate_id)
        )
    ''')
    print(f"Created: post_bootcamp_{BOOTCAMP_YEAR}")

    conn.commit()
    conn.close()

    print(f"\n{'='*70}")
    print(f"DATABASE SETUP COMPLETE")
    print(f"Location: {DATABASE_FILE}")
    print(f"{'='*70}\n")

if __name__ == '__main__':
    setup_database()
