#!/usr/bin/env python3
"""
Migration script to add password_hash field to users table
"""

import sqlite3
import os

def migrate():
    """Add password_hash column to users table"""
    db_path = 'instance/bandmate.db'
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'password_hash' not in columns:
            # Add the new column
            cursor.execute("ALTER TABLE users ADD COLUMN password_hash VARCHAR(255)")
            print("Added password_hash column to users table")
        else:
            print("password_hash column already exists")
        
        conn.commit()
        print("Migration completed successfully")
        
    except Exception as e:
        print(f"Error during migration: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    migrate()
