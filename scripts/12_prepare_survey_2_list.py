import pandas as pd
import sqlite3
from datetime import datetime

# Load personalized links
links_df = pd.read_csv('data/processed/2026_personalized_links.csv')

# Connect to database
conn = sqlite3.connect('database/project_access_2026.db')
cursor = conn.cursor()

print('Preparing Survey 2 send list...\n')

today = datetime.now().date()
send_list = []

for idx, row in links_df.iterrows():
    candidate_id = row['candidate_id']
    email = row['email'].lower().strip()
    first_name = row['first_name']
    last_name = row['last_name']
    survey_2_link = row['survey2_link']
    
    # Get survey send window from database
    cursor.execute('''
        SELECT survey_2_send_start, survey_2_send_end, survey_2_sent_date
        FROM candidate_mapping_2026
        WHERE candidate_id = ?
    ''', (candidate_id,))
    
    result = cursor.fetchone()
    
    if not result:
        print('WARNING: ' + first_name + ' not found in database')
        continue
    
    send_start_str, send_end_str, sent_date = result
    
    # Parse dates
    try:
        send_start = datetime.strptime(send_start_str, '%Y-%m-%d').date()
        send_end = datetime.strptime(send_end_str, '%Y-%m-%d').date()
    except:
        print('ERROR parsing dates for ' + first_name)
        continue
    
    # Check if already sent
    if sent_date:
        continue
    
    # Check if within send window
    if send_start <= today <= send_end:
        send_list.append({
            'candidate_id': candidate_id,
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'survey_2_link': survey_2_link,
            'send_start': send_start,
            'send_end': send_end
        })

# Create DataFrame and save
send_df = pd.DataFrame(send_list)

print('Ready to send: ' + str(len(send_df)) + ' bootcampers')
print('\nBootcampers ready for Survey 2:')
for idx, row in send_df.iterrows():
    print('  ' + row['first_name'] + ' (' + row['email'] + ')')

# Save the list
output_file = 'data/processed/survey_2_send_list_2026.csv'
send_df.to_csv(output_file, index=False)

print('\nSaved to: ' + output_file)

conn.close()
