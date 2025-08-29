#!/usr/bin/env python3
"""
Database migration script to convert duration from minutes to seconds.
This changes the duration_minutes field to duration_seconds and converts existing values.
"""

import sqlite3
import os
from pathlib import Path

def migrate_duration_to_seconds():
    """Convert duration from minutes to seconds"""
    
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
        
        print("🔄 Converting duration from minutes to seconds...")
        
        # 1. Create new table with duration_seconds field
        cursor.execute("""
            CREATE TABLE songs_new (
                id INTEGER PRIMARY KEY,
                title VARCHAR(200) NOT NULL,
                artist VARCHAR(200) NOT NULL,
                status VARCHAR(20) DEFAULT 'wishlist',
                duration_seconds INTEGER,
                last_rehearsed_on DATE,
                band_id INTEGER NOT NULL,
                spotify_track_id VARCHAR(50),
                album_art_url VARCHAR(500),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (band_id) REFERENCES bands (id)
            )
        """)
        
        # 2. Copy data from old table to new table, converting duration
        cursor.execute("""
            INSERT INTO songs_new 
            SELECT id, title, artist, status, 
                   CASE 
                       WHEN duration_minutes IS NOT NULL THEN CAST(duration_minutes * 60 AS INTEGER)
                       ELSE NULL 
                   END as duration_seconds,
                   last_rehearsed_on, band_id, spotify_track_id, album_art_url, created_at
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
            if column[1] == 'duration_seconds':
                duration_final = column
                break
        
        if duration_final and duration_final[2] == 'INTEGER':
            print("✅ Successfully converted duration to seconds")
        else:
            print("❌ Failed to convert duration to seconds")
            return False
        
        # Commit changes
        conn.commit()
        
        # Check if we have any songs
        cursor.execute("SELECT COUNT(*) FROM songs")
        song_count = cursor.fetchone()[0]
        print(f"📊 Total songs in database: {song_count}")
        
        # Show some example durations
        cursor.execute("SELECT title, duration_seconds FROM songs WHERE duration_seconds IS NOT NULL LIMIT 5")
        examples = cursor.fetchall()
        if examples:
            print("\n📝 Example durations (converted to seconds):")
            for title, duration_seconds in examples:
                minutes = duration_seconds // 60
                seconds = duration_seconds % 60
                print(f"   {title}: {minutes}:{seconds:02d} ({duration_seconds} seconds)")
        
        conn.close()
        
        print("\n✅ Duration migration completed successfully!")
        print("\n📝 The duration is now stored in seconds and displayed in MM:SS format")
        print("   Examples: 3:45, 6:30, 8:15")
        
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting duration to seconds migration...")
    print("=" * 50)
    
    success = migrate_duration_to_seconds()
    
    if success:
        print("\n🎉 Migration completed! Your app now uses seconds for duration.")
    else:
        print("\n💥 Migration failed. Please check the error messages above.")
        exit(1)
