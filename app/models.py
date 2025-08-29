from app import db
from flask_login import UserMixin
from datetime import datetime, date, timedelta
from enum import Enum
import uuid

class SongStatus(Enum):
    WISHLIST = 'wishlist'
    ACTIVE = 'active'

class ProgressStatus(Enum):
    TO_LISTEN = 'To Listen'
    IN_PRACTICE = 'In Practice'
    READY_FOR_REHEARSAL = 'Ready for Rehearsal'
    MASTERED = 'Mastered'

class InvitationStatus(Enum):
    PENDING = 'pending'
    ACCEPTED = 'accepted'
    EXPIRED = 'expired'

class Invitation(db.Model):
    """Band invitation model"""
    __tablename__ = 'invitations'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), unique=True, nullable=False, index=True)
    band_id = db.Column(db.Integer, db.ForeignKey('bands.id'), nullable=False)
    invited_by = db.Column(db.String(50), db.ForeignKey('users.id'), nullable=False)
    invited_email = db.Column(db.String(120), nullable=False)
    status = db.Column(db.Enum(InvitationStatus), default=InvitationStatus.PENDING)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    band = db.relationship('Band', back_populates='invitations')
    inviter = db.relationship('User', foreign_keys=[invited_by])
    
    def __repr__(self):
        return f'<Invitation {self.code} for {self.invited_email}>'
    
    @staticmethod
    def generate_code():
        """Generate a unique 8-character invitation code"""
        import random
        import string
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            if not Invitation.query.filter_by(code=code).first():
                return code
    
    @property
    def is_expired(self):
        """Check if invitation has expired"""
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_valid(self):
        """Check if invitation is valid and not expired"""
        return self.status == InvitationStatus.PENDING and not self.is_expired

class User(UserMixin, db.Model):
    """User model for band members"""
    __tablename__ = 'users'
    
    id = db.Column(db.String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    band_id = db.Column(db.Integer, db.ForeignKey('bands.id'), nullable=False)
    is_band_leader = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    band = db.relationship('Band', back_populates='members')
    progress = db.relationship('SongProgress', back_populates='user', cascade='all, delete-orphan')
    votes = db.relationship('Vote', back_populates='user', cascade='all, delete-orphan')
    sent_invitations = db.relationship('Invitation', foreign_keys='Invitation.invited_by', back_populates='inviter')
    
    def __repr__(self):
        return f'<User {self.name}>'

class Band(db.Model):
    """Band model"""
    __tablename__ = 'bands'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    members = db.relationship('User', back_populates='band', cascade='all, delete-orphan')
    songs = db.relationship('Song', back_populates='band', cascade='all, delete-orphan')
    invitations = db.relationship('Invitation', back_populates='band', cascade='all, delete-orphan')
    setlist_config = db.relationship('SetlistConfig', back_populates='band', uselist=False, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Band {self.name}>'
    
    def get_setlist_config(self):
        """Get or create default setlist configuration for the band"""
        if not self.setlist_config:
            # Create default configuration
            config = SetlistConfig(band_id=self.id)
            db.session.add(config)
            db.session.flush()  # Use flush instead of commit to avoid transaction issues
            return config
        return self.setlist_config

class Song(db.Model):
    """Song model"""
    __tablename__ = 'songs'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    artist = db.Column(db.String(200), nullable=False)
    status = db.Column(db.Enum(SongStatus), default=SongStatus.WISHLIST)
    duration_seconds = db.Column(db.Integer, nullable=True)
    last_rehearsed_on = db.Column(db.Date, nullable=True)
    band_id = db.Column(db.Integer, db.ForeignKey('bands.id'), nullable=False)
    spotify_track_id = db.Column(db.String(50), nullable=True, index=True)
    album_art_url = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    band = db.relationship('Band', back_populates='songs')
    progress = db.relationship('SongProgress', back_populates='song', cascade='all, delete-orphan')
    votes = db.relationship('Vote', back_populates='song', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Song {self.title} by {self.artist}>'
    
    @property
    def readiness_score(self):
        """Calculate overall readiness score for the song based on member progress"""
        if not self.progress:
            return 0
        
        total_progress = 0
        for prog in self.progress:
            if prog.status == ProgressStatus.MASTERED:
                total_progress += 4
            elif prog.status == ProgressStatus.READY_FOR_REHEARSAL:
                total_progress += 3
            elif prog.status == ProgressStatus.IN_PRACTICE:
                total_progress += 2
            elif prog.status == ProgressStatus.TO_LISTEN:
                total_progress += 1
        
        return total_progress / len(self.progress) if self.progress else 0

class SongProgress(db.Model):
    """Track individual member progress on songs"""
    __tablename__ = 'song_progress'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), db.ForeignKey('users.id'), nullable=False)
    song_id = db.Column(db.Integer, db.ForeignKey('songs.id'), nullable=False)
    status = db.Column(db.Enum(ProgressStatus), default=ProgressStatus.TO_LISTEN)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='progress')
    song = db.relationship('Song', back_populates='progress')
    
    # Unique constraint to ensure one progress record per user per song
    __table_args__ = (db.UniqueConstraint('user_id', 'song_id'),)
    
    def __repr__(self):
        return f'<SongProgress {self.user.name} - {self.song.title}: {self.status.value}>'

class Vote(db.Model):
    """Votes on wishlist songs"""
    __tablename__ = 'votes'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), db.ForeignKey('users.id'), nullable=False)
    song_id = db.Column(db.Integer, db.ForeignKey('songs.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='votes')
    song = db.relationship('Song', back_populates='votes')
    
    # Unique constraint to ensure one vote per user per song
    __table_args__ = (db.UniqueConstraint('user_id', 'song_id'),)
    
    def __repr__(self):
        return f'<Vote {self.user.name} -> {self.song.title}>'

class SetlistConfig(db.Model):
    """Band-specific setlist generation configuration"""
    __tablename__ = 'setlist_configs'
    
    id = db.Column(db.Integer, primary_key=True)
    band_id = db.Column(db.Integer, db.ForeignKey('bands.id'), nullable=False, unique=True)
    
    # Buffer percentages for time calculation
    new_songs_buffer_percent = db.Column(db.Float, default=20.0, nullable=False)  # 20% for new songs
    learned_songs_buffer_percent = db.Column(db.Float, default=10.0, nullable=False)  # 10% for mastered songs
    
    # Break time configuration
    break_time_minutes = db.Column(db.Integer, default=10, nullable=False)
    break_threshold_minutes = db.Column(db.Integer, default=90, nullable=False)  # Add break if session > 90 min
    
    # Time clustering settings
    min_session_minutes = db.Column(db.Integer, default=30, nullable=False)
    max_session_minutes = db.Column(db.Integer, default=240, nullable=False)  # 4 hours max
    time_cluster_minutes = db.Column(db.Integer, default=30, nullable=False)  # 30-minute intervals
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    band = db.relationship('Band', back_populates='setlist_config')
    
    def __repr__(self):
        return f'<SetlistConfig for {self.band.name}>'
    
    def is_break_needed(self, session_duration_minutes):
        """Check if break should be added based on session duration"""
        return session_duration_minutes >= self.break_threshold_minutes
    
    def get_clustered_duration(self, target_duration_minutes):
        """Cluster duration to nearest 30-minute interval within min/max bounds"""
        if target_duration_minutes < self.min_session_minutes:
            return self.min_session_minutes
        
        if target_duration_minutes > self.max_session_minutes:
            return self.max_session_minutes
        
        # Round to nearest 30-minute interval
        rounded = round(target_duration_minutes / self.time_cluster_minutes) * self.time_cluster_minutes
        
        # Ensure the rounded value is within bounds
        if rounded < self.min_session_minutes:
            rounded = self.min_session_minutes
        elif rounded > self.max_session_minutes:
            rounded = self.max_session_minutes
            
        return rounded
    
    def calculate_song_duration_with_buffer(self, song_duration_seconds, is_learned):
        """Calculate song duration with appropriate buffer percentage"""
        duration_minutes = song_duration_seconds / 60
        
        if is_learned:
            buffer_multiplier = 1 + (self.learned_songs_buffer_percent / 100)
        else:
            buffer_multiplier = 1 + (self.new_songs_buffer_percent / 100)
        
        return duration_minutes * buffer_multiplier
