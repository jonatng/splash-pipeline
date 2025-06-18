"""
Data loader for populating the database
"""

import logging
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from ...models.database import (
    Photo, PhotoStatistic, SearchTrend, ETLJob,
    get_session, close_session
)

logger = logging.getLogger(__name__)


class Loader:
    """Loads data into the data warehouse"""
    
    def __init__(self):
        self.session: Optional[Session] = None
    
    def __enter__(self):
        self.session = get_session()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            close_session(self.session)

    def _log_etl_job(self, job_name: str, job_type: str, status: str, 
                     records_processed: int = 0, error_message: str = None,
                     metadata: Dict[str, Any] = None) -> ETLJob:
        """Log ETL job execution"""
        job = ETLJob(
            job_name=job_name,
            job_type=job_type,
            status=status,
            records_processed=records_processed,
            error_message=error_message,
            metadata=metadata or {}
        )
        
        if status in ['completed', 'failed']:
            job.completed_at = datetime.now()
        
        self.session.add(job)
        self.session.commit()
        return job

    def load_photos(self, photos_data: List[Dict[str, Any]]) -> int:
        """Process and load photo data"""
        job = self._log_etl_job("load_photos", "load", "running")
        processed_count = 0
        
        try:
            for photo_data in photos_data:
                try:
                    # Transform photo metadata
                    photo = self._transform_photo_data(photo_data)
                    
                    # Check if photo already exists
                    existing_photo = self.session.query(Photo).filter(Photo.id == photo.id).first()
                    
                    if existing_photo:
                        # Update existing photo
                        for key, value in photo.__dict__.items():
                            if not key.startswith('_') and key != 'id':
                                setattr(existing_photo, key, value)
                    else:
                        # Add new photo
                        self.session.add(photo)
                    
                    # Process photo statistics if available
                    if 'statistics' in photo_data and photo_data['statistics']:
                        self._process_photo_statistics(photo.id, photo_data['statistics'])
                    
                    processed_count += 1
                    
                except Exception as e:
                    logger.error(f"Failed to process photo {photo_data.get('id', 'unknown')}: {e}")
                    continue
            
            self.session.commit()
            self._log_etl_job("load_photos", "load", "completed", processed_count)
            logger.info(f"Successfully loaded {processed_count} photos")
            
        except Exception as e:
            self.session.rollback()
            self._log_etl_job("load_photos", "load", "failed", processed_count, str(e))
            logger.error(f"Failed to load photos: {e}")
            raise
        
        return processed_count

    def _transform_photo_data(self, photo_data: Dict[str, Any]) -> Photo:
        """Transform raw photo data to Photo model"""
        # Parse dates
        created_at = datetime.fromisoformat(photo_data['created_at'].replace('Z', '+00:00'))
        updated_at = datetime.fromisoformat(photo_data['updated_at'].replace('Z', '+00:00'))
        
        # Extract user information
        user = photo_data.get('user', {})
        
        # Extract and clean tags
        tags = []
        if 'tags' in photo_data:
            tags = [tag.get('title', '') for tag in photo_data['tags'] if tag.get('title')]
        
        return Photo(
            id=photo_data['id'],
            created_at=created_at,
            updated_at=updated_at,
            width=photo_data['width'],
            height=photo_data['height'],
            color=photo_data.get('color'),
            blur_hash=photo_data.get('blur_hash'),
            downloads=photo_data.get('downloads', 0),
            likes=photo_data.get('likes', 0),
            views=photo_data.get('views', 0),
            description=photo_data.get('description'),
            alt_description=photo_data.get('alt_description'),
            urls=photo_data.get('urls', {}),
            links=photo_data.get('links', {}),
            user_id=user.get('id'),
            user_name=user.get('name'),
            user_username=user.get('username'),
            location=photo_data.get('location', {}),
            exif=photo_data.get('exif', {}),
            tags=tags,
            categories=photo_data.get('categories', [])
        )

    def _process_photo_statistics(self, photo_id: str, stats_data: Dict[str, Any]):
        """Process photo statistics"""
        # Get previous statistics for delta calculation
        prev_stats = self.session.query(PhotoStatistic)\
            .filter(PhotoStatistic.photo_id == photo_id)\
            .order_by(PhotoStatistic.recorded_at.desc())\
            .first()
        
        downloads = stats_data.get('downloads', {}).get('total', 0)
        likes = stats_data.get('likes', {}).get('total', 0)
        views = stats_data.get('views', {}).get('total', 0)
        
        # Calculate deltas
        download_delta = downloads - (prev_stats.downloads if prev_stats else 0)
        likes_delta = likes - (prev_stats.likes if prev_stats else 0)
        views_delta = views - (prev_stats.views if prev_stats else 0)
        
        stat = PhotoStatistic(
            photo_id=photo_id,
            downloads=downloads,
            likes=likes,
            views=views,
            download_delta=download_delta,
            likes_delta=likes_delta,
            views_delta=views_delta
        )
        
        self.session.add(stat)

    def load_trending_data(self, trending_data: Dict[str, Any]) -> int:
        """Process trending search terms"""
        job = self._log_etl_job("load_trending_data", "load", "running")
        processed_count = 0
        
        try:
            today = date.today()
            
            # Process trending searches
            for search_term in trending_data.get('trending_searches', []):
                # Simulate search count
                search_count = hash(search_term) % 1000 + 100
                
                trend = SearchTrend(
                    search_term=search_term,
                    search_count=search_count,
                    trend_date=today,
                    category='trending'
                )
                
                # Use merge to handle duplicates
                existing = self.session.query(SearchTrend)\
                    .filter(SearchTrend.search_term == search_term,
                           SearchTrend.trend_date == today)\
                    .first()
                
                if existing:
                    existing.search_count = search_count
                else:
                    self.session.add(trend)
                
                processed_count += 1
            
            self.session.commit()
            self._log_etl_job("load_trending_data", "load", "completed", processed_count)
            logger.info(f"Successfully loaded {processed_count} trending items")
            
        except Exception as e:
            self.session.rollback()
            self._log_etl_job("load_trending_data", "load", "failed", processed_count, str(e))
            logger.error(f"Failed to load trending data: {e}")
            raise
        
        return processed_count
