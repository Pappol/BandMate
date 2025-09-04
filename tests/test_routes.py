import json

from app import db
from app.models import Song, SongProgress, SongStatus, ProgressStatus


class TestMainRoutes:
    """Test main application routes."""

    def test_index_redirect_when_authenticated(self, client, app, test_user):
        """Test that index redirects to dashboard when user is authenticated."""
        with app.app_context():
            # Mock authentication
            with client.session_transaction() as sess:
                sess['_user_id'] = test_user.id
            
            response = client.get('/')
            assert response.status_code == 302  # Redirect
            assert 'dashboard' in response.location

    def test_index_show_login_when_not_authenticated(self, client):
        """Test that index shows login page when user is not authenticated."""
        response = client.get('/')
        assert response.status_code == 200
        assert b'BandMate' in response.data
        assert b'Login' in response.data

    def test_login_page(self, client):
        """Test login page display."""
        response = client.get('/login')
        assert response.status_code == 200
        assert b'Welcome to BandMate' in response.data
        assert b'Sign in with Google' in response.data

    def test_dashboard_requires_auth(self, client):
        """Test that dashboard requires authentication."""
        response = client.get('/dashboard')
        assert response.status_code == 302  # Redirect to login
        assert 'login' in response.location

    def test_wishlist_requires_auth(self, client):
        """Test that wishlist requires authentication."""
        response = client.get('/wishlist')
        assert response.status_code == 302  # Redirect to login
        assert 'login' in response.location

    def test_setlist_requires_auth(self, client):
        """Test that setlist generator requires authentication."""
        response = client.get('/setlist')
        assert response.status_code == 302  # Redirect to login
        assert 'login' in response.location

    def test_propose_song_requires_auth(self, client):
        """Test that propose song requires authentication."""
        response = client.get('/wishlist/propose')
        assert response.status_code == 302  # Redirect to login
        assert 'login' in response.location


class TestDashboardRoutes:
    """Test dashboard functionality."""

    def test_dashboard_with_data(self, client, app, test_band, test_user, test_song):
        """Test dashboard displays correctly with data."""
        with app.app_context():
            # Create progress record
            progress = SongProgress(
                user_id=test_user.id,
                song_id=test_song.id,
                status=ProgressStatus.IN_PRACTICE
            )
            db.session.add(progress)
            db.session.commit()

            # Mock authentication
            with client.session_transaction() as sess:
                sess['_user_id'] = test_user.id

            response = client.get('/dashboard')
            assert response.status_code == 200
            assert b'Song Dashboard' in response.data
            assert test_song.title.encode() in response.data
            assert test_user.name.encode() in response.data

    def test_dashboard_no_songs(self, client, app, test_band, test_user):
        """Test dashboard when no songs exist."""
        with app.app_context():
            # Mock authentication
            with client.session_transaction() as sess:
                sess['_user_id'] = test_user.id

            response = client.get('/dashboard')
            assert response.status_code == 200
            assert b'No songs yet' in response.data
            assert b'View Wishlist' in response.data


class TestWishlistRoutes:
    """Test wishlist functionality."""

    def test_wishlist_with_songs(self, client, app, test_band, test_user):
        """Test wishlist displays correctly with songs."""
        with app.app_context():
            # Create wishlist song
            song = Song(
                title="Wishlist Song",
                artist="Wishlist Artist",
                status=SongStatus.WISHLIST,
                band_id=test_band.id
            )
            db.session.add(song)
            db.session.commit()

            # Mock authentication
            with client.session_transaction() as sess:
                sess['_user_id'] = test_user.id

            response = client.get('/wishlist')
            assert response.status_code == 200
            assert b'Song Wishlist' in response.data
            assert song.title.encode() in response.data

    def test_wishlist_no_songs(self, client, app, test_band, test_user):
        """Test wishlist when no songs exist."""
        with app.app_context():
            # Mock authentication
            with client.session_transaction() as sess:
                sess['_user_id'] = test_user.id

            response = client.get('/wishlist')
            assert response.status_code == 200
            assert b'No songs in wishlist' in response.data
            assert b'Propose Your First Song' in response.data

    def test_propose_song_form(self, client, app, test_band, test_user):
        """Test propose song form display."""
        with app.app_context():
            # Mock authentication
            with client.session_transaction() as sess:
                sess['_user_id'] = test_user.id

            response = client.get('/wishlist/propose')
            assert response.status_code == 200
            assert b'Propose a New Song' in response.data
            assert b'Song Title' in response.data
            assert b'Artist/Band' in response.data

    def test_propose_song_submission(self, client, app, test_band, test_user):
        """Test propose song form submission."""
        with app.app_context():
            # Mock authentication
            with client.session_transaction() as sess:
                sess['_user_id'] = test_user.id

            response = client.post('/wishlist/propose', data={
                'title': 'New Song',
                'artist': 'New Artist',
                'duration': '5',
                'link': 'https://example.com'
            })

            assert response.status_code == 302  # Redirect
            assert 'wishlist' in response.location

            # Check song was created
            song = Song.query.filter_by(title='New Song').first()
            assert song is not None
            assert song.artist == 'New Artist'
            assert song.status == SongStatus.WISHLIST

    def test_propose_song_validation(self, client, app, test_band, test_user):
        """Test propose song form validation."""
        with app.app_context():
            # Mock authentication
            with client.session_transaction() as sess:
                sess['_user_id'] = test_user.id

            # Missing required fields
            response = client.post('/wishlist/propose', data={
                'title': '',
                'artist': 'New Artist'
            })

            assert response.status_code == 302  # Redirect
            # Should redirect back to form with error


class TestSetlistRoutes:
    """Test setlist generator functionality."""

    def test_setlist_generator_page(self, client, app, test_band, test_user):
        """Test setlist generator page display."""
        with app.app_context():
            # Mock authentication
            with client.session_transaction() as sess:
                sess['_user_id'] = test_user.id

            response = client.get('/setlist')
            assert response.status_code == 200
            assert b'Setlist Generator' in response.data
            assert b'Total Duration' in response.data
            assert b'Learning vs Maintenance Ratio' in response.data

    def test_generate_setlist_success(self, client, app, test_band, test_user, test_song):
        """Test successful setlist generation."""
        with app.app_context():
            # Mock authentication
            with client.session_transaction() as sess:
                sess['_user_id'] = test_user.id
                sess['current_band_id'] = test_band.id

            # Create progress record with valid status for setlist generation
            progress = SongProgress(
                user_id=test_user.id,
                song_id=test_song.id,
                status=ProgressStatus.READY_FOR_REHEARSAL
            )
            db.session.add(progress)
            db.session.commit()

            response = client.post('/generate_setlist',
                                  json={'duration_minutes_total': 60,
                                        'learning_ratio': 0.5})

            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'setlist' in data
            assert 'summary' in data
            assert data['summary']['total_duration'] == 60
            assert data['summary']['learning_ratio'] == 0.5

    def test_generate_setlist_invalid_params(self, client, app, test_band, test_user):
        """Test setlist generation with invalid parameters."""
        with app.app_context():
            # Mock authentication
            with client.session_transaction() as sess:
                sess['_user_id'] = test_user.id

            # Invalid duration
            response = client.post('/generate_setlist',
                                  json={'duration_minutes_total': -10,
                                        'learning_ratio': 0.5})
            assert response.status_code == 400

            # Invalid ratio
            response = client.post('/generate_setlist',
                                  json={'duration_minutes_total': 60,
                                        'learning_ratio': 1.5})
            assert response.status_code == 400

    def test_generate_setlist_no_songs(self, client, app, test_band, test_user):
        """Test setlist generation when no songs exist."""
        with app.app_context():
            # Mock authentication
            with client.session_transaction() as sess:
                sess['_user_id'] = test_user.id
                sess['current_band_id'] = test_band.id

            response = client.post('/generate_setlist',
                                  json={'duration_minutes_total': 60,
                                        'learning_ratio': 0.5})

            assert response.status_code == 400
            data = json.loads(response.data)
            assert 'error' in data
            assert 'No active songs found' in data['error']


class TestAPIRoutes:
    """Test API endpoints."""

    def test_update_progress_success(self, client, app, test_band, test_user, test_song):
        """Test successful progress update."""
        with app.app_context():
            # Mock authentication
            with client.session_transaction() as sess:
                sess['_user_id'] = test_user.id

            response = client.post('/api/progress',
                                  json={'song_id': test_song.id,
                                        'status': 'Ready for Rehearsal'})

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            assert 'Progress updated' in data['message']

            # Check database was updated
            progress = SongProgress.query.filter_by(
                user_id=test_user.id,
                song_id=test_song.id
            ).first()
            assert progress.status == ProgressStatus.READY_FOR_REHEARSAL

    def test_update_progress_invalid_status(self, client, app, test_band, test_user, test_song):
        """Test progress update with invalid status."""
        with app.app_context():
            # Mock authentication
            with client.session_transaction() as sess:
                sess['_user_id'] = test_user.id

            response = client.post('/api/progress',
                                  json={'song_id': test_song.id,
                                        'status': 'Invalid Status'})

            assert response.status_code == 400
            data = json.loads(response.data)
            assert 'error' in data

    def test_toggle_vote_success(self, client, app, test_band, test_user):
        """Test successful vote toggle."""
        with app.app_context():
            # Create wishlist song
            song = Song(
                title="Vote Song",
                artist="Vote Artist",
                status=SongStatus.WISHLIST,
                band_id=test_band.id
            )
            db.session.add(song)
            db.session.commit()

            # Mock authentication
            with client.session_transaction() as sess:
                sess['_user_id'] = test_user.id

            # Add vote
            response = client.post('/api/wishlist/vote',
                                  json={'song_id': song.id})

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            assert data['user_voted'] is True
            assert data['vote_count'] == 1

            # Remove vote
            response = client.post('/api/wishlist/vote',
                                  json={'song_id': song.id})

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            assert data['user_voted'] is False
            assert data['vote_count'] == 0

    def test_approve_song_success(self, client, app, test_band, test_user):
        """Test successful song approval."""
        with app.app_context():
            # Make user band leader
            test_user.is_band_leader = True
            db.session.commit()

            # Create wishlist song
            song = Song(
                title="Approve Song",
                artist="Approve Artist",
                status=SongStatus.WISHLIST,
                band_id=test_band.id
            )
            db.session.add(song)
            db.session.commit()

            # Mock authentication
            with client.session_transaction() as sess:
                sess['_user_id'] = test_user.id

            response = client.post('/api/wishlist/approve',
                                  json={'song_id': song.id})

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            assert 'approved' in data['message']

            # Check song status changed
            song = Song.query.get(song.id)
            assert song.status == SongStatus.ACTIVE

            # Check progress records created
            progress_count = SongProgress.query.filter_by(song_id=song.id).count()
            assert progress_count == 1  # Only test_user in band

    def test_approve_song_not_leader(self, client, app, test_band, test_user):
        """Test song approval by non-leader."""
        with app.app_context():
            # Ensure user is not leader
            test_user.is_band_leader = False
            db.session.commit()

            # Create wishlist song
            song = Song(
                title="Approve Song",
                artist="Approve Artist",
                status=SongStatus.WISHLIST,
                band_id=test_band.id
            )
            db.session.add(song)
            db.session.commit()

            # Mock authentication
            with client.session_transaction() as sess:
                sess['_user_id'] = test_user.id

            response = client.post('/api/wishlist/approve',
                                  json={'song_id': song.id})

            assert response.status_code == 403  # Forbidden


class TestErrorHandling:
    """Test error handling in routes."""

    def test_404_handler(self, client):
        """Test 404 error handling."""
        response = client.get('/nonexistent-route')
        assert response.status_code == 404

    def test_invalid_json_api(self, client, app, test_band, test_user):
        """Test API error handling with invalid JSON."""
        with app.app_context():
            # Mock authentication
            with client.session_transaction() as sess:
                sess['_user_id'] = test_user.id

            response = client.post('/api/progress',
                                  data='invalid json',
                                  content_type='application/json')

            assert response.status_code == 400
