import pytest
import tempfile
import os
from app import create_app, db
from app.models import User, Band, Song, SongProgress, Vote, SongStatus, ProgressStatus
from datetime import datetime, date, timedelta

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    # Create a temporary file to isolate the database for each test
    db_fd, db_path = tempfile.mkstemp()
    
    # Set test environment variables before creating app
    os.environ['FLASK_ENV'] = 'testing'
    os.environ['FLASK_SECRET_KEY'] = 'test-secret-key'
    os.environ['DATABASE_URL'] = f'sqlite:///{db_path}'
    os.environ['GOOGLE_CLIENT_ID'] = 'test-client-id'
    os.environ['GOOGLE_CLIENT_SECRET'] = 'test-client-secret'
    
    app = create_app()
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'WTF_CSRF_ENABLED': False,
        'FLASK_SECRET_KEY': 'test-secret-key',
        'GOOGLE_OAUTH_CLIENT_ID': 'test-client-id',
        'GOOGLE_OAUTH_CLIENT_SECRET': 'test-client-secret'
    })
    
    # Create the database and load test data
    with app.app_context():
        db.create_all()
        create_test_data()
        yield app
        db.session.remove()
        db.drop_all()
    
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """A test runner for the app's Click commands."""
    return app.test_cli_runner()

@pytest.fixture
def test_band():
    """Create a test band."""
    band = Band(name="Test Band")
    db.session.add(band)
    db.session.commit()
    return band

@pytest.fixture
def test_user(test_band):
    """Create a test user."""
    user = User(
        id="test_user_123",
        name="Test User",
        email="test@example.com",
        band_id=test_band.id,
        is_band_leader=True
    )
    db.session.add(user)
    db.session.commit()
    return user

@pytest.fixture
def test_song(test_band):
    """Create a test song."""
    song = Song(
        title="Test Song",
        artist="Test Artist",
        status=SongStatus.ACTIVE,
        duration_minutes=5,
        band_id=test_band.id
    )
    db.session.add(song)
    db.session.commit()
    return song

@pytest.fixture
def test_progress(test_user, test_song):
    """Create test progress record."""
    progress = SongProgress(
        user_id=test_user.id,
        song_id=test_song.id,
        status=ProgressStatus.IN_PRACTICE
    )
    db.session.add(progress)
    db.session.commit()
    return progress

def create_test_data():
    """Create test data for all tests."""
    # Create test band
    band = Band(name="Test Band")
    db.session.add(band)
    db.session.flush()
    
    # Create test users
    users = []
    for i in range(3):
        user = User(
            id=f"test_user_{i}",
            name=f"Test User {i}",
            email=f"user{i}@test.com",
            band_id=band.id,
            is_band_leader=(i == 0)
        )
        users.append(user)
        db.session.add(user)
    
    db.session.flush()
    
    # Create test songs
    songs = []
    for i in range(5):
        song = Song(
            title=f"Test Song {i}",
            artist=f"Test Artist {i}",
            status=SongStatus.ACTIVE if i < 3 else SongStatus.WISHLIST,
            duration_minutes=3 + i,
            band_id=band.id
        )
        songs.append(song)
        db.session.add(song)
    
    db.session.flush()
    
    # Create progress records for active songs
    for song in songs[:3]:  # Only active songs
        for user in users:
            progress = SongProgress(
                user_id=user.id,
                song_id=song.id,
                status=ProgressStatus.TO_LISTEN
            )
            db.session.add(progress)
    
    # Create some votes
    for song in songs[3:]:  # Only wishlist songs
        for user in users[:2]:  # Only first two users vote
            vote = Vote(
                user_id=user.id,
                song_id=song.id
            )
            db.session.add(vote)
    
    db.session.commit()
