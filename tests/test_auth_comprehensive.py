import pytest
from unittest.mock import patch, MagicMock
from flask import url_for, session
from app import db
from app.models import User, Band
from app.auth import handle_google_login, logout

class TestAuthenticationSystem:
    """Test comprehensive authentication functionality."""
    
    def test_handle_google_login_new_user(self, app, test_band):
        """Test Google OAuth login for new user."""
        with app.app_context():
            # Mock Google OAuth response
            mock_response = MagicMock()
            mock_response.ok = True
            mock_response.json.return_value = {
                'id': 'google_12345',
                'name': 'New Google User',
                'email': 'newuser@google.com'
            }
            
            with patch('app.auth.google.get', return_value=mock_response):
                # Test new user creation
                result = handle_google_login()
                
                # Should redirect to dashboard
                assert result.status_code == 302
                assert 'dashboard' in result.location
                
                # Check user was created
                user = User.query.filter_by(email='newuser@google.com').first()
                assert user is not None
                assert user.name == 'New Google User'
                assert user.id == 'google_12345'
                assert user.band_id == test_band.id
                assert user.is_band_leader is True  # First user becomes leader
    
    def test_handle_google_login_existing_user(self, app, test_user):
        """Test Google OAuth login for existing user."""
        with app.app_context():
            # Mock Google OAuth response for existing user
            mock_response = MagicMock()
            mock_response.ok = True
            mock_response.json.return_value = {
                'id': test_user.id,
                'name': test_user.name,
                'email': test_user.email
            }
            
            with patch('app.auth.google.get', return_value=mock_response):
                # Test existing user login
                result = handle_google_login()
                
                # Should redirect to dashboard
                assert result.status_code == 302
                assert 'dashboard' in result.location
    
    def test_handle_google_login_oauth_error(self, app):
        """Test Google OAuth login error handling."""
        with app.app_context():
            # Mock Google OAuth error
            with patch('app.auth.google.get', side_effect=Exception("OAuth Error")):
                result = handle_google_login()
                
                # Should redirect to login with error
                assert result.status_code == 302
                assert 'login' in result.location
    
    def test_handle_google_login_invalid_response(self, app):
        """Test Google OAuth login with invalid response."""
        with app.app_context():
            # Mock invalid Google OAuth response
            mock_response = MagicMock()
            mock_response.ok = False
            
            with patch('app.auth.google.get', return_value=mock_response):
                result = handle_google_login()
                
                # Should redirect to login with error
                assert result.status_code == 302
                assert 'login' in result.location
    
    def test_logout_functionality(self, app, test_user):
        """Test logout functionality."""
        with app.app_context():
            # Mock user login
            from flask_login import login_user
            login_user(test_user)
            
            # Test logout
            result = logout()
            
            # Should redirect to login
            assert result.status_code == 302
            assert 'login' in result.location
    
    def test_google_oauth_blueprint_registration(self, app):
        """Test that Google OAuth blueprint is properly registered."""
        with app.app_context():
            # Check if Google OAuth blueprint is registered
            blueprints = list(app.blueprints.keys())
            assert 'google' in blueprints, "Google OAuth blueprint not registered"
            
            # Check OAuth routes exist
            routes = [str(rule) for rule in app.url_map.iter_rules()]
            oauth_routes = [r for r in routes if 'google' in r]
            assert len(oauth_routes) >= 2, "Expected at least 2 Google OAuth routes"
    
    def test_oauth_redirect_uri_configuration(self, app):
        """Test OAuth redirect URI configuration."""
        with app.app_context():
            # Check that the redirect URI is correctly configured
            # The redirect URI should be /oauth/google/authorized
            routes = [str(rule) for rule in app.url_map.iter_rules()]
            authorized_routes = [r for r in routes if 'google' in r and 'authorized' in r]
            assert len(authorized_routes) > 0, "Google OAuth authorized route not found"
            
            # Check for the specific route pattern
            assert any('/oauth/google/authorized' in r for r in routes), "Incorrect OAuth redirect URI"

class TestDemoLoginSystem:
    """Test demo login functionality."""
    
    def test_demo_login_alice(self, client, app, test_band):
        """Test demo login for Alice."""
        with app.app_context():
            # Create Alice user
            alice = User(
                id="demo_alice@demo.com",
                name="Alice Johnson",
                email="alice@demo.com",
                band_id=test_band.id,
                is_band_leader=True
            )
            db.session.add(alice)
            db.session.commit()
            
            # Test demo login
            response = client.get('/demo-login/alice@demo.com')
            assert response.status_code == 302  # Redirect to dashboard
            assert 'dashboard' in response.location
    
    def test_demo_login_bob(self, client, app, test_band):
        """Test demo login for Bob."""
        with app.app_context():
            # Create Bob user
            bob = User(
                id="demo_bob@demo.com",
                name="Bob Smith",
                email="bob@demo.com",
                band_id=test_band.id,
                is_band_leader=False
            )
            db.session.add(bob)
            db.session.commit()
            
            # Test demo login
            response = client.get('/demo-login/bob@demo.com')
            assert response.status_code == 302  # Redirect to dashboard
            assert 'dashboard' in response.location
    
    def test_demo_login_carla(self, client, app, test_band):
        """Test demo login for Carla."""
        with app.app_context():
            # Create Carla user
            carla = User(
                id="demo_carla@demo.com",
                name="Carla Rodriguez",
                email="carla@demo.com",
                band_id=test_band.id,
                is_band_leader=False
            )
            db.session.add(carla)
            db.session.commit()
            
            # Test demo login
            response = client.get('/demo-login/carla@demo.com')
            assert response.status_code == 302  # Redirect to dashboard
            assert 'dashboard' in response.location
    
    def test_demo_login_nonexistent_user(self, client):
        """Test demo login for non-existent user."""
        response = client.get('/demo-login/nonexistent@demo.com')
        assert response.status_code == 302  # Redirect to login
        assert 'login' in response.location
    
    def test_demo_login_redirects_to_dashboard(self, client, app, test_band):
        """Test that demo login redirects to dashboard after successful login."""
        with app.app_context():
            # Create test user
            user = User(
                id="demo_test@demo.com",
                name="Test User",
                email="test@demo.com",
                band_id=test_band.id,
                is_band_leader=False
            )
            db.session.add(user)
            db.session.commit()
            
            # Test demo login
            response = client.get('/demo-login/test@demo.com')
            assert response.status_code == 302  # Redirect to dashboard
            assert 'dashboard' in response.location

class TestAuthenticationDecorators:
    """Test authentication decorators."""
    
    def test_login_required_decorator(self, client):
        """Test @login_required decorator."""
        # Try to access protected route without login
        response = client.get('/dashboard')
        assert response.status_code == 302  # Redirect to login
        assert 'login' in response.location
    
    def test_band_leader_required_decorator(self, client, app, test_band):
        """Test @band_leader_required decorator."""
        with app.app_context():
            # Create non-leader user
            member = User(
                id="member@test.com",
                name="Member User",
                email="member@test.com",
                band_id=test_band.id,
                is_band_leader=False
            )
            db.session.add(member)
            db.session.commit()
            
            # Mock login for member
            from flask_login import login_user
            login_user(member)
            
            # Try to access leader-only route
            # Note: This would need a route that uses @band_leader_required
            # For now, just test that the decorator exists
            from app.auth import band_leader_required
            assert callable(band_leader_required)
    
    def test_authentication_flow_integration(self, client, app, test_band):
        """Test complete authentication flow integration."""
        with app.app_context():
            # Create test user
            user = User(
                id="flow_test@test.com",
                name="Flow Test User",
                email="flow@test.com",
                band_id=test_band.id,
                is_band_leader=True
            )
            db.session.add(user)
            db.session.commit()
            
            # Test unauthenticated access
            response = client.get('/dashboard')
            assert response.status_code == 302  # Redirect to login
            
            # Test demo login
            response = client.get('/demo-login/flow@test.com')
            assert response.status_code == 302  # Redirect to dashboard
            
            # Test authenticated access
            response = client.get('/dashboard')
            assert response.status_code == 200  # Success

class TestOAuthConfiguration:
    """Test OAuth configuration and setup."""
    
    def test_oauth_environment_variables(self, app):
        """Test OAuth environment variable configuration."""
        with app.app_context():
            # Check that OAuth config is loaded
            assert 'GOOGLE_OAUTH_CLIENT_ID' in app.config
            assert 'GOOGLE_OAUTH_CLIENT_SECRET' in app.config
    
    def test_oauth_scope_configuration(self, app):
        """Test OAuth scope configuration."""
        with app.app_context():
            # Check that OAuth blueprint is registered with correct scopes
            if 'google' in app.blueprints:
                google_bp = app.blueprints['google']
                # The scopes should include userinfo.profile and userinfo.email
                # This is configured in the blueprint creation
    
    def test_oauth_redirect_uri_validation(self, app):
        """Test OAuth redirect URI validation."""
        with app.app_context():
            # The redirect URI should be /oauth/google/authorized
            # This should match what's configured in Google Cloud Console
            routes = [str(rule) for rule in app.url_map.iter_rules()]
            authorized_routes = [r for r in routes if 'google' in r and 'authorized' in r]
            
            assert len(authorized_routes) > 0, "OAuth authorized route not found"
            
            # Check for the correct URI pattern
            correct_uri_found = False
            for route in routes:
                if '/oauth/google/authorized' in route:
                    correct_uri_found = True
                    break
            
            assert correct_uri_found, "OAuth redirect URI should be /oauth/google/authorized"
