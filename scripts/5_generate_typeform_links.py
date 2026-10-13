"""
5_generate_typeform_links.py - Generate Personalized Typeform Links
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
import csv
from config.config import DATABASE_FILE, SURVEY_1_FORM_ID, SURVEY_2_FORM_ID, SURVEY_3_FORM_ID

def generate_links():
    """Generate personalized Typeform links for all bootcampers"""
    print("\n" + "="*70)
    print("🔗 GENERATING PERSONALIZED TYPEFORM LINKS")
    print("="*70 + "\n")
    
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT candidate_mapping.candidate_id, candidate_mapping.email,
               candidate_mapping.first_name, candidate_mapping.last_name
        FROM candidate_mapping_2026 as candidate_mapping
        ORDER BY candidate_mapping.candidate_id
    ''')
    
    bootcampers = cursor.fetchall()
    conn.close()
    
    links = []
    
    for candidate_id, email, first_name, last_name in bootcampers:
        survey1_link = f"https://typeform.com/to/{SURVEY_1_FORM_ID}?candidate_id={candidate_id}"
        survey2_link = f"https://typeform.com/to/{SURVEY_2_FORM_ID}?candidate_id={candidate_id}"
        survey3_link = f"https://typeform.com/to/{SURVEY_3_FORM_ID}?candidate_id={candidate_id}"
        
        links.append({
            'candidate_id': candidate_id,
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'survey1_link': survey1_link,
            'survey2_link': survey2_link,
            'survey3_link': survey3_link
        })
        
        print(f"✅ {candidate_id}")
    
    output_file = 'data/processed/2026_personalized_links.csv'
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'candidate_id', 'first_name', 'last_name', 'email',
            'survey1_link', 'survey2_link', 'survey3_link'
        ])
        writer.writeheader()
        writer.writerows(links)
    
    print(f"\n{'='*70}")
    print("✅ LINKS GENERATED")
    print(f"{'='*70}")
    print(f"Generated {len(links)} personalized links")
    print(f"Saved to: {output_file}")
    print(f"\nExample Survey 2 link:")
    print(f"   {links[0]['survey2_link']}")
    print(f"\nExample Survey 3 link:")
    print(f"   {links[0]['survey3_link']}")
    print(f"\n{'='*70}\n")

if __name__ == '__main__':
    generate_links()
