#!/usr/bin/env python3
"""
Database migration script to change duration_minutes from INTEGER to FLOAT.
This allows for decimal durations (e.g., 3.5 minutes).
"""

import sqlite3
import os
from pathlib import Path

def migrate_duration_field():
    """Change duration_minutes field from INTEGER to FLOAT"""
    
    # Get the database path
    db_path = Path("instance/bandmate.db")
    
    if not db_path.exists():
        print("❌ Database not found at instance/bandmate.db")
        print("Please run the application first to create the database.")
        return False
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔍 Checking current database schema...")
        
        # Check current column type
        cursor.execute("PRAGMA table_info(songs)")
        columns = cursor.fetchall()
        
        duration_column = None
        for column in columns:
            if column[1] == 'duration_minutes':
                duration_column = column
                break
        
        if not duration_column:
            print("❌ duration_minutes column not found")
            return False
        
        current_type = duration_column[2]
        print(f"Current duration_minutes type: {current_type}")
        
        if current_type == 'FLOAT':
            print("✅ duration_minutes is already FLOAT type")
            return True
        
        print("🔄 Converting duration_minutes from INTEGER to FLOAT...")
        
        # SQLite doesn't support ALTER COLUMN TYPE directly, so we need to recreate the table
        # This is a more complex migration that preserves data
        
        # 1. Create new table with FLOAT duration
        cursor.execute("""
            CREATE TABLE songs_new (
                id INTEGER PRIMARY KEY,
                title VARCHAR(200) NOT NULL,
                artist VARCHAR(200) NOT NULL,
                status VARCHAR(20) DEFAULT 'wishlist',
                duration_minutes FLOAT,
                last_rehearsed_on DATE,
                band_id INTEGER NOT NULL,
                spotify_track_id VARCHAR(50),
                album_art_url VARCHAR(500),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (band_id) REFERENCES bands (id)
            )
        """)
        
        # 2. Copy data from old table to new table
        cursor.execute("""
            INSERT INTO songs_new 
            SELECT id, title, artist, status, duration_minutes, last_rehearsed_on, 
                   band_id, spotify_track_id, album_art_url, created_at
            FROM songs
        """)
        
        # 3. Drop old table
        cursor.execute("DROP TABLE songs")
        
        # 4. Rename new table to original name
        cursor.execute("ALTER TABLE songs_new RENAME TO songs")
        
        # 5. Recreate indexes
        cursor.execute("CREATE INDEX ix_songs_spotify_track_id ON songs(spotify_track_id)")
        
        # 6. Verify the change
        cursor.execute("PRAGMA table_info(songs)")
        final_columns = cursor.fetchall()
        
        duration_final = None
        for column in final_columns:
            if column[1] == 'duration_minutes':
                duration_final = column
                break
        
        if duration_final and duration_final[2] == 'FLOAT':
            print("✅ Successfully converted duration_minutes to FLOAT")
        else:
            print("❌ Failed to convert duration_minutes to FLOAT")
            return False
        
        # Commit changes
        conn.commit()
        
        # Check if we have any songs
        cursor.execute("SELECT COUNT(*) FROM songs")
        song_count = cursor.fetchone()[0]
        print(f"📊 Total songs in database: {song_count}")
        
        # Show some example durations
        cursor.execute("SELECT title, duration_minutes FROM songs WHERE duration_minutes IS NOT NULL LIMIT 5")
        examples = cursor.fetchall()
        if examples:
            print("\n📝 Example durations:")
            for title, duration in examples:
                print(f"   {title}: {duration} minutes")
        
        conn.close()
        
        print("\n✅ Duration field migration completed successfully!")
        print("\n📝 The duration_minutes field now supports decimal values (e.g., 3.5 minutes)")
        
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting duration field migration...")
    print("=" * 50)
    
    success = migrate_duration_field()
    
    if success:
        print("\n🎉 Migration completed! Your app now supports decimal durations.")
    else:
        print("\n💥 Migration failed. Please check the error messages above.")
        exit(1)
