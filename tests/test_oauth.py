import pytest
from unittest.mock import patch, MagicMock
from flask import url_for
from app import create_app, db
from app.models import User, Band


@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    app = create_app('testing')
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture
def mock_google_oauth():
    """Mock Google OAuth responses."""
    with patch('flask_dance.contrib.google.google') as mock_google:
        # Mock the authorized property
        mock_google.authorized = False
        yield mock_google


class TestGoogleOAuth:
    """Test Google OAuth functionality."""
    
    def test_google_login_route_not_authorized(self, client, mock_google_oauth):
        """Test that /login/google redirects properly when not authorized."""
        response = client.get('/login/google')
        
        # Should redirect (302) when not authorized
        assert response.status_code == 302
        
        # Check that it's not redirecting to itself (which would cause infinite loop)
        location = response.headers.get('Location', '')
        assert '/login/google' not in location
        assert 'google.com' in location or 'accounts.google.com' in location
    
    def test_google_login_route_authorized(self, client, mock_google_oauth):
        """Test that /login/google works when authorized."""
        # Mock as authorized
        mock_google_oauth.authorized = True
        
        # Mock successful user info response
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {
            'id': '12345',
            'name': 'Test User',
            'email': 'test@example.com'
        }
        mock_google_oauth.get.return_value = mock_response
        
        response = client.get('/login/google')
        
        # Should redirect to dashboard after successful login
        assert response.status_code == 302
        location = response.headers.get('Location', '')
        assert '/dashboard' in location
    
    def test_google_login_infinite_loop_prevention(self, client, mock_google_oauth):
        """Test that Google login doesn't cause infinite redirects."""
        # Mock as not authorized
        mock_google_oauth.authorized = False
        
        # Make multiple requests to simulate potential loop
        for _ in range(3):
            response = client.get('/login/google')
            assert response.status_code == 302
            
            # Check that we're not redirecting to ourselves
            location = response.headers.get('Location', '')
            assert '/login/google' not in location
            
            # Follow the redirect to see where it goes
            if location.startswith('http'):
                # External redirect - this is good
                break
            elif location.startswith('/'):
                # Internal redirect - follow it
                response = client.get(location)
                # Should not redirect back to /login/google
                if response.status_code == 302:
                    new_location = response.headers.get('Location', '')
                    assert '/login/google' not in new_location
    
    def test_oauth_callback_route_exists(self, app):
        """Test that the OAuth callback route exists."""
        with app.app_context():
            # Check if the route exists in the app
            routes = [str(rule) for rule in app.url_map.iter_rules()]
            
            # Should have a callback route for Google OAuth
            callback_routes = [r for r in routes if 'google' in r and 'authorized' in r]
            assert len(callback_routes) > 0, "Google OAuth callback route not found"
    
    def test_oauth_blueprint_registration(self, app):
        """Test that Google OAuth blueprint is properly registered."""
        with app.app_context():
            # Check if Google OAuth blueprint is registered
            blueprints = list(app.blueprints.keys())
            
            # Should have the Google OAuth blueprint
            assert 'google' in blueprints, "Google OAuth blueprint not registered"
            
            # Check that the routes don't conflict
            routes = [str(rule) for rule in app.url_map.iter_rules()]
            
            # Should not have conflicting routes
            google_routes = [r for r in routes if 'google' in r]
            assert len(google_routes) >= 2, "Expected at least 2 Google OAuth routes"
            
            # Check for specific expected routes
            route_strings = [str(rule) for rule in app.url_map.iter_rules()]
            assert any('/login/google' in r for r in route_strings), "Google login route not found"
            assert any('/login/google/authorized' in r for r in route_strings), "Google callback route not found"


class TestOAuthIntegration:
    """Test OAuth integration with the rest of the app."""
    
    def test_oauth_flow_completeness(self, app):
        """Test that the complete OAuth flow is implemented."""
        with app.app_context():
            routes = [str(rule) for rule in app.url_map.iter_rules()]
            
            # Should have all necessary OAuth routes
            required_routes = [
                '/login/google',           # Initiate OAuth
                '/login/google/authorized' # Handle callback
            ]
            
            for route in required_routes:
                assert any(route in r for r in routes), f"Required route {route} not found"
    
    def test_oauth_redirect_chain(self, client, mock_google_oauth):
        """Test the complete redirect chain for OAuth."""
        # Mock as not authorized
        mock_google_oauth.authorized = False
        
        # Start OAuth flow
        response = client.get('/login/google')
        assert response.status_code == 302
        
        # Follow redirects to see the complete flow
        redirect_count = 0
        max_redirects = 5  # Prevent infinite loops in tests
        
        while response.status_code == 302 and redirect_count < max_redirects:
            location = response.headers.get('Location', '')
            
            # Should not redirect to ourselves
            assert '/login/google' not in location, f"Redirect loop detected at step {redirect_count}"
            
            # If it's an external redirect, that's good
            if location.startswith('http') and 'google.com' in location:
                break
            elif location.startswith('/'):
                # Follow internal redirect
                response = client.get(location)
                redirect_count += 1
            else:
                break
        
        # Should not have exceeded max redirects
        assert redirect_count < max_redirects, "Too many redirects - possible infinite loop"
