#!/usr/bin/env python3
"""
Migration script to add SetlistConfig table and populate with default values.
Run this after updating the models to create the new table.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import Band, SetlistConfig

def migrate_setlist_config():
    """Add SetlistConfig table and populate with default values"""
    app = create_app()
    
    with app.app_context():
        try:
            # Create the new table
            db.create_all()
            print("✅ SetlistConfig table created successfully")
            
            # Get all existing bands
            bands = Band.query.all()
            print(f"Found {len(bands)} existing bands")
            
            # Create default configuration for each band
            for band in bands:
                # Check if config already exists
                existing_config = SetlistConfig.query.filter_by(band_id=band.id).first()
                if not existing_config:
                    config = SetlistConfig(
                        band_id=band.id,
                        new_songs_buffer_percent=20.0,
                        learned_songs_buffer_percent=10.0,
                        break_time_minutes=10,
                        break_threshold_minutes=90,
                        min_session_minutes=30,
                        max_session_minutes=240,
                        time_cluster_minutes=30
                    )
                    db.session.add(config)
                    print(f"✅ Created default config for band: {band.name}")
                else:
                    print(f"ℹ️  Config already exists for band: {band.name}")
            
            # Commit all changes
            db.session.commit()
            print("✅ Migration completed successfully!")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Migration failed: {e}")
            return False
    
    return True

if __name__ == '__main__':
    print("🚀 Starting SetlistConfig migration...")
    success = migrate_setlist_config()
    if success:
        print("🎉 Migration completed successfully!")
        sys.exit(0)
    else:
        print("💥 Migration failed!")
        sys.exit(1)

