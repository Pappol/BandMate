#!/usr/bin/env python3
"""
Comprehensive seed data loader for BandMate production database
Loads realistic data with multiple bands, users, songs, and relationships
"""

import json
import os
import uuid
from datetime import datetime, date, timedelta
from pathlib import Path

from app import create_app, db
from app.models import (
    User, Band, Song, SongProgress, Vote, Invitation, SetlistConfig,
    SongStatus, ProgressStatus, InvitationStatus, UserRole
)
from sqlalchemy import text


class SeedDataLoader:
    """Loads comprehensive seed data into the database"""
    
    def __init__(self, app):
        self.app = app
        self.bands = {}
        self.users = {}
        self.songs = {}
        
    def load_from_file(self, file_path):
        """Load seed data from JSON file"""
        with open(file_path, 'r') as f:
            return json.load(f)
    
    def clear_existing_data(self):
        """Clear all existing data from the database"""
        print("🗑️  Clearing existing data...")
        
        # Clear in correct order to respect foreign key constraints
        Vote.query.delete()
        SongProgress.query.delete()
        Song.query.delete()
        Invitation.query.delete()
        SetlistConfig.query.delete()
        
        # Clear band membership table
        db.session.execute(text('DELETE FROM band_membership'))
        
        User.query.delete()
        Band.query.delete()
        
        db.session.commit()
        print("✅ Existing data cleared")
    
    def create_bands(self, bands_data):
        """Create bands from seed data"""
        print("🎸 Creating bands...")
        
        for band_data in bands_data:
            band = Band(
                name=band_data['name'],
                emoji=band_data.get('emoji'),
                color=band_data.get('color'),
                letter=band_data.get('letter'),
                allow_member_invites=band_data.get('allow_member_invites', False)
            )
            db.session.add(band)
            db.session.flush()  # Get the ID
            
            self.bands[band_data['name']] = band
            print(f"   Created band: {band.name} ({band.emoji})")
        
        db.session.commit()
        print(f"✅ Created {len(bands_data)} bands")
    
    def create_users(self, users_data):
        """Create users from seed data"""
        print("👥 Creating users...")
        
        for user_data in users_data:
            user = User(
                id=f"seed_{user_data['email']}",
                name=user_data['name'],
                email=user_data['email']
            )
            db.session.add(user)
            db.session.flush()  # Get the ID
            
            self.users[user_data['email']] = user
            print(f"   Created user: {user.name} ({user_data.get('instrument', 'Unknown')})")
        
        db.session.commit()
        print(f"✅ Created {len(users_data)} users")
    
    def create_band_memberships(self, users_data):
        """Create band memberships from seed data"""
        print("🔗 Creating band memberships...")
        
        for user_data in users_data:
            user = self.users[user_data['email']]
            
            for band_name, role_name in user_data.get('roles', {}).items():
                if band_name in self.bands:
                    band = self.bands[band_name]
                    role = UserRole.LEADER if role_name == 'leader' else UserRole.MEMBER
                    
                    # Insert into band_membership table
                    db.session.execute(
                        text('INSERT INTO band_membership (user_id, band_id, role, joined_at) VALUES (:user_id, :band_id, :role, :joined_at)'),
                        {
                            'user_id': user.id,
                            'band_id': band.id,
                            'role': role.value,
                            'joined_at': datetime.utcnow() - timedelta(days=30)  # Joined 30 days ago
                        }
                    )
                    print(f"   Added {user.name} to {band.name} as {role.value}")
        
        db.session.commit()
        print("✅ Band memberships created")
    
    def create_songs(self, songs_data):
        """Create songs from seed data"""
        print("🎵 Creating songs...")
        
        total_songs = 0
        for band_name, band_songs in songs_data.items():
            if band_name not in self.bands:
                continue
                
            band = self.bands[band_name]
            
            for song_data in band_songs:
                # Parse last_rehearsed_on if it exists
                last_rehearsed = None
                if song_data.get('last_rehearsed_on'):
                    last_rehearsed = datetime.strptime(song_data['last_rehearsed_on'], '%Y-%m-%d').date()
                
                song = Song(
                    title=song_data['title'],
                    artist=song_data['artist'],
                    status=SongStatus.ACTIVE if song_data['status'] == 'active' else SongStatus.WISHLIST,
                    duration_seconds=song_data['duration_seconds'],
                    last_rehearsed_on=last_rehearsed,
                    band_id=band.id,
                    spotify_track_id=song_data.get('spotify_track_id'),
                    album_art_url=song_data.get('album_art_url')
                )
                db.session.add(song)
                db.session.flush()  # Get the ID
                
                self.songs[f"{band_name}_{song_data['title']}"] = song
                total_songs += 1
                print(f"   Created song: {song.title} by {song.artist} for {band.name}")
        
        db.session.commit()
        print(f"✅ Created {total_songs} songs")
    
    def create_song_progress(self, progress_patterns, users_data):
        """Create song progress records"""
        print("📊 Creating song progress records...")
        
        progress_count = 0
        for band_name, user_patterns in progress_patterns.items():
            if band_name not in self.bands:
                continue
                
            band = self.bands[band_name]
            band_songs = [song for song in band.songs if song.status == SongStatus.ACTIVE]
            
            for user_email, pattern in user_patterns.items():
                if user_email not in self.users:
                    continue
                    
                user = self.users[user_email]
                
                # Determine progress status based on pattern
                if pattern == 'advanced':
                    statuses = [ProgressStatus.MASTERED, ProgressStatus.READY_FOR_REHEARSAL, ProgressStatus.IN_PRACTICE]
                elif pattern == 'intermediate':
                    statuses = [ProgressStatus.READY_FOR_REHEARSAL, ProgressStatus.IN_PRACTICE, ProgressStatus.TO_LISTEN]
                else:  # beginner
                    statuses = [ProgressStatus.IN_PRACTICE, ProgressStatus.TO_LISTEN, ProgressStatus.TO_LISTEN]
                
                for i, song in enumerate(band_songs):
                    # Vary progress based on song and user
                    status = statuses[i % len(statuses)]
                    
                    progress = SongProgress(
                        user_id=user.id,
                        song_id=song.id,
                        status=status,
                        updated_at=datetime.utcnow() - timedelta(days=7-i)  # Stagger updates
                    )
                    db.session.add(progress)
                    progress_count += 1
        
        db.session.commit()
        print(f"✅ Created {progress_count} progress records")
    
    def create_votes(self, songs_data):
        """Create votes on wishlist songs"""
        print("🗳️  Creating votes...")
        
        vote_count = 0
        for band_name, band_songs in songs_data.items():
            if band_name not in self.bands:
                continue
                
            band = self.bands[band_name]
            wishlist_songs = [song for song in band.songs if song.status == SongStatus.WISHLIST]
            band_members = [user for user in self.users.values() if user.is_member_of(band.id)]
            
            for song in wishlist_songs:
                # Random voting pattern - 60% chance each member votes
                for user in band_members:
                    if hash(f"{user.id}{song.id}") % 10 < 6:  # 60% chance
                        vote = Vote(
                            user_id=user.id,
                            song_id=song.id
                        )
                        db.session.add(vote)
                        vote_count += 1
        
        db.session.commit()
        print(f"✅ Created {vote_count} votes")
    
    def create_setlist_configs(self, setlist_configs):
        """Create setlist configurations for bands"""
        print("⚙️  Creating setlist configurations...")
        
        for band_name, config_data in setlist_configs.items():
            if band_name not in self.bands:
                continue
                
            band = self.bands[band_name]
            
            config = SetlistConfig(
                band_id=band.id,
                new_songs_buffer_percent=config_data['new_songs_buffer_percent'],
                learned_songs_buffer_percent=config_data['learned_songs_buffer_percent'],
                break_time_minutes=config_data['break_time_minutes'],
                break_threshold_minutes=config_data['break_threshold_minutes'],
                min_session_minutes=config_data['min_session_minutes'],
                max_session_minutes=config_data['max_session_minutes'],
                time_cluster_minutes=config_data['time_cluster_minutes']
            )
            db.session.add(config)
            print(f"   Created setlist config for {band.name}")
        
        db.session.commit()
        print("✅ Setlist configurations created")
    
    def create_invitations(self, invitations_data):
        """Create pending invitations"""
        print("📧 Creating invitations...")
        
        for inv_data in invitations_data:
            band_name = inv_data['band']
            if band_name not in self.bands:
                continue
                
            band = self.bands[band_name]
            inviter_email = inv_data['invited_by']
            if inviter_email not in self.users:
                continue
                
            inviter = self.users[inviter_email]
            
            invitation = Invitation(
                code=Invitation.generate_code(),
                band_id=band.id,
                invited_by=inviter.id,
                invited_email=inv_data['invited_email'],
                status=InvitationStatus.PENDING if inv_data['status'] == 'pending' else InvitationStatus.ACCEPTED,
                expires_at=datetime.utcnow() + timedelta(days=inv_data['expires_in_days'])
            )
            db.session.add(invitation)
            print(f"   Created invitation: {invitation.code} for {inv_data['invited_email']}")
        
        db.session.commit()
        print("✅ Invitations created")
    
    def load_comprehensive_data(self, seed_file_path):
        """Load all comprehensive seed data"""
        print("🚀 Loading comprehensive seed data...")
        print("=" * 50)
        
        # Load data from file
        data = self.load_from_file(seed_file_path)
        
        with self.app.app_context():
            # Clear existing data
            self.clear_existing_data()
            
            # Create all entities
            self.create_bands(data['bands'])
            self.create_users(data['users'])
            self.create_band_memberships(data['users'])
            self.create_songs(data['songs'])
            self.create_song_progress(data['progress_patterns'], data['users'])
            self.create_votes(data['songs'])
            self.create_setlist_configs(data['setlist_configs'])
            self.create_invitations(data['invitations'])
            
            print("=" * 50)
            print("🎉 Comprehensive seed data loaded successfully!")
            self.print_summary()
    
    def print_summary(self):
        """Print summary of loaded data"""
        print("\n📋 Data Summary:")
        print(f"   Bands: {Band.query.count()}")
        print(f"   Users: {User.query.count()}")
        print(f"   Songs: {Song.query.count()}")
        print(f"   Progress Records: {SongProgress.query.count()}")
        print(f"   Votes: {Vote.query.count()}")
        print(f"   Invitations: {Invitation.query.count()}")
        print(f"   Setlist Configs: {SetlistConfig.query.count()}")
        
        print("\n🎸 Band Details:")
        for band in Band.query.all():
            member_count = len([user for user in self.users.values() if user.is_member_of(band.id)])
            active_songs = len([song for song in band.songs if song.status == SongStatus.ACTIVE])
            wishlist_songs = len([song for song in band.songs if song.status == SongStatus.WISHLIST])
            print(f"   {band.name} ({band.emoji}): {member_count} members, {active_songs} active songs, {wishlist_songs} wishlist songs")


def main():
    """Main function to load comprehensive seed data"""
    app = create_app()
    loader = SeedDataLoader(app)
    
    # Path to comprehensive seed data
    seed_file = Path(__file__).parent / 'seed_data' / 'comprehensive_seed.json'
    
    if not seed_file.exists():
        print(f"❌ Seed file not found: {seed_file}")
        return
    
    loader.load_comprehensive_data(seed_file)


if __name__ == "__main__":
    main()
