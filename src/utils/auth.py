"""
Authentication utilities for Splash Visual Trends Analytics
"""

from typing import Optional
import os
from supabase import create_client, Client
from dotenv import load_dotenv
from src.utils.supabase import get_supabase
from src.models.database import User, get_db
from sqlalchemy.orm import Session
from datetime import datetime

load_dotenv()

def get_supabase() -> Client:
    """Initialize Supabase client."""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_ANON_KEY")
    
    if not supabase_url or not supabase_key:
        raise ValueError("Missing Supabase credentials in environment variables")
    
    return create_client(supabase_url, supabase_key)

def create_db_user(db: Session, supabase_uid: str, email: str) -> User:
    """Create a new user record in the database."""
    db_user = User(
        email=email,
        supabase_uid=supabase_uid,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

async def sign_up_user(email: str, password: str) -> dict:
    """Register a new user."""
    supabase = get_supabase()
    try:
        # Create user in Supabase
        response = supabase.auth.sign_up({
            "email": email,
            "password": password
        })
        
        # Create user in our database
        if response and response.user:
            db = next(get_db())
            try:
                create_db_user(db, response.user.id, email)
            except Exception as e:
                # If database creation fails, we should probably delete the Supabase user
                # but that's not exposed in the Python client yet
                raise Exception(f"Failed to create database user: {str(e)}")
            finally:
                db.close()
        
        return response
    except Exception as e:
        raise Exception(f"Error during sign up: {str(e)}")

async def sign_in_user(email: str, password: str) -> dict:
    """Sign in an existing user."""
    supabase = get_supabase()
    try:
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        # Update last login time
        if response and response.user:
            db = next(get_db())
            try:
                user = db.query(User).filter(User.supabase_uid == response.user.id).first()
                if user:
                    user.last_login = datetime.utcnow()
                    db.commit()
            finally:
                db.close()
        
        return response
    except Exception as e:
        raise Exception(f"Error during sign in: {str(e)}")

async def sign_out_user(session_token: str) -> None:
    """Sign out a user."""
    supabase = get_supabase()
    try:
        supabase.auth.sign_out()
    except Exception as e:
        raise Exception(f"Error during sign out: {str(e)}")

def get_current_user(access_token: str) -> Optional[dict]:
    """Get the current user from a session token."""
    supabase = get_supabase()
    try:
        user = supabase.auth.get_user(access_token)
        if user:
            # Get additional user info from our database
            db = next(get_db())
            try:
                db_user = db.query(User).filter(User.supabase_uid == user.id).first()
                if db_user:
                    # Combine Supabase and database user info
                    return {
                        **user.dict(),
                        "full_name": db_user.full_name,
                        "is_superuser": db_user.is_superuser,
                        "preferences": db_user.preferences
                    }
            finally:
                db.close()
        return user
    except Exception:
        return None

async def request_password_reset(email: str) -> bool:
    """Request a password reset email."""
    supabase = get_supabase()
    try:
        supabase.auth.reset_password_email(email)
        return True
    except Exception as e:
        raise Exception(f"Error requesting password reset: {str(e)}")

async def update_password(access_token: str, new_password: str) -> bool:
    """Update user's password."""
    supabase = get_supabase()
    try:
        supabase.auth.update_user(
            {"password": new_password},
            access_token
        )
        return True
    except Exception as e:
        raise Exception(f"Error updating password: {str(e)}")

async def update_user_profile(access_token: str, full_name: str = None, preferences: dict = None) -> bool:
    """Update user profile information."""
    try:
        user = supabase.auth.get_user(access_token)
        if user:
            db = next(get_db())
            try:
                db_user = db.query(User).filter(User.supabase_uid == user.id).first()
                if db_user:
                    if full_name is not None:
                        db_user.full_name = full_name
                    if preferences is not None:
                        db_user.preferences = preferences
                    db_user.updated_at = datetime.utcnow()
                    db.commit()
                    return True
            finally:
                db.close()
        return False
    except Exception as e:
        raise Exception(f"Error updating user profile: {str(e)}") 