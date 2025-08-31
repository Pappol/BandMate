#!/usr/bin/env python3
"""
Tests for band personalization functionality
Tests emoji, color, and letter assignment features
"""

import pytest
from app import create_app, db
from app.models import User, Band, UserRole
from datetime import datetime
from flask_login import login_user


@pytest.fixture
def app():
    """Create and configure a new app instance for testing"""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """Create a test client"""
    return app.test_client()


@pytest.fixture
def test_user(app):
    """Create a test user"""
    user = User(
        id='test_user_1',
        name='Test User',
        email='test@example.com'
    )
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def test_band(app, test_user):
    """Create a test band with personalization"""
    band = Band(
        name='Test Band',
        emoji='🎸',
        color='#FF5733',
        letter='T'
    )
    db.session.add(band)
    db.session.commit()
    
    # Add user as leader
    band.add_member(test_user, UserRole.LEADER)
    return band


@pytest.fixture
def test_band_no_personalization(app, test_user):
    """Create a test band without personalization"""
    band = Band(
        name='Plain Band'
    )
    db.session.add(band)
    db.session.commit()
    
    # Add user as leader
    band.add_member(test_user, UserRole.LEADER)
    return band


class TestBandPersonalizationModel:
    """Test band personalization model methods"""
    
    def test_band_creation_with_personalization(self, app, test_user):
        """Test creating a band with personalization fields"""
        band = Band(
            name='Rock Band',
            emoji='🤘',
            color='#FF0000',
            letter='R'
        )
        db.session.add(band)
        db.session.commit()
        
        assert band.emoji == '🤘'
        assert band.color == '#FF0000'
        assert band.letter == 'R'
    
    def test_get_display_identifier_with_emoji(self, app, test_band):
        """Test getting display identifier when emoji is set"""
        assert test_band.get_display_identifier() == '🎸'
    
    def test_get_display_identifier_with_letter(self, app, test_band_no_personalization):
        """Test getting display identifier when only letter is available"""
        test_band_no_personalization.letter = 'B'
        db.session.commit()
        
        assert test_band_no_personalization.get_display_identifier() == 'B'
    
    def test_get_display_identifier_fallback(self, app, test_band_no_personalization):
        """Test getting display identifier fallback to first letter of name"""
        assert test_band_no_personalization.get_display_identifier() == 'P'
    
    def test_get_display_color_custom(self, app, test_band):
        """Test getting custom display color"""
        assert test_band.get_display_color() == '#FF5733'
    
    def test_get_display_color_generated(self, app, test_band_no_personalization):
        """Test getting generated display color when none is set"""
        color = test_band_no_personalization.get_display_color()
        assert color.startswith('#')
        assert len(color) == 7
        
        # Should be consistent for the same band name
        color2 = test_band_no_personalization.get_display_color()
        assert color == color2
    
    def test_get_style_attributes(self, app, test_band):
        """Test getting style attributes with contrasting text color"""
        styles = test_band.get_style_attributes()
        
        assert 'background-color' in styles
        assert 'color' in styles
        assert styles['background-color'] == '#FF5733'
        
        # Text color should be contrasting
        assert styles['color'] in ['#000000', '#FFFFFF']
    
    def test_contrasting_text_color_light_background(self, app):
        """Test contrasting text color for light backgrounds"""
        band = Band(name='Light Band', color='#FFFFFF')
        styles = band.get_style_attributes()
        assert styles['color'] == '#000000'  # Black text on white background
    
    def test_contrasting_text_color_dark_background(self, app):
        """Test contrasting text color for dark backgrounds"""
        band = Band(name='Dark Band', color='#000000')
        styles = band.get_style_attributes()
        assert styles['color'] == '#FFFFFF'  # White text on black background


class TestBandPersonalizationRoutes:
    """Test band personalization routes"""
    
    def test_personalize_band_page_access(self, client, test_user, test_band):
        """Test accessing the personalize band page"""
        with client:
            login_user(test_user)
            with client.session_transaction() as sess:
                sess['current_band_id'] = test_band.id
            
            response = client.get('/band/personalize')
            assert response.status_code == 200
            
            # Check that the page loads correctly
            response_text = response.data.decode('utf-8')
            assert 'Personalize Your Band' in response_text
    
    def test_personalize_band_requires_login(self, client):
        """Test that personalize band requires authentication"""
        response = client.get('/band/personalize', follow_redirects=True)
        assert response.status_code == 200
        # Should redirect to login
    
    def test_personalize_band_requires_band_selection(self, client, test_user):
        """Test that personalize band requires band selection"""
        with client:
            login_user(test_user)
            with client.session_transaction() as sess:
                sess['current_band_id'] = None
            
            response = client.get('/band/personalize', follow_redirects=True)
            assert response.status_code == 200
            # Should redirect to band selection
    
    def test_personalize_band_requires_leadership(self, client, test_user, test_band):
        """Test that only band leaders can personalize"""
        # Change user role to member
        test_band.update_member_role(test_user.id, UserRole.MEMBER)
        
        with client:
            login_user(test_user)
            with client.session_transaction() as sess:
                sess['current_band_id'] = test_band.id
            
            response = client.post('/band/personalize', data={
                'emoji': '🎤',
                'color': '#00FF00',
                'letter': 'M'
            }, follow_redirects=True)
            
            assert response.status_code == 200
            # Should redirect to band management with error
    
    def test_update_band_personalization_success(self, client, test_user, test_band):
        """Test successfully updating band personalization"""
        with client:
            login_user(test_user)
            with client.session_transaction() as sess:
                sess['current_band_id'] = test_band.id
            
            response = client.post('/band/personalize', data={
                'emoji': '🎤',
                'color': '#00FF00',
                'letter': 'M'
            }, follow_redirects=True)
            
            assert response.status_code == 200
            
            # Check that the band was updated
            updated_band = Band.query.get(test_band.id)
            assert updated_band.emoji == '🎤'
            assert updated_band.color == '#00FF00'
            assert updated_band.letter == 'M'
    
    def test_update_band_personalization_validation(self, client, test_user, test_band):
        """Test personalization validation"""
        with client:
            login_user(test_user)
            with client.session_transaction() as sess:
                sess['current_band_id'] = test_band.id
            
            # Test invalid color format
            response = client.post('/band/personalize', data={
                'emoji': '🎤',
                'color': 'invalid-color',
                'letter': 'M'
            }, follow_redirects=True)
            
            assert response.status_code == 200
            # Should show validation error
            
            # Test emoji too long
            response = client.post('/band/personalize', data={
                'emoji': '🎤🎸🥁🎹🎷🎺🎻🎼🎵🎶',
                'color': '#00FF00',
                'letter': 'M'
            }, follow_redirects=True)
            
            assert response.status_code == 200
            # Should show validation error
            
            # Test letter too long
            response = client.post('/band/personalize', data={
                'emoji': '🎤',
                'color': '#00FF00',
                'letter': 'AB'
            }, follow_redirects=True)
            
            assert response.status_code == 200
            # Should show validation error


class TestBandPersonalizationIntegration:
    """Test band personalization integration with other features"""
    
    def test_band_management_shows_personalization(self, client, test_user, test_band):
        """Test that band management page shows personalization"""
        with client:
            login_user(test_user)
            with client.session_transaction() as sess:
                sess['current_band_id'] = test_band.id
            
            response = client.get('/band/management')
            assert response.status_code == 200
            
            # Check that personalization appears in response
            response_text = response.data.decode('utf-8')
            assert '🎸' in response_text  # Should show emoji
            assert '#FF5733' in response_text  # Should show color
            assert 'T' in response_text  # Should show letter
    
    def test_select_band_shows_personalization(self, client, test_user, test_band):
        """Test that band select page shows personalization"""
        with client:
            login_user(test_user)
            with client.session_transaction() as sess:
                sess['current_band_id'] = test_band.id
            
            response = client.get('/band/select')
            assert response.status_code == 200
            
            # Check that personalization appears in response
            response_text = response.data.decode('utf-8')
            assert '🎸' in response_text  # Should show emoji
            assert '#FF5733' in response_text  # Should show color
            assert 'T' in response_text  # Should show letter
    
    def test_navigation_shows_personalization(self, client, test_user, test_band):
        """Test that navigation shows band personalization"""
        with client:
            login_user(test_user)
            with client.session_transaction() as sess:
                sess['current_band_id'] = test_band.id
            
            response = client.get('/band/management')
            assert response.status_code == 200
            
            # Check that the band identifier appears in the page
            response_text = response.data.decode('utf-8')
            assert test_band.get_display_identifier() in response_text


class TestBandPersonalizationEdgeCases:
    """Test edge cases and error handling"""
    
    def test_empty_personalization_fields(self, client, test_user, test_band):
        """Test handling empty personalization fields"""
        with client:
            login_user(test_user)
            with client.session_transaction() as sess:
                sess['current_band_id'] = test_band.id
            
            response = client.post('/band/personalize', data={
                'emoji': '',
                'color': '',
                'letter': ''
            }, follow_redirects=True)
            
            assert response.status_code == 200
            
            # Check that fields are cleared
            updated_band = Band.query.get(test_band.id)
            assert updated_band.emoji is None
            assert updated_band.color is None
            assert updated_band.letter is None
    
    def test_partial_personalization_update(self, client, test_user, test_band):
        """Test updating only some personalization fields"""
        with client:
            login_user(test_user)
            with client.session_transaction() as sess:
                sess['current_band_id'] = test_band.id
            
            response = client.post('/band/personalize', data={
                'emoji': '🎤',
                'color': '',
                'letter': ''
            }, follow_redirects=True)
            
            assert response.status_code == 200
            
                    # Check that only emoji was updated
        updated_band = Band.query.get(test_band.id)
        assert updated_band.emoji == '🎤'
        assert updated_band.color is None  # Empty string becomes None
        assert updated_band.letter is None  # Empty string becomes None
    
    def test_unicode_emoji_handling(self, client, test_user, test_band):
        """Test handling of unicode emojis"""
        with client:
            login_user(test_user)
            with client.session_transaction() as sess:
                sess['current_band_id'] = test_band.id
            
            # Test with various emoji types
            test_emojis = ['🎸', '🤘', '🎤', '🥁', '🎹', '🎷', '🎺', '🎻', '🎼', '🎵', '🎶']
            
            for emoji in test_emojis:
                response = client.post('/band/personalize', data={
                    'emoji': emoji,
                    'color': test_band.color,
                    'letter': test_band.letter
                }, follow_redirects=True)
                
                assert response.status_code == 200
                
                # Verify emoji was saved
                updated_band = Band.query.get(test_band.id)
                assert updated_band.emoji == emoji
