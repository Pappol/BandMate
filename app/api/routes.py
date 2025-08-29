from flask import jsonify, request
from flask_login import current_user, login_required
from app.api import api
from app.auth import band_leader_required
from app.models import Song, SongProgress, Vote, SongStatus, ProgressStatus
from app import db
from datetime import datetime

@api.route('/progress', methods=['POST'])
@login_required
def update_progress():
    """Update song progress for current user"""
    try:
        data = request.get_json()
        song_id = data.get('song_id')
        status = data.get('status')
        
        if not song_id or not status:
            return jsonify({'error': 'Missing song_id or status'}), 400
        
        # Validate status
        try:
            progress_status = ProgressStatus(status)
        except ValueError:
            return jsonify({'error': 'Invalid status'}), 400
        
        # Check if song exists and user has access
        song = Song.query.filter_by(
            id=song_id,
            band_id=current_user.band_id
        ).first()
        
        if not song:
            return jsonify({'error': 'Song not found'}), 404
        
        # Update or create progress
        progress = SongProgress.query.filter_by(
            user_id=current_user.id,
            song_id=song_id
        ).first()
        
        if progress:
            progress.status = progress_status
            progress.updated_at = datetime.utcnow()
        else:
            progress = SongProgress(
                user_id=current_user.id,
                song_id=song_id,
                status=progress_status
            )
            db.session.add(progress)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Progress updated to {status}',
            'progress': {
                'status': status,
                'updated_at': progress.updated_at.isoformat()
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api.route('/wishlist/vote', methods=['POST'])
@login_required
def toggle_vote():
    """Toggle vote on wishlist song"""
    try:
        data = request.get_json()
        song_id = data.get('song_id')
        
        if not song_id:
            return jsonify({'error': 'Missing song_id'}), 400
        
        # Check if song exists and is in wishlist
        song = Song.query.filter_by(
            id=song_id,
            band_id=current_user.band_id,
            status=SongStatus.WISHLIST
        ).first()
        
        if not song:
            return jsonify({'error': 'Song not found or not in wishlist'}), 404
        
        # Check if user already voted
        existing_vote = Vote.query.filter_by(
            user_id=current_user.id,
            song_id=song_id
        ).first()
        
        if existing_vote:
            # Remove vote
            db.session.delete(existing_vote)
            action = 'removed'
        else:
            # Add vote
            vote = Vote(
                user_id=current_user.id,
                song_id=song_id
            )
            db.session.add(vote)
            action = 'added'
        
        db.session.commit()
        
        # Get updated vote count
        vote_count = Vote.query.filter_by(song_id=song_id).count()
        
        return jsonify({
            'success': True,
            'message': f'Vote {action}',
            'vote_count': vote_count,
            'user_voted': action == 'added'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api.route('/wishlist/approve', methods=['POST'])
@band_leader_required
def approve_song():
    """Approve song from wishlist to active (band leader only)"""
    try:
        data = request.get_json()
        song_id = data.get('song_id')
        
        if not song_id:
            return jsonify({'error': 'Missing song_id'}), 400
        
        # Check if song exists and is in wishlist
        song = Song.query.filter_by(
            id=song_id,
            band_id=current_user.band_id,
            status=SongStatus.WISHLIST
        ).first()
        
        if not song:
            return jsonify({'error': 'Song not found or not in wishlist'}), 404
        
        # Move song to active
        song.status = SongStatus.ACTIVE
        
        # Create progress records for all band members
        for member in current_user.band.members:
            progress = SongProgress(
                user_id=member.id,
                song_id=song_id,
                status=ProgressStatus.TO_LISTEN
            )
            db.session.add(progress)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Song "{song.title}" approved and moved to active repertoire'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api.route('/songs/<int:song_id>/rehearsed', methods=['POST'])
@login_required
def mark_rehearsed():
    """Mark song as rehearsed today"""
    try:
        song = Song.query.filter_by(
            id=song_id,
            band_id=current_user.band_id
        ).first()
        
        if not song:
            return jsonify({'error': 'Song not found'}), 404
        
        song.last_rehearsed_on = datetime.utcnow().date()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Song "{song.title}" marked as rehearsed today',
            'last_rehearsed': song.last_rehearsed_on.isoformat()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
