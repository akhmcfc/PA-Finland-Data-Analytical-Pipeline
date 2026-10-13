"""
run_api.py - Start the Flask API
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api import create_app

if __name__ == '__main__':
    app = create_app()
    
    print("\n" + "="*70)
    print("🚀 PROJECT ACCESS PIPELINE API")
    print("="*70)
    print("\nStarting Flask API server...")
    print("📍 http://localhost:5000")
    print("\nPublic endpoints:")
    print("  GET /api/2026/health")
    print("  GET /api/2026/bootcamp/count")
    print("  GET /api/2026/survey/1/summary")
    print("  GET /api/2026/survey/2/summary")
    print("  GET /api/2026/survey/3/summary")
    print("  GET /api/2026/universities/dream")
    print("  GET /api/2026/fields/distribution")
    print("  GET /api/2026/destinations/distribution")
    print("  GET /api/2026/dashboard")
    print("\nAdmin endpoints (require X-Admin-Password header):")
    print("  GET /api/2026/admin/bootcamper/<candidate_id>")
    print("  GET /api/2026/admin/health")
    print("\n" + "="*70 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
