#!/usr/bin/env python3
"""
BandMate Management Script
Handles database operations, seeding, and other management tasks
"""

import os
import sys
from datetime import datetime, date, timedelta
from pathlib import Path
from app import create_app, db
from app.models import User, Band, Song, SongProgress, Vote, SongStatus, ProgressStatus, UserRole
from sqlalchemy import text
from seed_loader import SeedDataLoader

def create_tables():
    """Create all database tables"""
    app = create_app()
    with app.app_context():
        db.create_all()
        print("✅ Database tables created successfully")
        print(f"   Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")

def seed_database():
    """Seed the database with demo data"""
    app = create_app()
    with app.app_context():
        # Clear existing data
        Vote.query.delete()
        SongProgress.query.delete()
        Song.query.delete()
        User.query.delete()
        Band.query.delete()
        
        # Clear band membership table
        db.session.execute(text('DELETE FROM band_membership'))
        
        print("🗑️  Cleared existing data")
        
        # Create demo band
        band = Band(name="The Demo Band")
        db.session.add(band)
        db.session.flush()  # Get the ID
        
        print(f"🎸 Created band: {band.name}")
        
        # Create demo users
        users_data = [
            {"name": "Alice Johnson", "email": "alice@demo.com", "is_leader": True},
            {"name": "Bob Smith", "email": "bob@demo.com", "is_leader": False},
            {"name": "Carla Rodriguez", "email": "carla@demo.com", "is_leader": False}
        ]
        
        users = []
        for user_data in users_data:
            user = User(
                id=f"demo_{user_data['email']}",
                name=user_data['name'],
                email=user_data['email'],
                band_id=band.id,
                is_band_leader=user_data['is_leader']
            )
            users.append(user)
            db.session.add(user)
        
        db.session.flush()
        print(f"👥 Created {len(users)} users")
        
        # Create new band membership records for the multi-band system
        
        for i, user in enumerate(users):
            role = UserRole.LEADER if users_data[i]['is_leader'] else UserRole.MEMBER
            # Insert into band_membership table
            db.session.execute(
                text('INSERT INTO band_membership (user_id, band_id, role, joined_at) VALUES (:user_id, :band_id, :role, :joined_at)'),
                {
                    'user_id': user.id,
                    'band_id': band.id,
                    'role': role.value,
                    'joined_at': datetime.utcnow()
                }
            )
        
        print("🔗 Created band membership records")
        
        # Create demo songs
        songs_data = [
            {
                "title": "Bohemian Rhapsody",
                "artist": "Queen",
                "status": SongStatus.ACTIVE,
                "duration_seconds": 360,
                "last_rehearsed_on": date.today() - timedelta(days=2)
            },
            {
                "title": "Hotel California",
                "artist": "Eagles",
                "status": SongStatus.ACTIVE,
                "duration_seconds": 360,
                "last_rehearsed_on": date.today() - timedelta(days=7)
            },
            {
                "title": "Stairway to Heaven",
                "artist": "Led Zeppelin",
                "status": SongStatus.ACTIVE,
                "duration_seconds": 480,
                "last_rehearsed_on": date.today() - timedelta(days=14)
            },
            {
                "title": "Sweet Child O' Mine",
                "artist": "Guns N' Roses",
                "status": SongStatus.ACTIVE,
                "duration_seconds": 300,
                "last_rehearsed_on": date.today() - timedelta(days=21)
            },
            {
                "title": "Wonderwall",
                "artist": "Oasis",
                "status": SongStatus.ACTIVE,
                "duration_seconds": 240,
                "last_rehearsed_on": date.today() - timedelta(days=30)
            },
            {
                "title": "Creep",
                "artist": "Radiohead",
                "status": SongStatus.WISHLIST,
                "duration_seconds": 240
            },
            {
                "title": "Zombie",
                "artist": "The Cranberries",
                "status": SongStatus.WISHLIST,
                "duration_seconds": 300
            },
            {
                "title": "Smells Like Teen Spirit",
                "artist": "Nirvana",
                "status": SongStatus.WISHLIST,
                "duration_seconds": 300
            }
        ]
        
        songs = []
        for song_data in songs_data:
            song = Song(
                title=song_data['title'],
                artist=song_data['artist'],
                status=song_data['status'],
                duration_seconds=song_data['duration_seconds'],
                last_rehearsed_on=song_data.get('last_rehearsed_on'),
                band_id=band.id
            )
            songs.append(song)
            db.session.add(song)
        
        db.session.flush()
        print(f"🎵 Created {len(songs)} songs")
        
        # Create progress records for active songs
        progress_statuses = [ProgressStatus.TO_LISTEN, ProgressStatus.IN_PRACTICE, ProgressStatus.READY_FOR_REHEARSAL, ProgressStatus.MASTERED]
        
        for song in songs:
            if song.status == SongStatus.ACTIVE:
                for i, user in enumerate(users):
                    # Vary progress based on user and song
                    if i == 0:  # Alice (leader) - generally more advanced
                        status = progress_statuses[min(3, i + 2)]
                    elif i == 1:  # Bob - intermediate
                        status = progress_statuses[min(3, i + 1)]
                    else:  # Carla - beginner
                        status = progress_statuses[i]
                    
                    progress = SongProgress(
                        user_id=user.id,
                        song_id=song.id,
                        status=status
                    )
                    db.session.add(progress)
        
        print("📊 Created progress records")
        
        # Create some votes on wishlist songs
        wishlist_songs = [s for s in songs if s.status == SongStatus.WISHLIST]
        for song in wishlist_songs:
            # Random voting pattern
            for user in users:
                if hash(f"{user.id}{song.id}") % 3 == 0:  # 1/3 chance to vote
                    vote = Vote(
                        user_id=user.id,
                        song_id=song.id
                    )
                    db.session.add(vote)
        
        print("🗳️  Created vote records")
        
        # Commit everything
        db.session.commit()
        print("✅ Database seeded successfully!")
        print(f"\n📋 Summary:")
        print(f"   Band: {band.name}")
        print(f"   Users: {len(users)}")
        print(f"   Songs: {len(songs)} (Active: {len([s for s in songs if s.status == SongStatus.ACTIVE])}, Wishlist: {len([s for s in songs if s.status == SongStatus.WISHLIST])})")
        print(f"\n🔑 Demo Login:")
        print(f"   Use any of these emails with Google OAuth:")
        for user in users:
            print(f"   - {user.email} ({'Leader' if user.is_band_leader else 'Member'})")

def reset_database():
    """Reset the database (drop all tables and recreate)"""
    app = create_app()
    with app.app_context():
        db.drop_all()
        print("🗑️  Dropped all tables")
        db.create_all()
        print("✅ Recreated all tables")

def show_status():
    """Show current database status"""
    app = create_app()
    with app.app_context():
        try:
            band_count = Band.query.count()
            user_count = User.query.count()
            song_count = Song.query.count()
            progress_count = SongProgress.query.count()
            vote_count = Vote.query.count()
            
            print("📊 Database Status:")
            print(f"   Bands: {band_count}")
            print(f"   Users: {user_count}")
            print(f"   Songs: {song_count}")
            print(f"   Progress Records: {progress_count}")
            print(f"   Votes: {vote_count}")
            
            if band_count > 0:
                print(f"\n🎸 Band Details:")
                for band in Band.query.all():
                    print(f"   {band.name} (ID: {band.id})")
                    print(f"     Members: {len(band.members)}")
                    print(f"     Songs: {len(band.songs)}")
                    
        except Exception as e:
            print(f"❌ Error checking status: {e}")

def seed_comprehensive():
    """Seed database with comprehensive production data"""
    app = create_app()
    loader = SeedDataLoader(app)
    
    # Path to comprehensive seed data
    seed_file = Path(__file__).parent / 'seed_data' / 'comprehensive_seed.json'
    
    if not seed_file.exists():
        print(f"❌ Comprehensive seed file not found: {seed_file}")
        return
    
    loader.load_comprehensive_data(seed_file)

def main():
    """Main CLI interface"""
    if len(sys.argv) < 2:
        print("BandMate Management Script")
        print("\nUsage:")
        print("  python manage.py create-tables     - Create database tables")
        print("  python manage.py seed              - Seed database with demo data")
        print("  python manage.py seed-comprehensive - Seed database with comprehensive production data")
        print("  python manage.py reset             - Reset database (drop all tables)")
        print("  python manage.py status            - Show database status")
        print("  python manage.py init-db           - Initialize database with comprehensive data")
        return
    
    command = sys.argv[1]
    
    if command == "create-tables":
        create_tables()
    elif command == "seed":
        seed_database()
    elif command == "seed-comprehensive":
        seed_comprehensive()
    elif command == "reset":
        reset_database()
    elif command == "status":
        show_status()
    elif command == "init-db":
        print("🚀 Initializing database with comprehensive data...")
        create_tables()
        seed_comprehensive()
    else:
        print(f"❌ Unknown command: {command}")
        print("Use: create-tables, seed, seed-comprehensive, reset, status, or init-db")

if __name__ == "__main__":
    main()
