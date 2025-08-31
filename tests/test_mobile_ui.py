"""
Test suite for mobile UI improvements
Tests the new mobile-responsive design, burger menu, and footer positioning.
"""

import pytest
from flask import url_for
from app import create_app
from app.models import User, Band, Song, SongProgress, Vote, UserRole
from app import db


@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    app = create_app('testing')
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture
def test_user(app, test_band):
    """Create a test user."""
    user = User(
        id='test_user_123',
        name='Test User',
        email='test@example.com'
    )
    db.session.add(user)
    db.session.commit()
    
    # Add user to band using the proper method
    test_band.add_member(user, UserRole.LEADER)
    db.session.commit()
    
    return user


@pytest.fixture
def test_band(app):
    """Create a test band."""
    band = Band(name='Test Band')
    db.session.add(band)
    db.session.commit()
    return band


class TestMobileUI:
    """Test mobile UI improvements and responsive design."""
    
    def test_mobile_menu_button_exists(self, client, app, test_user, test_band):
        """Test that the mobile menu button is present in the HTML."""
        with app.app_context():
            # Mock authentication
            with client.session_transaction() as sess:
                sess['_user_id'] = test_user.id
                sess['current_band_id'] = test_band.id
            
            # Get the dashboard page
            response = client.get('/dashboard')
            print(f"Response status: {response.status_code}")
            if response.status_code == 302:
                print(f"Redirect location: {response.location}")
            assert response.status_code == 200
            
            # Check that mobile menu button exists
            html = response.data.decode('utf-8')
            assert 'fas fa-bars' in html  # Burger menu icon
            assert 'mobileMenuOpen' in html  # Alpine.js state variable
            assert 'md:hidden' in html  # Mobile-only visibility class
    
    def test_desktop_navigation_hidden_on_mobile(self, client, app, test_user, test_band):
        """Test that desktop navigation is hidden on mobile devices."""
        with app.app_context():
            with client.session_transaction() as sess:
                sess['_user_id'] = test_user.id
                sess['current_band_id'] = test_band.id
            
            response = client.get('/dashboard')
            assert response.status_code == 200
            
            html = response.data.decode('utf-8')
            # Desktop navigation should have hidden md:block classes
            assert 'hidden md:block' in html
            # Mobile menu button should be visible on mobile
            assert 'md:hidden' in html
    
    def test_footer_positioning(self, client, app, test_user, test_band):
        """Test that footer is properly positioned and always visible."""
        with app.app_context():
            with client.session_transaction() as sess:
                sess['_user_id'] = test_user.id
                sess['current_band_id'] = test_band.id
            
            response = client.get('/dashboard')
            assert response.status_code == 200
            
            html = response.data.decode('utf-8')
            # Footer should have mt-auto class for proper positioning
            assert 'mt-auto' in html
            # Footer should contain the copyright text
            assert '© 2025 BandMate. Powered By Pappol' in html
    
    def test_responsive_breakpoints(self, client, app, test_user, test_band):
        """Test that responsive breakpoints are properly implemented."""
        with app.app_context():
            with client.session_transaction() as sess:
                sess['_user_id'] = test_user.id
                sess['current_band_id'] = test_band.id
            
            response = client.get('/dashboard')
            assert response.status_code == 200
            
            html = response.data.decode('utf-8')
            # Check for responsive utility classes
            assert 'sm:px-6' in html  # Small screen padding
            assert 'lg:px-8' in html  # Large screen padding
            assert 'text-sm sm:text-base' in html  # Responsive text sizing
    
    def test_font_awesome_integration(self, client, app, test_user, test_band):
        """Test that Font Awesome icons are properly loaded."""
        with app.app_context():
            with client.session_transaction() as sess:
                sess['_user_id'] = test_user.id
                sess['current_band_id'] = test_band.id
            
            response = client.get('/dashboard')
            assert response.status_code == 200
            
            html = response.data.decode('utf-8')
            # Check that Font Awesome CDN is loaded
            assert 'cdnjs.cloudflare.com/ajax/libs/font-awesome' in html
            # Check for specific icon classes
            assert 'fas fa-bars' in html  # Burger menu
            assert 'fas fa-users' in html  # Users icon
            assert 'fas fa-sign-out-alt' in html  # Logout icon
    
    def test_alpine_js_integration(self, client, app, test_user, test_band):
        """Test that Alpine.js is properly integrated for mobile menu functionality."""
        with app.app_context():
            with client.session_transaction() as sess:
                sess['_user_id'] = test_user.id
                sess['current_band_id'] = test_band.id
            
            response = client.get('/dashboard')
            assert response.status_code == 200
            
            html = response.data.decode('utf-8')
            # Check that Alpine.js is loaded
            assert 'unpkg.com/alpinejs' in html
            # Check for Alpine.js directives
            assert 'x-data' in html
            assert 'x-show' in html
            assert 'x-transition' in html
    
    def test_mobile_menu_structure(self, client, app, test_user, test_band):
        """Test that the mobile menu has the correct structure and content."""
        with app.app_context():
            with client.session_transaction() as sess:
                sess['_user_id'] = test_user.id
                sess['current_band_id'] = test_band.id
            
            response = client.get('/dashboard')
            assert response.status_code == 200
            
            html = response.data.decode('utf-8')
            # Check for mobile menu sections
            assert 'mobile-nav-item' in html  # Mobile navigation item class
            assert 'Dashboard' in html  # Menu content
            assert 'Bands' in html  # Band section
            assert 'Logout' in html  # User section
    
    def test_css_flexbox_layout(self, client, app, test_user, test_band):
        """Test that CSS flexbox is used for proper layout."""
        with app.app_context():
            with client.session_transaction() as sess:
                sess['_user_id'] = test_user.id
                sess['current_band_id'] = test_band.id
            
            response = client.get('/dashboard')
            assert response.status_code == 200
            
            html = response.data.decode('utf-8')
            # Check for flexbox CSS classes
            assert 'flex-1' in html  # Main content flex grow
            assert 'flex-direction: column' in html  # Body flexbox
    
    def test_mobile_transitions(self, client, app, test_user, test_band):
        """Test that mobile menu transitions are properly defined."""
        with app.app_context():
            with client.session_transaction() as sess:
                sess['_user_id'] = test_user.id
                sess['current_band_id'] = test_band.id
            
            response = client.get('/dashboard')
            assert response.status_code == 200
            
            html = response.data.decode('utf-8')
            # Check for transition CSS classes
            assert 'mobile-menu-enter' in html
            assert 'mobile-menu-leave' in html
            assert 'transition' in html


class TestMobileResponsiveness:
    """Test mobile responsiveness across different pages."""
    
    def test_dashboard_mobile_friendly(self, client, app, test_user, test_band):
        """Test that dashboard is mobile-friendly."""
        with app.app_context():
            with client.session_transaction() as sess:
                sess['_user_id'] = test_user.id
                sess['current_band_id'] = test_band.id
            
            response = client.get('/dashboard')
            assert response.status_code == 200
            
            html = response.data.decode('utf-8')
            # Check for mobile-friendly classes
            assert 'px-4 sm:px-6 lg:px-8' in html  # Responsive padding
            assert 'py-8' in html  # Consistent vertical padding
    
    def test_wishlist_mobile_friendly(self, client, app, test_user, test_band):
        """Test that wishlist page is mobile-friendly."""
        with app.app_context():
            with client.session_transaction() as sess:
                sess['_user_id'] = test_user.id
                sess['current_band_id'] = test_band.id
            
            response = client.get('/wishlist')
            assert response.status_code == 200
            
            html = response.data.decode('utf-8')
            # Check for responsive design elements
            assert 'px-4 sm:px-6 lg:px-8' in html
            assert 'py-8' in html
    
    def test_setlist_mobile_friendly(self, client, app, test_user, test_band):
        """Test that setlist page is mobile-friendly."""
        with app.app_context():
            with client.session_transaction() as sess:
                sess['_user_id'] = test_user.id
                sess['current_band_id'] = test_band.id
            
            response = client.get('/setlist')
            assert response.status_code == 200
            
            html = response.data.decode('utf-8')
            # Check for responsive design elements
            assert 'px-4 sm:px-6 lg:px-8' in html
            assert 'py-8' in html

