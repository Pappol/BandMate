#!/usr/bin/env python3
"""
Database migration script to add Spotify API fields to the songs table.
Run this script after updating the models to add the new columns.
"""

import sqlite3
import os
from pathlib import Path

def migrate_database():
    """Add Spotify fields to the songs table"""
    
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
        
        # Check if the columns already exist
        cursor.execute("PRAGMA table_info(songs)")
        columns = [column[1] for column in cursor.fetchall()]
        
        print(f"Current columns in songs table: {columns}")
        
        # Add new columns if they don't exist
        new_columns = [
            ('spotify_track_id', 'TEXT'),
            ('album_art_url', 'TEXT')
        ]
        
        for column_name, column_type in new_columns:
            if column_name not in columns:
                print(f"➕ Adding column: {column_name}")
                cursor.execute(f"ALTER TABLE songs ADD COLUMN {column_name} {column_type}")
                print(f"✅ Added column: {column_name}")
            else:
                print(f"ℹ️  Column {column_name} already exists")
        
        # Create index on spotify_track_id if it doesn't exist
        cursor.execute("PRAGMA index_list(songs)")
        indexes = [index[1] for index in cursor.fetchall()]
        
        if 'ix_songs_spotify_track_id' not in indexes:
            print("➕ Creating index on spotify_track_id")
            cursor.execute("CREATE INDEX ix_songs_spotify_track_id ON songs(spotify_track_id)")
            print("✅ Created index on spotify_track_id")
        else:
            print("ℹ️  Index on spotify_track_id already exists")
        
        # Commit changes
        conn.commit()
        
        # Verify the changes
        cursor.execute("PRAGMA table_info(songs)")
        final_columns = [column[1] for column in cursor.fetchall()]
        print(f"\n🎯 Final columns in songs table: {final_columns}")
        
        # Check if we have any songs
        cursor.execute("SELECT COUNT(*) FROM songs")
        song_count = cursor.fetchone()[0]
        print(f"📊 Total songs in database: {song_count}")
        
        conn.close()
        
        print("\n✅ Migration completed successfully!")
        print("\n📝 Next steps:")
        print("1. Set your Spotify API credentials in .env:")
        print("   SPOTIFY_CLIENT_ID=your-spotify-client-id")
        print("   SPOTIFY_CLIENT_SECRET=your-spotify-client-secret")
        print("2. Restart your Flask application")
        print("3. Test the new Spotify search functionality!")
        
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Spotify API database migration...")
    print("=" * 50)
    
    success = migrate_database()
    
    if success:
        print("\n🎉 Migration completed! Your app is ready for Spotify integration.")
    else:
        print("\n💥 Migration failed. Please check the error messages above.")
        exit(1)
