import pytest
from app import db
from app.models import User, Band, Invitation, InvitationStatus
from datetime import datetime, timedelta

class TestInvitationSystem:
    """Test band invitation system functionality."""
    
    def test_create_invitation(self, app, test_band, test_user):
        """Test creating a new invitation."""
        with app.app_context():
            # Test invitation creation
            invitation = Invitation(
                code=Invitation.generate_code(),
                band_id=test_band.id,
                invited_by=test_user.id,
                invited_email='newmember@example.com',
                expires_at=datetime.utcnow() + timedelta(days=7)
            )
            db.session.add(invitation)
            db.session.commit()
            
            assert invitation.id is not None
            assert len(invitation.code) == 8
            assert invitation.status == InvitationStatus.PENDING
            assert invitation.band_id == test_band.id
            assert invitation.invited_email == 'newmember@example.com'
    
    def test_invitation_code_uniqueness(self, app, test_band, test_user):
        """Test that invitation codes are unique."""
        with app.app_context():
            # Create first invitation
            invitation1 = Invitation(
                code=Invitation.generate_code(),
                band_id=test_band.id,
                invited_by=test_user.id,
                invited_email='member1@example.com',
                expires_at=datetime.utcnow() + timedelta(days=7)
            )
            db.session.add(invitation1)
            db.session.commit()
            
            # Create second invitation
            invitation2 = Invitation(
                code=Invitation.generate_code(),
                band_id=test_band.id,
                invited_by=test_user.id,
                invited_email='member2@example.com',
                expires_at=datetime.utcnow() + timedelta(days=7)
            )
            db.session.add(invitation2)
            db.session.commit()
            
            # Codes should be different
            assert invitation1.code != invitation2.code
            assert len(invitation1.code) == 8
            assert len(invitation2.code) == 8
    
    def test_invitation_expiration(self, app, test_band, test_user):
        """Test invitation expiration logic."""
        with app.app_context():
            # Create expired invitation
            expired_invitation = Invitation(
                code=Invitation.generate_code(),
                band_id=test_band.id,
                invited_by=test_user.id,
                invited_email='expired@example.com',
                expires_at=datetime.utcnow() - timedelta(days=1)  # Expired yesterday
            )
            db.session.add(expired_invitation)
            db.session.commit()
            
            # Test expiration properties
            assert expired_invitation.is_expired is True
            assert expired_invitation.is_valid is False
            
            # Create valid invitation
            valid_invitation = Invitation(
                code=Invitation.generate_code(),
                band_id=test_band.id,
                invited_by=test_user.id,
                invited_email='valid@example.com',
                expires_at=datetime.utcnow() + timedelta(days=7)  # Valid for 7 days
            )
            db.session.add(valid_invitation)
            db.session.commit()
            
            # Test validity properties
            assert valid_invitation.is_expired is False
            assert valid_invitation.is_valid is True
    
    def test_invitation_status_enum(self, app):
        """Test invitation status enum values."""
        assert InvitationStatus.PENDING.value == 'pending'
        assert InvitationStatus.ACCEPTED.value == 'accepted'
        assert InvitationStatus.EXPIRED.value == 'expired'
    
    def test_invitation_relationships(self, app, test_band, test_user):
        """Test invitation relationships."""
        with app.app_context():
            invitation = Invitation(
                code=Invitation.generate_code(),
                band_id=test_band.id,
                invited_by=test_user.id,
                invited_email='test@example.com',
                expires_at=datetime.utcnow() + timedelta(days=7)
            )
            db.session.add(invitation)
            db.session.commit()
            
            # Test relationships
            assert invitation.band == test_band
            assert invitation.inviter == test_user
            assert invitation in test_band.invitations
            assert invitation in test_user.sent_invitations
    
    def test_invitation_validation(self, app, test_band, test_user):
        """Test invitation validation logic."""
        with app.app_context():
            # Test valid invitation
            valid_invitation = Invitation(
                code=Invitation.generate_code(),
                band_id=test_band.id,
                invited_by=test_user.id,
                invited_email='valid@example.com',
                expires_at=datetime.utcnow() + timedelta(days=7)
            )
            db.session.add(valid_invitation)
            db.session.commit()
            
            # Test validation
            assert valid_invitation.is_valid is True
            
            # Test expired invitation
            expired_invitation = Invitation(
                code=Invitation.generate_code(),
                band_id=test_band.id,
                invited_by=test_user.id,
                invited_email='expired@example.com',
                expires_at=datetime.utcnow() - timedelta(days=1)
            )
            db.session.add(expired_invitation)
            db.session.commit()
            
            # Test validation
            assert expired_invitation.is_valid is False
            
            # Test accepted invitation
            accepted_invitation = Invitation(
                code=Invitation.generate_code(),
                band_id=test_band.id,
                invited_by=test_user.id,
                invited_email='accepted@example.com',
                status=InvitationStatus.ACCEPTED,
                expires_at=datetime.utcnow() + timedelta(days=7)
            )
            db.session.add(accepted_invitation)
            db.session.commit()
            
            # Test validation
            assert accepted_invitation.is_valid is False
