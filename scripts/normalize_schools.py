import sqlite3

conn = sqlite3.connect('database/project_access_2026.db')
cursor = conn.cursor()

# Mapping: old_name -> new_name
normalization_map = {
    'Ressu IB': 'Ressu',
    'Ressu IB world school': 'Ressu',
    'Ressu IB World School': 'Ressu',
    'Ressun lukio': 'Ressu',
    'Ressu lukio': 'Ressu',
    'Tampereen lyseon lukio IB': 'Tampereen lyseon lukio',
    'Oulun Lyseon lukion IB linja': 'Oulun Lyseon lukio',
    'Oulun Lyseon lukio IB-linja': 'Oulun Lyseon lukio',
    'Kulosaaren yhteiskoulu': 'Kulosaaren Yhteiskoulu',
    'Kulosaaren Yhteiskoulu, Yhteiskunta- ja talouslinja': 'Kulosaaren Yhteiskoulu',
    'Helsingin suomalainen yhteiskoulu': 'Helsingin Suomalainen Yhteiskoulu',
    'Gymnasiet Grankulla samskola': 'Gymnasiet Grankulla Samskola',
    'Mäkelänrinteen Lukio': 'Mäkelänrinteen lukio'
}

print('Normalizing school names...\n')

for old_name, new_name in normalization_map.items():
    cursor.execute(
        'UPDATE candidate_mapping_2026 SET high_school = ? WHERE high_school = ?',
        (new_name, old_name)
    )
    count = cursor.rowcount
    if count > 0:
        print(f'Updated {count}: {old_name} -> {new_name}')

conn.commit()

# Verify
print('\nVerifying normalized schools:')
cursor.execute('SELECT high_school, COUNT(*) as count FROM candidate_mapping_2026 GROUP BY high_school ORDER BY count DESC')
for row in cursor.fetchall():
    print(f'{row[0]}: {row[1]}')

conn.close()
print('\nDone!')
