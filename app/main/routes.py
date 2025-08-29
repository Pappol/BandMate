from flask import render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import current_user, login_user, logout_user
from flask_dance.contrib.google import google
from app.main import main
from app.auth import login_required, band_leader_required, handle_google_login, logout
from app.models import User, Band, Song, SongProgress, Vote, SongStatus, ProgressStatus
from app import db
from datetime import datetime, date
import json

@main.route('/')
def index():
    """Home page - redirect to dashboard if logged in, otherwise show login"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('login.html', config=current_app.config)

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
    return handle_google_login()

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
        
        if not title or not artist:
            flash('Title and artist are required.', 'error')
            return redirect(url_for('main.wishlist'))
        
        # Create new song
        song = Song(
            title=title,
            artist=artist,
            status=SongStatus.WISHLIST,
            band_id=current_user.band_id
        )
        db.session.add(song)
        db.session.commit()
        
        flash(f'Song "{title}" by {artist} has been added to the wishlist!', 'success')
        return redirect(url_for('main.wishlist'))
    
    return render_template('propose_song.html')

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
            # Check if all members have mastered the song
            all_mastered = True
            for member in current_user.band.members:
                progress = SongProgress.query.filter_by(
                    user_id=member.id,
                    song_id=song.id
                ).first()
                if not progress or progress.status != ProgressStatus.MASTERED:
                    all_mastered = False
                    break
            
            if all_mastered:
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
