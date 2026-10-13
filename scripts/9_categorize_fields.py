"""
Categorize free-text field_of_study responses into fixed buckets using Claude.
Stores results in a new table for the dashboard to read from.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
import json
from dotenv import load_dotenv
import anthropic
from config.config import DATABASE_FILE

load_dotenv()

CATEGORIES = [
    'STEM/Engineering',
    'Business/Economics',
    'Law',
    'Medicine/Health',
    'Social Sciences',
    'Humanities',
    'Arts/Media',
    'Undecided/Exploring'
]

CATEGORIZE_TOOL = {
    'name': 'categorize_fields',
    'description': 'Categorize each student field-of-study response into one or more fixed categories.',
    'input_schema': {
        'type': 'object',
        'properties': {
            'results': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'candidate_id': {'type': 'string'},
                        'categories': {
                            'type': 'array',
                            'items': {'type': 'string', 'enum': CATEGORIES},
                            'description': 'One or more categories that best match this response. If the response expresses genuine uncertainty between fields, include all mentioned categories plus Undecided/Exploring if appropriate.'
                        }
                    },
                    'required': ['candidate_id', 'categories']
                }
            }
        },
        'required': ['results']
    }
}

def categorize_fields():
    separator = '=' * 70
    print('')
    print(separator)
    print('CATEGORIZING FIELD OF STUDY RESPONSES')
    print(separator)
    print('')

    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    cursor.execute('SELECT candidate_id, field_of_study FROM pre_bootcamp_2026 WHERE field_of_study IS NOT NULL')
    rows = cursor.fetchall()
    print('Responses to categorize: ' + str(len(rows)))

    client = anthropic.Anthropic(default_headers={'anthropic-workspace-id': os.getenv('ANTHROPIC_WORKSPACE_ID')})

    responses_text = '\n'.join([cid + ': ' + text for cid, text in rows])

    message = client.messages.create(
        model='claude-sonnet-4-5',
        max_tokens=4096,
        system='You categorize student field-of-study interest statements (mixed English/Finnish, often free-text and uncertain) into fixed categories. A response can match multiple categories. Use the categorize_fields tool to report results for every candidate_id given.',
        messages=[{
            'role': 'user',
            'content': 'Categorize these field-of-study responses:\n\n' + responses_text
        }],
        tools=[CATEGORIZE_TOOL],
        tool_choice={'type': 'tool', 'name': 'categorize_fields'}
    )

    tool_use = None
    for block in message.content:
        if block.type == 'tool_use':
            tool_use = block
            break

    if not tool_use:
        print('ERROR: Model did not return structured results')
        return

    results = tool_use.input['results']
    print('Categorized: ' + str(len(results)) + ' responses')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS field_categories_2026 (
            candidate_id TEXT,
            category TEXT,
            PRIMARY KEY (candidate_id, category)
        )
    ''')
    cursor.execute('DELETE FROM field_categories_2026')

    for r in results:
        cid = r['candidate_id']
        for cat in r['categories']:
            cursor.execute('INSERT OR IGNORE INTO field_categories_2026 (candidate_id, category) VALUES (?, ?)', (cid, cat))

    conn.commit()

    cursor.execute('SELECT category, COUNT(DISTINCT candidate_id) FROM field_categories_2026 GROUP BY category ORDER BY COUNT(DISTINCT candidate_id) DESC')
    print('')
    print('Category distribution:')
    for cat, count in cursor.fetchall():
        print('   ' + cat + ': ' + str(count))

    conn.close()

    print('')
    print(separator)
    print('FIELD CATEGORIZATION COMPLETE')
    print(separator)
    print('')

if __name__ == '__main__':
    categorize_fields()
