from flask import render_template, redirect, url_for, flash, request, jsonify, current_app, session
from flask_login import current_user, login_user, logout_user
from flask_dance.contrib.google import google
from app.main import main
from app.auth import login_required, band_leader_required, handle_google_login, logout
from app.models import User, Band, Song, SongProgress, Vote, SongStatus, ProgressStatus, Invitation, InvitationStatus, SetlistConfig, UserRole, band_membership
from app import db
from app.spotify import spotify_api
from datetime import datetime, date, timedelta
import json

@main.route('/')
def index():
    """Home page - show landing page for new users, redirect to dashboard if logged in"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('landing.html', config=current_app.config)

@main.route('/color-test')
def color_test():
    """Test page to showcase the new color palette"""
    return render_template('color_test.html')

@main.route('/login')
def login():
    """Login page with Google OAuth button"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('login.html', config=current_app.config)

@main.route('/demo-login/<email>')
def demo_login(email):
    """Demo login route for testing without Google OAuth"""
    # Find the demo user by email
    user = User.query.filter_by(email=email).first()
    if user:
        login_user(user)
        
        # Check if user has any bands
        if user.bands:
            # User has bands - redirect to band selection
            flash(f'Demo login successful! Welcome back, {user.name}!', 'success')
            return redirect(url_for('main.select_band'))
        else:
            # User has no bands - redirect to band selection (which will show create/join options)
            flash(f'Demo login successful! Welcome back, {user.name}!', 'success')
            return redirect(url_for('main.select_band'))
    else:
        flash('Demo user not found. Available demo users: alice@demo.com, bob@demo.com, carla@demo.com', 'error')
        return redirect(url_for('main.login'))

@main.route('/login/google')
def google_login():
    """Initiate Google OAuth login"""
    try:
        if not google.authorized:
            return redirect(url_for('google.login'))
        return handle_google_login()
    except Exception as e:
        # OAuth not configured or error occurred
        current_app.logger.error(f"Google OAuth error: {e}")
        flash('Google OAuth is not configured. Please use demo login instead.', 'warning')
        return redirect(url_for('main.login'))

@main.route('/login/google/authorized')
def google_authorized():
    """Handle Google OAuth callback and user creation"""
    if not google.authorized:
        flash('Google OAuth failed. Please try again.', 'error')
        return redirect(url_for('main.login'))
    
    try:
        resp = google.get('/oauth2/v2/userinfo')
        if resp.ok:
            google_user_info = resp.json()
            
            # Check if user exists
            user = User.query.filter_by(email=google_user_info['email']).first()
            
            if not user:
                # New user - redirect to onboarding
                session['google_user_info'] = google_user_info
                return redirect(url_for('main.onboarding'))
            
            # Existing user - log them in
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

@main.route('/onboarding')
def onboarding():
    """Onboarding page for new users"""
    if 'google_user_info' not in session:
        flash('Please log in with Google first.', 'warning')
        return redirect(url_for('main.login'))
    
    google_user_info = session['google_user_info']
    
    # Check if user already exists (in case they refresh the page)
    existing_user = User.query.filter_by(email=google_user_info['email']).first()
    if existing_user:
        login_user(existing_user)
        session.pop('google_user_info', None)
        
        # Check if user has any bands
        if existing_user.bands:
            # User has bands - redirect to band selection
            return redirect(url_for('main.select_band'))
        else:
            # User has no bands - redirect to band selection (which will show create/join options)
            return redirect(url_for('main.select_band'))
    
    return render_template('onboarding.html', user_info=google_user_info)

@main.route('/create_band', methods=['POST'])
def create_band():
    """Create a new band and user"""
    if 'google_user_info' not in session:
        flash('Please log in with Google first.', 'warning')
        return redirect(url_for('main.login'))
    
    band_name = request.form.get('band_name')
    if not band_name:
        flash('Band name is required.', 'error')
        return redirect(url_for('main.onboarding'))
    
    google_user_info = session['google_user_info']
    
    try:
        # Create new band
        band = Band(name=band_name)
        db.session.add(band)
        db.session.flush()  # Get the ID
        
        # Create new user
        user = User(
            id=google_user_info['id'],
            name=google_user_info['name'],
            email=google_user_info['email']
        )
        db.session.add(user)
        db.session.flush()  # Get the user ID
        
        # Add user to band with leader role
        band.add_member(user, UserRole.LEADER)
        
        # Set current band in session
        session['current_band_id'] = band.id
        
        # Log in the user
        login_user(user)
        session.pop('google_user_info', None)
        
        flash(f'Welcome to BandMate! Your band "{band_name}" has been created.', 'success')
        return redirect(url_for('main.dashboard'))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating band: {e}")
        flash('Failed to create band. Please try again.', 'error')
        return redirect(url_for('main.onboarding'))

@main.route('/join_band', methods=['POST'])
def join_band_legacy():
    """Join an existing band (legacy function)"""
    if 'google_user_info' not in session:
        flash('Please log in with Google first.', 'warning')
        return redirect(url_for('main.login'))
    
    invitation_code = request.form.get('invitation_code')
    if not invitation_code:
        flash('Invitation code is required.', 'error')
        return redirect(url_for('main.onboarding'))
    
    google_user_info = session['google_user_info']
    
    # For now, we'll use a simple approach - join the first available band
    # In a real app, you'd have proper invitation codes
    band = Band.query.first()
    if not band:
        flash('No bands available to join.', 'error')
        return redirect(url_for('main.onboarding'))
    
    try:
        # Create new user
        user = User(
            id=google_user_info['id'],
            name=google_user_info['name'],
            email=google_user_info['email'],
            band_id=band.id,
            is_band_leader=False
        )
        db.session.add(user)
        db.session.commit()
        
        # Log in the user
        login_user(user)
        session.pop('google_user_info', None)
        
        flash(f'Welcome to BandMate! You\'ve joined "{band.name}".', 'success')
        return redirect(url_for('main.dashboard'))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error joining band: {e}")
        flash('Failed to join band. Please try again.', 'error')
        return redirect(url_for('main.onboarding'))

@main.route('/demo_mode')
def demo_mode():
    """Demo mode for new users"""
    if 'google_user_info' not in session:
        flash('Please log in with Google first.', 'warning')
        return redirect(url_for('main.login'))
    
    google_user_info = session['google_user_info']
    
    try:
        # Create demo user and assign to demo band
        demo_band = Band.query.filter_by(name="The Demo Band").first()
        if not demo_band:
            demo_band = Band(name="The Demo Band")
            db.session.add(demo_band)
            db.session.flush()
        
        user = User(
            id=google_user_info['id'],
            name=google_user_info['name'],
            email=google_user_info['email']
        )
        db.session.add(user)
        db.session.flush()  # Get the user ID
        
        # Add user to demo band
        demo_band.add_member(user, UserRole.MEMBER)
        
        # Set current band in session
        session['current_band_id'] = demo_band.id
        
        # Log in the user
        login_user(user)
        session.pop('google_user_info', None)
        
        flash('Welcome to BandMate! You\'re now in demo mode with sample data.', 'success')
        return redirect(url_for('main.dashboard'))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating demo user: {e}")
        flash('Failed to enter demo mode. Please try again.', 'error')
        return redirect(url_for('main.onboarding'))

@main.route('/logout')
@login_required
def logout_route():
    """Logout route"""
    return logout()

@main.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard showing active songs and member progress"""
    # Get current band from session
    current_band_id = session.get('current_band_id')
    if not current_band_id:
        # No current band set - check if user has any bands
        if current_user.bands:
            # User has bands but none selected - redirect to band selection
            return redirect(url_for('main.select_band'))
        else:
            # User has no bands - redirect to onboarding
            return redirect(url_for('main.onboarding'))
    
    # Verify user is a member of the current band
    if not current_user.is_member_of(current_band_id):
        flash('You are not a member of the current band.', 'error')
        return redirect(url_for('main.select_band'))
    
    # Get active songs for the current band
    active_songs = Song.query.filter_by(
        band_id=current_band_id,
        status=SongStatus.ACTIVE
    ).all()
    
    # Get all band members
    band_members = User.query.join(band_membership).filter(
        band_membership.c.band_id == current_band_id
    ).all()
    
    # Get progress for all songs and members
    song_progress = {}
    for song in active_songs:
        song_progress[song.id] = {}
        for member in band_members:
            progress = SongProgress.query.filter_by(
                user_id=member.id,
                song_id=song.id
            ).first()
            song_progress[song.id][member.id] = progress
    
    return render_template('dashboard.html',
                         songs=active_songs,
                         members=band_members,
                         song_progress=song_progress)

@main.route('/wishlist')
@login_required
def wishlist():
    """Show wishlist songs and voting"""
    # Get current band from session
    current_band_id = session.get('current_band_id')
    if not current_band_id:
        flash('No band selected. Please select a band first.', 'warning')
        return redirect(url_for('main.select_band'))
    
    current_band = Band.query.get(current_band_id)
    if not current_band:
        flash('Band not found.', 'error')
        return redirect(url_for('main.select_band'))
    
    wishlist_songs = Song.query.filter_by(
        band_id=current_band_id,
        status=SongStatus.WISHLIST
    ).all()
    
    # Get vote counts for each song
    for song in wishlist_songs:
        song.vote_count = Vote.query.filter_by(song_id=song.id).count()
        song.user_voted = Vote.query.filter_by(
            song_id=song.id,
            user_id=current_user.id
        ).first() is not None
    
    return render_template('wishlist.html', songs=wishlist_songs, current_band=current_band)

@main.route('/wishlist/propose', methods=['GET', 'POST'])
@login_required
def propose_song():
    """Propose a new song for the wishlist"""
    if request.method == 'POST':
        title = request.form.get('title')
        artist = request.form.get('artist')
        link = request.form.get('link', '')
        spotify_track_id = request.form.get('spotify_track_id', '')
        album_art_url = request.form.get('album_art_url', '')
        duration_seconds = request.form.get('duration_seconds', '')
        
        if not title or not artist:
            flash('Title and artist are required.', 'error')
            return redirect(url_for('main.wishlist'))
        
        # Get current band from session
        current_band_id = session.get('current_band_id')
        if not current_band_id:
            flash('No band selected. Please select a band first.', 'warning')
            return redirect(url_for('main.select_band'))
        
        # Create new song
        song = Song(
            title=title,
            artist=artist,
            status=SongStatus.WISHLIST,
            band_id=current_band_id,
            spotify_track_id=spotify_track_id if spotify_track_id else None,
            album_art_url=album_art_url if album_art_url else None,
            duration_seconds=int(duration_seconds) if duration_seconds and duration_seconds.isdigit() else None
        )
        db.session.add(song)
        db.session.commit()
        
        flash(f'Song "{title}" by {artist} has been added to the wishlist!', 'success')
        return redirect(url_for('main.wishlist'))
    
    return render_template('propose_song.html')

@main.route('/api/spotify/search')
@login_required
def spotify_search():
    """Search for songs using Spotify API"""
    query = request.args.get('q', '').strip()
    
    if not query:
        return jsonify({'error': 'Search query is required'}), 400
    
    if len(query) < 2:
        return jsonify({'error': 'Search query must be at least 2 characters'}), 400
    
    try:
        result = spotify_api.search_tracks(query, limit=10)
        
        if result.get('error'):
            return jsonify({'error': result['error']}), 400
        
        return jsonify({'tracks': result['tracks']})
    except Exception as e:
        current_app.logger.error(f"Spotify search error: {e}")
        return jsonify({'error': 'Failed to search Spotify'}), 500

@main.route('/setlist')
@login_required
def setlist_generator():
    """Setlist generator interface"""
    return render_template('setlist.html')

@main.route('/generate_setlist', methods=['POST'])
@login_required
def generate_setlist():
    """Generate optimized setlist based on parameters"""
    try:
        data = request.get_json()
        duration_total = int(data.get('duration_minutes_total', 120))
        learning_ratio = float(data.get('learning_ratio', 0.6))
        
        # Validate inputs
        if duration_total <= 0 or learning_ratio < 0 or learning_ratio > 1:
            return jsonify({'error': 'Invalid parameters'}), 400
        
        # Get current band from session
        current_band_id = session.get('current_band_id')
        if not current_band_id:
            return jsonify({'error': 'No band selected'}), 400
        
        current_band = Band.query.get(current_band_id)
        if not current_band:
            return jsonify({'error': 'Band not found'}), 400
        
        # Get band's setlist configuration
        band_config = current_band.get_setlist_config()
        
        # Cluster duration to nearest 30-minute interval
        clustered_duration = band_config.get_clustered_duration(duration_total)
        
        # Calculate time allocation with clustered duration
        time_learning = round(clustered_duration * learning_ratio)
        time_maintenance = clustered_duration - time_learning
        
        # Get songs for the user's band
        active_songs = Song.query.filter_by(
            band_id=current_user.band_id,
            status=SongStatus.ACTIVE
        ).all()
        
        # Separate songs into learning and maintenance pools
        learning_pool = []
        maintenance_pool = []
        
        for song in active_songs:
            # Check if all members have mastered the song or are ready for rehearsal
            all_ready_or_mastered = True
            for member in current_user.band.members:
                progress = SongProgress.query.filter_by(
                    user_id=member.id,
                    song_id=song.id
                ).first()
                if not progress or progress.status not in [ProgressStatus.READY_FOR_REHEARSAL, ProgressStatus.MASTERED]:
                    all_ready_or_mastered = False
                    break
            
            if all_ready_or_mastered:
                maintenance_pool.append(song)
            else:
                learning_pool.append(song)
        
        # Sort learning pool by readiness score (descending)
        learning_pool.sort(key=lambda x: x.readiness_score, reverse=True)
        
        # Sort maintenance pool by last rehearsed date (oldest first)
        maintenance_pool.sort(key=lambda x: x.last_rehearsed_on or date.min)
        

        
        # Build learning setlist
        learning_setlist = []
        learning_time = 0
        
        for song in learning_pool:
            if song.duration_seconds:
                # Calculate duration with new songs buffer
                song_duration_with_buffer = band_config.calculate_song_duration_with_buffer(
                    song.duration_seconds, is_learned=False
                )
                
                if learning_time + song_duration_with_buffer <= time_learning:
                    learning_setlist.append({
                        'title': song.title,
                        'artist': song.artist,
                        'duration_minutes': round(song.duration_seconds / 60, 1),
                        'duration_with_buffer': round(song_duration_with_buffer, 1),
                        'buffer_percent': band_config.new_songs_buffer_percent,
                        'block': 'learning',
                        'readiness_score': round(song.readiness_score, 2)
                    })
                    learning_time += song_duration_with_buffer
        
        # Build maintenance setlist
        maintenance_setlist = []
        maintenance_time = 0
        
        for song in maintenance_pool:
            if song.duration_seconds:
                # Calculate duration with learned songs buffer
                song_duration_with_buffer = band_config.calculate_song_duration_with_buffer(
                    song.duration_seconds, is_learned=True
                )
                
                if maintenance_time + song_duration_with_buffer <= time_maintenance:
                    maintenance_setlist.append({
                        'title': song.title,
                        'artist': song.artist,
                        'duration_minutes': round(song.duration_seconds / 60, 1),
                        'duration_with_buffer': round(song_duration_with_buffer, 1),
                        'buffer_percent': band_config.learned_songs_buffer_percent,
                        'block': 'maintenance',
                        'last_rehearsed': song.last_rehearsed_on.isoformat() if song.last_rehearsed_on else 'Never'
                    })
                    maintenance_time += song_duration_with_buffer
        
        # Combine setlists
        full_setlist = learning_setlist + maintenance_setlist
        
        # Add break based on configuration
        break_info = None
        if band_config.is_break_needed(clustered_duration):
            break_info = {
                'position': 'mid-session',
                'duration': band_config.break_time_minutes,
                'description': f'{band_config.break_time_minutes}-minute break'
            }
        
        # Calculate cumulative times with buffer durations
        cumulative_time = 0
        for item in full_setlist:
            cumulative_time += item['duration_with_buffer']
            item['cumulative_time'] = round(cumulative_time, 1)
        
        result = {
            'setlist': full_setlist,
            'summary': {
                'total_duration': clustered_duration,
                'original_duration': duration_total,
                'learning_time': round(learning_time, 1),
                'maintenance_time': round(maintenance_time, 1),
                'learning_ratio': learning_ratio,
                'break_info': break_info,
                'config': {
                    'new_songs_buffer': band_config.new_songs_buffer_percent,
                    'learned_songs_buffer': band_config.learned_songs_buffer_percent,
                    'break_time': band_config.break_time_minutes,
                    'break_threshold': band_config.break_threshold_minutes,
                    'time_cluster': band_config.time_cluster_minutes
                }
            }
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main.route('/start-fresh')
@login_required
def start_fresh():
    """Start fresh page - allows users to leave current band and start over"""
    return render_template('start_fresh.html')

@main.route('/create-new-band', methods=['POST'])
@login_required
def create_new_band_legacy():
    """Create a new band and leave the current one (legacy function)"""
    band_name = request.form.get('band_name')
    if not band_name:
        flash('Band name is required.', 'error')
        return redirect(url_for('main.start_fresh'))
    
    try:
        # Leave current band (remove from all bands)
        current_band_id = session.get('current_band_id')
        if current_band_id:
            current_band = Band.query.get(current_band_id)
            if current_band:
                current_band.remove_member(current_user.id)
        
        # Create new band
        new_band = Band(name=band_name)
        db.session.add(new_band)
        db.session.flush()  # Get the ID
        
        # Add user to new band as leader
        new_band.add_member(current_user, UserRole.LEADER)
        
        # Set as current band
        session['current_band_id'] = new_band.id
        
        flash(f'Successfully created new band "{band_name}"!', 'success')
        return redirect(url_for('main.dashboard'))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating new band: {e}")
        flash('Failed to create new band. Please try again.', 'error')
        return redirect(url_for('main.start_fresh'))

@main.route('/join-different-band', methods=['POST'])
@login_required
def join_different_band():
    """Join a different band using invitation code"""
    invitation_code = request.form.get('invitation_code')
    if not invitation_code:
        flash('Invitation code is required.', 'error')
        return redirect(url_for('main.start_fresh'))
    
    try:
        # Find invitation by code
        invitation = Invitation.query.filter_by(code=invitation_code).first()
        if not invitation or not invitation.is_valid:
            flash('Invalid or expired invitation code. Please check and try again.', 'error')
            return redirect(url_for('main.start_fresh'))
        
        # Leave current band (remove from all bands)
        current_band_id = session.get('current_band_id')
        if current_band_id:
            current_band = Band.query.get(current_band_id)
            if current_band:
                current_band.remove_member(current_user.id)
        
        # Join new band
        band = Band.query.get(invitation.band_id)
        band.add_member(current_user, UserRole.MEMBER)
        
        # Mark invitation as accepted
        invitation.status = InvitationStatus.ACCEPTED
        
        # Set as current band
        session['current_band_id'] = band.id
        
        flash(f'Successfully joined "{band.name}"!', 'success')
        return redirect(url_for('main.dashboard'))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error joining band: {e}")
        flash('Failed to join band. Please try again.', 'error')
        return redirect(url_for('main.start_fresh'))

@main.route('/handle-oauth-callback')
def handle_oauth_callback():
    """Handle OAuth callback from Flask-Dance"""
    if not google.authorized:
        flash('Google OAuth failed. Please try again.', 'error')
        return redirect(url_for('main.login'))
    
    try:
        resp = google.get('/oauth2/v2/userinfo')
        if resp.ok:
            google_user_info = resp.json()
            
            # Check if user exists
            user = User.query.filter_by(email=google_user_info['email']).first()
            
            if not user:
                # New user - redirect to onboarding
                session['google_user_info'] = google_user_info
                return redirect(url_for('main.onboarding'))
            
            # Existing user - log them in
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

@main.route('/band/management')
@login_required
def band_management():
    """Band management page for leaders to invite and manage members"""
    # Get current band from session
    current_band_id = session.get('current_band_id')
    if not current_band_id:
        flash('No band selected. Please select a band first.', 'warning')
        return redirect(url_for('main.select_band'))
    
    current_band = Band.query.get(current_band_id)
    if not current_band:
        flash('Band not found.', 'error')
        return redirect(url_for('main.select_band'))
    
    # Get all members of the current band
    band_members = User.query.join(band_membership).filter(
        band_membership.c.band_id == current_band_id
    ).all()
    
    # Get pending invitations for the current band
    pending_invitations = []
    if current_user.is_leader_of(current_band_id):
        pending_invitations = Invitation.query.filter_by(
            band_id=current_band_id,
            status=InvitationStatus.PENDING
        ).all()
    
    return render_template('band_management.html', 
                         current_band=current_band,
                         band_members=band_members,
                         pending_invitations=pending_invitations)

@main.route('/band/invite', methods=['POST'])
@login_required
def invite_member():
    """Invite a new member to the band"""
    # Get current band from session
    current_band_id = session.get('current_band_id')
    if not current_band_id:
        flash('No band selected. Please select a band first.', 'warning')
        return redirect(url_for('main.select_band'))
    
    if not current_user.is_leader_of(current_band_id):
        flash('Only band leaders can invite new members.', 'error')
        return redirect(url_for('main.band_management'))
    
    email = request.form.get('email')
    message = request.form.get('message', '')
    
    if not email:
        flash('Email address is required.', 'error')
        return redirect(url_for('main.band_management'))
    
    # Get current band from session
    current_band_id = session.get('current_band_id')
    if not current_band_id:
        flash('No band selected. Please select a band first.', 'warning')
        return redirect(url_for('main.select_band'))
    
    # Check if user already exists in the band
    existing_user = User.query.join(band_membership).filter(
        band_membership.c.band_id == current_band_id,
        User.email == email
    ).first()
    if existing_user:
        flash(f'{email} is already a member of your band.', 'error')
        return redirect(url_for('main.band_management'))
    
    # Check if invitation already exists
    existing_invitation = Invitation.query.filter_by(
        invited_email=email,
        band_id=current_band_id,
        status=InvitationStatus.PENDING
    ).first()
    
    if existing_invitation:
        flash(f'An invitation has already been sent to {email}.', 'error')
        return redirect(url_for('main.band_management'))
    
    try:
        # Create new invitation
        invitation = Invitation(
            code=Invitation.generate_code(),
            band_id=current_band_id,
            invited_by=current_user.id,
            invited_email=email,
            expires_at=datetime.utcnow() + timedelta(days=7)  # Expires in 7 days
        )
        db.session.add(invitation)
        db.session.commit()
        
        # In a real app, you would send an email here
        # For now, we'll just show the invitation code
        flash(f'Invitation sent to {email}! Invitation code: {invitation.code}', 'success')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating invitation: {e}")
        flash('Failed to send invitation. Please try again.', 'error')
    
    return redirect(url_for('main.band_management'))

@main.route('/band/join/<invitation_code>')
def join_band_with_code(invitation_code):
    """Join a band using an invitation code"""
    if current_user.is_authenticated:
        flash('You are already logged in. Please log out first to join with a different account.', 'warning')
        return redirect(url_for('main.dashboard'))
    
    # Find the invitation
    invitation = Invitation.query.filter_by(code=invitation_code).first()
    
    if not invitation:
        flash('Invalid invitation code.', 'error')
        return redirect(url_for('main.login'))
    
    if invitation.status != InvitationStatus.PENDING:
        flash('This invitation has already been used or expired.', 'error')
        return redirect(url_for('main.login'))
    
    if invitation.is_expired:
        flash('This invitation has expired.', 'error')
        return redirect(url_for('main.login'))
    
    # Store invitation info in session for the join process
    session['invitation_code'] = invitation_code
    session['invited_band_id'] = invitation.band_id
    
    flash(f'You have been invited to join {invitation.band.name}! Please log in or create an account.', 'info')
    return redirect(url_for('main.login'))

@main.route('/band/resend-invitation/<int:invitation_id>', methods=['POST'])
@login_required
def resend_invitation(invitation_id):
    """Resend an invitation"""
    # Get current band from session
    current_band_id = session.get('current_band_id')
    if not current_band_id:
        return jsonify({'error': 'No band selected'}), 400
    
    if not current_user.is_leader_of(current_band_id):
        return jsonify({'error': 'Unauthorized'}), 403
    
    invitation = Invitation.query.get_or_404(invitation_id)
    
    if invitation.band_id != current_band_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    if invitation.status != InvitationStatus.PENDING:
        return jsonify({'error': 'Invitation cannot be resent'}), 400
    
    try:
        # Extend expiration date
        invitation.expires_at = datetime.utcnow() + timedelta(days=7)
        db.session.commit()
        
        # In a real app, you would send an email here
        flash(f'Invitation resent to {invitation.invited_email}', 'success')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error resending invitation: {e}")
        return jsonify({'error': 'Failed to resend invitation'}), 500
    
    return jsonify({'success': True})

@main.route('/band/cancel-invitation/<int:invitation_id>', methods=['POST'])
@login_required
def cancel_invitation(invitation_id):
    """Cancel an invitation"""
    # Get current band from session
    current_band_id = session.get('current_band_id')
    if not current_band_id:
        return jsonify({'error': 'No band selected'}), 400
    
    if not current_user.is_leader_of(current_band_id):
        return jsonify({'error': 'Unauthorized'}), 403
    
    invitation = Invitation.query.get_or_404(invitation_id)
    
    if invitation.band_id != current_band_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        invitation.status = InvitationStatus.EXPIRED
        db.session.commit()
        flash(f'Invitation to {invitation.invited_email} cancelled.', 'success')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error cancelling invitation: {e}")
        return jsonify({'error': 'Failed to cancel invitation'}), 500
    
    return jsonify({'success': True})

@main.route('/band/remove-member/<string:member_id>', methods=['POST'])
@login_required
def remove_member(member_id):
    """Remove a member from the band"""
    # Get current band from session
    current_band_id = session.get('current_band_id')
    if not current_band_id:
        flash('No band selected. Please select a band first.', 'warning')
        return redirect(url_for('main.select_band'))
    
    if not current_user.is_leader_of(current_band_id):
        flash('Only band leaders can remove members.', 'error')
        return redirect(url_for('main.band_management'))
    
    if member_id == current_user.id:
        flash('You cannot remove yourself from the band.', 'error')
        return redirect(url_for('main.band_management'))
    
    member = User.query.get_or_404(member_id)
    
    if not member.is_member_of(current_band_id):
        flash('Member not found in your band.', 'error')
        return redirect(url_for('main.band_management'))
    
    if member.get_band_role(current_band_id) == UserRole.LEADER.value:
        flash('Cannot remove another band leader.', 'error')
        return redirect(url_for('main.band_management'))
    
    try:
        # Remove the member
        db.session.delete(member)
        db.session.commit()
        flash(f'{member.name} has been removed from the band.', 'success')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error removing member: {e}")
        flash('Failed to remove member. Please try again.', 'error')
    
    return redirect(url_for('main.band_management'))

@main.route('/setlist/config')
@login_required
@band_leader_required
def setlist_config():
    """Setlist configuration management page for band leaders"""
    band_config = current_user.band.get_setlist_config()
    return render_template('setlist_config.html', config=band_config)

@main.route('/api/setlist/config', methods=['GET'])
@login_required
@band_leader_required
def get_setlist_config():
    """Get current setlist configuration"""
    band_config = current_user.band.get_setlist_config()
    return jsonify({
        'new_songs_buffer_percent': band_config.new_songs_buffer_percent,
        'learned_songs_buffer_percent': band_config.learned_songs_buffer_percent,
        'break_time_minutes': band_config.break_time_minutes,
        'break_threshold_minutes': band_config.break_threshold_minutes,
        'min_session_minutes': band_config.min_session_minutes,
        'max_session_minutes': band_config.max_session_minutes,
        'time_cluster_minutes': band_config.time_cluster_minutes
    })

@main.route('/api/setlist/config', methods=['PUT'])
@login_required
@band_leader_required
def update_setlist_config():
    """Update setlist configuration"""
    try:
        data = request.get_json()
        band_config = current_user.band.get_setlist_config()
        
        # Update configuration fields
        if 'new_songs_buffer_percent' in data:
            band_config.new_songs_buffer_percent = float(data['new_songs_buffer_percent'])
        if 'learned_songs_buffer_percent' in data:
            band_config.learned_songs_buffer_percent = float(data['learned_songs_buffer_percent'])
        if 'break_time_minutes' in data:
            band_config.break_time_minutes = int(data['break_time_minutes'])
        if 'break_threshold_minutes' in data:
            band_config.break_threshold_minutes = int(data['break_threshold_minutes'])
        if 'min_session_minutes' in data:
            band_config.min_session_minutes = int(data['min_session_minutes'])
        if 'max_session_minutes' in data:
            band_config.max_session_minutes = int(data['max_session_minutes'])
        if 'time_cluster_minutes' in data:
            band_config.time_cluster_minutes = int(data['time_cluster_minutes'])
        
        # Validate ranges
        if not (0 <= band_config.new_songs_buffer_percent <= 100):
            return jsonify({'error': 'New songs buffer must be between 0 and 100'}), 400
        if not (0 <= band_config.learned_songs_buffer_percent <= 100):
            return jsonify({'error': 'Learned songs buffer must be between 0 and 100'}), 400
        if not (5 <= band_config.break_time_minutes <= 30):
            return jsonify({'error': 'Break time must be between 5 and 30 minutes'}), 400
        if not (60 <= band_config.break_threshold_minutes <= 180):
            return jsonify({'error': 'Break threshold must be between 60 and 180 minutes'}), 400
        if not (15 <= band_config.min_session_minutes <= 60):
            return jsonify({'error': 'Minimum session must be between 15 and 60 minutes'}), 400
        if not (120 <= band_config.max_session_minutes <= 300):
            return jsonify({'error': 'Maximum session must be between 120 and 300 minutes'}), 400
        if not (15 <= band_config.time_cluster_minutes <= 60):
            return jsonify({'error': 'Time cluster must be between 15 and 60 minutes'}), 400
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Configuration updated successfully'})
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating setlist config: {e}")
        return jsonify({'error': 'Failed to update configuration'}), 500

@main.route('/band/switch/<int:band_id>')
@login_required
def switch_band(band_id):
    """Switch to a different band"""
    # Check if user is a member of the requested band
    if not current_user.is_member_of(band_id):
        flash('You are not a member of that band.', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Update session with new band
    session['current_band_id'] = band_id
    flash(f'Switched to band: {Band.query.get(band_id).name}', 'success')
    
    # Redirect back to the page they were on, or dashboard
    return redirect(request.referrer or url_for('main.dashboard'))

@main.route('/band/select')
@login_required
def select_band():
    """Show band selection page for users with multiple bands"""
    user_bands = current_user.bands
    
    if not user_bands:
        # User has no bands - show create/join options instead of redirecting
        flash('You are not a member of any bands. Create a new band or join an existing one.', 'info')
        return render_template('select_band.html', bands=[])
    
    if len(user_bands) == 1:
        # User has only one band - set it as current and redirect to dashboard
        session['current_band_id'] = user_bands[0].id
        return redirect(url_for('main.dashboard'))
    
    # User has multiple bands - show selection page
    return render_template('select_band.html', bands=user_bands)

@main.route('/band/create', methods=['GET', 'POST'])
@login_required
def create_new_band():
    """Create a new band and add the user as leader"""
    if request.method == 'POST':
        band_name = request.form.get('band_name')
        if not band_name:
            flash('Band name is required.', 'error')
            return redirect(url_for('main.create_new_band'))
        
        try:
            # Create new band
            band = Band(name=band_name)
            db.session.add(band)
            db.session.flush()  # Get the ID
            
            # Add user as leader
            band.add_member(current_user, UserRole.LEADER)
            
            # Set as current band
            session['current_band_id'] = band.id
            
            flash(f'Band "{band_name}" created successfully! You are now the leader.', 'success')
            return redirect(url_for('main.dashboard'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating band: {e}")
            flash('Failed to create band. Please try again.', 'error')
            return redirect(url_for('main.create_new_band'))
    
    return render_template('create_band.html')

@main.route('/band/join', methods=['GET', 'POST'])
@login_required
def join_band():
    """Join an existing band using invitation code"""
    if request.method == 'POST':
        invitation_code = request.form.get('invitation_code')
        if not invitation_code:
            flash('Invitation code is required.', 'error')
            return redirect(url_for('main.join_band'))
        
        # Find invitation
        invitation = Invitation.query.filter_by(code=invitation_code).first()
        
        if not invitation or not invitation.is_valid:
            flash('Invalid or expired invitation code.', 'error')
            return redirect(url_for('main.join_band'))
        
        # Check if user is already a member
        if current_user.is_member_of(invitation.band_id):
            flash('You are already a member of this band.', 'info')
            return redirect(url_for('main.dashboard'))
        
        try:
            # Add user to band
            band = Band.query.get(invitation.band_id)
            band.add_member(current_user, UserRole.MEMBER)
            
            # Mark invitation as accepted
            invitation.status = InvitationStatus.ACCEPTED
            db.session.commit()
            
            # Set as current band
            session['current_band_id'] = band.id
            
            flash(f'Welcome to "{band.name}"!', 'success')
            return redirect(url_for('main.dashboard'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error joining band: {e}")
            flash('Failed to join band. Please try again.', 'error')
            return redirect(url_for('main.join_band'))
    
    return render_template('join_band.html')
