from functools import wraps
from flask import current_app, redirect, url_for, flash, session
from flask_login import current_user, login_user, logout_user
from flask_dance.contrib.google import google
from app.models import User, Band, UserRole, band_membership
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
        
        # Get current band from session
        current_band_id = session.get('current_band_id')
        if not current_band_id:
            flash('No band selected. Please select a band first.', 'warning')
            return redirect(url_for('main.select_band'))
        
        if not current_user.is_leader_of(current_band_id):
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
                    email=google_user_info['email']
                )
                db.session.add(user)
                db.session.flush()  # Get the user ID
                
                # Add user to default band
                # Check if band has any members using the new system
                band_members = User.query.join(band_membership).filter(
                    band_membership.c.band_id == default_band.id
                ).all()
                role = UserRole.LEADER if len(band_members) == 0 else UserRole.MEMBER
                default_band.add_member(user, role)
                
                # Set current band in session
                session['current_band_id'] = default_band.id
                
                db.session.commit()
            
            # Log in the user
            login_user(user)
            
            # Check if user has any bands
            if user.bands:
                # User has bands - redirect to band selection
                return redirect(url_for('main.select_band'))
            else:
                # User has no bands - redirect to band selection (which will show create/join options)
                return redirect(url_for('main.select_band'))
            
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
