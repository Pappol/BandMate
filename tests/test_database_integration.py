#!/usr/bin/env python3
"""
Comprehensive Database Integration Tests for BandMate
Tests all database models, relationships, and complex queries
"""

import pytest
import os
from datetime import datetime, date, timedelta
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
    # Use test configuration
    os.environ['FLASK_ENV'] = 'testing'
    os.environ['DATABASE_URL'] = 'postgresql://test_user:test_pass@localhost:5432/bandmate_test'
    
    app = create_app('testing')
    
    with app.app_context():
        # Create all tables
        db.create_all()
        yield app
        # Clean up
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Test client"""
    return app.test_client()


@pytest.fixture
def sample_bands(app):
    """Create sample bands for testing"""
    with app.app_context():
        bands = []
        
        # Create Thunder Road band
        thunder_road = Band(
            name="Thunder Road",
            emoji="⚡",
            color="#FF6B6B",
            letter="T",
            allow_member_invites=True
        )
        db.session.add(thunder_road)
        
        # Create Neon Dreams band
        neon_dreams = Band(
            name="Neon Dreams",
            emoji="🌃",
            color="#9B59B6",
            letter="N",
            allow_member_invites=False
        )
        db.session.add(neon_dreams)
        
        db.session.commit()
        bands.extend([thunder_road, neon_dreams])
        
        return bands


@pytest.fixture
def sample_users(app):
    """Create sample users for testing"""
    with app.app_context():
        users = []
        
        # Create test users
        user_data = [
            {"name": "Sarah Mitchell", "email": "sarah@test.com", "instrument": "Lead Vocals"},
            {"name": "Marcus Johnson", "email": "marcus@test.com", "instrument": "Lead Guitar"},
            {"name": "Elena Rodriguez", "email": "elena@test.com", "instrument": "Bass Guitar"},
            {"name": "David Chen", "email": "david@test.com", "instrument": "Drums"}
        ]
        
        for data in user_data:
            user = User(
                id=f"test_{data['email']}",
                name=data['name'],
                email=data['email']
            )
            db.session.add(user)
            users.append(user)
        
        db.session.commit()
        return users


@pytest.fixture
def sample_songs(app, sample_bands):
    """Create sample songs for testing"""
    with app.app_context():
        songs = []
        
        # Songs for Thunder Road
        thunder_road = sample_bands[0]
        thunder_songs = [
            {"title": "Bohemian Rhapsody", "artist": "Queen", "status": SongStatus.ACTIVE, "duration_seconds": 355},
            {"title": "Hotel California", "artist": "Eagles", "status": SongStatus.ACTIVE, "duration_seconds": 391},
            {"title": "Don't Stop Believin'", "artist": "Journey", "status": SongStatus.WISHLIST, "duration_seconds": 251}
        ]
        
        for song_data in thunder_songs:
            song = Song(
                title=song_data['title'],
                artist=song_data['artist'],
                status=song_data['status'],
                duration_seconds=song_data['duration_seconds'],
                band_id=thunder_road.id
            )
            db.session.add(song)
            songs.append(song)
        
        # Songs for Neon Dreams
        neon_dreams = sample_bands[1]
        neon_songs = [
            {"title": "Digital Dreams", "artist": "Neon Dreams", "status": SongStatus.ACTIVE, "duration_seconds": 245},
            {"title": "Synthetic Love", "artist": "Neon Dreams", "status": SongStatus.WISHLIST, "duration_seconds": 198}
        ]
        
        for song_data in neon_songs:
            song = Song(
                title=song_data['title'],
                artist=song_data['artist'],
                status=song_data['status'],
                duration_seconds=song_data['duration_seconds'],
                band_id=neon_dreams.id
            )
            db.session.add(song)
            songs.append(song)
        
        db.session.commit()
        return songs


class TestUserBandRelationships:
    """Test multi-band user relationships and role management"""
    
    def test_user_can_join_multiple_bands(self, app, sample_users, sample_bands):
        """Test that users can be members of multiple bands with different roles"""
        with app.app_context():
            user = sample_users[0]  # Sarah
            thunder_road = sample_bands[0]
            neon_dreams = sample_bands[1]
            
            # Add user to Thunder Road as leader
            thunder_road.add_member(user, UserRole.LEADER)
            
            # Add user to Neon Dreams as member
            neon_dreams.add_member(user, UserRole.MEMBER)
            
            # Verify memberships
            assert user.is_member_of(thunder_road.id)
            assert user.is_member_of(neon_dreams.id)
            assert user.is_leader_of(thunder_road.id)
            assert not user.is_leader_of(neon_dreams.id)
            
            # Verify roles
            assert user.get_band_role(thunder_road.id) == UserRole.LEADER.value
            assert user.get_band_role(neon_dreams.id) == UserRole.MEMBER.value
    
    def test_band_member_management(self, app, sample_users, sample_bands):
        """Test adding, removing, and updating band members"""
        with app.app_context():
            user = sample_users[0]
            band = sample_bands[0]
            
            # Add member
            success = band.add_member(user, UserRole.MEMBER)
            assert success
            assert user.is_member_of(band.id)
            
            # Try to add same member again (should fail)
            success = band.add_member(user, UserRole.MEMBER)
            assert not success
            
            # Update role
            band.update_member_role(user.id, UserRole.LEADER)
            assert user.get_band_role(band.id) == UserRole.LEADER.value
            
            # Remove member
            band.remove_member(user.id)
            assert not user.is_member_of(band.id)
    
    def test_band_invitation_permissions(self, app, sample_users, sample_bands):
        """Test band invitation permissions based on settings and roles"""
        with app.app_context():
            leader = sample_users[0]
            member = sample_users[1]
            band = sample_bands[0]  # Thunder Road (allows member invites)
            restricted_band = sample_bands[1]  # Neon Dreams (restricts member invites)
            
            # Add users to bands
            band.add_member(leader, UserRole.LEADER)
            band.add_member(member, UserRole.MEMBER)
            restricted_band.add_member(leader, UserRole.LEADER)
            restricted_band.add_member(member, UserRole.MEMBER)
            
            # Test invitation permissions
            assert band.can_user_invite(leader.id)  # Leader can always invite
            assert band.can_user_invite(member.id)  # Member can invite (setting enabled)
            assert restricted_band.can_user_invite(leader.id)  # Leader can always invite
            assert not restricted_band.can_user_invite(member.id)  # Member cannot invite (setting disabled)


class TestSongManagement:
    """Test song creation, status changes, and progress tracking"""
    
    def test_song_creation_and_status_changes(self, app, sample_bands):
        """Test creating songs and changing their status"""
        with app.app_context():
            band = sample_bands[0]
            
            # Create song
            song = Song(
                title="Test Song",
                artist="Test Artist",
                status=SongStatus.WISHLIST,
                duration_seconds=240,
                band_id=band.id
            )
            db.session.add(song)
            db.session.commit()
            
            # Verify creation
            assert song.id is not None
            assert song.status == SongStatus.WISHLIST
            assert song.band_id == band.id
            
            # Change status
            song.status = SongStatus.ACTIVE
            db.session.commit()
            
            # Verify status change
            updated_song = Song.query.get(song.id)
            assert updated_song.status == SongStatus.ACTIVE
    
    def test_song_progress_tracking(self, app, sample_users, sample_songs):
        """Test individual member progress on songs"""
        with app.app_context():
            user = sample_users[0]
            active_song = next(song for song in sample_songs if song.status == SongStatus.ACTIVE)
            
            # Create progress record
            progress = SongProgress(
                user_id=user.id,
                song_id=active_song.id,
                status=ProgressStatus.TO_LISTEN
            )
            db.session.add(progress)
            db.session.commit()
            
            # Verify progress creation
            assert progress.id is not None
            assert progress.status == ProgressStatus.TO_LISTEN
            
            # Update progress
            progress.status = ProgressStatus.IN_PRACTICE
            progress.updated_at = datetime.utcnow()
            db.session.commit()
            
            # Verify progress update
            updated_progress = SongProgress.query.get(progress.id)
            assert updated_progress.status == ProgressStatus.IN_PRACTICE
    
    def test_song_readiness_score_calculation(self, app, sample_users, sample_songs):
        """Test song readiness score calculation based on member progress"""
        with app.app_context():
            active_song = next(song for song in sample_songs if song.status == SongStatus.ACTIVE)
            
            # Create progress records for different users
            users = sample_users[:3]
            statuses = [ProgressStatus.MASTERED, ProgressStatus.READY_FOR_REHEARSAL, ProgressStatus.IN_PRACTICE]
            
            for user, status in zip(users, statuses):
                progress = SongProgress(
                    user_id=user.id,
                    song_id=active_song.id,
                    status=status
                )
                db.session.add(progress)
            
            db.session.commit()
            
            # Calculate readiness score
            score = active_song.readiness_score
            
            # Expected score: (4 + 3 + 2) / 3 = 3.0
            expected_score = (4 + 3 + 2) / 3
            assert abs(score - expected_score) < 0.01
    
    def test_song_unique_constraints(self, app, sample_users, sample_songs):
        """Test that users can only have one progress record per song"""
        with app.app_context():
            user = sample_users[0]
            song = sample_songs[0]
            
            # Create first progress record
            progress1 = SongProgress(
                user_id=user.id,
                song_id=song.id,
                status=ProgressStatus.TO_LISTEN
            )
            db.session.add(progress1)
            db.session.commit()
            
            # Try to create duplicate progress record
            progress2 = SongProgress(
                user_id=user.id,
                song_id=song.id,
                status=ProgressStatus.IN_PRACTICE
            )
            db.session.add(progress2)
            
            # Should raise IntegrityError due to unique constraint
            with pytest.raises(IntegrityError):
                db.session.commit()


class TestVotingSystem:
    """Test voting system and vote counting functionality"""
    
    def test_vote_creation_and_counting(self, app, sample_users, sample_songs):
        """Test creating votes and counting them"""
        with app.app_context():
            users = sample_users[:3]
            wishlist_song = next(song for song in sample_songs if song.status == SongStatus.WISHLIST)
            
            # Create votes
            for user in users:
                vote = Vote(
                    user_id=user.id,
                    song_id=wishlist_song.id
                )
                db.session.add(vote)
            
            db.session.commit()
            
            # Verify vote count
            vote_count = Vote.query.filter_by(song_id=wishlist_song.id).count()
            assert vote_count == 3
            
            # Verify vote relationships
            song_votes = wishlist_song.votes
            assert len(song_votes) == 3
            
            for vote in song_votes:
                assert vote.user in users
                assert vote.song == wishlist_song
    
    def test_vote_unique_constraints(self, app, sample_users, sample_songs):
        """Test that users can only vote once per song"""
        with app.app_context():
            user = sample_users[0]
            song = sample_songs[0]
            
            # Create first vote
            vote1 = Vote(
                user_id=user.id,
                song_id=song.id
            )
            db.session.add(vote1)
            db.session.commit()
            
            # Try to create duplicate vote
            vote2 = Vote(
                user_id=user.id,
                song_id=song.id
            )
            db.session.add(vote2)
            
            # Should raise IntegrityError due to unique constraint
            with pytest.raises(IntegrityError):
                db.session.commit()
    
    def test_vote_cascade_delete(self, app, sample_users, sample_songs):
        """Test that votes are deleted when user or song is deleted"""
        with app.app_context():
            user = sample_users[0]
            song = sample_songs[0]
            
            # Create vote
            vote = Vote(
                user_id=user.id,
                song_id=song.id
            )
            db.session.add(vote)
            db.session.commit()
            
            vote_id = vote.id
            
            # Delete user
            db.session.delete(user)
            db.session.commit()
            
            # Verify vote is deleted
            deleted_vote = Vote.query.get(vote_id)
            assert deleted_vote is None


class TestInvitationSystem:
    """Test band invitation creation, validation, and expiration"""
    
    def test_invitation_creation_and_validation(self, app, sample_users, sample_bands):
        """Test creating and validating invitations"""
        with app.app_context():
            inviter = sample_users[0]
            band = sample_bands[0]
            
            # Create invitation
            invitation = Invitation(
                code=Invitation.generate_code(),
                band_id=band.id,
                invited_by=inviter.id,
                invited_email="newuser@test.com",
                expires_at=datetime.utcnow() + timedelta(days=7)
            )
            db.session.add(invitation)
            db.session.commit()
            
            # Verify invitation properties
            assert invitation.code is not None
            assert len(invitation.code) == 8
            assert invitation.status == InvitationStatus.PENDING
            assert invitation.is_valid
            assert not invitation.is_expired
    
    def test_invitation_expiration(self, app, sample_users, sample_bands):
        """Test invitation expiration logic"""
        with app.app_context():
            inviter = sample_users[0]
            band = sample_bands[0]
            
            # Create expired invitation
            invitation = Invitation(
                code=Invitation.generate_code(),
                band_id=band.id,
                invited_by=inviter.id,
                invited_email="expired@test.com",
                expires_at=datetime.utcnow() - timedelta(days=1)  # Expired yesterday
            )
            db.session.add(invitation)
            db.session.commit()
            
            # Verify expiration
            assert invitation.is_expired
            assert not invitation.is_valid
    
    def test_invitation_code_uniqueness(self, app, sample_users, sample_bands):
        """Test that invitation codes are unique"""
        with app.app_context():
            inviter = sample_users[0]
            band = sample_bands[0]
            
            # Create multiple invitations
            codes = set()
            for i in range(10):
                invitation = Invitation(
                    code=Invitation.generate_code(),
                    band_id=band.id,
                    invited_by=inviter.id,
                    invited_email=f"user{i}@test.com",
                    expires_at=datetime.utcnow() + timedelta(days=7)
                )
                db.session.add(invitation)
                codes.add(invitation.code)
            
            db.session.commit()
            
            # Verify all codes are unique
            assert len(codes) == 10


class TestSetlistConfiguration:
    """Test setlist configuration and generation algorithms"""
    
    def test_setlist_config_creation(self, app, sample_bands):
        """Test creating setlist configurations for bands"""
        with app.app_context():
            band = sample_bands[0]
            
            # Create setlist config
            config = SetlistConfig(
                band_id=band.id,
                new_songs_buffer_percent=25.0,
                learned_songs_buffer_percent=15.0,
                break_time_minutes=15,
                break_threshold_minutes=90,
                min_session_minutes=45,
                max_session_minutes=180,
                time_cluster_minutes=15
            )
            db.session.add(config)
            db.session.commit()
            
            # Verify config creation
            assert config.id is not None
            assert config.band_id == band.id
            assert config.new_songs_buffer_percent == 25.0
    
    def test_setlist_config_default_creation(self, app, sample_bands):
        """Test automatic creation of default setlist config"""
        with app.app_context():
            band = sample_bands[0]
            
            # Get or create config (should create default)
            config = band.get_setlist_config()
            
            # Verify default config
            assert config is not None
            assert config.band_id == band.id
            assert config.new_songs_buffer_percent == 20.0  # Default value
            assert config.learned_songs_buffer_percent == 10.0  # Default value
    
    def test_break_needed_calculation(self, app, sample_bands):
        """Test break needed calculation based on session duration"""
        with app.app_context():
            band = sample_bands[0]
            config = SetlistConfig(
                band_id=band.id,
                break_threshold_minutes=90
            )
            db.session.add(config)
            db.session.commit()
            
            # Test break needed logic
            assert not config.is_break_needed(60)  # Below threshold
            assert not config.is_break_needed(90)  # At threshold
            assert config.is_break_needed(120)  # Above threshold
    
    def test_duration_clustering(self, app, sample_bands):
        """Test duration clustering to nearest interval"""
        with app.app_context():
            band = sample_bands[0]
            config = SetlistConfig(
                band_id=band.id,
                min_session_minutes=30,
                max_session_minutes=180,
                time_cluster_minutes=15
            )
            db.session.add(config)
            db.session.commit()
            
            # Test clustering
            assert config.get_clustered_duration(25) == 30  # Below minimum
            assert config.get_clustered_duration(35) == 30  # Round down to 30
            assert config.get_clustered_duration(40) == 45  # Round up to 45
            assert config.get_clustered_duration(200) == 180  # Above maximum
    
    def test_song_duration_with_buffer(self, app, sample_bands):
        """Test song duration calculation with buffer percentages"""
        with app.app_context():
            band = sample_bands[0]
            config = SetlistConfig(
                band_id=band.id,
                new_songs_buffer_percent=25.0,
                learned_songs_buffer_percent=10.0
            )
            db.session.add(config)
            db.session.commit()
            
            # Test buffer calculations
            song_duration = 240  # 4 minutes
            
            # New song (25% buffer)
            new_song_duration = config.calculate_song_duration_with_buffer(song_duration, False)
            expected_new = 240 * 1.25  # 300 seconds
            assert abs(new_song_duration - expected_new) < 0.01
            
            # Learned song (10% buffer)
            learned_song_duration = config.calculate_song_duration_with_buffer(song_duration, True)
            expected_learned = 240 * 1.10  # 264 seconds
            assert abs(learned_song_duration - expected_learned) < 0.01


class TestDataIntegrity:
    """Test foreign key constraints, cascading deletes, and data consistency"""
    
    def test_band_cascade_delete(self, app, sample_bands, sample_songs):
        """Test that deleting a band cascades to related data"""
        with app.app_context():
            band = sample_bands[0]
            band_id = band.id
            song_ids = [song.id for song in sample_songs if song.band_id == band_id]
            
            # Delete band
            db.session.delete(band)
            db.session.commit()
            
            # Verify songs are deleted
            for song_id in song_ids:
                song = Song.query.get(song_id)
                assert song is None
    
    def test_user_cascade_delete(self, app, sample_users, sample_songs):
        """Test that deleting a user cascades to related data"""
        with app.app_context():
            user = sample_users[0]
            user_id = user.id
            
            # Create progress and vote records
            song = sample_songs[0]
            progress = SongProgress(
                user_id=user_id,
                song_id=song.id,
                status=ProgressStatus.TO_LISTEN
            )
            vote = Vote(
                user_id=user_id,
                song_id=song.id
            )
            db.session.add_all([progress, vote])
            db.session.commit()
            
            progress_id = progress.id
            vote_id = vote.id
            
            # Delete user
            db.session.delete(user)
            db.session.commit()
            
            # Verify related records are deleted
            assert SongProgress.query.get(progress_id) is None
            assert Vote.query.get(vote_id) is None
    
    def test_foreign_key_constraints(self, app, sample_users):
        """Test that foreign key constraints prevent invalid references"""
        with app.app_context():
            user = sample_users[0]
            
            # Try to create song with invalid band_id
            with pytest.raises(IntegrityError):
                song = Song(
                    title="Test Song",
                    artist="Test Artist",
                    status=SongStatus.ACTIVE,
                    duration_seconds=240,
                    band_id=99999  # Non-existent band
                )
                db.session.add(song)
                db.session.commit()
            
            # Try to create progress with invalid user_id
            with pytest.raises(IntegrityError):
                progress = SongProgress(
                    user_id="invalid_user_id",
                    song_id=1,
                    status=ProgressStatus.TO_LISTEN
                )
                db.session.add(progress)
                db.session.commit()


class TestPerformanceQueries:
    """Test complex queries and performance with realistic data volumes"""
    
    def test_band_member_queries(self, app, sample_users, sample_bands):
        """Test queries for band members and their roles"""
        with app.app_context():
            band = sample_bands[0]
            users = sample_users[:3]
            
            # Add users to band with different roles
            band.add_member(users[0], UserRole.LEADER)
            band.add_member(users[1], UserRole.MEMBER)
            band.add_member(users[2], UserRole.MEMBER)
            
            # Test query for all band members
            members = [user for user in User.query.all() if user.is_member_of(band.id)]
            assert len(members) == 3
            
            # Test query for band leaders
            leaders = [user for user in members if user.is_leader_of(band.id)]
            assert len(leaders) == 1
            assert leaders[0] == users[0]
    
    def test_song_progress_aggregation(self, app, sample_users, sample_songs):
        """Test aggregating song progress across multiple users"""
        with app.app_context():
            users = sample_users[:3]
            song = sample_songs[0]
            
            # Create progress records
            statuses = [ProgressStatus.MASTERED, ProgressStatus.READY_FOR_REHEARSAL, ProgressStatus.IN_PRACTICE]
            for user, status in zip(users, statuses):
                progress = SongProgress(
                    user_id=user.id,
                    song_id=song.id,
                    status=status
                )
                db.session.add(progress)
            
            db.session.commit()
            
            # Test progress aggregation
            progress_records = SongProgress.query.filter_by(song_id=song.id).all()
            assert len(progress_records) == 3
            
            # Test status distribution
            status_counts = {}
            for progress in progress_records:
                status = progress.status.value
                status_counts[status] = status_counts.get(status, 0) + 1
            
            assert status_counts['Mastered'] == 1
            assert status_counts['Ready for Rehearsal'] == 1
            assert status_counts['In Practice'] == 1
    
    def test_vote_aggregation(self, app, sample_users, sample_songs):
        """Test vote counting and aggregation"""
        with app.app_context():
            users = sample_users[:3]
            song = sample_songs[0]
            
            # Create votes
            for user in users:
                vote = Vote(
                    user_id=user.id,
                    song_id=song.id
                )
                db.session.add(vote)
            
            db.session.commit()
            
            # Test vote counting
            vote_count = Vote.query.filter_by(song_id=song.id).count()
            assert vote_count == 3
            
            # Test vote aggregation by song
            songs_with_votes = db.session.query(Song, db.func.count(Vote.id).label('vote_count')) \
                .outerjoin(Vote) \
                .group_by(Song.id) \
                .all()
            
            song_vote_count = next((count for song, count in songs_with_votes if song.id == song.id), 0)
            assert song_vote_count == 3
    
    def test_complex_band_queries(self, app, sample_users, sample_bands, sample_songs):
        """Test complex queries involving multiple relationships"""
        with app.app_context():
            # Set up data
            band = sample_bands[0]
            users = sample_users[:2]
            
            # Add users to band
            band.add_member(users[0], UserRole.LEADER)
            band.add_member(users[1], UserRole.MEMBER)
            
            # Create progress for active songs
            active_songs = [song for song in sample_songs if song.band_id == band.id and song.status == SongStatus.ACTIVE]
            for song in active_songs:
                for user in users:
                    progress = SongProgress(
                        user_id=user.id,
                        song_id=song.id,
                        status=ProgressStatus.IN_PRACTICE
                    )
                    db.session.add(progress)
            
            db.session.commit()
            
            # Test complex query: bands with their member count and active song count
            band_stats = db.session.query(
                Band.name,
                db.func.count(db.distinct(db.text('band_membership.user_id'))).label('member_count'),
                db.func.count(db.distinct(Song.id)).label('active_song_count')
            ).outerjoin(db.text('band_membership'), Band.id == db.text('band_membership.band_id')) \
             .outerjoin(Song, (Band.id == Song.band_id) & (Song.status == SongStatus.ACTIVE)) \
             .group_by(Band.id, Band.name) \
             .all()
            
            band_stat = next((stat for stat in band_stats if stat.name == band.name), None)
            assert band_stat is not None
            assert band_stat.member_count == 2
            assert band_stat.active_song_count == 2


class TestDatabaseTransactions:
    """Test database transaction handling and rollback scenarios"""
    
    def test_transaction_rollback(self, app, sample_users, sample_bands):
        """Test that failed transactions are properly rolled back"""
        with app.app_context():
            user = sample_users[0]
            band = sample_bands[0]
            
            # Start transaction
            db.session.begin()
            
            try:
                # Add user to band
                band.add_member(user, UserRole.MEMBER)
                
                # Try to create invalid data that will fail
                invalid_song = Song(
                    title="",  # Empty title should fail validation
                    artist="Test Artist",
                    status=SongStatus.ACTIVE,
                    duration_seconds=240,
                    band_id=99999  # Invalid band_id
                )
                db.session.add(invalid_song)
                db.session.commit()
                
            except Exception:
                # Rollback on error
                db.session.rollback()
            
            # Verify rollback worked
            assert not user.is_member_of(band.id)
            assert Song.query.filter_by(title="").first() is None
    
    def test_bulk_operations(self, app, sample_bands):
        """Test bulk database operations"""
        with app.app_context():
            band = sample_bands[0]
            
            # Bulk insert songs
            songs_data = [
                {"title": f"Song {i}", "artist": f"Artist {i}", "status": SongStatus.ACTIVE, "duration_seconds": 240}
                for i in range(10)
            ]
            
            songs = []
            for data in songs_data:
                song = Song(
                    title=data['title'],
                    artist=data['artist'],
                    status=data['status'],
                    duration_seconds=data['duration_seconds'],
                    band_id=band.id
                )
                songs.append(song)
            
            db.session.add_all(songs)
            db.session.commit()
            
            # Verify bulk insert
            band_songs = Song.query.filter_by(band_id=band.id).all()
            assert len(band_songs) == 10
            
            # Bulk update
            Song.query.filter_by(band_id=band.id).update({Song.status: SongStatus.WISHLIST})
            db.session.commit()
            
            # Verify bulk update
            wishlist_songs = Song.query.filter_by(band_id=band.id, status=SongStatus.WISHLIST).all()
            assert len(wishlist_songs) == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
