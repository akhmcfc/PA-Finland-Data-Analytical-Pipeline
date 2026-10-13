"""
Security utilities for admin endpoints
"""

import os
from functools import wraps
from flask import request, jsonify
from config.config import ADMIN_PASSWORD

def require_admin_password(f):
    """Decorator to require admin password header"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get password from header
        password = request.headers.get('X-Admin-Password')
        
        if not password:
            return jsonify({"error": "Admin password required"}), 401
        
        if password != ADMIN_PASSWORD:
            return jsonify({"error": "Invalid admin password"}), 401
        
        return f(*args, **kwargs)
    
    return decorated_function

def log_admin_access(action, resource, user_id=None):
    """Log admin access for security audit"""
    import datetime
    
    log_entry = f"{datetime.datetime.now()} | Action: {action} | Resource: {resource} | User: {user_id}\n"
    
    # Append to security log
    os.makedirs('logs', exist_ok=True)
    with open('logs/admin_access.log', 'a') as f:
        f.write(log_entry)
