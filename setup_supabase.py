#!/usr/bin/env python3
"""
Setup script for Supabase database initialization
"""

import os
import sys
from datetime import datetime, date, timedelta
import logging
from sqlalchemy import text

# Add src to path
sys.path.append('src')

from models.database import (
    create_tables, get_session, close_session,
    Photo, PhotoStatistic, SearchTrend, TagAnalysis, 
    TagCooccurrence, PhotographerAnalysis, DailyTrend, ETLJob
)

def check_supabase_connection():
    """Check if we can connect to Supabase"""
    try:
        session = get_session()
        # Test a simple query
        result = session.execute(text("SELECT 1 as test")).fetchone()
        close_session(session)
        
        if result and result[0] == 1:
            print("✅ Successfully connected to Supabase!")
            return True
        else:
            print("❌ Supabase connection test failed")
            return False
            
    except Exception as e:
        print(f"❌ Failed to connect to Supabase: {e}")
        print("\n💡 Make sure you have:")
        print("1. Set your Supabase credentials in .env file")
        print("2. Your Supabase project is running")
        print("3. The database is accessible from your IP")
        return False

def create_supabase_tables():
    """Create tables in Supabase"""
    try:
        print("📋 Creating database tables...")
        create_tables()
        print("✅ Tables created successfully!")
        return True
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False

def create_sample_data():
    """Create sample data for testing"""
    session = get_session()
    
    try:
        # Check if we already have data
        existing_photos = session.query(Photo).count()
        if existing_photos > 0:
            print(f"📊 Found {existing_photos} existing photos. Skipping sample data creation.")
            return True
        
        print("📊 Creating sample data...")
        
        # Sample photos
        sample_photos = [
            Photo(
                id="sample_001",
                created_at=datetime.now() - timedelta(days=5),
                updated_at=datetime.now() - timedelta(days=5),
                width=3000,
                height=2000,
                color="#FF5733",
                blur_hash="LGF5]+Yk^6#M@-5c,1J5@[or[Q6.",
                downloads=1250,
                likes=89,
                views=5420,
                description="Beautiful sunset over the mountains",
                alt_description="Orange and pink sunset behind mountain silhouettes",
                urls={
                    "raw": "https://images.unsplash.com/photo-001?ixid=raw",
                    "full": "https://images.unsplash.com/photo-001?ixid=full",
                    "regular": "https://images.unsplash.com/photo-001?ixid=regular",
                    "small": "https://images.unsplash.com/photo-001?ixid=small",
                    "thumb": "https://images.unsplash.com/photo-001?ixid=thumb"
                },
                links={
                    "self": "https://api.unsplash.com/photos/photo_001",
                    "html": "https://unsplash.com/photos/photo_001",
                    "download": "https://unsplash.com/photos/photo_001/download"
                },
                user_id="user_001",
                user_name="John Photographer",
                user_username="johnphoto",
                location={
                    "name": "Rocky Mountains, Colorado",
                    "city": "Denver",
                    "country": "United States"
                },
                exif={
                    "make": "Canon",
                    "model": "EOS R5",
                    "exposure_time": "1/125",
                    "aperture": "5.6",
                    "focal_length": "85.0",
                    "iso": 200
                },
                tags=["sunset", "mountains", "landscape", "nature", "orange", "sky"],
                categories=["nature", "landscape"]
            ),
            Photo(
                id="sample_002",
                created_at=datetime.now() - timedelta(days=3),
                updated_at=datetime.now() - timedelta(days=3),
                width=2400,
                height=3600,
                color="#2E8B57",
                blur_hash="LBF5]+Yk^6#M@-5c,1J5@[or[Q6.",
                downloads=890,
                likes=156,
                views=3240,
                description="Urban street photography in black and white",
                alt_description="Person walking down a busy city street",
                urls={
                    "raw": "https://images.unsplash.com/photo-002?ixid=raw",
                    "full": "https://images.unsplash.com/photo-002?ixid=full",
                    "regular": "https://images.unsplash.com/photo-002?ixid=regular",
                    "small": "https://images.unsplash.com/photo-002?ixid=small",
                    "thumb": "https://images.unsplash.com/photo-002?ixid=thumb"
                },
                links={
                    "self": "https://api.unsplash.com/photos/photo-002",
                    "html": "https://unsplash.com/photos/photo-002",
                    "download": "https://unsplash.com/photos/photo-002/download"
                },
                user_id="user_002",
                user_name="Sarah Street",
                user_username="sarahstreet",
                location={
                    "name": "New York City, NY",
                    "city": "New York",
                    "country": "United States"
                },
                exif={
                    "make": "Sony",
                    "model": "A7R IV",
                    "exposure_time": "1/60",
                    "aperture": "2.8",
                    "focal_length": "35.0",
                    "iso": 800
                },
                tags=["street", "urban", "city", "people", "black and white", "photography"],
                categories=["street", "urban"]
            ),
            Photo(
                id="sample_003",
                created_at=datetime.now() - timedelta(days=1),
                updated_at=datetime.now() - timedelta(days=1),
                width=4000,
                height=2667,
                color="#4169E1",
                blur_hash="LCF5]+Yk^6#M@-5c,1J5@[or[Q6.",
                downloads=2100,
                likes=234,
                views=8750,
                description="Minimalist architecture with clean lines",
                alt_description="Modern building with geometric patterns",
                urls={
                    "raw": "https://images.unsplash.com/photo-003?ixid=raw",
                    "full": "https://images.unsplash.com/photo-003?ixid=full",
                    "regular": "https://images.unsplash.com/photo-003?ixid=regular",
                    "small": "https://images.unsplash.com/photo-003?ixid=small",
                    "thumb": "https://images.unsplash.com/photo-003?ixid=thumb"
                },
                links={
                    "self": "https://api.unsplash.com/photos/photo-003",
                    "html": "https://unsplash.com/photos/photo-003",
                    "download": "https://unsplash.com/photos/photo-003/download"
                },
                user_id="user_003",
                user_name="Alex Architecture",
                user_username="alexarch",
                location={
                    "name": "Tokyo, Japan",
                    "city": "Tokyo",
                    "country": "Japan"
                },
                exif={
                    "make": "Nikon",
                    "model": "D850",
                    "exposure_time": "1/250",
                    "aperture": "8.0",
                    "focal_length": "24.0",
                    "iso": 100
                },
                tags=["architecture", "minimalist", "modern", "building", "geometric", "blue"],
                categories=["architecture", "design"]
            )
        ]
        
        # Add photos
        for photo in sample_photos:
            session.add(photo)
        
        # Sample search trends
        search_trends = [
            SearchTrend(search_term="sunset", search_count=1250, trend_date=date.today() - timedelta(days=1)),
            SearchTrend(search_term="architecture", search_count=890, trend_date=date.today() - timedelta(days=1)),
            SearchTrend(search_term="street photography", search_count=756, trend_date=date.today() - timedelta(days=1)),
            SearchTrend(search_term="nature", search_count=2100, trend_date=date.today() - timedelta(days=1)),
            SearchTrend(search_term="minimalist", search_count=445, trend_date=date.today() - timedelta(days=1)),
        ]
        
        for trend in search_trends:
            session.add(trend)
        
        # Sample ETL job
        etl_job = ETLJob(
            job_name="supabase_setup",
            job_type="setup",
            status="completed",
            started_at=datetime.now() - timedelta(minutes=5),
            completed_at=datetime.now(),
            records_processed=3,
            meta_data={"sample_data": True, "photos": 3, "trends": 5}
        )
        session.add(etl_job)
        
        # Commit all changes
        session.commit()
        print("✅ Sample data created successfully!")
        return True
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error creating sample data: {e}")
        return False
    finally:
        close_session(session)

def main():
    """Main setup function"""
    print("🚀 Setting up Splash Analytics with Supabase...")
    
    # Check environment variables
    required_vars = ['DATABASE_URL', 'SUPABASE_URL']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("💡 Please update your .env file with Supabase credentials")
        return False
    
    # Step 1: Test connection
    if not check_supabase_connection():
        return False
    
    # Step 2: Create tables
    if not create_supabase_tables():
        return False
    
    # Step 3: Create sample data
    if not create_sample_data():
        return False
    
    print("\n🎉 Supabase setup completed successfully!")
    print("\nNext steps:")
    print("1. Add your Unsplash API key to .env file")
    print("2. Run the pipeline: make pipeline")
    print("3. Start the dashboard: streamlit run src/dashboard/main.py")
    
    return True

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    success = main()
    exit(0 if success else 1) 