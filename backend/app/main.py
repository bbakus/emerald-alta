from flask import Flask, jsonify
from flask_restful import Api
from flask_jwt_extended import JWTManager
from flask_cors import CORS
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create Flask app
app = Flask(__name__)

# Configure app
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///emerald_altar.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'super-secret-key')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 5200
app.config['PROPAGATE_EXCEPTIONS'] = True
app.config['JWT_TOKEN_LOCATION'] = ['headers']
app.config['JWT_HEADER_NAME'] = 'Authorization'
app.config['JWT_HEADER_TYPE'] = 'Bearer'

# Enable CORS - configure for all routes (not just /api/)
CORS(app, origins="http://localhost:3000", supports_credentials=True)

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

# Initialize JWT
jwt = JWTManager(app)

# Initialize REST API
api = Api(app)

# Import routes
from app.routes import initialize_routes

# Initialize routes
initialize_routes(api)

if __name__ == '__main__':
    app.run(debug=True)
