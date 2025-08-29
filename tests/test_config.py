import pytest
import os
import tempfile

@pytest.fixture(scope="session")
def test_config():
    """Test configuration for the entire test session."""
    # Set test environment variables
    os.environ['FLASK_ENV'] = 'testing'
    os.environ['FLASK_SECRET_KEY'] = 'test-secret-key'
    os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
    os.environ['GOOGLE_CLIENT_ID'] = 'test-client-id'
    os.environ['GOOGLE_CLIENT_SECRET'] = 'test-client-secret'
    
    return {
        'TESTING': True,
        'FLASK_SECRET_KEY': 'test-secret-key',
        'DATABASE_URL': 'sqlite:///:memory:',
        'GOOGLE_CLIENT_ID': 'test-client-id',
        'GOOGLE_CLIENT_SECRET': 'test-client-secret',
        'WTF_CSRF_ENABLED': False
    }

@pytest.fixture(scope="function")
def temp_db():
    """Create a temporary database for each test."""
    db_fd, db_path = tempfile.mkstemp()
    yield db_path
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture(scope="function")
def app_with_temp_db(temp_db):
    """Create app with temporary database."""
    from app import create_app, db
    
    app = create_app()
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{temp_db}',
        'WTF_CSRF_ENABLED': False,
        'FLASK_SECRET_KEY': 'test-secret-key'
    })
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture(scope="function")
def client_with_temp_db(app_with_temp_db):
    """Create test client with temporary database."""
    return app_with_temp_db.test_client()
