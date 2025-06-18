# 📊 Splash Visual Trends Analytics

A modern Visual Trends Analytics application powered by Unsplash data, built with FastAPI, Streamlit, dbt, and Supabase. This project analyzes visual trends, photographer performance, and engagement patterns in visual content.

## 🏗️ Architecture

**ELT Pipeline Architecture:**
- **Extract**: Modular `Extractor` class → Unsplash API data ingestion
- **Load**: Dedicated `Loader` class → Direct to Supabase PostgreSQL 
- **Transform**: `Transformer` class + dbt models → Analytics and aggregations
- **Orchestrate**: `PipelineRunner` → Complete ELT workflow management

**Tech Stack:**
- 🚀 **Backend**: FastAPI, SQLAlchemy, Pydantic
- 📊 **Frontend**: Streamlit dashboard with Plotly charts  
- 🗄️ **Database**: Supabase (PostgreSQL) with Row Level Security
- 🔐 **Authentication**: Supabase Auth with JWT tokens
- 🔄 **Data Pipeline**: Modular ELT architecture with Python + dbt transformations
- 🛠️ **Database Maintenance**: Automated cleanup jobs with pg_cron
- 🐳 **Infrastructure**: Docker Compose for local development
- 📈 **Analytics**: Pandas, NumPy, advanced SQL analytics

## 🚀 Quick Start

### 1. Clone and Setup
```bash
git clone <your-repo>
cd splash-pipeline
make install  # Install Python dependencies
```

## 🎯 Onboarding Guide

### New to the Project? Start Here!

This comprehensive guide will get you up and running with the Splash Visual Trends Analytics platform in under 30 minutes.

#### 📋 Prerequisites
- **Python 3.8+** installed on your system
- **Git** for version control
- **Supabase account** (free tier available)
- **Unsplash Developer account** (free)
- **Basic knowledge** of Python, SQL, and command line

#### 🎬 Step-by-Step Walkthrough

##### Phase 1: Environment Setup (5 minutes)
1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd splash-pipeline
   ```

2. **Install dependencies**
   ```bash
   make install
   # Or manually: pip install -r requirements.txt
   ```

3. **Verify installation**
   ```bash
   python --version  # Should be 3.8+
   make env-check    # Check environment setup
   ```

##### Phase 2: Database Setup (10 minutes)
1. **Create Supabase project**
   - Go to [app.supabase.com](https://app.supabase.com)
   - Click "New Project"
   - Choose organization and name your project
   - Wait for database provisioning (~2 minutes)

2. **Get your credentials**
   - Navigate to Settings → API
   - Copy your Project URL and API keys
   - Go to Settings → Database for connection string

3. **Configure environment**
   ```bash
   cp .env.example .env  # Copy template
   # Edit .env with your Supabase credentials
   ```

4. **Initialize database**
   ```bash
   make supabase-setup
   python setup_supabase.py
   ```

##### Phase 3: API Setup (5 minutes)
1. **Get Unsplash API key**
   - Visit [unsplash.com/developers](https://unsplash.com/developers)
   - Click "Register as a developer"
   - Create a new application
   - Copy your Access Key

2. **Add to environment**
   ```bash
   # Add to your .env file
   UNSPLASH_ACCESS_KEY=your_access_key_here
   ```

##### Phase 4: First Run (5 minutes)
1. **Test the pipeline**
   ```bash
   # Run a small test batch
   python src/elt/run_elt.py --batch-size 10 --log-level INFO
   ```

2. **Start the application**
   ```bash
   make dev
   # Or with Docker: make up
   ```

3. **Access the dashboard**
   - API: http://localhost:8000
   - Dashboard: http://localhost:8501
   - API Docs: http://localhost:8000/docs

##### Phase 5: Explore Features (5 minutes)
1. **Dashboard Overview**
   - Navigate through different analytics pages
   - Explore photo trends and tag analysis
   - Check photographer insights

2. **API Exploration**
   - Visit http://localhost:8000/docs
   - Try the interactive API endpoints
   - Test authentication flows

#### 🎓 Learning Path

**Beginner (Week 1)**
- [ ] Complete onboarding setup
- [ ] Run your first ELT pipeline
- [ ] Explore the dashboard features
- [ ] Understand the data models

**Intermediate (Week 2)**
- [ ] Customize pipeline parameters
- [ ] Add new data transformations
- [ ] Create custom dashboard views
- [ ] Set up automated scheduling

**Advanced (Week 3+)**
- [ ] Extend the API with new endpoints
- [ ] Add new data sources
- [ ] Implement custom analytics
- [ ] Contribute to the project

#### 🆘 Common First-Time Issues

**Database Connection Issues**
```bash
# Test your connection
make supabase-test

# Common fixes:
# 1. Check DATABASE_URL format
# 2. Verify Supabase project is active
# 3. Ensure IP is whitelisted (if applicable)
```

**API Rate Limits**
```bash
# Start with smaller batches
python src/elt/run_elt.py --batch-size 5

# Check your Unsplash plan limits
# Free tier: 50 requests/hour
```

**Import Errors**
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Check Python path
python -c "import sys; print(sys.path)"
```

#### 🎯 Success Checklist

After completing onboarding, you should be able to:
- [ ] ✅ Run the ELT pipeline successfully
- [ ] ✅ Access the dashboard and see data
- [ ] ✅ Make API calls and get responses
- [ ] ✅ Understand the project structure
- [ ] ✅ Know where to find documentation

#### 🤝 Getting Help

**Documentation**
- 📖 This README for comprehensive setup
- 🔧 [Troubleshooting section](#-troubleshooting) for common issues
- 📊 API docs at http://localhost:8000/docs

**Community**
- 🐛 [GitHub Issues](../../issues) for bug reports
- 💡 [Discussions](../../discussions) for questions
- 📧 Contact maintainers for urgent issues

**Next Steps**
- Explore the [Development Commands](#️-development-commands)
- Learn about [ELT Pipeline Architecture](#-elt-pipeline-architecture)
- Check out [Configuration options](#-configuration)

### 2. Configure Supabase
1. Create a Supabase project at [app.supabase.com](https://app.supabase.com)
2. Get your credentials from project settings
3. Create a `.env` file with your Supabase credentials:

```bash
# Create .env file with your Supabase credentials
touch .env
```

**Required Supabase Configuration:**
```env
# Database connection
DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres
POSTGRES_HOST=db.[YOUR-PROJECT-REF].supabase.co
POSTGRES_PASSWORD=[YOUR-PASSWORD]

# API access  
SUPABASE_URL=https://[YOUR-PROJECT-REF].supabase.co
SUPABASE_ANON_KEY=[YOUR-ANON-KEY]
SUPABASE_SERVICE_ROLE_KEY=[YOUR-SERVICE-ROLE-KEY]
```

### 3. Initialize Database
```bash
make supabase-setup  # Create tables and sample data
# Run database migrations
python setup_supabase.py  # Initialize core tables
# Apply user management migrations
psql $DATABASE_URL -f migrations/create_users_table.sql
psql $DATABASE_URL -f migrations/create_user_cleanup_job.sql
```

### 4. Get Unsplash API Key
1. Go to [unsplash.com/developers](https://unsplash.com/developers)
2. Create an application
3. Add your Access Key to `.env`:
```env
UNSPLASH_ACCESS_KEY=your_unsplash_access_key_here

# Optional: Rate limiting configuration (defaults shown)
UNSPLASH_RATE_LIMIT_PER_HOUR=5000    # Your API plan limit
UNSPLASH_BATCH_SIZE=20               # Photos per batch
UNSPLASH_MAX_RETRIES=3               # Retry attempts
UNSPLASH_BASE_DELAY=1                # Base delay (seconds)
UNSPLASH_MAX_DELAY=300               # Max delay (seconds)
```

> 📋 **Note**: See [RATE_LIMITING.md](RATE_LIMITING.md) for detailed rate limit configuration by API plan type.

### 5. Run the Application
```bash
# Option 1: Local development
make dev

# Option 2: Docker Compose
make up
```

**Access Points:**
- 🌐 API: http://localhost:8000
- 📊 Dashboard: http://localhost:8501  
- 📚 API Docs: http://localhost:8000/docs

## 🛠️ Development Commands

### Database Operations
```bash
make supabase-setup    # Initialize Supabase database
make supabase-test     # Test Supabase connection  
make env-check        # Check environment variables

# Database Migrations
psql $DATABASE_URL -f migrations/create_users_table.sql    # Create users table
psql $DATABASE_URL -f migrations/create_user_cleanup_job.sql # Setup cleanup jobs

# Monitor cleanup operations
psql $DATABASE_URL -c "SELECT * FROM cleanup_operations_summary;"
```

### ELT Pipeline Operations
```bash
# Full ELT Pipeline
python src/elt/run_elt.py                    # Run complete ELT pipeline
python src/elt/run_elt.py --batch-size 100  # Custom batch size

# Individual Phases
python src/elt/run_elt.py --extract-only    # Extract data only
python src/elt/run_elt.py --transform-only  # Transform data only

# Advanced Options
python src/elt/run_elt.py --analysis-date 2024-12-20  # Specific analysis date
python src/elt/run_elt.py --log-level DEBUG           # Detailed logging

# Legacy Commands (still supported)
make pipeline         # Run full ELT pipeline
make dbt-run         # Run dbt transformations only
make dbt-test        # Run dbt tests
make dbt-docs        # Generate dbt documentation
```

### Development
```bash
make install         # Install dependencies
make dev            # Start development servers
make test           # Run tests
make lint           # Run code linting
make format         # Format code
```

### Docker Operations
```bash
make build          # Build images
make up            # Start all services  
make down          # Stop services
make logs          # View logs
make clean         # Clean Docker resources
```

## 📊 Data Models

### Core Tables (Raw Data)
- **users**: User authentication and profile data with Supabase integration
- **photos**: Raw photo metadata from Unsplash
- **search_trends**: Search term trending data
- **photo_statistics**: Engagement metrics over time
- **cleanup_logs**: Database maintenance and cleanup operation logs

### Analytics Models (dbt Transformations)
- **stg_photos**: Cleaned photos with calculated fields
- **int_tag_metrics**: Tag performance analysis
- **int_photographer_metrics**: Photographer analytics
- **mart_daily_trends**: Time-series trend analysis
- **mart_tag_cooccurrence**: Tag relationship networks

### User Management
- **Row Level Security (RLS)**: Users can only access their own data
- **Automated Cleanup**: Daily cleanup jobs to remove duplicate users
- **Audit Logging**: All cleanup operations are logged for monitoring

## 🎯 Key Features

### 🔐 User Authentication & Management
- **Supabase Auth Integration**: Secure user authentication with JWT tokens
- **Row Level Security**: Data isolation ensuring users only access their own data
- **Automated User Cleanup**: Daily cron jobs to remove duplicate user records
- **Audit Logging**: Complete audit trail of all database maintenance operations
- **User Profile Management**: Update preferences and profile information

### 📈 Analytics Dashboard
- **Trend Analysis**: Visual trends over time with interactive charts
- **Tag Performance**: Most popular tags, engagement rates, co-occurrence
- **Photographer Insights**: Top performers, engagement scores, style analysis
- **Search Trends**: Trending searches and content discovery patterns
- **Color Analysis**: Color palette trends and emotional associations

### 🔄 Modular ELT Pipeline
- **Extract (`Extractor`)**: Dedicated class for Unsplash API data ingestion
- **Load (`Loader`)**: Specialized class for data warehouse loading
- **Transform (`Transformer`)**: Python-based analysis + dbt transformations
- **Orchestration (`PipelineRunner`)**: Complete workflow management
- **CLI Interface**: Command-line tool for pipeline operations
- **Data Quality**: Automated testing and validation
- **Documentation**: Self-documenting data models and lineage

### 🚀 API Endpoints
- `GET /photos` - Photo search and filtering
- `GET /trends` - Trending analysis data
- `GET /analytics` - Advanced analytics queries
- `GET /search` - Search functionality
- `GET /health` - System health checks
- `POST /auth/login` - User authentication
- `GET /users/me` - Current user profile
- `PUT /users/me` - Update user profile

## 📁 Project Structure

```
splash-pipeline/
├── src/
│   ├── api/           # FastAPI application
│   ├── dashboard/     # Streamlit dashboard
│   ├── elt/          # ELT pipeline (modular architecture)
│   │   ├── extract/   # Data extraction module
│   │   │   ├── __init__.py
│   │   │   └── extractor.py      # Extractor class
│   │   ├── load/      # Data loading module
│   │   │   ├── __init__.py
│   │   │   └── loader.py         # Loader class
│   │   ├── transform/ # Data transformation module
│   │   │   ├── __init__.py
│   │   │   └── transformer.py    # Transformer class
│   │   ├── pipeline_runner.py    # ELT orchestration
│   │   ├── run_elt.py           # CLI interface
│   │   └── unsplash_client.py   # API client
│   ├── models/       # SQLAlchemy models
│   └── utils/        # Authentication utilities
├── migrations/       # Database migration scripts
│   ├── create_users_table.sql     # User management setup
│   └── create_user_cleanup_job.sql # Automated cleanup jobs
├── dbt_project/      # dbt transformations
│   ├── models/
│   │   ├── staging/  # Cleaned source data
│   │   ├── intermediate/ # Business logic
│   │   └── marts/    # Analytics tables
│   └── tests/        # dbt tests
├── setup_supabase.py # Database initialization script
├── docker-compose.yml # Service orchestration
├── requirements.txt   # Python dependencies
├── RATE_LIMITING.md  # Rate limiting documentation
└── Makefile          # Development commands
```

## 🔧 Configuration

### Environment Variables
Key configuration options include:
- **Supabase**: Database credentials and connection settings
- **Unsplash API**: Access key and rate limiting parameters
- **dbt**: Profile paths and transformation settings
- **Application**: Logging levels and server configurations
- **Authentication**: JWT secrets and session management

Required environment variables:
```env
# Supabase Configuration
DATABASE_URL=postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
SUPABASE_URL=https://[PROJECT-REF].supabase.co
SUPABASE_ANON_KEY=[YOUR-ANON-KEY]
SUPABASE_SERVICE_ROLE_KEY=[YOUR-SERVICE-ROLE-KEY]

# Unsplash API
UNSPLASH_ACCESS_KEY=[YOUR-ACCESS-KEY]

# Authentication
JWT_SECRET_KEY=[RANDOM-SECRET-KEY]
```

### dbt Configuration
- **Profiles**: `dbt_project/profiles.yml` 
- **Project**: `dbt_project/dbt_project.yml`
- **Models**: Materialized as views (staging/intermediate) and tables (marts)

## 🔧 Database Maintenance

### Automated Cleanup Jobs
The application includes automated database maintenance through pg_cron:

- **Daily User Cleanup**: Runs at 3 AM UTC daily to remove duplicate user records
- **Cleanup Monitoring**: View `cleanup_operations_summary` for maintenance history
- **Manual Cleanup**: Run `SELECT cleanup_duplicate_users();` to trigger manually

### Migration Management
Database migrations are located in the `migrations/` directory:

1. **User Table Setup**: `create_users_table.sql` - Creates user management infrastructure
2. **Cleanup Jobs**: `create_user_cleanup_job.sql` - Sets up automated maintenance

Apply migrations in order:
```bash
psql $DATABASE_URL -f migrations/create_users_table.sql
psql $DATABASE_URL -f migrations/create_user_cleanup_job.sql
```

## 🔄 ELT Pipeline Architecture

### Modular Design
The ELT pipeline is built with a modular architecture for maintainability and scalability:

#### 🔍 Extract Phase (`src/elt/extract/extractor.py`)
- **Purpose**: Raw data ingestion from Unsplash API
- **Features**: 
  - Rate limiting and retry logic
  - Batch processing with configurable sizes
  - Error handling and logging
- **Usage**: `extractor.extract_photos(batch_size=50)`

#### 💾 Load Phase (`src/elt/load/loader.py`)
- **Purpose**: Direct loading into Supabase data warehouse
- **Features**:
  - Session management and transactions
  - Data transformation during loading
  - ETL job logging and tracking
- **Usage**: `loader.load_photos(photos_data)`

#### �� Transform Phase (`src/elt/transform/transformer.py`)
- **Purpose**: Data analysis and aggregations
- **Features**:
  - Tag analysis and co-occurrence
  - Photographer performance metrics
  - Daily trend generation
  - Integration with dbt transformations
- **Usage**: `transformer.analyze_tags(analysis_date)`

#### 🎯 Orchestration (`src/elt/pipeline_runner.py`)
- **Purpose**: Complete ELT workflow management
- **Features**:
  - Phase-by-phase execution
  - Error handling and recovery
  - Comprehensive logging and reporting
  - dbt integration
- **Usage**: `runner.run_full_elt_pipeline()`

### CLI Interface (`src/elt/run_elt.py`)
Command-line interface for pipeline operations:

```bash
# Full pipeline with options
python src/elt/run_elt.py --batch-size 100 --log-level DEBUG

# Individual phases
python src/elt/run_elt.py --extract-only
python src/elt/run_elt.py --transform-only --analysis-date 2024-12-20

# Help and options
python src/elt/run_elt.py --help
```

### Data Quality & Monitoring
- **ETL Job Tracking**: All operations logged with status and metadata
- **Error Handling**: Graceful failure handling with detailed error messages
- **Progress Monitoring**: Real-time progress updates and execution summaries
- **dbt Integration**: Automated testing and documentation generation

## 🐛 Troubleshooting

### Database Issues
- **Connection**: Verify `DATABASE_URL` in `.env` matches your Supabase project
- **Permissions**: Ensure your Supabase user has necessary permissions for cron jobs
- **Migrations**: Check migration logs if cleanup jobs aren't running:
  ```sql
  SELECT * FROM cleanup_logs ORDER BY created_at DESC LIMIT 10;
  ```

### ELT Pipeline Issues
- **API Rate Limits**: Check Unsplash API usage and adjust batch sizes
- **Transform Failures**: Review ETL job logs: `SELECT * FROM etl_jobs ORDER BY started_at DESC;`
- **dbt Issues**: Run `dbt debug` to check dbt configuration
- **CLI Problems**: Use `--log-level DEBUG` for detailed troubleshooting

### Authentication Issues
- **JWT Tokens**: Verify `JWT_SECRET_KEY` is set and consistent across restarts
- **Supabase Auth**: Ensure `SUPABASE_ANON_KEY` and `SUPABASE_SERVICE_ROLE_KEY` are correct
- **RLS Policies**: Check that Row Level Security policies are properly configured

## 📊 Migration from PostgreSQL

This project has been migrated from local PostgreSQL to Supabase for better scalability and reduced infrastructure complexity:

### ✅ What Changed
- ❌ Removed local PostgreSQL container
- ❌ Removed PostgreSQL volumes and health checks  
- ✅ Added Supabase configuration
- ✅ Updated dbt to connect to Supabase
- ✅ Created Supabase setup script
- ✅ Updated Docker Compose (3 services vs 6 originally)
- ✅ Refactored ETL to modular ELT architecture

### 🎯 Benefits
- **🌐 Cloud-native**: No local database management
- **📈 Scalable**: Automatic scaling with Supabase
- **🔒 Secure**: Built-in authentication and RLS
- **⚡ Fast**: Global CDN and optimized queries
- **💰 Cost-effective**: Pay for what you use
- **🔧 Simple**: Fewer moving parts in development
- **🔄 Modular**: Separate Extract, Load, Transform phases

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes  
4. Run tests: `make test`
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For issues and questions:
1. Check the [documentation](docs/)
2. Review [common issues](docs/troubleshooting.md)  
3. Create a GitHub issue

---

Built with ❤️ using FastAPI, Streamlit, dbt, and Supabase