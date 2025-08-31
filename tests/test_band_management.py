import pytest
from app import create_app, db
from app.models import User, Band, UserRole, Invitation, InvitationStatus
from app.auth import login_required
from datetime import datetime, timedelta
import json
from flask_login import login_user


@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def test_user(app):
    user = User(
        id='test_user_1',
        name='Test User',
        email='test@example.com'
    )
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def test_band(app):
    band = Band(name='Test Band')
    db.session.add(band)
    db.session.commit()
    return band


@pytest.fixture
def test_leader(app, test_user, test_band):
    # Add user as leader to band
    from sqlalchemy import text
    db.session.execute(
        text('INSERT INTO band_membership (user_id, band_id, role) VALUES (:user_id, :band_id, :role)'),
        {'user_id': test_user.id, 'band_id': test_band.id, 'role': UserRole.LEADER.value}
    )
    db.session.commit()
    return test_user


@pytest.fixture
def test_member(app, test_band):
    member = User(
        id='test_member_1',
        name='Test Member',
        email='member@example.com'
    )
    db.session.add(member)
    
    # Add member to band
    from sqlalchemy import text
    db.session.execute(
        text('INSERT INTO band_membership (user_id, band_id, role) VALUES (:user_id, :band_id, :role)'),
        {'user_id': member.id, 'band_id': test_band.id, 'role': UserRole.MEMBER.value}
    )
    db.session.commit()
    return member


class TestBandManagement:
    """Test band management functionality"""
    
    def test_band_management_page_access(self, client, test_leader, test_band):
        """Test that band leaders can access the band management page"""
        with client.session_transaction() as sess:
            sess['current_band_id'] = test_band.id
        
        # Login the user
        with client:
            login_user(test_leader)
            response = client.get('/band/management')
            assert response.status_code == 200
            assert b'Band Management' in response.data
            assert b'Test Band' in response.data
    
    def test_band_management_requires_login(self, client):
        """Test that band management requires authentication"""
        response = client.get('/band/management')
        assert response.status_code == 302  # Redirect to login
    
    def test_band_management_requires_band_selection(self, client, test_leader):
        """Test that band management requires a selected band"""
        with client:
            login_user(test_leader)
            response = client.get('/band/management')
            assert response.status_code == 302  # Redirect to select band
    
    def test_band_management_requires_leadership(self, client, test_member, test_band):
        """Test that only band leaders can access management"""
        with client.session_transaction() as sess:
            sess['current_band_id'] = test_band.id
        
        with client:
            login_user(test_member)
            response = client.get('/band/management')
            assert response.status_code == 200  # Should still work for members to view
    
    def test_invite_member_success(self, client, test_leader, test_band):
        """Test successful member invitation"""
        with client.session_transaction() as sess:
            sess['current_band_id'] = test_band.id
        
        with client:
            login_user(test_leader)
            response = client.post('/band/invite', data={
                'email': 'newmember@example.com',
                'message': 'Welcome to the band!'
            })
            
            assert response.status_code == 302  # Redirect after success
            
            # Check invitation was created
            invitation = Invitation.query.filter_by(
                invited_email='newmember@example.com',
                band_id=test_band.id
            ).first()
            assert invitation is not None
            assert invitation.status == InvitationStatus.PENDING
    
    def test_invite_member_requires_leadership(self, client, test_member, test_band):
        """Test that only leaders can invite members"""
        with client.session_transaction() as sess:
            sess['current_band_id'] = test_band.id
        
        with client:
            login_user(test_member)
            response = client.post('/band/invite', data={
                'email': 'newmember@example.com'
            })
            
            assert response.status_code == 302  # Redirect with error
    
    def test_invite_existing_member(self, client, test_leader, test_band, test_member):
        """Test that existing members cannot be invited again"""
        with client.session_transaction() as sess:
            sess['current_band_id'] = test_band.id
        
        with client:
            login_user(test_leader)
            response = client.post('/band/invite', data={
                'email': test_member.email
            })
            
            assert response.status_code == 302  # Redirect with error
    
    def test_remove_member_success(self, client, test_leader, test_band, test_member):
        """Test successful member removal"""
        with client.session_transaction() as sess:
            sess['current_band_id'] = test_band.id
        
        # Verify member is in band
        assert test_member.is_member_of(test_band.id)
        
        with client:
            login_user(test_leader)
            response = client.post(f'/band/remove-member/{test_member.id}')
            
            assert response.status_code == 302  # Redirect after success
            
            # Verify member was removed from band
            assert not test_member.is_member_of(test_band.id)
            
            # Verify user still exists (not deleted)
            assert User.query.get(test_member.id) is not None
    
    def test_remove_member_requires_leadership(self, client, test_member, test_band):
        """Test that only leaders can remove members"""
        with client.session_transaction() as sess:
            sess['current_band_id'] = test_band.id
        
        # Create another member to remove
        other_member = User(
            id='other_member',
            name='Other Member',
            email='other@example.com'
        )
        db.session.add(other_member)
        
        from sqlalchemy import text
        db.session.execute(
            text('INSERT INTO band_membership (user_id, band_id, role) VALUES (:user_id, :band_id, :role)'),
            {'user_id': other_member.id, 'band_id': test_band.id, 'role': UserRole.MEMBER.value}
        )
        db.session.commit()
        
        with client:
            login_user(test_member)
            response = client.post(f'/band/remove-member/{other_member.id}')
            
            assert response.status_code == 302  # Redirect with error
            
            # Verify member was not removed
            assert other_member.is_member_of(test_band.id)
    
    def test_remove_self_not_allowed(self, client, test_leader, test_band):
        """Test that leaders cannot remove themselves"""
        with client.session_transaction() as sess:
            sess['current_band_id'] = test_band.id
        
        with client:
            login_user(test_leader)
            response = client.post(f'/band/remove-member/{test_leader.id}')
            
            assert response.status_code == 302  # Redirect with error
            
            # Verify leader is still in band
            assert test_leader.is_member_of(test_band.id)
    
    def test_remove_other_leader_not_allowed(self, client, test_leader, test_band):
        """Test that leaders cannot remove other leaders"""
        with client.session_transaction() as sess:
            sess['current_band_id'] = test_band.id
        
        # Create another leader
        other_leader = User(
            id='other_leader',
            name='Other Leader',
            email='leader2@example.com'
        )
        db.session.add(other_leader)
        
        from sqlalchemy import text
        db.session.execute(
            text('INSERT INTO band_membership (user_id, band_id, role) VALUES (:user_id, :band_id, :role)'),
            {'user_id': other_leader.id, 'band_id': test_band.id, 'role': UserRole.LEADER.value}
        )
        db.session.commit()
        
        with client:
            login_user(test_leader)
            response = client.post(f'/band/remove-member/{other_leader.id}')
            
            assert response.status_code == 302  # Redirect with error
            
            # Verify other leader is still in band
            assert other_leader.is_member_of(test_band.id)
    
    def test_resend_invitation(self, client, test_leader, test_band):
        """Test resending an invitation"""
        # Create an invitation
        invitation = Invitation(
            code='TEST1234',
            band_id=test_band.id,
            invited_by=test_leader.id,
            invited_email='test@example.com',
            expires_at=datetime.utcnow() + timedelta(days=1)
        )
        db.session.add(invitation)
        db.session.commit()
        
        with client.session_transaction() as sess:
            sess['current_band_id'] = test_band.id
        
        with client:
            login_user(test_leader)
            response = client.post(f'/band/resend-invitation/{invitation.id}')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
    
    def test_cancel_invitation(self, client, test_leader, test_band):
        """Test cancelling an invitation"""
        # Create an invitation
        invitation = Invitation(
            code='TEST1234',
            band_id=test_band.id,
            invited_by=test_leader.id,
            invited_email='test@example.com',
            expires_at=datetime.utcnow() + timedelta(days=1)
        )
        db.session.add(invitation)
        db.session.commit()
        
        with client.session_transaction() as sess:
            sess['current_band_id'] = test_band.id
        
        with client:
            login_user(test_leader)
            response = client.post(f'/band/cancel-invitation/{invitation.id}')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            
            # Verify invitation was cancelled
            db.session.refresh(invitation)
            assert invitation.status == InvitationStatus.EXPIRED


class TestBandManagementModels:
    """Test band management model methods"""
    
    def test_user_band_role(self, test_user, test_band):
        """Test getting user's role in a band"""
        # Add user to band as member
        from sqlalchemy import text
        db.session.execute(
            text('INSERT INTO band_membership (user_id, band_id, role) VALUES (:user_id, :band_id, :role)'),
            {'user_id': test_user.id, 'band_id': test_band.id, 'role': UserRole.MEMBER.value}
        )
        db.session.commit()
        
        assert test_user.get_band_role(test_band.id) == UserRole.MEMBER.value
        assert test_user.is_member_of(test_band.id) is True
        assert test_user.is_leader_of(test_band.id) is False
    
    def test_user_leader_role(self, test_user, test_band):
        """Test getting user's role in a band"""
        # Add user to band as leader
        from sqlalchemy import text
        db.session.execute(
            text('INSERT INTO band_membership (user_id, band_id, role) VALUES (:user_id, :band_id, :role)'),
            {'user_id': test_user.id, 'band_id': test_band.id, 'role': UserRole.LEADER.value}
        )
        db.session.commit()
        
        assert test_user.get_band_role(test_band.id) == UserRole.LEADER.value
        assert test_user.is_member_of(test_band.id) is True
        assert test_user.is_leader_of(test_band.id) is True
    
    def test_band_add_member(self, test_band, test_user):
        """Test adding a member to a band"""
        success = test_band.add_member(test_user, UserRole.MEMBER)
        assert success is True
        assert test_user.is_member_of(test_band.id) is True
        
        # Try to add again (should fail)
        success = test_band.add_member(test_user, UserRole.MEMBER)
        assert success is False
    
    def test_invitation_generation(self, app):
        """Test invitation code generation"""
        with app.app_context():
            code1 = Invitation.generate_code()
            code2 = Invitation.generate_code()
            
            assert len(code1) == 8
            assert len(code2) == 8
            assert code1 != code2
            assert code1.isalnum()
            assert code2.isalnum()
    
    def test_invitation_expiration(self):
        """Test invitation expiration logic"""
        # Create expired invitation
        expired_invitation = Invitation(
            code='EXPIRED1',
            band_id=1,
            invited_by='test',
            invited_email='test@example.com',
            status=InvitationStatus.PENDING,
            expires_at=datetime.utcnow() - timedelta(days=1)
        )
        
        # Create valid invitation
        valid_invitation = Invitation(
            code='VALID12',
            band_id=1,
            invited_by='test',
            invited_email='test@example.com',
            status=InvitationStatus.PENDING,
            expires_at=datetime.utcnow() + timedelta(days=1)
        )
        
        assert expired_invitation.is_expired is True
        assert valid_invitation.is_expired is False
        assert expired_invitation.is_valid is False
        assert valid_invitation.is_valid is True
