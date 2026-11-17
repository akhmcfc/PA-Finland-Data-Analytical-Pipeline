# Copy this file to config/config.py. Secrets come from environment variables only.
"""
Configuration settings for 2026 bootcamp pipeline
"""

import os
from datetime import datetime

# Cohort year being processed (set PA_YEAR before running)
BOOTCAMP_YEAR = int(os.environ.get("PA_YEAR", "2026"))
def require_year():
    """Stop unless PA_YEAR is set. Scripts that write a cohort data call this first."""
    if "PA_YEAR" not in os.environ:
        raise SystemExit("Set PA_YEAR first, e.g. PA_YEAR=2027")
    return BOOTCAMP_YEAR

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
DATABASE_DIR = os.path.join(BASE_DIR, 'database')
SCRIPTS_DIR = os.path.join(BASE_DIR, 'scripts')

# File paths
RAW_DATA_FILE = os.path.join(DATA_DIR, 'raw', f'PA_Fin_{BOOTCAMP_YEAR}_Bootcamp_Applications.csv')
BOOTCAMPERS_FILE = os.path.join(DATA_DIR, 'processed', f'PA_{BOOTCAMP_YEAR}_bootcampers_final.csv')
DATABASE_FILE = os.environ.get("PA_DB", os.path.join(DATABASE_DIR, "project_access_2026.db"))

# Cohort configuration
CANDIDATE_ID_PREFIX = f"PA-{BOOTCAMP_YEAR}"

# Typeform IDs (fill in after creating forms)
SURVEY_1_FORM_ID = "YOUR_SURVEY_1_FORM_ID"
SURVEY_2_FORM_ID = "YOUR_SURVEY_2_FORM_ID"
SURVEY_3_FORM_ID = "YOUR_SURVEY_3_FORM_ID"

# Logging
LOG_LEVEL = "INFO"
LOG_FILE = os.path.join(BASE_DIR, 'logs', f'pipeline_{datetime.now().strftime("%Y%m%d")}.log')

TYPEFORM_API_TOKEN = os.environ.get("TYPEFORM_API_TOKEN", "")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD") or __import__("secrets").token_hex(16)

