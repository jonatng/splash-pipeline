"""
Login page for Splash Visual Trends Analytics
"""

import streamlit as st
import requests
from typing import Optional
import os

def init_session_state():
    """Initialize session state variables."""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "access_token" not in st.session_state:
        st.session_state.access_token = None
    if "user_email" not in st.session_state:
        st.session_state.user_email = None
    if "reset_password_mode" not in st.session_state:
        st.session_state.reset_password_mode = False

def login(email: str, password: str) -> Optional[dict]:
    """Attempt to log in user."""
    try:
        response = requests.post(
            f"{os.getenv('API_URL', 'http://localhost:8000')}/auth/token",
            data={"username": email, "password": password}
        )
        if response.status_code == 200:
            return response.json()
        return None
    except Exception:
        return None

def signup(email: str, password: str) -> Optional[dict]:
    """Attempt to sign up user."""
    try:
        response = requests.post(
            f"{os.getenv('API_URL', 'http://localhost:8000')}/auth/signup",
            json={"email": email, "password": password}
        )
        if response.status_code == 200:
            return response.json()
        return None
    except Exception:
        return None

def request_password_reset(email: str) -> bool:
    """Request password reset email."""
    try:
        response = requests.post(
            f"{os.getenv('API_URL', 'http://localhost:8000')}/auth/reset-password",
            json={"email": email}
        )
        return response.status_code == 200
    except Exception:
        return False

def update_password(token: str, new_password: str) -> bool:
    """Update user password."""
    try:
        response = requests.post(
            f"{os.getenv('API_URL', 'http://localhost:8000')}/auth/update-password",
            headers={"Authorization": f"Bearer {token}"},
            json={"new_password": new_password}
        )
        return response.status_code == 200
    except Exception:
        return False

def main():
    st.set_page_config(
        page_title="Login - Splash Visual Trends",
        layout="centered",
        initial_sidebar_state="collapsed"
    )
    
    init_session_state()

    if st.session_state.authenticated:
        st.success(f"Logged in as {st.session_state.user_email}")
        
        # Add password update form for authenticated users
        with st.expander("Update Password"):
            with st.form("update_password_form"):
                new_password = st.text_input("New Password", type="password")
                confirm_password = st.text_input("Confirm New Password", type="password")
                submit = st.form_submit_button("Update Password")
                
                if submit:
                    if not new_password:
                        st.error("Please enter a new password")
                    elif new_password != confirm_password:
                        st.error("Passwords do not match")
                    else:
                        if update_password(st.session_state.access_token, new_password):
                            st.success("Password updated successfully!")
                        else:
                            st.error("Failed to update password")
        
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.session_state.access_token = None
            st.session_state.user_email = None
            st.experimental_rerun()
        return

    # Center the login form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.title("🔐 Login")
        st.markdown("Welcome to Splash Visual Trends Analytics")
        
        # Login Form
        with st.form("login_form", clear_on_submit=False):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login", use_container_width=True)
            
            if submitted:
                if not email or not password:
                    st.error("Please enter both email and password")
                else:
                    result = login(email, password)
                    if result:
                        st.session_state.authenticated = True
                        st.session_state.access_token = result["access_token"]
                        st.session_state.user_email = email
                        st.success("Successfully logged in!")
                        st.experimental_rerun()
                    else:
                        st.error("Invalid email or password")
        
        # Sign up option
        st.markdown("---")
        st.markdown("Don't have an account?")
        if st.button("Sign Up", use_container_width=True):
            st.session_state.show_signup = True
        
        # Show sign up form if button was clicked
        if st.session_state.get('show_signup', False):
            st.markdown("### Create Account")
            with st.form("signup_form", clear_on_submit=True):
                new_email = st.text_input("Email", key="signup_email")
                new_password = st.text_input("Password", type="password", key="signup_password")
                confirm_password = st.text_input("Confirm Password", type="password")
                signup_submitted = st.form_submit_button("Create Account", use_container_width=True)
                
                if signup_submitted:
                    if not new_email or not new_password:
                        st.error("Please fill in all fields")
                    elif new_password != confirm_password:
                        st.error("Passwords do not match")
                    else:
                        result = signup(new_email, new_password)
                        if result:
                            st.session_state.authenticated = True
                            st.session_state.access_token = result["access_token"]
                            st.session_state.user_email = new_email
                            st.success("Successfully signed up and logged in!")
                            st.experimental_rerun()
                        else:
                            st.error("Error during sign up. Email might already be registered.")

if __name__ == "__main__":
    main() 