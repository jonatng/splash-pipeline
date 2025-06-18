"""
FastAPI application for Splash Visual Trends Analytics
"""

import os
from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
import logging

from ..models.database import (
    get_db, Photo, PhotoStatistic, SearchTrend, TagAnalysis, 
    TagCooccurrence, PhotographerAnalysis, DailyTrend, ETLJob
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Splash Visual Trends Analytics API",
    description="API for analyzing visual trends from Unsplash data",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Splash Visual Trends Analytics API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint"""
    try:
        # Check database connection
        photo_count = db.query(func.count(Photo.id)).scalar()
        
        return {
            "status": "healthy",
            "database": "connected",
            "total_photos": photo_count,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Service unhealthy")


@app.get("/photos")
async def get_photos(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    order_by: str = Query("created_at", regex="^(created_at|likes|downloads|views)$"),
    db: Session = Depends(get_db)
):
    """Get photos with pagination"""
    try:
        query = db.query(Photo)
        
        # Apply ordering
        if order_by == "created_at":
            query = query.order_by(desc(Photo.created_at))
        elif order_by == "likes":
            query = query.order_by(desc(Photo.likes))
        elif order_by == "downloads":
            query = query.order_by(desc(Photo.downloads))
        elif order_by == "views":
            query = query.order_by(desc(Photo.views))
        
        # Apply pagination
        photos = query.offset(offset).limit(limit).all()
        
        # Get total count
        total = db.query(func.count(Photo.id)).scalar()
        
        return {
            "photos": [
                {
                    "id": photo.id,
                    "description": photo.description,
                    "alt_description": photo.alt_description,
                    "width": photo.width,
                    "height": photo.height,
                    "color": photo.color,
                    "likes": photo.likes,
                    "downloads": photo.downloads,
                    "views": photo.views,
                    "created_at": photo.created_at.isoformat(),
                    "urls": photo.urls,
                    "user": {
                        "id": photo.user_id,
                        "username": photo.user_username,
                        "name": photo.user_name
                    },
                    "tags": photo.tags
                }
                for photo in photos
            ],
            "pagination": {
                "total": total,
                "limit": limit,
                "offset": offset,
                "has_next": offset + limit < total
            }
        }
    except Exception as e:
        logger.error(f"Failed to get photos: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve photos")


@app.get("/photos/{photo_id}")
async def get_photo(photo_id: str, db: Session = Depends(get_db)):
    """Get a specific photo by ID"""
    try:
        photo = db.query(Photo).filter(Photo.id == photo_id).first()
        
        if not photo:
            raise HTTPException(status_code=404, detail="Photo not found")
        
        # Get latest statistics
        latest_stats = db.query(PhotoStatistic)\
            .filter(PhotoStatistic.photo_id == photo_id)\
            .order_by(desc(PhotoStatistic.recorded_at))\
            .first()
        
        return {
            "id": photo.id,
            "description": photo.description,
            "alt_description": photo.alt_description,
            "width": photo.width,
            "height": photo.height,
            "color": photo.color,
            "blur_hash": photo.blur_hash,
            "likes": photo.likes,
            "downloads": photo.downloads,
            "views": photo.views,
            "created_at": photo.created_at.isoformat(),
            "updated_at": photo.updated_at.isoformat(),
            "urls": photo.urls,
            "links": photo.links,
            "user": {
                "id": photo.user_id,
                "username": photo.user_username,
                "name": photo.user_name
            },
            "location": photo.location,
            "exif": photo.exif,
            "tags": photo.tags,
            "categories": photo.categories,
            "latest_statistics": {
                "likes": latest_stats.likes if latest_stats else photo.likes,
                "downloads": latest_stats.downloads if latest_stats else photo.downloads,
                "views": latest_stats.views if latest_stats else photo.views,
                "recorded_at": latest_stats.recorded_at.isoformat() if latest_stats else None
            } if latest_stats else None
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get photo {photo_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve photo")


@app.get("/trends/search")
async def get_search_trends(
    days: int = Query(7, ge=1, le=30),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get search trends for the last N days"""
    try:
        start_date = date.today() - timedelta(days=days)
        
        trends = db.query(SearchTrend)\
            .filter(SearchTrend.trend_date >= start_date)\
            .order_by(desc(SearchTrend.search_count))\
            .limit(limit)\
            .all()
        
        return {
            "search_trends": [
                {
                    "search_term": trend.search_term,
                    "search_count": trend.search_count,
                    "trend_date": trend.trend_date.isoformat(),
                    "category": trend.category
                }
                for trend in trends
            ],
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": date.today().isoformat(),
                "days": days
            }
        }
    except Exception as e:
        logger.error(f"Failed to get search trends: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve search trends")


@app.get("/trends/tags")
async def get_tag_trends(
    analysis_date: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get tag analysis trends"""
    try:
        if analysis_date:
            target_date = datetime.strptime(analysis_date, "%Y-%m-%d").date()
        else:
            target_date = date.today()
        
        tags = db.query(TagAnalysis)\
            .filter(TagAnalysis.analysis_date == target_date)\
            .order_by(desc(TagAnalysis.total_likes))\
            .limit(limit)\
            .all()
        
        return {
            "tag_analysis": [
                {
                    "tag_name": tag.tag_name,
                    "photo_count": tag.photo_count,
                    "total_likes": tag.total_likes,
                    "total_downloads": tag.total_downloads,
                    "avg_likes": float(tag.avg_likes),
                    "avg_downloads": float(tag.avg_downloads),
                    "analysis_date": tag.analysis_date.isoformat()
                }
                for tag in tags
            ],
            "analysis_date": target_date.isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get tag trends: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve tag trends")


@app.get("/trends/photographers")
async def get_photographer_trends(
    analysis_date: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    order_by: str = Query("total_likes", regex="^(total_likes|total_downloads|total_photos|avg_likes_per_photo)$"),
    db: Session = Depends(get_db)
):
    """Get photographer performance trends"""
    try:
        if analysis_date:
            target_date = datetime.strptime(analysis_date, "%Y-%m-%d").date()
        else:
            target_date = date.today()
        
        query = db.query(PhotographerAnalysis)\
            .filter(PhotographerAnalysis.analysis_date == target_date)
        
        # Apply ordering
        if order_by == "total_likes":
            query = query.order_by(desc(PhotographerAnalysis.total_likes))
        elif order_by == "total_downloads":
            query = query.order_by(desc(PhotographerAnalysis.total_downloads))
        elif order_by == "total_photos":
            query = query.order_by(desc(PhotographerAnalysis.total_photos))
        elif order_by == "avg_likes_per_photo":
            query = query.order_by(desc(PhotographerAnalysis.avg_likes_per_photo))
        
        photographers = query.limit(limit).all()
        
        return {
            "photographer_analysis": [
                {
                    "user_id": photographer.user_id,
                    "username": photographer.username,
                    "full_name": photographer.full_name,
                    "total_photos": photographer.total_photos,
                    "total_likes": photographer.total_likes,
                    "total_downloads": photographer.total_downloads,
                    "avg_likes_per_photo": float(photographer.avg_likes_per_photo),
                    "avg_downloads_per_photo": float(photographer.avg_downloads_per_photo),
                    "follower_count": photographer.follower_count,
                    "analysis_date": photographer.analysis_date.isoformat()
                }
                for photographer in photographers
            ],
            "analysis_date": target_date.isoformat(),
            "order_by": order_by
        }
    except Exception as e:
        logger.error(f"Failed to get photographer trends: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve photographer trends")


@app.get("/trends/daily")
async def get_daily_trends(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Get daily aggregated trends"""
    try:
        start_date = date.today() - timedelta(days=days)
        
        trends = db.query(DailyTrend)\
            .filter(DailyTrend.trend_date >= start_date)\
            .order_by(desc(DailyTrend.trend_date))\
            .all()
        
        return {
            "daily_trends": [
                {
                    "trend_date": trend.trend_date.isoformat(),
                    "total_photos": trend.total_photos,
                    "total_likes": trend.total_likes,
                    "total_downloads": trend.total_downloads,
                    "total_views": trend.total_views,
                    "avg_likes_per_photo": float(trend.avg_likes_per_photo),
                    "avg_downloads_per_photo": float(trend.avg_downloads_per_photo),
                    "top_tags": trend.top_tags,
                    "top_colors": trend.top_colors
                }
                for trend in trends
            ],
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": date.today().isoformat(),
                "days": days
            }
        }
    except Exception as e:
        logger.error(f"Failed to get daily trends: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve daily trends")


@app.get("/analytics/tag-cooccurrence")
async def get_tag_cooccurrence(
    analysis_date: Optional[str] = Query(None),
    min_count: int = Query(2, ge=1),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """Get tag co-occurrence analysis"""
    try:
        if analysis_date:
            target_date = datetime.strptime(analysis_date, "%Y-%m-%d").date()
        else:
            target_date = date.today()
        
        cooccurrences = db.query(TagCooccurrence)\
            .filter(TagCooccurrence.analysis_date == target_date)\
            .filter(TagCooccurrence.cooccurrence_count >= min_count)\
            .order_by(desc(TagCooccurrence.cooccurrence_count))\
            .limit(limit)\
            .all()
        
        return {
            "tag_cooccurrence": [
                {
                    "tag1": cooc.tag1,
                    "tag2": cooc.tag2,
                    "cooccurrence_count": cooc.cooccurrence_count,
                    "analysis_date": cooc.analysis_date.isoformat()
                }
                for cooc in cooccurrences
            ],
            "analysis_date": target_date.isoformat(),
            "min_count": min_count
        }
    except Exception as e:
        logger.error(f"Failed to get tag co-occurrence: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve tag co-occurrence")


@app.get("/analytics/statistics")
async def get_analytics_statistics(db: Session = Depends(get_db)):
    """Get overall analytics statistics"""
    try:
        # Get basic counts
        total_photos = db.query(func.count(Photo.id)).scalar()
        total_photographers = db.query(func.count(func.distinct(Photo.user_id))).scalar()
        
        # Get recent activity (last 7 days)
        week_ago = date.today() - timedelta(days=7)
        recent_photos = db.query(func.count(Photo.id))\
            .filter(func.date(Photo.created_at) >= week_ago)\
            .scalar()
        
        # Get top performing photo
        top_photo = db.query(Photo)\
            .order_by(desc(Photo.likes))\
            .first()
        
        # Get most recent ETL job
        latest_etl = db.query(ETLJob)\
            .order_by(desc(ETLJob.started_at))\
            .first()
        
        return {
            "overview": {
                "total_photos": total_photos,
                "total_photographers": total_photographers,
                "recent_photos_7_days": recent_photos
            },
            "top_photo": {
                "id": top_photo.id,
                "description": top_photo.description,
                "likes": top_photo.likes,
                "downloads": top_photo.downloads,
                "user_username": top_photo.user_username
            } if top_photo else None,
            "latest_etl_job": {
                "job_name": latest_etl.job_name,
                "status": latest_etl.status,
                "started_at": latest_etl.started_at.isoformat(),
                "completed_at": latest_etl.completed_at.isoformat() if latest_etl.completed_at else None,
                "records_processed": latest_etl.records_processed
            } if latest_etl else None,
            "generated_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get analytics statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve analytics statistics")


@app.get("/search/photos")
async def search_photos(
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Search photos by description, tags, or user"""
    try:
        # Simple text search (in production, use full-text search)
        query = db.query(Photo).filter(
            (Photo.description.ilike(f"%{q}%")) |
            (Photo.alt_description.ilike(f"%{q}%")) |
            (Photo.user_username.ilike(f"%{q}%")) |
            (Photo.user_name.ilike(f"%{q}%"))
        )
        
        # Get total count for pagination
        total = query.count()
        
        # Apply pagination and ordering
        photos = query.order_by(desc(Photo.likes))\
            .offset(offset)\
            .limit(limit)\
            .all()
        
        return {
            "query": q,
            "photos": [
                {
                    "id": photo.id,
                    "description": photo.description,
                    "alt_description": photo.alt_description,
                    "likes": photo.likes,
                    "downloads": photo.downloads,
                    "urls": photo.urls,
                    "user": {
                        "username": photo.user_username,
                        "name": photo.user_name
                    },
                    "tags": photo.tags
                }
                for photo in photos
            ],
            "pagination": {
                "total": total,
                "limit": limit,
                "offset": offset,
                "has_next": offset + limit < total
            }
        }
    except Exception as e:
        logger.error(f"Failed to search photos: {e}")
        raise HTTPException(status_code=500, detail="Failed to search photos")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 