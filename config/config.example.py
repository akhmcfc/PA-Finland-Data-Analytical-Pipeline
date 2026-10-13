# Copy to config/config.py. Secrets come from environment variables only.
import os
TYPEFORM_API_TOKEN = os.environ.get("TYPEFORM_API_TOKEN", "")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD") or __import__("secrets").token_hex(16)
