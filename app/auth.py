from functools import wraps
from flask import current_app, redirect, url_for, flash, session
from flask_login import current_user, login_user, logout_user
from flask_dance.contrib.google import google
from app.models import User, Band
from app import db

def login_required(f):
    """Decorator to require login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('main.login'))
        return f(*args, **kwargs)
    return decorated_function

def band_leader_required(f):
    """Decorator to require band leader permissions"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('main.login'))
        
        if not current_user.is_band_leader:
            flash('Only band leaders can perform this action.', 'error')
            return redirect(url_for('main.dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function

def handle_google_login():
    """Handle Google OAuth login and user creation"""
    try:
        resp = google.get('/oauth2/v2/userinfo')
        if resp.ok:
            google_user_info = resp.json()
            
            # Check if user exists
            user = User.query.filter_by(email=google_user_info['email']).first()
            
            if not user:
                # Create new user and assign to default band
                default_band = Band.query.first()
                if not default_band:
                    # Create default band if none exists
                    default_band = Band(name="The Demo Band")
                    db.session.add(default_band)
                    db.session.flush()  # Get the ID
                
                user = User(
                    id=google_user_info['id'],
                    name=google_user_info['name'],
                    email=google_user_info['email'],
                    band_id=default_band.id,
                    is_band_leader=len(default_band.members) == 0  # First user becomes leader
                )
                db.session.add(user)
                db.session.commit()
            
            # Log in the user
            login_user(user)
            return redirect(url_for('main.dashboard'))
            
    except Exception as e:
        current_app.logger.error(f"Google OAuth error: {e}")
        flash('Authentication failed. Please try again.', 'error')
        return redirect(url_for('main.login'))
    
    flash('Authentication failed. Please try again.', 'error')
    return redirect(url_for('main.login'))

def logout():
    """Handle user logout"""
    logout_user()
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('main.login'))
