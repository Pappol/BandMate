import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set OAuth insecure transport for development BEFORE importing OAuth libraries
if os.getenv('FLASK_ENV') == 'development' or os.getenv('FLASK_DEBUG') == '1':
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    print("⚠️  Development mode: OAuth insecure transport enabled")

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_dance.contrib.google import make_google_blueprint

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()


def create_app(config_name=None):
    """Application factory pattern for Flask app"""
    app = Flask(__name__,
                template_folder='main/templates',
                static_folder='main/static')

    # Configuration
    app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL',
                                                      'sqlite:///instance/bandmate.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Google OAuth configuration
    app.config['GOOGLE_OAUTH_CLIENT_ID'] = os.getenv('GOOGLE_CLIENT_ID')
    app.config['GOOGLE_OAUTH_CLIENT_SECRET'] = os.getenv('GOOGLE_CLIENT_SECRET')

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # Configure login manager
    login_manager.login_view = 'main.login'
    login_manager.login_message = 'Please log in to access this page.'

    # Google OAuth blueprint - only register if credentials are provided
    if (app.config['GOOGLE_OAUTH_CLIENT_ID'] and
        app.config['GOOGLE_OAUTH_CLIENT_ID'] != 'your-google-client-id.apps.googleusercontent.com' and
        app.config['GOOGLE_OAUTH_CLIENT_SECRET'] and
        app.config['GOOGLE_OAUTH_CLIENT_SECRET'] != 'your-google-client-secret'):

        # Register main blueprint FIRST (so our custom routes take precedence)
        from app.main import main as main_blueprint
        app.register_blueprint(main_blueprint)

        from app.api import api as api_blueprint
        app.register_blueprint(api_blueprint, url_prefix='/api')

        # Then register Google OAuth blueprint
        google_bp = make_google_blueprint(
            client_id=app.config['GOOGLE_OAUTH_CLIENT_ID'],
            client_secret=app.config['GOOGLE_OAUTH_CLIENT_SECRET'],
            scope=['openid',
                   'https://www.googleapis.com/auth/userinfo.profile',
                   'https://www.googleapis.com/auth/userinfo.email'],
            redirect_to='main.google_authorized'
        )
        app.register_blueprint(google_bp, url_prefix='/oauth')
        print("✅ Google OAuth blueprint registered")
    else:
        print("⚠️  Google OAuth credentials not configured - OAuth login will not work")

        # Register blueprints even without OAuth
        from app.main import main as main_blueprint
        app.register_blueprint(main_blueprint)

        from app.api import api as api_blueprint
        app.register_blueprint(api_blueprint, url_prefix='/api')

    # Import models to ensure they are registered with SQLAlchemy
    from app import models

    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return db.session.get(User, user_id)

    # Context processor to make current band available in all templates
    @app.context_processor
    def inject_current_band():
        """Make current band available in all templates"""
        from app.models import Band
        from flask import session
        current_band = None

        if 'current_band_id' in session:
            current_band = db.session.get(Band, session['current_band_id'])

        return dict(current_band=current_band)

    return app
