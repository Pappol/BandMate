from flask import render_template, redirect, url_for, flash, request, jsonify, current_app, session
from flask_login import current_user, login_user, logout_user
from flask_dance.contrib.google import google
from app.main import main
from app.auth import login_required, band_leader_required, handle_google_login, logout
from app.models import User, Band, Song, SongProgress, Vote, SongStatus, ProgressStatus, Invitation, InvitationStatus
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
        flash(f'Demo login successful! Welcome back, {user.name}!', 'success')
        return redirect(url_for('main.dashboard'))
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
            flash(f'Welcome back, {user.name}!', 'success')
            return redirect(url_for('main.dashboard'))
            
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
        return redirect(url_for('main.dashboard'))
    
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
            email=google_user_info['email'],
            band_id=band.id,
            is_band_leader=True  # Creator becomes leader
        )
        db.session.add(user)
        db.session.commit()
        
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
def join_band():
    """Join an existing band"""
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
            email=google_user_info['email'],
            band_id=demo_band.id,
            is_band_leader=False
        )
        db.session.add(user)
        db.session.commit()
        
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
    # Get active songs for the user's band
    active_songs = Song.query.filter_by(
        band_id=current_user.band_id,
        status=SongStatus.ACTIVE
    ).all()
    
    # Get all band members
    band_members = User.query.filter_by(band_id=current_user.band_id).all()
    
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
    wishlist_songs = Song.query.filter_by(
        band_id=current_user.band_id,
        status=SongStatus.WISHLIST
    ).all()
    
    # Get vote counts for each song
    for song in wishlist_songs:
        song.vote_count = Vote.query.filter_by(song_id=song.id).count()
        song.user_voted = Vote.query.filter_by(
            song_id=song.id,
            user_id=current_user.id
        ).first() is not None
    
    return render_template('wishlist.html', songs=wishlist_songs)

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
        duration_minutes = request.form.get('duration_minutes', '')
        
        if not title or not artist:
            flash('Title and artist are required.', 'error')
            return redirect(url_for('main.wishlist'))
        
        # Create new song
        song = Song(
            title=title,
            artist=artist,
            status=SongStatus.WISHLIST,
            band_id=current_user.band_id,
            spotify_track_id=spotify_track_id if spotify_track_id else None,
            album_art_url=album_art_url if album_art_url else None,
            duration_minutes=float(duration_minutes) if duration_minutes and duration_minutes.replace('.', '').isdigit() else None
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
        
        # Calculate time allocation
        time_learning = round(duration_total * learning_ratio)
        time_maintenance = duration_total - time_learning
        
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
            if song.duration_minutes and learning_time + song.duration_minutes <= time_learning:
                learning_setlist.append({
                    'title': song.title,
                    'artist': song.artist,
                    'duration_minutes': song.duration_minutes,
                    'block': 'learning',
                    'readiness_score': round(song.readiness_score, 2)
                })
                learning_time += song.duration_minutes
        
        # Build maintenance setlist
        maintenance_setlist = []
        maintenance_time = 0
        
        for song in maintenance_pool:
            if song.duration_minutes and maintenance_time + song.duration_minutes <= time_maintenance:
                maintenance_setlist.append({
                    'title': song.title,
                    'artist': song.artist,
                    'duration_minutes': song.duration_minutes,
                    'block': 'maintenance',
                    'last_rehearsed': song.last_rehearsed_on.isoformat() if song.last_rehearsed_on else 'Never'
                })
                maintenance_time += song.duration_minutes
        
        # Combine setlists
        full_setlist = learning_setlist + maintenance_setlist
        
        # Add break if total time > 90 minutes
        break_info = None
        if duration_total > 90:
            break_info = {
                'position': 'mid-session',
                'duration': 10,
                'description': '10-minute break'
            }
        
        # Calculate cumulative times
        cumulative_time = 0
        for item in full_setlist:
            cumulative_time += item['duration_minutes']
            item['cumulative_time'] = cumulative_time
        
        result = {
            'setlist': full_setlist,
            'summary': {
                'total_duration': duration_total,
                'learning_time': learning_time,
                'maintenance_time': maintenance_time,
                'learning_ratio': learning_ratio,
                'break_info': break_info
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
def create_new_band():
    """Create a new band and leave the current one"""
    band_name = request.form.get('band_name')
    if not band_name:
        flash('Band name is required.', 'error')
        return redirect(url_for('main.start_fresh'))
    
    try:
        # Leave current band
        if current_user.band:
            # Remove user from current band
            current_user.band_id = None
            db.session.commit()
        
        # Create new band
        new_band = Band(
            name=band_name,
            created_by=current_user.id
        )
        db.session.add(new_band)
        db.session.flush()  # Get the ID
        
        # Add user to new band as leader
        current_user.band_id = new_band.id
        current_user.is_band_leader = True
        
        db.session.commit()
        
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
        # Find band by invitation code
        band = Band.query.filter_by(invitation_code=invitation_code).first()
        if not band:
            flash('Invalid invitation code. Please check and try again.', 'error')
            return redirect(url_for('main.start_fresh'))
        
        # Leave current band
        if current_user.band:
            current_user.band_id = None
            db.session.commit()
        
        # Join new band
        current_user.band_id = band.id
        current_user.is_band_leader = False  # Reset band leader status
        
        db.session.commit()
        
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
            flash(f'Welcome back, {user.name}!', 'success')
            return redirect(url_for('main.dashboard'))
            
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
    # Get pending invitations for the band
    pending_invitations = []
    if current_user.is_band_leader:
        pending_invitations = Invitation.query.filter_by(
            band_id=current_user.band_id,
            status=InvitationStatus.PENDING
        ).all()
    
    return render_template('band_management.html', pending_invitations=pending_invitations)

@main.route('/band/invite', methods=['POST'])
@login_required
def invite_member():
    """Invite a new member to the band"""
    if not current_user.is_band_leader:
        flash('Only band leaders can invite new members.', 'error')
        return redirect(url_for('main.band_management'))
    
    email = request.form.get('email')
    message = request.form.get('message', '')
    
    if not email:
        flash('Email address is required.', 'error')
        return redirect(url_for('main.band_management'))
    
    # Check if user already exists in the band
    existing_user = User.query.filter_by(email=email, band_id=current_user.band_id).first()
    if existing_user:
        flash(f'{email} is already a member of your band.', 'error')
        return redirect(url_for('main.band_management'))
    
    # Check if invitation already exists
    existing_invitation = Invitation.query.filter_by(
        invited_email=email,
        band_id=current_user.band_id,
        status=InvitationStatus.PENDING
    ).first()
    
    if existing_invitation:
        flash(f'An invitation has already been sent to {email}.', 'error')
        return redirect(url_for('main.band_management'))
    
    try:
        # Create new invitation
        invitation = Invitation(
            code=Invitation.generate_code(),
            band_id=current_user.band_id,
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
    if not current_user.is_band_leader:
        return jsonify({'error': 'Unauthorized'}), 403
    
    invitation = Invitation.query.get_or_404(invitation_id)
    
    if invitation.band_id != current_user.band_id:
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
    if not current_user.is_band_leader:
        return jsonify({'error': 'Unauthorized'}), 403
    
    invitation = Invitation.query.get_or_404(invitation_id)
    
    if invitation.band_id != current_user.band_id:
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
    if not current_user.is_band_leader:
        flash('Only band leaders can remove members.', 'error')
        return redirect(url_for('main.band_management'))
    
    if member_id == current_user.id:
        flash('You cannot remove yourself from the band.', 'error')
        return redirect(url_for('main.band_management'))
    
    member = User.query.get_or_404(member_id)
    
    if member.band_id != current_user.band_id:
        flash('Member not found in your band.', 'error')
        return redirect(url_for('main.band_management'))
    
    if member.is_band_leader:
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
