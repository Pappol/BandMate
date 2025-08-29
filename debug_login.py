#!/usr/bin/env python3
"""
Debug script to test login functionality
"""

from app import create_app, db
from app.models import User, Band
from flask_login import login_user, current_user
from sqlalchemy import text

def test_login():
    """Test the login functionality"""
    app = create_app()
    with app.app_context():
        print("🔍 Testing login functionality...")
        
        # Check if users exist
        users = User.query.all()
        print(f"📊 Found {len(users)} users:")
        for user in users:
            print(f"  - {user.email}: {user.name}")
        
        # Check if bands exist
        bands = Band.query.all()
        print(f"🎸 Found {len(bands)} bands:")
        for band in bands:
            print(f"  - {band.name} (ID: {band.id})")
        
        # Check band membership
        print("\n🔗 Checking band membership...")
        for user in users:
            print(f"\n👤 {user.name} ({user.email}):")
            print(f"  - Legacy band_id: {user.band_id}")
            print(f"  - Legacy is_band_leader: {user.is_band_leader}")
            print(f"  - New bands: {[b.name for b in user.bands]}")
            
            if user.bands:
                for band in user.bands:
                    role = user.get_band_role(band.id)
                    print(f"    - {band.name}: {role}")
        
        # Test band membership table
        print("\n📋 Checking band_membership table...")
        result = db.session.execute(text('SELECT * FROM band_membership'))
        rows = result.fetchall()
        print(f"  - Found {len(rows)} band membership records:")
        for row in rows:
            print(f"    - User: {row[0]}, Band: {row[1]}, Role: {row[2]}, Joined: {row[3]}")

if __name__ == "__main__":
    test_login()
