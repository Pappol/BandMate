#!/usr/bin/env python3
"""
Migration script to add invitations table to existing database
"""

import os
import sys
from app import create_app, db
from app.models import Invitation, InvitationStatus

def migrate_invitations():
    """Add invitations table to existing database"""
    app = create_app()
    
    with app.app_context():
        try:
            # Create the invitations table
            db.create_all()
            print("✅ Invitations table created successfully")
            
            # Check if table exists
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            if 'invitations' in inspector.get_table_names():
                print("✅ Invitations table verified in database")
            else:
                print("❌ Invitations table not found in database")
                return False
                
        except Exception as e:
            print(f"❌ Error creating invitations table: {e}")
            return False
    
    return True

if __name__ == "__main__":
    print("🔄 Migrating database to add invitations table...")
    if migrate_invitations():
        print("✅ Migration completed successfully!")
    else:
        print("❌ Migration failed!")
        sys.exit(1)
