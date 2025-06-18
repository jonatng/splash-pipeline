"""
Database models and connection setup for Splash Visual Trends Analytics
"""

import os
from datetime import datetime, date
from typing import Optional, Dict, Any, List
from sqlalchemy import (
    create_engine, Column, String, Integer, DateTime, Date, 
    Text, JSON, Numeric, ForeignKey, UniqueConstraint, Index, Float, Boolean
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.sql import func
import uuid
from dotenv import load_dotenv

load_dotenv()

# Database configuration - use SQLite for local testing
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./splash_analytics.db")

# Create engine and session
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Session:
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class Photo(Base):
    """Photo model for storing Unsplash photo metadata"""
    __tablename__ = "photos"

    id = Column(String(50), primary_key=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)
    color = Column(String(7))
    blur_hash = Column(String(100))
    downloads = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    views = Column(Integer, default=0)
    description = Column(Text)
    alt_description = Column(Text)
    urls = Column(JSON)
    links = Column(JSON)
    user_id = Column(String(50))
    user_name = Column(String(255))
    user_username = Column(String(255))
    location = Column(JSON)
    exif = Column(JSON)
    tags = Column(JSON)
    categories = Column(JSON)
    extracted_at = Column(DateTime, default=func.now())

    # Relationships
    statistics = relationship("PhotoStatistic", back_populates="photo")

    def __repr__(self):
        return f"<Photo(id='{self.id}', description='{self.description[:50] if self.description else ''}...')>"


class PhotoStatistic(Base):
    """Photo statistics for time series analysis"""
    __tablename__ = "photo_statistics"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    photo_id = Column(String(50), ForeignKey("photos.id"))
    recorded_at = Column(DateTime, default=func.now())
    downloads = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    views = Column(Integer, default=0)
    download_delta = Column(Integer, default=0)
    likes_delta = Column(Integer, default=0)
    views_delta = Column(Integer, default=0)

    # Relationships
    photo = relationship("Photo", back_populates="statistics")

    def __repr__(self):
        return f"<PhotoStatistic(photo_id='{self.photo_id}', recorded_at='{self.recorded_at}')>"


class SearchTrend(Base):
    """Search trends and trending terms"""
    __tablename__ = "search_trends"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    search_term = Column(String(255), nullable=False)
    search_count = Column(Integer, default=0)
    trend_date = Column(Date, nullable=False)
    category = Column(String(100))
    extracted_at = Column(DateTime, default=func.now())

    __table_args__ = (
        UniqueConstraint('search_term', 'trend_date', name='uq_search_term_date'),
    )

    def __repr__(self):
        return f"<SearchTrend(term='{self.search_term}', date='{self.trend_date}')>"


class TagAnalysis(Base):
    """Tag analysis for understanding tag performance"""
    __tablename__ = "tag_analysis"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tag_name = Column(String(255), nullable=False)
    photo_count = Column(Integer, default=0)
    total_likes = Column(Integer, default=0)
    total_downloads = Column(Integer, default=0)
    avg_likes = Column(Numeric(10, 2), default=0)
    avg_downloads = Column(Numeric(10, 2), default=0)
    analysis_date = Column(Date, nullable=False)
    trend_score = Column(Float)
    updated_at = Column(DateTime)
    co_occurring_tags = Column(JSON)

    __table_args__ = (
        UniqueConstraint('tag_name', 'analysis_date', name='uq_tag_analysis_date'),
    )

    def __repr__(self):
        return f"<TagAnalysis(tag='{self.tag_name}', date='{self.analysis_date}')>"


class TagCooccurrence(Base):
    """Tag co-occurrence analysis"""
    __tablename__ = "tag_cooccurrence"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tag1 = Column(String(255), nullable=False)
    tag2 = Column(String(255), nullable=False)
    cooccurrence_count = Column(Integer, default=0)
    analysis_date = Column(Date, nullable=False)

    __table_args__ = (
        UniqueConstraint('tag1', 'tag2', 'analysis_date', name='uq_tag_cooccurrence_date'),
    )

    def __repr__(self):
        return f"<TagCooccurrence(tag1='{self.tag1}', tag2='{self.tag2}')>"


class PhotographerAnalysis(Base):
    """Photographer performance analysis"""
    __tablename__ = "photographer_analysis"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(50), nullable=False)
    username = Column(String(255))
    full_name = Column(String(255))
    total_photos = Column(Integer, default=0)
    total_likes = Column(Integer, default=0)
    total_downloads = Column(Integer, default=0)
    avg_likes_per_photo = Column(Numeric(10, 2), default=0)
    avg_downloads_per_photo = Column(Numeric(10, 2), default=0)
    follower_count = Column(Integer, default=0)
    analysis_date = Column(Date, nullable=False)
    favorite_tags = Column(JSON)
    style_analysis = Column(JSON)
    updated_at = Column(DateTime)

    __table_args__ = (
        UniqueConstraint('user_id', 'analysis_date', name='uq_photographer_analysis_date'),
    )

    def __repr__(self):
        return f"<PhotographerAnalysis(username='{self.username}', date='{self.analysis_date}')>"


class DailyTrend(Base):
    """Daily aggregated trends"""
    __tablename__ = "daily_trends"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    trend_date = Column(Date, nullable=False, unique=True)
    total_photos = Column(Integer, default=0)
    total_likes = Column(Integer, default=0)
    total_downloads = Column(Integer, default=0)
    total_views = Column(Integer, default=0)
    avg_likes_per_photo = Column(Numeric(10, 2), default=0)
    avg_downloads_per_photo = Column(Numeric(10, 2), default=0)
    top_tags = Column(JSON)
    top_colors = Column(JSON)
    color_palette = Column(JSON)
    created_at = Column(DateTime, default=func.now())

    def __repr__(self):
        return f"<DailyTrend(date='{self.trend_date}', photos={self.total_photos})>"


class ExternalData(Base):
    """External data integration"""
    __tablename__ = "external_data"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    data_source = Column(String(100), nullable=False)
    data_type = Column(String(100), nullable=False)
    data_date = Column(Date, nullable=False)
    data_content = Column(JSON)
    meta_data = Column(JSON)
    created_at = Column(DateTime, default=func.now())

    def __repr__(self):
        return f"<ExternalData(source='{self.data_source}', type='{self.data_type}')>"


class ETLJob(Base):
    """ETL job tracking"""
    __tablename__ = "etl_jobs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_name = Column(String(255), nullable=False)
    job_type = Column(String(50), nullable=False)  # 'extract', 'load', 'transform'
    status = Column(String(50), nullable=False)  # 'running', 'completed', 'failed'
    started_at = Column(DateTime, default=func.now())
    completed_at = Column(DateTime)
    records_processed = Column(Integer, default=0)
    error_message = Column(Text)
    meta_data = Column(JSON)

    def __repr__(self):
        return f"<ETLJob(name='{self.job_name}', status='{self.status}')>"


class User(Base):
    """User model for storing authenticated user information"""
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    supabase_uid = Column(String(255), unique=True, nullable=False)
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_login = Column(DateTime)
    preferences = Column(JSON, default=dict)

    def __repr__(self):
        return f"<User(email='{self.email}')>"


def create_tables():
    """Create all tables"""
    Base.metadata.create_all(bind=engine)


def get_session() -> Session:
    """Get a new database session"""
    return SessionLocal()


def close_session(session: Session):
    """Close database session"""
    session.close() 