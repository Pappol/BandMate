#!/usr/bin/env python3
"""
Database Relationship Tests for BandMate
Tests complex relationships, cascading operations, and data consistency
"""

import pytest
import os
from datetime import datetime, timedelta
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app import create_app, db
from app.models import (
    User, Band, Song, SongProgress, Vote, Invitation, SetlistConfig,
    SongStatus, ProgressStatus, InvitationStatus, UserRole
)


@pytest.fixture
def app():
    """Create test application with PostgreSQL database"""
    os.environ['FLASK_ENV'] = 'testing'
    os.environ['DATABASE_URL'] = 'postgresql://test_user:test_pass@localhost:5432/bandmate_test'
    
    app = create_app('testing')
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def complex_band_setup(app):
    """Create a complex band setup with multiple relationships"""
    with app.app_context():
        # Create bands
        bands = []
        band_data = [
            {"name": "Thunder Road", "emoji": "⚡", "color": "#FF6B6B", "letter": "T"},
            {"name": "Neon Dreams", "emoji": "🌃", "color": "#9B59B6", "letter": "N"},
            {"name": "Acoustic Souls", "emoji": "🎵", "color": "#2ECC71", "letter": "A"}
        ]
        
        for data in band_data:
            band = Band(
                name=data['name'],
                emoji=data['emoji'],
                color=data['color'],
                letter=data['letter'],
                allow_member_invites=True
            )
            db.session.add(band)
            bands.append(band)
        
        db.session.commit()
        
        # Create users with multi-band memberships
        users = []
        user_data = [
            {
                "name": "Sarah Mitchell", "email": "sarah@test.com",
                "bands": [("Thunder Road", "leader"), ("Neon Dreams", "member")]
            },
            {
                "name": "Marcus Johnson", "email": "marcus@test.com",
                "bands": [("Thunder Road", "member"), ("Acoustic Souls", "leader")]
            },
            {
                "name": "Elena Rodriguez", "email": "elena@test.com",
                "bands": [("Neon Dreams", "leader"), ("Acoustic Souls", "member")]
            },
            {
                "name": "David Chen", "email": "david@test.com",
                "bands": [("Thunder Road", "member")]
            }
        ]
        
        for data in user_data:
            user = User(
                id=f"rel_test_{data['email']}",
                name=data['name'],
                email=data['email']
            )
            db.session.add(user)
            users.append(user)
        
        db.session.commit()
        
        # Create band memberships
        for user_data_item in user_data:
            user = next(u for u in users if u.email == user_data_item['email'])
            for band_name, role_name in user_data_item['bands']:
                band = next(b for b in bands if b.name == band_name)
                role = UserRole.LEADER if role_name == "leader" else UserRole.MEMBER
                band.add_member(user, role)
        
        # Create songs for each band
        songs = []
        song_data = [
            # Thunder Road songs
            {"band": "Thunder Road", "title": "Bohemian Rhapsody", "artist": "Queen", "status": SongStatus.ACTIVE, "duration": 355},
            {"band": "Thunder Road", "title": "Hotel California", "artist": "Eagles", "status": SongStatus.ACTIVE, "duration": 391},
            {"band": "Thunder Road", "title": "Don't Stop Believin'", "artist": "Journey", "status": SongStatus.WISHLIST, "duration": 251},
            
            # Neon Dreams songs
            {"band": "Neon Dreams", "title": "Digital Dreams", "artist": "Neon Dreams", "status": SongStatus.ACTIVE, "duration": 245},
            {"band": "Neon Dreams", "title": "Synthetic Love", "artist": "Neon Dreams", "status": SongStatus.WISHLIST, "duration": 198},
            
            # Acoustic Souls songs
            {"band": "Acoustic Souls", "title": "Hallelujah", "artist": "Leonard Cohen", "status": SongStatus.ACTIVE, "duration": 272},
            {"band": "Acoustic Souls", "title": "The Sound of Silence", "artist": "Simon & Garfunkel", "status": SongStatus.WISHLIST, "duration": 199}
        ]
        
        for data in song_data:
            band = next(b for b in bands if b.name == data['band'])
            song = Song(
                title=data['title'],
                artist=data['artist'],
                status=data['status'],
                duration_seconds=data['duration'],
                band_id=band.id
            )
            db.session.add(song)
            songs.append(song)
        
        db.session.commit()
        
        return {
            'bands': bands,
            'users': users,
            'songs': songs
        }


class TestMultiBandRelationships:
    """Test complex multi-band relationships"""
    
    def test_user_primary_band_logic(self, app, complex_band_setup):
        """Test user primary band determination logic"""
        with app.app_context():
            users = complex_band_setup['users']
            bands = complex_band_setup['bands']
            
            # Test primary band logic
            sarah = next(u for u in users if u.name == "Sarah Mitchell")
            primary_band = sarah.get_primary_band()
            
            # Primary band should be the first band they joined
            assert primary_band is not None
            assert primary_band.name in ["Thunder Road", "Neon Dreams"]
    
    def test_cross_band_song_access(self, app, complex_band_setup):
        """Test that users can only access songs from their bands"""
        with app.app_context():
            users = complex_band_setup['users']
            songs = complex_band_setup['songs']
            
            sarah = next(u for u in users if u.name == "Sarah Mitchell")
            david = next(u for u in users if u.name == "David Chen")
            
            # Sarah is in Thunder Road and Neon Dreams
            thunder_songs = [s for s in songs if s.band.name == "Thunder Road"]
            neon_songs = [s for s in songs if s.band.name == "Neon Dreams"]
            acoustic_songs = [s for s in songs if s.band.name == "Acoustic Souls"]
            
            # Sarah should be able to access Thunder Road and Neon Dreams songs
            for song in thunder_songs + neon_songs:
                assert sarah.is_member_of(song.band_id)
            
            # Sarah should not be able to access Acoustic Souls songs
            for song in acoustic_songs:
                assert not sarah.is_member_of(song.band_id)
            
            # David is only in Thunder Road
            for song in thunder_songs:
                assert david.is_member_of(song.band_id)
            
            for song in neon_songs + acoustic_songs:
                assert not david.is_member_of(song.band_id)
    
    def test_band_leader_permissions(self, app, complex_band_setup):
        """Test band leader permissions across multiple bands"""
        with app.app_context():
            users = complex_band_setup['users']
            bands = complex_band_setup['bands']
            
            sarah = next(u for u in users if u.name == "Sarah Mitchell")
            marcus = next(u for u in users if u.name == "Marcus Johnson")
            
            thunder_road = next(b for b in bands if b.name == "Thunder Road")
            neon_dreams = next(b for b in bands if b.name == "Neon Dreams")
            acoustic_souls = next(b for b in bands if b.name == "Acoustic Souls")
            
            # Sarah is leader of Thunder Road, member of Neon Dreams
            assert sarah.is_leader_of(thunder_road.id)
            assert not sarah.is_leader_of(neon_dreams.id)
            assert not sarah.is_leader_of(acoustic_souls.id)
            
            # Marcus is member of Thunder Road, leader of Acoustic Souls
            assert not marcus.is_leader_of(thunder_road.id)
            assert not marcus.is_leader_of(neon_dreams.id)
            assert marcus.is_leader_of(acoustic_souls.id)
    
    def test_band_invitation_cross_band(self, app, complex_band_setup):
        """Test band invitations across different bands"""
        with app.app_context():
            users = complex_band_setup['users']
            bands = complex_band_setup['bands']
            
            sarah = next(u for u in users if u.name == "Sarah Mitchell")
            marcus = next(u for u in users if u.name == "Marcus Johnson")
            
            thunder_road = next(b for b in bands if b.name == "Thunder Road")
            acoustic_souls = next(b for b in bands if b.name == "Acoustic Souls")
            
            # Sarah can invite to Thunder Road (she's leader) but not Acoustic Souls
            assert thunder_road.can_user_invite(sarah.id)
            assert not acoustic_souls.can_user_invite(sarah.id)
            
            # Marcus can invite to Acoustic Souls (he's leader) but not Thunder Road
            assert not thunder_road.can_user_invite(marcus.id)
            assert acoustic_souls.can_user_invite(marcus.id)


class TestCascadingOperations:
    """Test cascading delete and update operations"""
    
    def test_band_deletion_cascade(self, app, complex_band_setup):
        """Test that deleting a band cascades to all related data"""
        with app.app_context():
            bands = complex_band_setup['bands']
            songs = complex_band_setup['songs']
            
            thunder_road = next(b for b in bands if b.name == "Thunder Road")
            thunder_songs = [s for s in songs if s.band_id == thunder_road.id]
            
            # Create some progress and votes for Thunder Road songs
            sarah = next(u for u in complex_band_setup['users'] if u.name == "Sarah Mitchell")
            for song in thunder_songs:
                if song.status == SongStatus.ACTIVE:
                    progress = SongProgress(
                        user_id=sarah.id,
                        song_id=song.id,
                        status=ProgressStatus.IN_PRACTICE
                    )
                    db.session.add(progress)
                else:
                    vote = Vote(
                        user_id=sarah.id,
                        song_id=song.id
                    )
                    db.session.add(vote)
            
            db.session.commit()
            
            # Store IDs for verification
            song_ids = [s.id for s in thunder_songs]
            progress_ids = [p.id for p in SongProgress.query.filter(SongProgress.song_id.in_(song_ids)).all()]
            vote_ids = [v.id for v in Vote.query.filter(Vote.song_id.in_(song_ids)).all()]
            
            # Delete the band
            db.session.delete(thunder_road)
            db.session.commit()
            
            # Verify all related data is deleted
            for song_id in song_ids:
                assert Song.query.get(song_id) is None
            
            for progress_id in progress_ids:
                assert SongProgress.query.get(progress_id) is None
            
            for vote_id in vote_ids:
                assert Vote.query.get(vote_id) is None
    
    def test_user_deletion_cascade(self, app, complex_band_setup):
        """Test that deleting a user cascades to their progress and votes"""
        with app.app_context():
            users = complex_band_setup['users']
            songs = complex_band_setup['songs']
            
            sarah = next(u for u in users if u.name == "Sarah Mitchell")
            
            # Create progress and votes for Sarah
            for song in songs:
                if sarah.is_member_of(song.band_id):
                    if song.status == SongStatus.ACTIVE:
                        progress = SongProgress(
                            user_id=sarah.id,
                            song_id=song.id,
                            status=ProgressStatus.IN_PRACTICE
                        )
                        db.session.add(progress)
                    else:
                        vote = Vote(
                            user_id=sarah.id,
                            song_id=song.id
                        )
                        db.session.add(vote)
            
            db.session.commit()
            
            # Store IDs for verification
            progress_ids = [p.id for p in SongProgress.query.filter_by(user_id=sarah.id).all()]
            vote_ids = [v.id for v in Vote.query.filter_by(user_id=sarah.id).all()]
            
            # Delete the user
            db.session.delete(sarah)
            db.session.commit()
            
            # Verify all related data is deleted
            for progress_id in progress_ids:
                assert SongProgress.query.get(progress_id) is None
            
            for vote_id in vote_ids:
                assert Vote.query.get(vote_id) is None
    
    def test_song_deletion_cascade(self, app, complex_band_setup):
        """Test that deleting a song cascades to progress and votes"""
        with app.app_context():
            users = complex_band_setup['users']
            songs = complex_band_setup['songs']
            
            # Find a song with progress and votes
            test_song = None
            for song in songs:
                if song.status == SongStatus.ACTIVE:
                    # Create progress for this song
                    sarah = next(u for u in users if u.name == "Sarah Mitchell")
                    if sarah.is_member_of(song.band_id):
                        progress = SongProgress(
                            user_id=sarah.id,
                            song_id=song.id,
                            status=ProgressStatus.IN_PRACTICE
                        )
                        db.session.add(progress)
                        test_song = song
                        break
            
            if test_song:
                # Create votes for wishlist songs
                for song in songs:
                    if song.status == SongStatus.WISHLIST:
                        sarah = next(u for u in users if u.name == "Sarah Mitchell")
                        if sarah.is_member_of(song.band_id):
                            vote = Vote(
                                user_id=sarah.id,
                                song_id=song.id
                            )
                            db.session.add(vote)
                            test_song = song
                            break
                
                db.session.commit()
                
                # Store IDs for verification
                progress_ids = [p.id for p in SongProgress.query.filter_by(song_id=test_song.id).all()]
                vote_ids = [v.id for v in Vote.query.filter_by(song_id=test_song.id).all()]
                
                # Delete the song
                db.session.delete(test_song)
                db.session.commit()
                
                # Verify all related data is deleted
                for progress_id in progress_ids:
                    assert SongProgress.query.get(progress_id) is None
                
                for vote_id in vote_ids:
                    assert Vote.query.get(vote_id) is None


class TestDataConsistency:
    """Test data consistency and integrity constraints"""
    
    def test_band_membership_consistency(self, app, complex_band_setup):
        """Test that band membership data remains consistent"""
        with app.app_context():
            users = complex_band_setup['users']
            bands = complex_band_setup['bands']
            
            # Test that user.is_member_of() matches actual database state
            for user in users:
                for band in bands:
                    # Check through relationship
                    is_member_through_relationship = band in user.bands
                    
                    # Check through direct query
                    is_member_direct = user.is_member_of(band.id)
                    
                    # Both should match
                    assert is_member_through_relationship == is_member_direct
    
    def test_song_band_consistency(self, app, complex_band_setup):
        """Test that song-band relationships remain consistent"""
        with app.app_context():
            songs = complex_band_setup['songs']
            bands = complex_band_setup['bands']
            
            for song in songs:
                # Check that song.band matches the band with song.band_id
                band = next(b for b in bands if b.id == song.band_id)
                assert song.band == band
                
                # Check that song is in the band's songs
                assert song in band.songs
    
    def test_progress_user_song_consistency(self, app, complex_band_setup):
        """Test that progress records maintain consistency with users and songs"""
        with app.app_context():
            users = complex_band_setup['users']
            songs = complex_band_setup['songs']
            
            # Create some progress records
            sarah = next(u for u in users if u.name == "Sarah Mitchell")
            active_songs = [s for s in songs if s.status == SongStatus.ACTIVE and sarah.is_member_of(s.band_id)]
            
            for song in active_songs[:2]:  # Create progress for first 2 songs
                progress = SongProgress(
                    user_id=sarah.id,
                    song_id=song.id,
                    status=ProgressStatus.IN_PRACTICE
                )
                db.session.add(progress)
            
            db.session.commit()
            
            # Verify consistency
            for progress in SongProgress.query.filter_by(user_id=sarah.id).all():
                # Check that progress.user matches the user
                assert progress.user == sarah
                
                # Check that progress.song is in sarah's accessible songs
                assert sarah.is_member_of(progress.song.band_id)
                
                # Check that progress.song matches the song
                song = Song.query.get(progress.song_id)
                assert progress.song == song
    
    def test_vote_consistency(self, app, complex_band_setup):
        """Test that vote records maintain consistency"""
        with app.app_context():
            users = complex_band_setup['users']
            songs = complex_band_setup['songs']
            
            # Create some votes
            sarah = next(u for u in users if u.name == "Sarah Mitchell")
            wishlist_songs = [s for s in songs if s.status == SongStatus.WISHLIST and sarah.is_member_of(s.band_id)]
            
            for song in wishlist_songs[:2]:  # Create votes for first 2 wishlist songs
                vote = Vote(
                    user_id=sarah.id,
                    song_id=song.id
                )
                db.session.add(vote)
            
            db.session.commit()
            
            # Verify consistency
            for vote in Vote.query.filter_by(user_id=sarah.id).all():
                # Check that vote.user matches the user
                assert vote.user == sarah
                
                # Check that vote.song is in sarah's accessible songs
                assert sarah.is_member_of(vote.song.band_id)
                
                # Check that vote.song matches the song
                song = Song.query.get(vote.song_id)
                assert vote.song == song


class TestComplexQueries:
    """Test complex queries involving multiple relationships"""
    
    def test_band_statistics_query(self, app, complex_band_setup):
        """Test complex query for band statistics"""
        with app.app_context():
            bands = complex_band_setup['bands']
            
            # Query: For each band, get member count, active song count, and wishlist song count
            band_stats = []
            for band in bands:
                member_count = len([user for user in complex_band_setup['users'] if user.is_member_of(band.id)])
                active_songs = [song for song in band.songs if song.status == SongStatus.ACTIVE]
                wishlist_songs = [song for song in band.songs if song.status == SongStatus.WISHLIST]
                
                band_stats.append({
                    'band': band.name,
                    'members': member_count,
                    'active_songs': len(active_songs),
                    'wishlist_songs': len(wishlist_songs)
                })
            
            # Verify statistics
            assert len(band_stats) == 3
            
            # Thunder Road should have 2 members (Sarah and David)
            thunder_stats = next(s for s in band_stats if s['band'] == 'Thunder Road')
            assert thunder_stats['members'] == 2
            assert thunder_stats['active_songs'] == 2
            assert thunder_stats['wishlist_songs'] == 1
    
    def test_user_band_activity_query(self, app, complex_band_setup):
        """Test complex query for user activity across bands"""
        with app.app_context():
            users = complex_band_setup['users']
            
            # Query: For each user, get their bands and activity level
            user_activity = []
            for user in users:
                user_bands = [band for band in complex_band_setup['bands'] if user.is_member_of(band.id)]
                is_leader_count = sum(1 for band in user_bands if user.is_leader_of(band.id))
                
                user_activity.append({
                    'user': user.name,
                    'band_count': len(user_bands),
                    'leader_count': is_leader_count,
                    'bands': [band.name for band in user_bands]
                })
            
            # Verify activity data
            assert len(user_activity) == 4
            
            # Sarah should be in 2 bands, leader of 1
            sarah_activity = next(a for a in user_activity if a['user'] == 'Sarah Mitchell')
            assert sarah_activity['band_count'] == 2
            assert sarah_activity['leader_count'] == 1
            assert 'Thunder Road' in sarah_activity['bands']
            assert 'Neon Dreams' in sarah_activity['bands']
    
    def test_song_readiness_analysis(self, app, complex_band_setup):
        """Test complex query for song readiness analysis"""
        with app.app_context():
            users = complex_band_setup['users']
            songs = complex_band_setup['songs']
            
            # Create progress records for analysis
            sarah = next(u for u in users if u.name == "Sarah Mitchell")
            marcus = next(u for u in users if u.name == "Marcus Johnson")
            
            active_songs = [s for s in songs if s.status == SongStatus.ACTIVE]
            
            for i, song in enumerate(active_songs[:3]):  # Create progress for first 3 active songs
                if sarah.is_member_of(song.band_id):
                    progress = SongProgress(
                        user_id=sarah.id,
                        song_id=song.id,
                        status=ProgressStatus.MASTERED if i == 0 else ProgressStatus.IN_PRACTICE
                    )
                    db.session.add(progress)
                
                if marcus.is_member_of(song.band_id):
                    progress = SongProgress(
                        user_id=marcus.id,
                        song_id=song.id,
                        status=ProgressStatus.READY_FOR_REHEARSAL if i == 0 else ProgressStatus.TO_LISTEN
                    )
                    db.session.add(progress)
            
            db.session.commit()
            
            # Analyze song readiness
            readiness_analysis = []
            for song in active_songs:
                progress_records = SongProgress.query.filter_by(song_id=song.id).all()
                if progress_records:
                    readiness_score = song.readiness_score
                    member_count = len(progress_records)
                    
                    readiness_analysis.append({
                        'song': song.title,
                        'band': song.band.name,
                        'readiness_score': readiness_score,
                        'member_count': member_count
                    })
            
            # Verify analysis
            assert len(readiness_analysis) > 0
            
            # Check that readiness scores are calculated correctly
            for analysis in readiness_analysis:
                assert 0 <= analysis['readiness_score'] <= 4  # Score should be between 0 and 4
                assert analysis['member_count'] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
