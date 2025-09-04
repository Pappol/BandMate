#!/usr/bin/env python3
"""
Test script to verify PostgreSQL setup and comprehensive seed data
"""

import os
import sys
from app import create_app, db
from app.models import User, Band, Song, SongProgress, Vote, Invitation, SetlistConfig

def test_database_connection():
    """Test database connection and basic operations"""
    print("🔍 Testing database connection...")
    
    app = create_app()
    with app.app_context():
        try:
            # Test basic connection
            result = db.session.execute(db.text("SELECT 1")).scalar()
            print(f"✅ Database connection successful: {result}")
            
            # Test table creation
            db.create_all()
            print("✅ Tables created/verified")
            
            # Test basic queries
            band_count = Band.query.count()
            user_count = User.query.count()
            song_count = Song.query.count()
            
            print(f"📊 Current data:")
            print(f"   Bands: {band_count}")
            print(f"   Users: {user_count}")
            print(f"   Songs: {song_count}")
            
            return True
            
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False

def test_comprehensive_data():
    """Test comprehensive seed data loading"""
    print("\n🌱 Testing comprehensive seed data...")
    
    try:
        from seed_loader import SeedDataLoader
        
        app = create_app()
        loader = SeedDataLoader(app)
        
        # Load comprehensive data
        seed_file = "seed_data/comprehensive_seed.json"
        if os.path.exists(seed_file):
            loader.load_comprehensive_data(seed_file)
            print("✅ Comprehensive seed data loaded successfully")
            return True
        else:
            print(f"❌ Seed file not found: {seed_file}")
            return False
            
    except Exception as e:
        print(f"❌ Failed to load comprehensive data: {e}")
        return False

def test_band_functionality():
    """Test band-related functionality"""
    print("\n🎸 Testing band functionality...")
    
    app = create_app()
    with app.app_context():
        try:
            # Test band queries
            bands = Band.query.all()
            print(f"   Found {len(bands)} bands")
            
            for band in bands:
                members = [user for user in User.query.all() if user.is_member_of(band.id)]
                active_songs = [song for song in band.songs if song.status.value == 'active']
                wishlist_songs = [song for song in band.songs if song.status.value == 'wishlist']
                
                print(f"   {band.name} ({band.emoji}): {len(members)} members, {len(active_songs)} active songs, {len(wishlist_songs)} wishlist songs")
            
            return True
            
        except Exception as e:
            print(f"❌ Band functionality test failed: {e}")
            return False

def test_user_functionality():
    """Test user-related functionality"""
    print("\n👥 Testing user functionality...")
    
    app = create_app()
    with app.app_context():
        try:
            users = User.query.all()
            print(f"   Found {len(users)} users")
            
            for user in users:
                bands = [band for band in Band.query.all() if user.is_member_of(band.id)]
                print(f"   {user.name}: member of {len(bands)} bands")
                
                for band in bands:
                    role = user.get_band_role(band.id)
                    print(f"     - {band.name}: {role}")
            
            return True
            
        except Exception as e:
            print(f"❌ User functionality test failed: {e}")
            return False

def main():
    """Run all tests"""
    print("🚀 BandMate PostgreSQL Setup Test")
    print("=" * 50)
    
    tests = [
        test_database_connection,
        test_comprehensive_data,
        test_band_functionality,
        test_user_functionality
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! PostgreSQL setup is working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
