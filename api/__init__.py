"""
Flask API application factory
"""

from flask import Flask
from flask_cors import CORS

def create_app():
    """Create and configure Flask app"""
    app = Flask(__name__)

    # Enable CORS for dashboard
    CORS(app, resources={
        r"/api/*": {
            "origins": ["*"],
            "methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["Content-Type"]
        }
    })

    # Register routes
    from api.routes import public_routes, admin_routes, multi_year_routes
    app.register_blueprint(public_routes.bp)
    app.register_blueprint(admin_routes.bp)
    app.register_blueprint(multi_year_routes.bp)

    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return {"error": "Endpoint not found"}, 404

    @app.errorhandler(500)
    def server_error(error):
        return {"error": "Internal server error"}, 500

    return app
