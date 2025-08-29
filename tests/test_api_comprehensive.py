import pytest
import json
from app import db
from app.models import User, Band, Song, SongProgress, Vote, SongStatus, ProgressStatus

class TestAPISongManagement:
    """Test API song management functionality."""
    
    def test_get_songs_api(self, client, app, test_band, test_user, test_song):
        """Test GET /api/songs endpoint."""
        with app.app_context():
            # Mock authentication
            from flask_login import login_user
            login_user(test_user)
            
            # Test getting songs
            response = client.get('/api/songs')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert 'songs' in data
            assert len(data['songs']) > 0
            
            # Check song data structure
            song = data['songs'][0]
            assert 'id' in song
            assert 'title' in song
            assert 'artist' in song
            assert 'status' in song
    
    def test_create_song_api(self, client, app, test_band, test_user):
        """Test POST /api/songs endpoint."""
        with app.app_context():
            # Mock authentication
            from flask_login import login_user
            login_user(test_user)
            
            # Test creating a new song
            song_data = {
                'title': 'New API Song',
                'artist': 'New API Artist',
                'status': 'wishlist',
                'duration_minutes': 5
            }
            
            response = client.post('/api/songs', 
                                data=json.dumps(song_data),
                                content_type='application/json')
            
            assert response.status_code == 201
            
            # Check song was created
            data = json.loads(response.data)
            assert data['title'] == 'New API Song'
            assert data['artist'] == 'New API Artist'
            assert data['status'] == 'wishlist'
    
    def test_update_song_api(self, client, app, test_band, test_user, test_song):
        """Test PUT /api/songs/<id> endpoint."""
        with app.app_context():
            # Mock authentication
            from flask_login import login_user
            login_user(test_user)
            
            # Test updating a song
            update_data = {
                'title': 'Updated Song Title',
                'status': 'active'
            }
            
            response = client.put(f'/api/songs/{test_song.id}',
                               data=json.dumps(update_data),
                               content_type='application/json')
            
            assert response.status_code == 200
            
            # Check song was updated
            data = json.loads(response.data)
            assert data['title'] == 'Updated Song Title'
            assert data['status'] == 'active'
    
    def test_delete_song_api(self, client, app, test_band, test_user, test_song):
        """Test DELETE /api/songs/<id> endpoint."""
        with app.app_context():
            # Mock authentication
            from flask_login import login_user
            login_user(test_user)
            
            # Test deleting a song
            response = client.delete(f'/api/songs/{test_song.id}')
            assert response.status_code == 200
            
            # Check song was deleted
            deleted_song = Song.query.get(test_song.id)
            assert deleted_song is None
    
    def test_song_progress_api(self, client, app, test_band, test_user, test_song):
        """Test song progress API endpoints."""
        with app.app_context():
            # Mock authentication
            from flask_login import login_user
            login_user(test_user)
            
            # Create progress record
            progress = SongProgress(
                user_id=test_user.id,
                song_id=test_song.id,
                status=ProgressStatus.IN_PRACTICE
            )
            db.session.add(progress)
            db.session.commit()
            
            # Test getting progress
            response = client.get(f'/api/songs/{test_song.id}/progress')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert 'progress' in data
            assert len(data['progress']) > 0
    
    def test_song_voting_api(self, client, app, test_band, test_user, test_song):
        """Test song voting API endpoints."""
        with app.app_context():
            # Mock authentication
            from flask_login import login_user
            login_user(test_user)
            
            # Test voting for a song
            response = client.post(f'/api/songs/{test_song.id}/vote')
            assert response.status_code == 200
            
            # Check vote was created
            vote = Vote.query.filter_by(
                user_id=test_user.id,
                song_id=test_song.id
            ).first()
            assert vote is not None
    
    def test_song_search_api(self, client, app, test_band, test_user):
        """Test song search API functionality."""
        with app.app_context():
            # Mock authentication
            from flask_login import login_user
            login_user(test_user)
            
            # Create multiple songs for search testing
            songs_data = [
                {'title': 'Rock Song', 'artist': 'Rock Artist', 'status': 'active'},
                {'title': 'Jazz Song', 'artist': 'Jazz Artist', 'status': 'wishlist'},
                {'title': 'Pop Song', 'artist': 'Pop Artist', 'status': 'active'}
            ]
            
            for song_data in songs_data:
                song = Song(
                    title=song_data['title'],
                    artist=song_data['artist'],
                    status=SongStatus(song_data['status']),
                    band_id=test_band.id
                )
                db.session.add(song)
            
            db.session.commit()
            
            # Test search by title
            response = client.get('/api/songs/search?q=Rock')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert len(data['songs']) > 0
            assert any('Rock' in song['title'] for song in data['songs'])
            
            # Test search by artist
            response = client.get('/api/songs/search?q=Jazz Artist')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert len(data['songs']) > 0
            assert any('Jazz Artist' in song['artist'] for song in data['songs'])

class TestAPIUserManagement:
    """Test API user management functionality."""
    
    def test_get_user_profile_api(self, client, app, test_band, test_user):
        """Test GET /api/user/profile endpoint."""
        with app.app_context():
            # Mock authentication
            from flask_login import login_user
            login_user(test_user)
            
            # Test getting user profile
            response = client.get('/api/user/profile')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert data['id'] == test_user.id
            assert data['name'] == test_user.name
            assert data['email'] == test_user.email
            assert data['band_id'] == test_user.band_id
    
    def test_update_user_profile_api(self, client, app, test_band, test_user):
        """Test PUT /api/user/profile endpoint."""
        with app.app_context():
            # Mock authentication
            from flask_login import login_user
            login_user(test_user)
            
            # Test updating user profile
            update_data = {
                'name': 'Updated User Name'
            }
            
            response = client.put('/api/user/profile',
                               data=json.dumps(update_data),
                               content_type='application/json')
            
            assert response.status_code == 200
            
            # Check user was updated
            data = json.loads(response.data)
            assert data['name'] == 'Updated User Name'
    
    def test_get_user_progress_api(self, client, app, test_band, test_user, test_song):
        """Test GET /api/user/progress endpoint."""
        with app.app_context():
            # Mock authentication
            from flask_login import login_user
            login_user(test_user)
            
            # Create progress record
            progress = SongProgress(
                user_id=test_user.id,
                song_id=test_song.id,
                status=ProgressStatus.READY_FOR_REHEARSAL
            )
            db.session.add(progress)
            db.session.commit()
            
            # Test getting user progress
            response = client.get('/api/user/progress')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert 'progress' in data
            assert len(data['progress']) > 0

class TestAPIBandManagement:
    """Test API band management functionality."""
    
    def test_get_band_info_api(self, client, app, test_band, test_user):
        """Test GET /api/band endpoint."""
        with app.app_context():
            # Mock authentication
            from flask_login import login_user
            login_user(test_user)
            
            # Test getting band info
            response = client.get('/api/band')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert data['id'] == test_band.id
            assert data['name'] == test_band.name
            assert 'members' in data
            assert 'songs' in data
    
    def test_get_band_members_api(self, client, app, test_band, test_user):
        """Test GET /api/band/members endpoint."""
        with app.app_context():
            # Mock authentication
            from flask_login import login_user
            login_user(test_user)
            
            # Test getting band members
            response = client.get('/api/band/members')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert 'members' in data
            assert len(data['members']) > 0
            
            # Check member data structure
            member = data['members'][0]
            assert 'id' in member
            assert 'name' in member
            assert 'email' in member
            assert 'is_band_leader' in member
    
    def test_get_band_statistics_api(self, client, app, test_band, test_user):
        """Test GET /api/band/statistics endpoint."""
        with app.app_context():
            # Mock authentication
            from flask_login import login_user
            login_user(test_user)
            
            # Test getting band statistics
            response = client.get('/api/band/statistics')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert 'total_songs' in data
            assert 'active_songs' in data
            assert 'wishlist_songs' in data
            assert 'total_members' in data

class TestAPISetlistGeneration:
    """Test API setlist generation functionality."""
    
    def test_generate_setlist_api(self, client, app, test_band, test_user, test_song):
        """Test POST /api/setlist/generate endpoint."""
        with app.app_context():
            # Mock authentication
            from flask_login import login_user
            login_user(test_user)
            
            # Create progress record
            progress = SongProgress(
                user_id=test_user.id,
                song_id=test_song.id,
                status=ProgressStatus.READY_FOR_REHEARSAL
            )
            db.session.add(progress)
            db.session.commit()
            
            # Test setlist generation
            setlist_data = {
                'duration_minutes_total': 60,
                'learning_ratio': 0.6
            }
            
            response = client.post('/api/setlist/generate',
                                data=json.dumps(setlist_data),
                                content_type='application/json')
            
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert 'setlist' in data
            assert 'summary' in data
            assert data['summary']['total_duration'] == 60
            assert data['summary']['learning_ratio'] == 0.6
    
    def test_get_setlist_history_api(self, client, app, test_band, test_user):
        """Test GET /api/setlist/history endpoint."""
        with app.app_context():
            # Mock authentication
            from flask_login import login_user
            login_user(test_user)
            
            # Test getting setlist history
            response = client.get('/api/setlist/history')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert 'setlists' in data
            # Note: This would need actual setlist history data to be meaningful

class TestAPIErrorHandling:
    """Test API error handling and validation."""
    
    def test_invalid_json_request(self, client, app, test_user):
        """Test API with invalid JSON request."""
        with app.app_context():
            # Mock authentication
            from flask_login import login_user
            login_user(test_user)
            
            # Test with invalid JSON
            response = client.post('/api/songs',
                                data='invalid json',
                                content_type='application/json')
            
            assert response.status_code == 400
    
    def test_missing_required_fields(self, client, app, test_user):
        """Test API with missing required fields."""
        with app.app_context():
            # Mock authentication
            from flask_login import login_user
            login_user(test_user)
            
            # Test creating song without required fields
            song_data = {
                'title': 'Incomplete Song'
                # Missing artist and status
            }
            
            response = client.post('/api/songs',
                                data=json.dumps(song_data),
                                content_type='application/json')
            
            assert response.status_code == 400
    
    def test_unauthorized_access(self, client):
        """Test API access without authentication."""
        # Test without authentication
        response = client.get('/api/songs')
        assert response.status_code == 401 or response.status_code == 302
    
    def test_resource_not_found(self, client, app, test_user):
        """Test API with non-existent resource."""
        with app.app_context():
            # Mock authentication
            from flask_login import login_user
            login_user(test_user)
            
            # Test accessing non-existent song
            response = client.get('/api/songs/99999')
            assert response.status_code == 404
    
    def test_invalid_data_validation(self, client, app, test_user):
        """Test API with invalid data validation."""
        with app.app_context():
            # Mock authentication
            from flask_login import login_user
            login_user(test_user)
            
            # Test with invalid song status
            song_data = {
                'title': 'Invalid Status Song',
                'artist': 'Invalid Artist',
                'status': 'invalid_status',
                'duration_minutes': -5  # Invalid duration
            }
            
            response = client.post('/api/songs',
                                data=json.dumps(song_data),
                                content_type='application/json')
            
            assert response.status_code == 400

class TestAPIPerformance:
    """Test API performance and response times."""
    
    def test_api_response_time(self, client, app, test_band, test_user):
        """Test API response time is reasonable."""
        with app.app_context():
            # Mock authentication
            from flask_login import login_user
            login_user(test_user)
            
            import time
            
            # Test response time for songs endpoint
            start_time = time.time()
            response = client.get('/api/songs')
            end_time = time.time()
            
            response_time = end_time - start_time
            
            assert response.status_code == 200
            assert response_time < 1.0  # Should respond within 1 second
    
    def test_api_pagination(self, client, app, test_band, test_user):
        """Test API pagination functionality."""
        with app.app_context():
            # Mock authentication
            from flask_login import login_user
            login_user(test_user)
            
            # Create multiple songs for pagination testing
            for i in range(25):  # Create 25 songs
                song = Song(
                    title=f'Pagination Song {i}',
                    artist=f'Pagination Artist {i}',
                    status=SongStatus.ACTIVE,
                    band_id=test_band.id
                )
                db.session.add(song)
            
            db.session.commit()
            
            # Test pagination parameters
            response = client.get('/api/songs?page=1&per_page=10')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert 'songs' in data
            assert len(data['songs']) <= 10  # Should respect per_page limit
            assert 'pagination' in data
            assert data['pagination']['page'] == 1
            assert data['pagination']['per_page'] == 10
