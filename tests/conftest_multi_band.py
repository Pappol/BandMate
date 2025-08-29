"""
Test configuration for multi-band functionality
Provides fixtures and setup for testing the new multi-band features.
"""

import pytest
import tempfile
import os
from app import create_app, db
from app.models import User, Band, UserRole


@pytest.fixture(scope='session')
def app():
    """Create a Flask app instance for testing."""
    # Create a temporary database file
    db_fd, db_path = tempfile.mkstemp()
    
    app = create_app('testing')
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret-key'
    })
    
    return app


@pytest.fixture(scope='function')
def client(app):
    """Create a test client for the app."""
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.drop_all()


@pytest.fixture(scope='function')
def sample_bands(app):
    """Create sample bands for testing."""
    with app.app_context():
        bands = []
        for i in range(3):
            band = Band(name=f"Test Band {i+1}")
            db.session.add(band)
            bands.append(band)
        
        db.session.commit()
        return bands


@pytest.fixture(scope='function')
def sample_users(app):
    """Create sample users for testing."""
    with app.app_context():
        users = []
        for i in range(3):
            user = User(
                id=f"user_{i+1}",
                name=f"User {i+1}",
                email=f"user{i+1}@test.com"
            )
            db.session.add(user)
            users.append(user)
        
        db.session.commit()
        return users


@pytest.fixture(scope='function')
def authenticated_user(app, sample_users):
    """Create an authenticated user session."""
    with app.test_request_context():
        from flask_login import login_user
        user = sample_users[0]
        login_user(user)
        return user


@pytest.fixture(scope='function')
def multi_band_user(app, sample_bands, sample_users):
    """Create a user that belongs to multiple bands."""
    with app.app_context():
        user = sample_users[0]
        
        # Add user to multiple bands with different roles
        band1 = sample_bands[0]
        band2 = sample_bands[1]
        
        band1.add_member(user, UserRole.LEADER)
        band2.add_member(user, UserRole.MEMBER)
        
        return user, [band1, band2]


@pytest.fixture(scope='function')
def band_with_members(app, sample_bands, sample_users):
    """Create a band with multiple members."""
    with app.app_context():
        band = sample_bands[0]
        users = sample_users[:2]  # Use first two users
        
        # Add users to band
        band.add_member(users[0], UserRole.LEADER)
        band.add_member(users[1], UserRole.MEMBER)
        
        return band, users


@pytest.fixture(scope='function')
def session_with_band(app, sample_bands):
    """Create a session with a current band set."""
    with app.test_request_context() as ctx:
        band = sample_bands[0]
        ctx.session['current_band_id'] = band.id
        return ctx.session, band


def pytest_configure(config):
    """Configure pytest for multi-band testing."""
    # Add custom markers
    config.addinivalue_line(
        "markers", "multi_band: mark test as multi-band functionality test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers."""
    for item in items:
        # Mark all tests in this file as multi_band tests
        if "test_multi_band" in item.nodeid:
            item.add_marker(pytest.mark.multi_band)
        
        # Mark slow tests
        if "test_legacy_compatibility" in item.nodeid:
            item.add_marker(pytest.mark.slow)
