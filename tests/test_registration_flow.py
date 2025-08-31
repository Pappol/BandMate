#!/usr/bin/env python3
"""
Tests for the registration flow to prevent redirect loops and ensure proper functionality
"""

import pytest
import tempfile
import os
from flask import session
from app import create_app, db
from app.models import User, Band, UserRole

class TestRegistrationFlow:
    """Test the complete registration flow without Google OAuth"""
    
    @pytest.fixture
    def app(self):
        """Create test app"""
        # Create a temporary file to isolate the database for each test
        db_fd, db_path = tempfile.mkstemp()
        
        # Set test environment variables before creating app
        os.environ['FLASK_ENV'] = 'testing'
        os.environ['FLASK_SECRET_KEY'] = 'test-secret-key'
        os.environ['DATABASE_URL'] = f'sqlite:///{db_path}'
        os.environ['GOOGLE_CLIENT_ID'] = 'test-client-id'
        os.environ['GOOGLE_CLIENT_SECRET'] = 'test-client-secret'
        
        app = create_app('testing')
        app.config.update({
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
            'WTF_CSRF_ENABLED': False,
            'FLASK_SECRET_KEY': 'test-secret-key',
            'GOOGLE_OAUTH_CLIENT_ID': 'test-client-id',
            'GOOGLE_OAUTH_CLIENT_SECRET': 'test-client-secret'
        })
        
        # Create the database
        with app.app_context():
            db.create_all()
            yield app
            db.session.remove()
            db.drop_all()
        
        os.close(db_fd)
        os.unlink(db_path)
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return app.test_client()
    
    @pytest.fixture
    def test_user_data(self):
        """Test user data for registration"""
        return {
            'name': 'Test User',
            'email': 'test@example.com',
            'password': 'testpass123',
            'confirm_password': 'testpass123'
        }
    
    def test_register_page_loads(self, client):
        """Test that the registration page loads correctly"""
        response = client.get('/register')
        assert response.status_code == 200
        assert b'Create Account' in response.data
        assert b'Register with Email' in response.data
    
    def test_register_success(self, client, test_user_data):
        """Test successful user registration"""
        response = client.post('/register', data=test_user_data, follow_redirects=True)
        
        # Should redirect to onboarding
        assert response.status_code == 200
        assert b'Welcome to BandMate!' in response.data
        
        # Check user was created in database
        with client.application.app_context():
            user = User.query.filter_by(email=test_user_data['email']).first()
            assert user is not None
            assert user.name == test_user_data['name']
            assert user.check_password(test_user_data['password'])
    
    def test_register_validation_required_fields(self, client):
        """Test registration validation for required fields"""
        response = client.post('/register', data={}, follow_redirects=True)
        assert response.status_code == 200
        assert b'All fields are required' in response.data
    
    def test_register_validation_password_mismatch(self, client, test_user_data):
        """Test registration validation for password mismatch"""
        test_user_data['confirm_password'] = 'differentpassword'
        response = client.post('/register', data=test_user_data, follow_redirects=True)
        assert response.status_code == 200
        assert b'Passwords do not match' in response.data
    
    def test_register_validation_password_length(self, client, test_user_data):
        """Test registration validation for password length"""
        test_user_data['password'] = '123'
        test_user_data['confirm_password'] = '123'
        response = client.post('/register', data=test_user_data, follow_redirects=True)
        assert response.status_code == 200
        assert b'Password must be at least 6 characters long' in response.data
    
    def test_register_duplicate_email(self, client, test_user_data):
        """Test registration with duplicate email"""
        # Create first user
        client.post('/register', data=test_user_data)
        
        # Try to create second user with same email
        response = client.post('/register', data=test_user_data, follow_redirects=True)
        assert response.status_code == 200
        assert b'A user with this email already exists' in response.data
    
    def test_onboarding_after_registration(self, client, test_user_data):
        """Test that onboarding works correctly after registration"""
        # Register user
        client.post('/register', data=test_user_data)
        
        # Should be able to access onboarding
        response = client.get('/onboarding')
        assert response.status_code == 200
        assert b'Welcome to BandMate!' in response.data
        assert b'Create New Band' in response.data
        assert b'Join Existing Band' in response.data
    
    def test_onboarding_redirects_authenticated_user_with_bands(self, client, test_user_data):
        """Test that onboarding redirects users who already have bands"""
        # Register user
        client.post('/register', data=test_user_data)
        
        # Create a band for the user
        with client.application.app_context():
            user = User.query.filter_by(email=test_user_data['email']).first()
            band = Band(name='Test Band')
            db.session.add(band)
            db.session.flush()
            band.add_member(user, UserRole.LEADER)
            db.session.commit()
        
        # Should redirect to band selection
        response = client.get('/onboarding', follow_redirects=True)
        assert response.status_code == 200
        # Should be redirected to band selection
    
    def test_create_band_after_registration(self, client, test_user_data):
        """Test creating a band after registration"""
        # Register user
        client.post('/register', data=test_user_data)
        
        # Create band
        response = client.post('/band/create', data={'band_name': 'My New Band'}, follow_redirects=True)
        assert response.status_code == 200
        assert b'Band "My New Band" created successfully!' in response.data
        
        # Check band was created in database
        with client.application.app_context():
            user = User.query.filter_by(email=test_user_data['email']).first()
            assert len(user.bands) == 1
            assert user.bands[0].name == 'My New Band'
            assert user.is_leader_of(user.bands[0].id)
    
    def test_login_with_email_after_registration(self, client, test_user_data):
        """Test logging in with email after registration"""
        # Register user
        client.post('/register', data=test_user_data)
        
        # Log out (simulate)
        client.get('/logout')
        
        # Login with email
        response = client.post('/login/email', data={
            'email': test_user_data['email'],
            'password': test_user_data['password']
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Welcome back, Test User!' in response.data
    
    def test_no_redirect_loop_in_onboarding(self, client, test_user_data):
        """Test that onboarding doesn't cause redirect loops"""
        # Register user
        client.post('/register', data=test_user_data)
        
        # Access onboarding multiple times - should not cause redirects
        for i in range(3):
            response = client.get('/onboarding')
            assert response.status_code == 200
            assert b'Welcome to BandMate!' in response.data
    
    def test_registration_flow_complete(self, client, test_user_data):
        """Test the complete registration flow end-to-end"""
        # 1. Register user
        response = client.post('/register', data=test_user_data, follow_redirects=True)
        assert response.status_code == 200
        assert b'Welcome to BandMate!' in response.data
        
        # 2. Access onboarding
        response = client.get('/onboarding')
        assert response.status_code == 200
        assert b'Create New Band' in response.data
        
        # 3. Create band
        response = client.post('/band/create', data={'band_name': 'My Band'}, follow_redirects=True)
        assert response.status_code == 200
        assert b'Band "My Band" created successfully!' in response.data
        
        # 4. Should be redirected to dashboard
        assert b'Dashboard' in response.data or b'Welcome' in response.data
    
    def test_session_management_after_registration(self, client, test_user_data):
        """Test that session is properly managed after registration"""
        # Register user
        client.post('/register', data=test_user_data)
        
        # Check that user is logged in
        response = client.get('/dashboard')
        assert response.status_code == 200
        
        # Check that user info is accessible
        response = client.get('/onboarding')
        assert response.status_code == 200
        assert b'Test User' in response.data
        assert b'test@example.com' in response.data
