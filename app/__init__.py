from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
import os

# Load environment variables with error handling
try:
    load_dotenv()
except Exception as e:
    print(f"Warning: Could not load .env file: {e}")
    print("Using default environment variables")

def create_app():
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['DEBUG'] = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    # Enable CORS for frontend communication (dev and prod)
    app.config['MAX_CONTENT_LENGTH'] = 25 * 1024 * 1024  # 25 MB upload limit
    # Allowed origins can be configured via CORS_ORIGINS env var (comma-separated)
    origins_env = os.getenv('CORS_ORIGINS', 'http://localhost:5173,http://127.0.0.1:5173')
    allowed_origins = [o.strip() for o in origins_env.split(',') if o.strip()]

    CORS(
        app,
        resources={r"/*": {"origins": allowed_origins}},
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "Accept"],
        expose_headers=["Content-Type"],
        supports_credentials=True,
    )
    
    # Root route
    @app.route('/')
    def root():
        return {
            'message': 'Gradalyze API is running!',
            'version': '1.0.0',
            'endpoints': {
                'health': '/health',
                'auth': '/api/auth',
                'analysis': '/api/analysis',
                'dossier': '/api/dossier'
            }
        }
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        return {'status': 'healthy', 'message': 'Gradalyze API is running'}
    
    # Register blueprints
    from app.routes import auth, dossier, users, ocr_cert, ocr_tor, objective_1, objective_1_cs, objective_2, objective_3
    app.register_blueprint(auth.bp)
    app.register_blueprint(dossier.bp)
    app.register_blueprint(users.bp)
    app.register_blueprint(objective_3.bp)
    app.register_blueprint(ocr_cert.bp)
    app.register_blueprint(ocr_tor.bp)
    app.register_blueprint(objective_1.bp)
    app.register_blueprint(objective_1_cs.bp)
    app.register_blueprint(objective_2.bp)
    
    return app
