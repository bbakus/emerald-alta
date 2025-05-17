from flask import Flask, request, make_response, jsonify
from flask_restful import Api
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from .routes import initialize_routes
from .db import db, init_db
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_app():
    app = Flask(__name__)
    
    # Configure CORS
    CORS(app, origins="http://localhost:3000", supports_credentials=True)
    
    # Configure database
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///emerald_altar.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize database
    db.init_app(app)
    
    # Configure JWT
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'super-secret-key')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 5200
    app.config['PROPAGATE_EXCEPTIONS'] = True
    app.config['JWT_TOKEN_LOCATION'] = ['headers']
    app.config['JWT_HEADER_NAME'] = 'Authorization'
    app.config['JWT_HEADER_TYPE'] = 'Bearer'
    jwt = JWTManager(app)
    
    # Add CORS headers even for errors
    @app.errorhandler(500)
    def handle_500(error):
        app.logger.error(f"500 error: {error}")
        response = jsonify({"error": "Internal server error", "details": str(error)})
        response.status_code = 500
        return response

    @app.errorhandler(404)
    def handle_404(error):
        app.logger.error(f"404 error: {error}")
        response = jsonify({"error": "Resource not found", "details": str(error)})
        response.status_code = 404
        return response
    
    # Initialize API routes
    api = Api(app)
    initialize_routes(api)
    
    # Create database tables
    with app.app_context():
        init_db()
    
    return app
