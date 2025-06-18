#!/usr/bin/env python3
"""
Database migration runner for adding missing columns to tag_analysis table
"""

import os
import sys
from pathlib import Path
import logging

# Add src to path
sys.path.append('src')

from sqlalchemy import text
from models.database import get_session, close_session

def run_migration():
    """Run the tag_analysis columns migration"""
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Read migration file
    migration_file = Path("migrations/add_tag_analysis_columns.sql")
    
    if not migration_file.exists():
        logger.error(f"Migration file not found: {migration_file}")
        return False
    
    try:
        with open(migration_file, 'r') as f:
            migration_sql = f.read()
        
        logger.info("Starting migration: add_tag_analysis_columns...")
        
        # Execute migration
        session = get_session()
        
        # Execute the entire migration as one block to handle functions properly
        logger.info("Executing migration SQL...")
        session.execute(text(migration_sql))
        
        session.commit()
        logger.info("✅ Migration completed successfully!")
        
        # Verify the columns were added
        result = session.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'tag_analysis' 
            AND column_name IN ('trend_score', 'updated_at', 'co_occurring_tags')
            ORDER BY column_name
        """)).fetchall()
        
        logger.info("✅ Verified new columns:")
        for row in result:
            logger.info(f"  - {row[0]}: {row[1]}")
        
        close_session(session)
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        if 'session' in locals():
            session.rollback()
            close_session(session)
        return False

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1) 