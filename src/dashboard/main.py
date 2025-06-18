"""
Streamlit Dashboard for Splash Visual Trends Analytics
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
from datetime import datetime, date, timedelta
import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from src.models.database import get_session, close_session, Photo, TagAnalysis, DailyTrend, PhotographerAnalysis
from sqlalchemy import func, desc

# Check authentication
if 'authenticated' not in st.session_state or not st.session_state.authenticated:
    st.warning("Please log in to access the dashboard.")
    st.stop()

# Page configuration
st.set_page_config(
    page_title="Splash Visual Trends Analytics",
    page_icon="📸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .insight-box {
        background-color: #e8f4fd;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #1f77b4;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.markdown('<h1 class="main-header">📸 Splash Visual Trends Analytics</h1>', unsafe_allow_html=True)

# Sidebar
st.sidebar.title("Navigation")
page = st.sidebar.selectbox(
    "Choose a page",
    ["Overview", "Photo Trends", "Tag Analysis", "Photographer Insights", "Search Trends", "Data Quality"]
)

# API base URL
API_BASE_URL = os.getenv("API_URL", "http://localhost:8000")

@st.cache_data(ttl=300)  # Cache for 5 minutes
def fetch_api_data(endpoint):
    """Fetch data from the API with caching"""
    try:
        headers = {}
        if st.session_state.get('access_token'):
            headers['Authorization'] = f"Bearer {st.session_state.access_token}"
        
        response = requests.get(
            f"{API_BASE_URL}{endpoint}",
            headers=headers
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"Connection Error: {e}")
        return None

def get_db_data():
    """Get data directly from database"""
    try:
        session = get_session()
        return session
    except Exception as e:
        st.error(f"Database connection error: {e}")
        return None

def format_number(num):
    """Format large numbers with K, M suffixes"""
    if num >= 1_000_000:
        return f"{num/1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num/1_000:.1f}K"
    else:
        return str(num)

# Overview Page
if page == "Overview":
    st.header("📊 Analytics Overview")
    
    # Fetch overview statistics
    stats_data = fetch_api_data("/analytics/statistics")
    
    if stats_data:
        overview = stats_data.get("overview", {})
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="Total Photos",
                value=format_number(overview.get("total_photos", 0))
            )
        
        with col2:
            st.metric(
                label="Total Photographers",
                value=format_number(overview.get("total_photographers", 0))
            )
        
        with col3:
            st.metric(
                label="Recent Photos (7 days)",
                value=format_number(overview.get("recent_photos_7_days", 0))
            )
        
        with col4:
            if stats_data.get("latest_etl_job"):
                etl_status = stats_data["latest_etl_job"]["status"]
                st.metric(
                    label="ETL Status",
                    value=etl_status.title(),
                    delta="✅" if etl_status == "completed" else "⚠️"
                )
        
        # Top performing photo
        if stats_data.get("top_photo"):
            st.subheader("🏆 Top Performing Photo")
            top_photo = stats_data["top_photo"]
            
            col1, col2 = st.columns([1, 2])
            with col1:
                st.metric("Likes", format_number(top_photo["likes"]))
                st.metric("Downloads", format_number(top_photo["downloads"]))
            
            with col2:
                st.write(f"**Photographer:** {top_photo['user_username']}")
                st.write(f"**Description:** {top_photo['description'][:100]}...")
        
        # Daily trends chart
        daily_trends_data = fetch_api_data("/trends/daily?days=30")
        if daily_trends_data and daily_trends_data.get("daily_trends"):
            st.subheader("📈 30-Day Trends")
            
            df = pd.DataFrame(daily_trends_data["daily_trends"])
            df['trend_date'] = pd.to_datetime(df['trend_date'])
            
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=('Total Photos', 'Total Likes', 'Avg Likes per Photo', 'Avg Downloads per Photo'),
                specs=[[{"secondary_y": False}, {"secondary_y": False}],
                       [{"secondary_y": False}, {"secondary_y": False}]]
            )
            
            # Total Photos
            fig.add_trace(
                go.Scatter(x=df['trend_date'], y=df['total_photos'], name='Photos'),
                row=1, col=1
            )
            
            # Total Likes
            fig.add_trace(
                go.Scatter(x=df['trend_date'], y=df['total_likes'], name='Likes'),
                row=1, col=2
            )
            
            # Avg Likes per Photo
            fig.add_trace(
                go.Scatter(x=df['trend_date'], y=df['avg_likes_per_photo'], name='Avg Likes'),
                row=2, col=1
            )
            
            # Avg Downloads per Photo
            fig.add_trace(
                go.Scatter(x=df['trend_date'], y=df['avg_downloads_per_photo'], name='Avg Downloads'),
                row=2, col=2
            )
            
            fig.update_layout(height=600, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

# Photo Trends Page
elif page == "Photo Trends":
    st.header("📸 Photo Trends Analysis")
    
    # Fetch recent photos
    photos_data = fetch_api_data("/photos?limit=50&order_by=likes")
    
    if photos_data and photos_data.get("photos"):
        photos = photos_data["photos"]
        df = pd.DataFrame(photos)
        
        # Photo performance distribution
        st.subheader("📊 Photo Performance Distribution")
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.histogram(
                df, x='likes', nbins=20,
                title='Distribution of Likes',
                labels={'likes': 'Number of Likes', 'count': 'Number of Photos'}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.histogram(
                df, x='downloads', nbins=20,
                title='Distribution of Downloads',
                labels={'downloads': 'Number of Downloads', 'count': 'Number of Photos'}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Color analysis
        if 'color' in df.columns:
            st.subheader("🎨 Color Trends")
            color_counts = df['color'].value_counts().head(10)
            
            fig = px.bar(
                x=color_counts.index,
                y=color_counts.values,
                title='Top 10 Photo Colors',
                labels={'x': 'Color', 'y': 'Count'},
                color=color_counts.index
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Top photos table
        st.subheader("🏆 Top Performing Photos")
        display_df = df[['description', 'likes', 'downloads', 'user']].copy()
        display_df['photographer'] = display_df['user'].apply(lambda x: x.get('username', 'Unknown'))
        display_df = display_df.drop('user', axis=1)
        display_df['description'] = display_df['description'].apply(
            lambda x: x[:50] + "..." if x and len(x) > 50 else x
        )
        
        st.dataframe(
            display_df.head(10),
            column_config={
                "description": "Description",
                "likes": st.column_config.NumberColumn("Likes", format="%d"),
                "downloads": st.column_config.NumberColumn("Downloads", format="%d"),
                "photographer": "Photographer"
            },
            hide_index=True
        )

# Tag Analysis Page
elif page == "Tag Analysis":
    st.header("🏷️ Tag Analysis")
    
    # Date selector
    analysis_date = st.date_input(
        "Select Analysis Date",
        value=date.today(),
        max_value=date.today()
    )
    
    # Fetch tag trends
    tag_data = fetch_api_data(f"/trends/tags?analysis_date={analysis_date}")
    
    if tag_data and tag_data.get("tag_analysis"):
        tags = tag_data["tag_analysis"]
        df = pd.DataFrame(tags)
        
        if not df.empty:
            # Top tags by different metrics
            st.subheader("📊 Top Tags Performance")
            
            metric = st.selectbox(
                "Select Metric",
                ["total_likes", "total_downloads", "photo_count", "avg_likes", "avg_downloads"]
            )
            
            top_tags = df.nlargest(15, metric)
            
            fig = px.bar(
                top_tags,
                x='tag_name',
                y=metric,
                title=f'Top 15 Tags by {metric.replace("_", " ").title()}',
                labels={'tag_name': 'Tag', metric: metric.replace("_", " ").title()}
            )
            fig.update_xaxes(tickangle=45)
            st.plotly_chart(fig, use_container_width=True)
            
            # Tag performance scatter plot
            st.subheader("📈 Tag Performance Analysis")
            
            fig = px.scatter(
                df,
                x='avg_likes',
                y='avg_downloads',
                size='photo_count',
                hover_name='tag_name',
                title='Tag Performance: Average Likes vs Downloads',
                labels={
                    'avg_likes': 'Average Likes per Photo',
                    'avg_downloads': 'Average Downloads per Photo',
                    'photo_count': 'Number of Photos'
                }
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Tag co-occurrence
            cooccurrence_data = fetch_api_data(f"/analytics/tag-cooccurrence?analysis_date={analysis_date}&limit=20")
            
            if cooccurrence_data and cooccurrence_data.get("tag_cooccurrence"):
                st.subheader("🔗 Tag Co-occurrence Analysis")
                
                cooc_df = pd.DataFrame(cooccurrence_data["tag_cooccurrence"])
                cooc_df['tag_pair'] = cooc_df['tag1'] + ' + ' + cooc_df['tag2']
                
                fig = px.bar(
                    cooc_df.head(15),
                    x='tag_pair',
                    y='cooccurrence_count',
                    title='Top 15 Tag Pairs',
                    labels={'tag_pair': 'Tag Pair', 'cooccurrence_count': 'Co-occurrence Count'}
                )
                fig.update_xaxes(tickangle=45)
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning(f"No tag analysis data available for {analysis_date}")

# Photographer Insights Page
elif page == "Photographer Insights":
    st.header("👨‍💻 Photographer Insights")
    
    # Date selector
    analysis_date = st.date_input(
        "Select Analysis Date",
        value=date.today(),
        max_value=date.today(),
        key="photographer_date"
    )
    
    # Metric selector
    order_by = st.selectbox(
        "Order by",
        ["total_likes", "total_downloads", "total_photos", "avg_likes_per_photo"],
        format_func=lambda x: x.replace("_", " ").title()
    )
    
    # Fetch photographer data
    photographer_data = fetch_api_data(f"/trends/photographers?analysis_date={analysis_date}&order_by={order_by}&limit=50")
    
    if photographer_data and photographer_data.get("photographer_analysis"):
        photographers = photographer_data["photographer_analysis"]
        df = pd.DataFrame(photographers)
        
        if not df.empty:
            # Top photographers
            st.subheader(f"🏆 Top Photographers by {order_by.replace('_', ' ').title()}")
            
            top_photographers = df.head(15)
            
            fig = px.bar(
                top_photographers,
                x='username',
                y=order_by,
                title=f'Top 15 Photographers by {order_by.replace("_", " ").title()}',
                labels={'username': 'Photographer', order_by: order_by.replace("_", " ").title()}
            )
            fig.update_xaxes(tickangle=45)
            st.plotly_chart(fig, use_container_width=True)
            
            # Photographer performance analysis
            st.subheader("📊 Photographer Performance Analysis")
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.scatter(
                    df,
                    x='total_photos',
                    y='avg_likes_per_photo',
                    size='total_likes',
                    hover_name='username',
                    title='Photos vs Average Likes per Photo',
                    labels={
                        'total_photos': 'Total Photos',
                        'avg_likes_per_photo': 'Average Likes per Photo',
                        'total_likes': 'Total Likes'
                    }
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                fig = px.scatter(
                    df,
                    x='total_photos',
                    y='avg_downloads_per_photo',
                    size='total_downloads',
                    hover_name='username',
                    title='Photos vs Average Downloads per Photo',
                    labels={
                        'total_photos': 'Total Photos',
                        'avg_downloads_per_photo': 'Average Downloads per Photo',
                        'total_downloads': 'Total Downloads'
                    }
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Top photographers table
            st.subheader("📋 Top Photographers Details")
            
            display_df = df[['username', 'full_name', 'total_photos', 'total_likes', 'total_downloads', 
                           'avg_likes_per_photo', 'avg_downloads_per_photo']].head(20)
            
            st.dataframe(
                display_df,
                column_config={
                    "username": "Username",
                    "full_name": "Full Name",
                    "total_photos": st.column_config.NumberColumn("Photos", format="%d"),
                    "total_likes": st.column_config.NumberColumn("Total Likes", format="%d"),
                    "total_downloads": st.column_config.NumberColumn("Total Downloads", format="%d"),
                    "avg_likes_per_photo": st.column_config.NumberColumn("Avg Likes/Photo", format="%.1f"),
                    "avg_downloads_per_photo": st.column_config.NumberColumn("Avg Downloads/Photo", format="%.1f")
                },
                hide_index=True
            )
        else:
            st.warning(f"No photographer analysis data available for {analysis_date}")

# Search Trends Page
elif page == "Search Trends":
    st.header("🔍 Search Trends")
    
    # Days selector
    days = st.slider("Select time period (days)", 1, 30, 7)
    
    # Fetch search trends
    search_data = fetch_api_data(f"/trends/search?days={days}&limit=50")
    
    if search_data and search_data.get("search_trends"):
        trends = search_data["search_trends"]
        df = pd.DataFrame(trends)
        
        if not df.empty:
            # Top search terms
            st.subheader("🔥 Trending Search Terms")
            
            fig = px.bar(
                df.head(20),
                x='search_term',
                y='search_count',
                title=f'Top 20 Search Terms (Last {days} days)',
                labels={'search_term': 'Search Term', 'search_count': 'Search Count'}
            )
            fig.update_xaxes(tickangle=45)
            st.plotly_chart(fig, use_container_width=True)
            
            # Search trends over time (if we have date data)
            if 'trend_date' in df.columns:
                df['trend_date'] = pd.to_datetime(df['trend_date'])
                
                # Group by date and sum search counts
                daily_searches = df.groupby('trend_date')['search_count'].sum().reset_index()
                
                fig = px.line(
                    daily_searches,
                    x='trend_date',
                    y='search_count',
                    title='Daily Search Activity',
                    labels={'trend_date': 'Date', 'search_count': 'Total Search Count'}
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Search terms table
            st.subheader("📋 Search Terms Details")
            
            display_df = df[['search_term', 'search_count', 'category', 'trend_date']].head(30)
            
            st.dataframe(
                display_df,
                column_config={
                    "search_term": "Search Term",
                    "search_count": st.column_config.NumberColumn("Search Count", format="%d"),
                    "category": "Category",
                    "trend_date": "Date"
                },
                hide_index=True
            )
        else:
            st.warning(f"No search trends data available for the last {days} days")

# Data Quality Page
elif page == "Data Quality":
    st.header("🔍 Data Quality Dashboard")
    
    # Health check
    health_data = fetch_api_data("/health")
    
    if health_data:
        st.subheader("🏥 System Health")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            status = health_data.get("status", "unknown")
            st.metric(
                "System Status",
                status.title(),
                delta="✅" if status == "healthy" else "❌"
            )
        
        with col2:
            db_status = health_data.get("database", "unknown")
            st.metric(
                "Database",
                db_status.title(),
                delta="✅" if db_status == "connected" else "❌"
            )
        
        with col3:
            total_photos = health_data.get("total_photos", 0)
            st.metric("Total Photos", format_number(total_photos))
    
    # ETL Job Status
    stats_data = fetch_api_data("/analytics/statistics")
    
    if stats_data and stats_data.get("latest_etl_job"):
        st.subheader("⚙️ Latest ETL Job")
        
        etl_job = stats_data["latest_etl_job"]
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Job Name", etl_job["job_name"])
        
        with col2:
            status = etl_job["status"]
            st.metric(
                "Status",
                status.title(),
                delta="✅" if status == "completed" else "⚠️"
            )
        
        with col3:
            st.metric("Records Processed", format_number(etl_job["records_processed"]))
        
        with col4:
            started_at = datetime.fromisoformat(etl_job["started_at"])
            st.metric("Started", started_at.strftime("%H:%M"))
    
    # Data freshness
    st.subheader("📅 Data Freshness")
    
    # This would typically check the most recent data timestamps
    st.info("Data freshness checks would be implemented here to ensure data is up-to-date.")
    
    # Data completeness
    st.subheader("📊 Data Completeness")
    
    # This would check for missing data, null values, etc.
    st.info("Data completeness checks would be implemented here to identify data gaps.")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
        <p>Splash Visual Trends Analytics Dashboard | Built with Streamlit & FastAPI</p>
    </div>
    """,
    unsafe_allow_html=True
) 