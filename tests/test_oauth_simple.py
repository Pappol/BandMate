import pytest
from flask import url_for

from app import create_app, db


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


class TestGoogleOAuth:
    """Test Google OAuth functionality."""

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

    def test_google_login_route_redirects(self, client):
        """Test that /login/google redirects properly."""
        response = client.get('/login/google')

        # Should redirect (302) when not authorized
        assert response.status_code == 302

        # Check that it's not redirecting to itself (which would cause infinite loop)
        location = response.headers.get('Location', '')
        assert '/login/google' not in location, "Google login route is redirecting to itself - infinite loop!"

        # Should redirect to Flask-Dance OAuth endpoint first
        assert '/oauth/google' in location, f"Expected Flask-Dance OAuth redirect, got: {location}"

        # Follow the Flask-Dance redirect to see if it goes to Google
        if location.startswith('/'):
            response = client.get(location)
            if response.status_code == 302:
                oauth_location = response.headers.get('Location', '')
                # Flask-Dance should redirect to Google's OAuth endpoint
                assert ('google.com' in oauth_location or
                        'accounts.google.com' in oauth_location), (
                    f"Expected Google OAuth redirect, got: {oauth_location}")

    def test_no_infinite_redirect_loop(self, client):
        """Test that Google login doesn't cause infinite redirects."""
        # Make multiple requests to simulate potential loop
        for i in range(3):
            response = client.get('/login/google')
            assert response.status_code == 302, f"Request {i+1} should redirect"

            # Check that we're not redirecting to ourselves
            location = response.headers.get('Location', '')
            assert '/login/google' not in location, (
                f"Request {i+1} redirects to itself - infinite loop!")

            # If it's an external redirect, that's good
            if location.startswith('http') and 'google.com' in location:
                break
            elif location.startswith('/'):
                # Internal redirect - follow it
                response = client.get(location)
                # Should not redirect back to /login/google
                if response.status_code == 302:
                    new_location = response.headers.get('Location', '')
                    assert '/login/google' not in new_location, (
                        f"Internal redirect {i+1} goes back to Google login - infinite loop!")
