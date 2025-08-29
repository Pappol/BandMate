#!/usr/bin/env python3
"""
Migration script to implement multi-band functionality
This script will:
1. Create the new BandMembership association table
2. Migrate existing user-band relationships
3. Update the User and Band models
"""

import os
import sys
from datetime import datetime
from app import create_app, db
from app.models import User, Band
from sqlalchemy import text

def create_band_membership_table():
    """Create the new BandMembership association table"""
    app = create_app()
    with app.app_context():
        try:
            # Create the BandMembership table
            with db.engine.connect() as conn:
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS band_membership (
                        user_id VARCHAR(50) NOT NULL,
                        band_id INTEGER NOT NULL,
                        role VARCHAR(20) NOT NULL DEFAULT 'member',
                        joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (user_id, band_id),
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                        FOREIGN KEY (band_id) REFERENCES bands(id) ON DELETE CASCADE
                    )
                """))
                conn.commit()
            print("✅ Created band_membership table")
            
            # Create index for better performance
            with db.engine.connect() as conn:
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_band_membership_user 
                    ON band_membership(user_id)
                """))
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_band_membership_band 
                    ON band_membership(band_id)
                """))
                conn.commit()
            print("✅ Created indexes for band_membership table")
            
        except Exception as e:
            print(f"❌ Error creating band_membership table: {e}")
            return False
    
    return True

def migrate_existing_relationships():
    """Migrate existing user-band relationships to the new table"""
    app = create_app()
    with app.app_context():
        try:
            # Get all existing users with their band relationships
            users = User.query.all()
            migrated_count = 0
            
            for user in users:
                if hasattr(user, 'band_id') and user.band_id:
                    # Insert into band_membership table
                    role = 'leader' if getattr(user, 'is_band_leader', False) else 'member'
                    
                    with db.engine.connect() as conn:
                        conn.execute(text("""
                            INSERT OR REPLACE INTO band_membership (user_id, band_id, role, joined_at)
                            VALUES (:user_id, :band_id, :role, :joined_at)
                        """), {"user_id": user.id, "band_id": user.band_id, "role": role, "joined_at": user.created_at})
                        conn.commit()
                    
                    migrated_count += 1
            
            print(f"✅ Migrated {migrated_count} user-band relationships")
            
        except Exception as e:
            print(f"❌ Error migrating relationships: {e}")
            return False
    
    return True

def update_user_table():
    """Update the User table to remove old columns"""
    app = create_app()
    with app.app_context():
        try:
            # Remove the old band_id and is_band_leader columns
            # Note: SQLite doesn't support DROP COLUMN, so we'll need to recreate the table
            
            # First, let's check if the columns exist
            with db.engine.connect() as conn:
                result = conn.execute(text("PRAGMA table_info(users)"))
                columns = [row[1] for row in result.fetchall()]
            
            if 'band_id' in columns or 'is_band_leader' in columns:
                print("⚠️  SQLite detected - cannot drop columns directly")
                print("   The old columns will remain but won't be used")
                print("   Consider using Flask-Migrate for proper column management")
            else:
                print("✅ Old columns already removed or don't exist")
            
        except Exception as e:
            print(f"❌ Error updating user table: {e}")
            return False
    
    return True

def verify_migration():
    """Verify that the migration was successful"""
    app = create_app()
    with app.app_context():
        try:
            # Check if band_membership table exists and has data
            with db.engine.connect() as conn:
                result = conn.execute(text("SELECT COUNT(*) FROM band_membership"))
                membership_count = result.fetchone()[0]
            
            # Check user count
            user_count = User.query.count()
            
            print(f"📊 Migration Verification:")
            print(f"   Users: {user_count}")
            print(f"   Band Memberships: {membership_count}")
            
            if membership_count > 0:
                print("✅ Migration appears successful")
                return True
            else:
                print("❌ No band memberships found - migration may have failed")
                return False
                
        except Exception as e:
            print(f"❌ Error verifying migration: {e}")
            return False

def main():
    """Main migration function"""
    print("🚀 Starting Multi-Band Migration...")
    print("=" * 50)
    
    # Step 1: Create the new table
    if not create_band_membership_table():
        print("❌ Failed to create band_membership table")
        return
    
    # Step 2: Migrate existing data
    if not migrate_existing_relationships():
        print("❌ Failed to migrate existing relationships")
        return
    
    # Step 3: Update user table (note: limited with SQLite)
    if not update_user_table():
        print("❌ Failed to update user table")
        return
    
    # Step 4: Verify migration
    if not verify_migration():
        print("❌ Migration verification failed")
        return
    
    print("=" * 50)
    print("🎉 Multi-Band Migration Completed Successfully!")
    print("\n📝 Next Steps:")
    print("1. Update the models.py file to use the new relationships")
    print("2. Update the routes to handle multiple bands")
    print("3. Add band switching functionality")
    print("4. Test the new multi-band features")

if __name__ == "__main__":
    main()
