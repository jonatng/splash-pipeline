"""
Main entry point for Splash Visual Trends Analytics Dashboard
"""

import streamlit as st
from src.dashboard.main import main as dashboard_main
from src.dashboard.pages.login import main as login_main

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'access_token' not in st.session_state:
    st.session_state.access_token = None
if 'user_email' not in st.session_state:
    st.session_state.user_email = None
if 'show_signup' not in st.session_state:
    st.session_state.show_signup = False

# Configure the page
st.set_page_config(
    page_title="Splash Visual Trends Analytics",
    page_icon="📸",
    layout="wide",
    initial_sidebar_state="expanded" if st.session_state.authenticated else "collapsed"
)

# Display appropriate interface based on authentication state
if not st.session_state.authenticated:
    login_main()
else:
    dashboard_main() 