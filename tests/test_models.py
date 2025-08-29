import pytest
from app import db
from app.models import User, Band, Song, SongProgress, Vote, SongStatus, ProgressStatus
from datetime import datetime, date, timedelta

class TestBand:
    """Test Band model functionality."""
    
    def test_create_band(self, app):
        """Test creating a new band."""
        with app.app_context():
            band = Band(name="Test Band")
            db.session.add(band)
            db.session.commit()
            
            assert band.id is not None
            assert band.name == "Test Band"
            assert band.created_at is not None
            assert len(band.members) == 0
            assert len(band.songs) == 0
    
    def test_band_relationships(self, app, test_band, test_user, test_song):
        """Test band relationships with users and songs."""
        with app.app_context():
            assert test_band.members == [test_user]
            assert test_song in test_band.songs
            assert test_user.band == test_band

class TestUser:
    """Test User model functionality."""
    
    def test_create_user(self, app, test_band):
        """Test creating a new user."""
        with app.app_context():
            user = User(
                id="new_user_123",
                name="New User",
                email="new@example.com",
                band_id=test_band.id,
                is_band_leader=False
            )
            db.session.add(user)
            db.session.commit()
            
            assert user.id == "new_user_123"
            assert user.name == "New User"
            assert user.email == "new@example.com"
            assert user.band_id == test_band.id
            assert user.is_band_leader is False
            assert user.created_at is not None
    
    def test_user_relationships(self, app, test_user, test_band, test_song):
        """Test user relationships."""
        with app.app_context():
            assert test_user.band == test_band
            assert test_user in test_band.members
    
    def test_user_progress(self, app, test_user, test_song):
        """Test user progress tracking."""
        with app.app_context():
            progress = SongProgress(
                user_id=test_user.id,
                song_id=test_song.id,
                status=ProgressStatus.READY_FOR_REHEARSAL
            )
            db.session.add(progress)
            db.session.commit()
            
            assert progress in test_user.progress
            assert progress.song == test_song
            assert progress.user == test_user

class TestSong:
    """Test Song model functionality."""
    
    def test_create_song(self, app, test_band):
        """Test creating a new song."""
        with app.app_context():
            song = Song(
                title="New Song",
                artist="New Artist",
                status=SongStatus.WISHLIST,
                duration_minutes=4,
                band_id=test_band.id
            )
            db.session.add(song)
            db.session.commit()
            
            assert song.id is not None
            assert song.title == "New Song"
            assert song.artist == "New Artist"
            assert song.status == SongStatus.WISHLIST
            assert song.duration_minutes == 4
            assert song.band_id == test_band.id
            assert song.created_at is not None
    
    def test_song_relationships(self, app, test_song, test_band):
        """Test song relationships."""
        with app.app_context():
            assert test_song.band == test_band
            assert test_song in test_band.songs
    
    def test_song_readiness_score(self, app, test_band):
        """Test song readiness score calculation."""
        with app.app_context():
            # Create users
            user1 = User(id="user1", name="User 1", email="user1@test.com", band_id=test_band.id)
            user2 = User(id="user2", name="User 2", email="user2@test.com", band_id=test_band.id)
            db.session.add_all([user1, user2])
            
            # Create song
            song = Song(title="Test Song", artist="Test Artist", status=SongStatus.ACTIVE, band_id=test_band.id)
            db.session.add(song)
            db.session.flush()
            
            # Create progress records
            progress1 = SongProgress(user_id=user1.id, song_id=song.id, status=ProgressStatus.MASTERED)
            progress2 = SongProgress(user_id=user2.id, song_id=song.id, status=ProgressStatus.READY_FOR_REHEARSAL)
            db.session.add_all([progress1, progress2])
            db.session.commit()
            
            # Test readiness score calculation
            # Mastered = 4, Ready for Rehearsal = 3
            # Average = (4 + 3) / 2 = 3.5
            expected_score = 3.5
            assert abs(song.readiness_score - expected_score) < 0.01
    
    def test_song_status_enum(self, app, test_band):
        """Test song status enum values."""
        with app.app_context():
            song = Song(
                title="Test Song",
                artist="Test Artist",
                status=SongStatus.WISHLIST,
                band_id=test_band.id
            )
            db.session.add(song)
            db.session.commit()
            
            assert song.status == SongStatus.WISHLIST
            assert song.status.value == 'wishlist'
            
            # Change status
            song.status = SongStatus.ACTIVE
            db.session.commit()
            assert song.status == SongStatus.ACTIVE
            assert song.status.value == 'active'

class TestSongProgress:
    """Test SongProgress model functionality."""
    
    def test_create_progress(self, app, test_user, test_song):
        """Test creating a new progress record."""
        with app.app_context():
            progress = SongProgress(
                user_id=test_user.id,
                song_id=test_song.id,
                status=ProgressStatus.IN_PRACTICE
            )
            db.session.add(progress)
            db.session.commit()
            
            assert progress.id is not None
            assert progress.user_id == test_user.id
            assert progress.song_id == test_song.id
            assert progress.status == ProgressStatus.IN_PRACTICE
            assert progress.updated_at is not None
    
    def test_progress_status_enum(self, app, test_user, test_song):
        """Test progress status enum values."""
        with app.app_context():
            progress = SongProgress(
                user_id=test_user.id,
                song_id=test_song.id,
                status=ProgressStatus.TO_LISTEN
            )
            db.session.add(progress)
            db.session.commit()
            
            assert progress.status == ProgressStatus.TO_LISTEN
            assert progress.status.value == 'To Listen'
            
            # Test all status values
            statuses = [
                ProgressStatus.TO_LISTEN,
                ProgressStatus.IN_PRACTICE,
                ProgressStatus.READY_FOR_REHEARSAL,
                ProgressStatus.MASTERED
            ]
            
            for status in statuses:
                progress.status = status
                db.session.commit()
                assert progress.status == status
    
    def test_progress_unique_constraint(self, app, test_user, test_song):
        """Test that only one progress record per user per song is allowed."""
        with app.app_context():
            # Create first progress record
            progress1 = SongProgress(
                user_id=test_user.id,
                song_id=test_song.id,
                status=ProgressStatus.TO_LISTEN
            )
            db.session.add(progress1)
            db.session.commit()
            
            # Try to create duplicate
            progress2 = SongProgress(
                user_id=test_user.id,
                song_id=test_song.id,
                status=ProgressStatus.IN_PRACTICE
            )
            db.session.add(progress2)
            
            # Should raise an integrity error
            with pytest.raises(Exception):
                db.session.commit()

class TestVote:
    """Test Vote model functionality."""
    
    def test_create_vote(self, app, test_user, test_song):
        """Test creating a new vote."""
        with app.app_context():
            vote = Vote(
                user_id=test_user.id,
                song_id=test_song.id
            )
            db.session.add(vote)
            db.session.commit()
            
            assert vote.id is not None
            assert vote.user_id == test_user.id
            assert vote.song_id == test_song.id
            assert vote.created_at is not None
    
    def test_vote_relationships(self, app, test_user, test_song):
        """Test vote relationships."""
        with app.app_context():
            vote = Vote(user_id=test_user.id, song_id=test_song.id)
            db.session.add(vote)
            db.session.commit()
            
            assert vote.user == test_user
            assert vote.song == test_song
            assert vote in test_user.votes
            assert vote in test_song.votes
    
    def test_vote_unique_constraint(self, app, test_user, test_song):
        """Test that only one vote per user per song is allowed."""
        with app.app_context():
            # Create first vote
            vote1 = Vote(user_id=test_user.id, song_id=test_song.id)
            db.session.add(vote1)
            db.session.commit()
            
            # Try to create duplicate
            vote2 = Vote(user_id=test_user.id, song_id=test_song.id)
            db.session.add(vote2)
            
            # Should raise an integrity error
            with pytest.raises(Exception):
                db.session.commit()

class TestModelRelationships:
    """Test complex model relationships and cascading."""
    
    def test_cascade_delete_band(self, app, test_band, test_user, test_song):
        """Test that deleting a band cascades to users and songs."""
        with app.app_context():
            # Create some additional data
            progress = SongProgress(
                user_id=test_user.id,
                song_id=test_song.id,
                status=ProgressStatus.TO_LISTEN
            )
            vote = Vote(user_id=test_user.id, song_id=test_song.id)
            db.session.add_all([progress, vote])
            db.session.commit()
            
            # Verify data exists
            assert User.query.count() > 0
            assert Song.query.count() > 0
            assert SongProgress.query.count() > 0
            assert Vote.query.count() > 0
            
            # Delete band
            db.session.delete(test_band)
            db.session.commit()
            
            # Verify cascade deletion
            assert User.query.count() == 0
            assert Song.query.count() == 0
            assert SongProgress.query.count() == 0
            assert Vote.query.count() == 0
    
    def test_cascade_delete_user(self, app, test_user, test_song):
        """Test that deleting a user cascades to progress and votes."""
        with app.app_context():
            # Create progress and vote
            progress = SongProgress(
                user_id=test_user.id,
                song_id=test_song.id,
                status=ProgressStatus.TO_LISTEN
            )
            vote = Vote(user_id=test_user.id, song_id=test_song.id)
            db.session.add_all([progress, vote])
            db.session.commit()
            
            # Verify data exists
            assert SongProgress.query.count() > 0
            assert Vote.query.count() > 0
            
            # Delete user
            db.session.delete(test_user)
            db.session.commit()
            
            # Verify cascade deletion
            assert SongProgress.query.count() == 0
            assert Vote.query.count() == 0
    
    def test_cascade_delete_song(self, app, test_song, test_user):
        """Test that deleting a song cascades to progress and votes."""
        with app.app_context():
            # Create progress and vote
            progress = SongProgress(
                user_id=test_user.id,
                song_id=test_song.id,
                status=ProgressStatus.TO_LISTEN
            )
            vote = Vote(user_id=test_user.id, song_id=test_song.id)
            db.session.add_all([progress, vote])
            db.session.commit()
            
            # Verify data exists
            assert SongProgress.query.count() > 0
            assert Vote.query.count() > 0
            
            # Delete song
            db.session.delete(test_song)
            db.session.commit()
            
            # Verify cascade deletion
            assert SongProgress.query.count() == 0
            assert Vote.query.count() == 0
