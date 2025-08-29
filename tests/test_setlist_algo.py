import pytest
from app import create_app, db
from app.models import User, Band, Song, SongProgress, SongStatus, ProgressStatus
from app.main.routes import generate_setlist_logic
from datetime import datetime, date, timedelta

class TestSetlistAlgorithm:
    """Test the setlist generation algorithm."""
    
    @pytest.fixture
    def setup_band_with_songs(self, app):
        """Setup a test band with various songs and progress states."""
        with app.app_context():
            # Create band
            band = Band(name="Test Band")
            db.session.add(band)
            db.session.flush()
            
            # Create users
            users = []
            for i in range(3):
                user = User(
                    id=f"user_{i}",
                    name=f"User {i}",
                    email=f"user{i}@test.com",
                    band_id=band.id,
                    is_band_leader=(i == 0)
                )
                users.append(user)
                db.session.add(user)
            
            db.session.flush()
            
            # Create songs with different characteristics
            songs = []
            
            # Song 1: All members mastered (maintenance pool)
            song1 = Song(
                title="Mastered Song 1",
                artist="Artist 1",
                status=SongStatus.ACTIVE,
                duration_minutes=4,
                last_rehearsed_on=date.today() - timedelta(days=30),
                band_id=band.id
            )
            songs.append(song1)
            db.session.add(song1)
            
            # Song 2: All members mastered (maintenance pool)
            song2 = Song(
                title="Mastered Song 2",
                artist="Artist 2",
                status=SongStatus.ACTIVE,
                duration_minutes=5,
                last_rehearsed_on=date.today() - timedelta(days=15),
                band_id=band.id
            )
            songs.append(song2)
            db.session.add(song2)
            
            # Song 3: Mixed progress (learning pool)
            song3 = Song(
                title="Learning Song 1",
                artist="Artist 3",
                status=SongStatus.ACTIVE,
                duration_minutes=6,
                band_id=band.id
            )
            songs.append(song3)
            db.session.add(song3)
            
            # Song 4: Mixed progress (learning pool)
            song4 = Song(
                title="Learning Song 2",
                artist="Artist 4",
                status=SongStatus.ACTIVE,
                duration_minutes=3,
                band_id=band.id
            )
            songs.append(song4)
            db.session.add(song4)
            
            # Song 5: No progress yet (learning pool)
            song5 = Song(
                title="New Song",
                artist="Artist 5",
                status=SongStatus.ACTIVE,
                duration_minutes=7,
                band_id=band.id
            )
            songs.append(song5)
            db.session.add(song5)
            
            db.session.flush()
            
            # Create progress records
            # Song 1: All mastered
            for user in users:
                progress = SongProgress(
                    user_id=user.id,
                    song_id=song1.id,
                    status=ProgressStatus.MASTERED
                )
                db.session.add(progress)
            
            # Song 2: All mastered
            for user in users:
                progress = SongProgress(
                    user_id=user.id,
                    song_id=song2.id,
                    status=ProgressStatus.MASTERED
                )
                db.session.add(progress)
            
            # Song 3: Mixed progress (high readiness)
            progress1 = SongProgress(user_id=users[0].id, song_id=song3.id, status=ProgressStatus.MASTERED)
            progress2 = SongProgress(user_id=users[1].id, song_id=song3.id, status=ProgressStatus.READY_FOR_REHEARSAL)
            progress3 = SongProgress(user_id=users[2].id, song_id=song3.id, status=ProgressStatus.IN_PRACTICE)
            db.session.add_all([progress1, progress2, progress3])
            
            # Song 4: Mixed progress (medium readiness)
            progress1 = SongProgress(user_id=users[0].id, song_id=song4.id, status=ProgressStatus.READY_FOR_REHEARSAL)
            progress2 = SongProgress(user_id=users[1].id, song_id=song4.id, status=ProgressStatus.IN_PRACTICE)
            progress3 = SongProgress(user_id=users[2].id, song_id=song4.id, status=ProgressStatus.TO_LISTEN)
            db.session.add_all([progress1, progress2, progress3])
            
            # Song 5: No progress (low readiness)
            for user in users:
                progress = SongProgress(
                    user_id=user.id,
                    song_id=song5.id,
                    status=ProgressStatus.TO_LISTEN
                )
                db.session.add(progress)
            
            db.session.commit()
            
            return {
                'band': band,
                'users': users,
                'songs': songs,
                'mastered_songs': [song1, song2],
                'learning_songs': [song3, song4, song5]
            }
    
    def test_basic_setlist_generation(self, app, setup_band_with_songs):
        """Test basic setlist generation with balanced parameters."""
        with app.app_context():
            data = {
                'duration_minutes_total': 60,
                'learning_ratio': 0.6
            }
            
            result = generate_setlist_logic(data, setup_band_with_songs['band'])
            
            assert 'setlist' in result
            assert 'summary' in result
            assert result['summary']['total_duration'] == 60
            assert result['summary']['learning_ratio'] == 0.6
            
            # Should have learning and maintenance songs
            setlist = result['setlist']
            learning_songs = [s for s in setlist if s['block'] == 'learning']
            maintenance_songs = [s for s in setlist if s['block'] == 'maintenance']
            
            assert len(learning_songs) > 0
            assert len(maintenance_songs) > 0
    
    def test_all_learning_setlist(self, app, setup_band_with_songs):
        """Test setlist with 100% learning ratio."""
        with app.app_context():
            data = {
                'duration_minutes_total': 60,
                'learning_ratio': 1.0
            }
            
            result = generate_setlist_logic(data, setup_band_with_songs['band'])
            
            setlist = result['setlist']
            learning_songs = [s for s in setlist if s['block'] == 'learning']
            maintenance_songs = [s for s in setlist if s['block'] == 'maintenance']
            
            assert len(maintenance_songs) == 0
            assert len(learning_songs) > 0
            
            # Learning songs should be sorted by readiness score (descending)
            readiness_scores = [s['readiness_score'] for s in learning_songs]
            assert readiness_scores == sorted(readiness_scores, reverse=True)
    
    def test_all_maintenance_setlist(self, app, setup_band_with_songs):
        """Test setlist with 0% learning ratio."""
        with app.app_context():
            data = {
                'duration_minutes_total': 60,
                'learning_ratio': 0.0
            }
            
            result = generate_setlist_logic(data, setup_band_with_songs['band'])
            
            setlist = result['setlist']
            learning_songs = [s for s in setlist if s['block'] == 'learning']
            maintenance_songs = [s for s in setlist if s['block'] == 'maintenance']
            
            assert len(learning_songs) == 0
            assert len(maintenance_songs) > 0
            
            # Maintenance songs should be sorted by last rehearsed date (oldest first)
            last_rehearsed_dates = [s['last_rehearsed'] for s in maintenance_songs]
            # Note: 'Never' will be sorted first, then by date
            assert 'Never' not in last_rehearsed_dates or last_rehearsed_dates[0] == 'Never'
    
    def test_short_duration_setlist(self, app, setup_band_with_songs):
        """Test setlist generation with very short duration."""
        with app.app_context():
            data = {
                'duration_minutes_total': 15,
                'learning_ratio': 0.5
            }
            
            result = generate_setlist_logic(data, setup_band_with_songs['band'])
            
            setlist = result['setlist']
            total_duration = sum(s['duration_minutes'] for s in setlist)
            
            assert total_duration <= 15
            assert len(setlist) > 0
    
    def test_long_duration_setlist(self, app, setup_band_with_songs):
        """Test setlist generation with long duration and break insertion."""
        with app.app_context():
            data = {
                'duration_minutes_total': 120,
                'learning_ratio': 0.5
            }
            
            result = generate_setlist_logic(data, setup_band_with_songs['band'])
            
            assert 'break_info' in result['summary']
            assert result['summary']['break_info']['duration'] == 10
            assert result['summary']['break_info']['position'] == 'mid-session'
    
    def test_edge_case_tiny_duration(self, app, setup_band_with_songs):
        """Test setlist generation with extremely small duration."""
        with app.app_context():
            data = {
                'duration_minutes_total': 5,
                'learning_ratio': 0.5
            }
            
            result = generate_setlist_logic(data, setup_band_with_songs['band'])
            
            setlist = result['setlist']
            total_duration = sum(s['duration_minutes'] for s in setlist)
            
            assert total_duration <= 5
            # Should still get some songs if they fit
    
    def test_edge_case_max_duration(self, app, setup_band_with_songs):
        """Test setlist generation with maximum duration."""
        with app.app_context():
            data = {
                'duration_minutes_total': 300,  # 5 hours
                'learning_ratio': 0.5
            }
            
            result = generate_setlist_logic(data, setup_band_with_songs['band'])
            
            setlist = result['setlist']
            total_duration = sum(s['duration_minutes'] for s in setlist)
            
            assert total_duration <= 300
            assert len(setlist) > 0
    
    def test_empty_learning_pool(self, app, app):
        """Test setlist generation when no learning songs exist."""
        with app.app_context():
            # Create band with only mastered songs
            band = Band(name="Test Band")
            db.session.add(band)
            db.session.flush()
            
            user = User(id="user1", name="User 1", email="user1@test.com", band_id=band.id)
            db.session.add(user)
            db.session.flush()
            
            song = Song(
                title="Mastered Song",
                artist="Artist",
                status=SongStatus.ACTIVE,
                duration_minutes=5,
                band_id=band.id
            )
            db.session.add(song)
            db.session.flush()
            
            # All users mastered the song
            progress = SongProgress(
                user_id=user.id,
                song_id=song.id,
                status=ProgressStatus.MASTERED
            )
            db.session.add(progress)
            db.session.commit()
            
            data = {
                'duration_minutes_total': 60,
                'learning_ratio': 0.6
            }
            
            result = generate_setlist_logic(data, band)
            
            setlist = result['setlist']
            learning_songs = [s for s in setlist if s['block'] == 'learning']
            maintenance_songs = [s for s in setlist if s['block'] == 'maintenance']
            
            assert len(learning_songs) == 0
            assert len(maintenance_songs) > 0
    
    def test_empty_maintenance_pool(self, app):
        """Test setlist generation when no maintenance songs exist."""
        with app.app_context():
            # Create band with only learning songs
            band = Band(name="Test Band")
            db.session.add(band)
            db.session.flush()
            
            user = User(id="user1", name="User 1", email="user1@test.com", band_id=band.id)
            db.session.add(user)
            db.session.flush()
            
            song = Song(
                title="Learning Song",
                artist="Artist",
                status=SongStatus.ACTIVE,
                duration_minutes=5,
                band_id=band.id
            )
            db.session.add(song)
            db.session.flush()
            
            # User not mastered the song
            progress = SongProgress(
                user_id=user.id,
                song_id=song.id,
                status=ProgressStatus.IN_PRACTICE
            )
            db.session.add(progress)
            db.session.commit()
            
            data = {
                'duration_minutes_total': 60,
                'learning_ratio': 0.4
            }
            
            result = generate_setlist_logic(data, band)
            
            setlist = result['setlist']
            learning_songs = [s for s in setlist if s['block'] == 'learning']
            maintenance_songs = [s for s in setlist if s['block'] == 'maintenance']
            
            assert len(learning_songs) > 0
            assert len(maintenance_songs) == 0
    
    def test_songs_too_long_to_fit(self, app, setup_band_with_songs):
        """Test setlist generation when songs are too long to fit in time."""
        with app.app_context():
            # Add a very long song
            long_song = Song(
                title="Very Long Song",
                artist="Artist",
                status=SongStatus.ACTIVE,
                duration_minutes=100,  # Too long for 60-minute setlist
                band_id=setup_band_with_songs['band'].id
            )
            db.session.add(long_song)
            db.session.flush()
            
            # Add progress for the long song
            for user in setup_band_with_songs['users']:
                progress = SongProgress(
                    user_id=user.id,
                    song_id=long_song.id,
                    status=ProgressStatus.IN_PRACTICE
                )
                db.session.add(progress)
            
            db.session.commit()
            
            data = {
                'duration_minutes_total': 60,
                'learning_ratio': 0.5
            }
            
            result = generate_setlist_logic(data, setup_band_with_songs['band'])
            
            setlist = result['setlist']
            total_duration = sum(s['duration_minutes'] for s in setlist)
            
            assert total_duration <= 60
            # The long song should not be included
            long_song_titles = [s['title'] for s in setlist if s['title'] == 'Very Long Song']
            assert len(long_song_titles) == 0
    
    def test_cumulative_time_calculation(self, app, setup_band_with_songs):
        """Test that cumulative time is calculated correctly."""
        with app.app_context():
            data = {
                'duration_minutes_total': 60,
                'learning_ratio': 0.5
            }
            
            result = generate_setlist_logic(data, setup_band_with_songs['band'])
            
            setlist = result['setlist']
            cumulative_time = 0
            
            for song in setlist:
                cumulative_time += song['duration_minutes']
                assert song['cumulative_time'] == cumulative_time
    
    def test_break_insertion_logic(self, app, setup_band_with_songs):
        """Test break insertion for long setlists."""
        with app.app_context():
            # Test with duration just above 90 minutes
            data = {
                'duration_minutes_total': 95,
                'learning_ratio': 0.5
            }
            
            result = generate_setlist_logic(data, setup_band_with_songs['band'])
            
            assert 'break_info' in result['summary']
            assert result['summary']['break_info']['duration'] == 10
            
            # Test with duration below 90 minutes
            data = {
                'duration_minutes_total': 85,
                'learning_ratio': 0.5
            }
            
            result = generate_setlist_logic(data, setup_band_with_songs['band'])
            
            assert 'break_info' not in result['summary'] or result['summary']['break_info'] is None

def generate_setlist_logic(data, band):
    """Helper function to test the setlist generation logic."""
    from app.main.routes import generate_setlist
    
    # Mock the request context
    from flask import request
    import json
    
    # Create a mock request
    class MockRequest:
        def __init__(self, json_data):
            self.json = json_data
    
    # Store original request
    original_request = request._get_current_object()
    
    try:
        # Mock the request
        request._get_current_object = lambda: MockRequest(data)
        
        # Call the function
        from app.main.routes import generate_setlist
        result = generate_setlist()
        
        # Parse the JSON response
        if hasattr(result, 'json'):
            return result.json
        else:
            return json.loads(result.data)
    
    finally:
        # Restore original request
        request._get_current_object = lambda: original_request
