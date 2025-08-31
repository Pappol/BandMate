import pytest
from app import create_app, db
from app.models import User, Band, UserRole, Invitation, InvitationStatus
from flask_login import login_user
from datetime import datetime, timedelta


@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def test_band(app):
    band = Band(name='Test Band', allow_member_invites=False)
    db.session.add(band)
    db.session.commit()
    return band


@pytest.fixture
def test_leader(app, test_band):
    user = User(
        id='leader123',
        name='Test Leader',
        email='leader@test.com'
    )
    db.session.add(user)
    db.session.commit()
    
    # Add user to band as leader
    test_band.add_member(user, UserRole.LEADER)
    return user


@pytest.fixture
def test_member(app, test_band):
    user = User(
        id='member123',
        name='Test Member',
        email='member@test.com'
    )
    db.session.add(user)
    db.session.commit()
    
    # Add user to band as member
    test_band.add_member(user, UserRole.MEMBER)
    return user


class TestMemberInvites:
    """Test member invitation functionality"""
    
    def test_leader_can_always_invite(self, app, test_band, test_leader):
        """Test that band leaders can always send invitations"""
        with app.test_request_context():
            assert test_band.can_user_invite(test_leader.id) is True
    
    def test_member_cannot_invite_by_default(self, app, test_band, test_member):
        """Test that regular members cannot invite by default"""
        with app.test_request_context():
            assert test_band.can_user_invite(test_member.id) is False
    
    def test_member_can_invite_when_enabled(self, app, test_band, test_member):
        """Test that regular members can invite when setting is enabled"""
        test_band.allow_member_invites = True
        db.session.commit()
        
        with app.test_request_context():
            assert test_band.can_user_invite(test_member.id) is True
    
    def test_toggle_member_invites(self, app, test_band, test_leader, client):
        """Test that leaders can toggle member invitation setting with proper session"""
        with app.test_request_context():
            login_user(test_leader)
            
            # Set up session
            with client.session_transaction() as sess:
                sess['current_band_id'] = test_band.id
            
            # Initially disabled
            assert test_band.allow_member_invites is False
            
            # Toggle to enabled
            response = client.post('/band/toggle-member-invites')
            assert response.status_code == 302  # Redirect
            
            # Check that setting was toggled
            db.session.refresh(test_band)
            assert test_band.allow_member_invites is True
    
    def test_non_leader_cannot_toggle_setting(self, app, test_band, test_member, client):
        """Test that non-leaders cannot toggle member invitation setting"""
        with app.test_request_context():
            login_user(test_member)
            
            response = client.post('/band/toggle-member-invites')
            assert response.status_code == 302  # Redirect
            
            # Setting should remain unchanged
            db.session.refresh(test_band)
            assert test_band.allow_member_invites is False
    
    def test_member_can_invite_when_enabled(self, app, test_band, test_member, client):
        """Test that members can send invitations when the setting is enabled"""
        # Enable member invitations
        test_band.allow_member_invites = True
        db.session.commit()
        
        with app.test_request_context():
            login_user(test_member)
            
            # Set up session
            with client.session_transaction() as sess:
                sess['current_band_id'] = test_band.id
            
            # Member should be able to invite
            response = client.post('/band/invite', data={
                'email': 'newmember@test.com',
                'message': 'Welcome to the band!'
            })
            
            assert response.status_code == 302  # Redirect
            
            # Check that invitation was created
            invitation = Invitation.query.filter_by(
                invited_email='newmember@test.com',
                band_id=test_band.id
            ).first()
            
            assert invitation is not None
            assert invitation.invited_by == test_member.id
            assert invitation.status == InvitationStatus.PENDING
    
    def test_member_cannot_invite_when_disabled(self, app, test_band, test_member, client):
        """Test that members cannot send invitations when the setting is disabled"""
        with app.test_request_context():
            login_user(test_member)
            
            # Member should not be able to invite
            response = client.post('/band/invite', data={
                'email': 'newmember@test.com',
                'message': 'Welcome to the band!'
            })
            
            assert response.status_code == 302  # Redirect
            
            # Check that no invitation was created
            invitation = Invitation.query.filter_by(
                invited_email='newmember@test.com',
                band_id=test_band.id
            ).first()
            
            assert invitation is None
