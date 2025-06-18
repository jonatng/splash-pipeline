"""
Data transformer for running analysis and aggregations
"""

import logging
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from collections import Counter, defaultdict

from ...models.database import (
    Photo, TagAnalysis, TagCooccurrence, PhotographerAnalysis,
    DailyTrend, ETLJob, get_session, close_session
)

logger = logging.getLogger(__name__)


class Transformer:
    """Runs data transformations and analysis"""

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

    def analyze_tags(self, analysis_date: date = None) -> int:
        """Analyze tag performance and co-occurrence"""
        if not analysis_date:
            analysis_date = date.today()
        
        job = self._log_etl_job("analyze_tags", "transform", "running", metadata={'date': str(analysis_date)})
        processed_count = 0
        
        try:
            # Get all photos with tags
            photos = self.session.query(Photo).filter(Photo.tags.isnot(None)).all()
            
            tag_stats = defaultdict(lambda: {'photo_count': 0, 'total_likes': 0, 'total_downloads': 0})
            tag_pairs = defaultdict(int)
            
            # Analyze tags
            for photo in photos:
                if not photo.tags:
                    continue
                
                photo_tags = photo.tags if isinstance(photo.tags, list) else []
                
                for tag in photo_tags:
                    tag_stats[tag]['photo_count'] += 1
                    tag_stats[tag]['total_likes'] += photo.likes or 0
                    tag_stats[tag]['total_downloads'] += photo.downloads or 0
                
                for i, tag1 in enumerate(photo_tags):
                    for tag2 in photo_tags[i+1:]:
                        pair = tuple(sorted([tag1, tag2]))
                        tag_pairs[pair] += 1
            
            # Save tag analysis
            for tag, stats in tag_stats.items():
                avg_likes = stats['total_likes'] / stats['photo_count'] if stats['photo_count'] > 0 else 0
                avg_downloads = stats['total_downloads'] / stats['photo_count'] if stats['photo_count'] > 0 else 0
                
                analysis = TagAnalysis(
                    tag_name=tag,
                    photo_count=stats['photo_count'],
                    total_likes=stats['total_likes'],
                    total_downloads=stats['total_downloads'],
                    avg_likes=avg_likes,
                    avg_downloads=avg_downloads,
                    analysis_date=analysis_date
                )
                
                existing = self.session.query(TagAnalysis).filter_by(tag_name=tag, analysis_date=analysis_date).first()
                if existing:
                    existing.photo_count = stats['photo_count']
                    existing.total_likes = stats['total_likes']
                    existing.total_downloads = stats['total_downloads']
                    existing.avg_likes = avg_likes
                    existing.avg_downloads = avg_downloads
                else:
                    self.session.add(analysis)
                
                processed_count += 1
            
            # Save tag co-occurrence
            for (tag1, tag2), count in tag_pairs.items():
                if count < 2: continue
                cooccurrence = TagCooccurrence(
                    tag1=tag1, tag2=tag2, cooccurrence_count=count, analysis_date=analysis_date
                )
                existing = self.session.query(TagCooccurrence).filter_by(tag1=tag1, tag2=tag2, analysis_date=analysis_date).first()
                if existing:
                    existing.cooccurrence_count = count
                else:
                    self.session.add(cooccurrence)

            self.session.commit()
            self._log_etl_job("analyze_tags", "transform", "completed", processed_count, metadata={'date': str(analysis_date)})
            logger.info(f"Successfully analyzed {processed_count} tags for {analysis_date}")
            
        except Exception as e:
            self.session.rollback()
            self._log_etl_job("analyze_tags", "transform", "failed", processed_count, str(e), metadata={'date': str(analysis_date)})
            logger.error(f"Failed to analyze tags: {e}")
            raise
        
        return processed_count

    def analyze_photographers(self, analysis_date: date = None) -> int:
        """Analyze photographer performance"""
        if not analysis_date:
            analysis_date = date.today()
        
        job = self._log_etl_job("analyze_photographers", "transform", "running", metadata={'date': str(analysis_date)})
        processed_count = 0
        
        try:
            photographer_stats = self.session.query(
                Photo.user_id, Photo.user_username, Photo.user_name,
                func.count(Photo.id).label('total_photos'),
                func.sum(Photo.likes).label('total_likes'),
                func.sum(Photo.downloads).label('total_downloads')
            ).filter(Photo.user_id.isnot(None)).group_by(
                Photo.user_id, Photo.user_username, Photo.user_name
            ).all()
            
            for stats in photographer_stats:
                avg_likes = (stats.total_likes or 0) / stats.total_photos if stats.total_photos > 0 else 0
                avg_downloads = (stats.total_downloads or 0) / stats.total_photos if stats.total_photos > 0 else 0
                
                analysis = PhotographerAnalysis(
                    user_id=stats.user_id, username=stats.user_username, full_name=stats.user_name,
                    total_photos=stats.total_photos, total_likes=stats.total_likes or 0,
                    total_downloads=stats.total_downloads or 0, avg_likes_per_photo=avg_likes,
                    avg_downloads_per_photo=avg_downloads, analysis_date=analysis_date
                )
                
                existing = self.session.query(PhotographerAnalysis).filter_by(user_id=stats.user_id, analysis_date=analysis_date).first()
                if existing:
                    existing.total_photos = stats.total_photos
                    existing.total_likes = stats.total_likes or 0
                    existing.total_downloads = stats.total_downloads or 0
                    existing.avg_likes_per_photo = avg_likes
                    existing.avg_downloads_per_photo = avg_downloads
                else:
                    self.session.add(analysis)
                
                processed_count += 1
            
            self.session.commit()
            self._log_etl_job("analyze_photographers", "transform", "completed", processed_count, metadata={'date': str(analysis_date)})
            logger.info(f"Successfully analyzed {processed_count} photographers for {analysis_date}")
            
        except Exception as e:
            self.session.rollback()
            self._log_etl_job("analyze_photographers", "transform", "failed", processed_count, str(e), metadata={'date': str(analysis_date)})
            logger.error(f"Failed to analyze photographers: {e}")
            raise
        
        return processed_count

    def generate_daily_trends(self, trend_date: date = None) -> bool:
        """Generate daily trend aggregations"""
        if not trend_date:
            trend_date = date.today()
        
        job = self._log_etl_job("generate_daily_trends", "transform", "running", metadata={'date': str(trend_date)})
        
        try:
            daily_stats = self.session.query(
                func.count(Photo.id).label('total_photos'),
                func.sum(Photo.likes).label('total_likes'),
                func.sum(Photo.downloads).label('total_downloads'),
                func.sum(Photo.views).label('total_views')
            ).filter(func.date(Photo.created_at) == trend_date).first()
            
            if not daily_stats or daily_stats.total_photos == 0:
                logger.warning(f"No photos found for date {trend_date}")
                self._log_etl_job("generate_daily_trends", "transform", "completed", 0, "No data", metadata={'date': str(trend_date)})
                return False
            
            avg_likes = (daily_stats.total_likes or 0) / daily_stats.total_photos
            avg_downloads = (daily_stats.total_downloads or 0) / daily_stats.total_photos
            top_tags = self._get_top_tags_for_date(trend_date)
            top_colors = self._get_top_colors_for_date(trend_date)
            
            trend = DailyTrend(
                trend_date=trend_date,
                total_photos=daily_stats.total_photos,
                total_likes=daily_stats.total_likes or 0,
                total_downloads=daily_stats.total_downloads or 0,
                total_views=daily_stats.total_views or 0,
                avg_likes_per_photo=avg_likes,
                avg_downloads_per_photo=avg_downloads,
                top_tags=top_tags,
                top_colors=top_colors
            )
            
            existing = self.session.query(DailyTrend).filter_by(trend_date=trend_date).first()
            if existing:
                existing.total_photos = trend.total_photos
                existing.total_likes = trend.total_likes
                existing.total_downloads = trend.total_downloads
                existing.total_views = trend.total_views
                existing.avg_likes_per_photo = trend.avg_likes_per_photo
                existing.avg_downloads_per_photo = trend.avg_downloads_per_photo
                existing.top_tags = trend.top_tags
                existing.top_colors = trend.top_colors
            else:
                self.session.add(trend)
            
            self.session.commit()
            self._log_etl_job("generate_daily_trends", "transform", "completed", 1, metadata={'date': str(trend_date)})
            logger.info(f"Successfully generated daily trends for {trend_date}")
            
        except Exception as e:
            self.session.rollback()
            self._log_etl_job("generate_daily_trends", "transform", "failed", 0, str(e), metadata={'date': str(trend_date)})
            logger.error(f"Failed to generate daily trends: {e}")
            raise
        
        return True
    
    def _get_top_tags_for_date(self, trend_date: date, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top tags for a specific date"""
        photos = self.session.query(Photo.tags).filter(
            func.date(Photo.created_at) == trend_date,
            Photo.tags.isnot(None)
        ).all()
        
        tag_counts = Counter()
        for p_tags in photos:
            tags = p_tags[0] if isinstance(p_tags[0], list) else []
            tag_counts.update(tags)
        
        return [{'tag': tag, 'count': count} for tag, count in tag_counts.most_common(limit)]
    
    def _get_top_colors_for_date(self, trend_date: date, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top colors for a specific date"""
        colors = self.session.query(
            Photo.color, func.count(Photo.id).label('count')
        ).filter(
            func.date(Photo.created_at) == trend_date,
            Photo.color.isnot(None)
        ).group_by(Photo.color).order_by(
            func.count(Photo.id).desc()
        ).limit(limit).all()
        
        return [{'color': color.color, 'count': color.count} for color in colors]
