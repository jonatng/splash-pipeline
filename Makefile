.PHONY: help setup build up down logs clean test lint format install dev

# Default target
help:
	@echo "🚀 Splash Visual Trends Analytics - Available Commands"
	@echo "=================================================="
	@echo "setup     - Run the setup script"
	@echo "build     - Build Docker images"
	@echo "up        - Start all services"
	@echo "down      - Stop all services"
	@echo "logs      - View logs from all services"
	@echo "clean     - Clean up Docker resources"
	@echo "test      - Run tests"
	@echo "lint      - Run code linting"
	@echo "format    - Format code"
	@echo "install   - Install Python dependencies"
	@echo "dev       - Start development environment"
	@echo "dbt-run   - Run dbt transformations"
	@echo "dbt-test  - Run dbt tests"
	@echo "dbt-docs  - Generate and serve dbt documentation"
	@echo "pipeline  - Run the full ETL pipeline"
	@echo "supabase-setup - Initialize Supabase database"

# Setup the application
setup:
	@echo "🚀 Setting up Splash Visual Trends Analytics..."
	@chmod +x scripts/setup.sh
	@./scripts/setup.sh

# Build Docker images
build:
	@echo "🐳 Building Docker images..."
	@docker-compose build

# Start all services
up:
	@echo "🚀 Starting all services..."
	@docker-compose up -d

# Stop all services
down:
	@echo "🛑 Stopping all services..."
	@docker-compose down

# View logs
logs:
	@echo "📋 Viewing logs..."
	@docker-compose logs -f

# Clean up Docker resources
clean:
	@echo "🧹 Cleaning up Docker resources..."
	@docker-compose down -v
	@docker system prune -f

# Run tests
test:
	@echo "🧪 Running tests..."
	@python -m pytest tests/ -v

# Run linting
lint:
	@echo "🔍 Running code linting..."
	@python -m flake8 src/ tests/
	@python -m mypy src/

# Format code
format:
	@echo "✨ Formatting code..."
	@python -m black src/ tests/
	@python -m isort src/ tests/

# Install Python dependencies
install:
	@echo "📦 Installing Python dependencies..."
	@pip install -r requirements.txt

# Start development environment
dev: install
	@echo "🛠️ Starting development environment..."
	@echo "Starting FastAPI development server..."
	@uvicorn src.api.main:app --reload --port 8000 &
	@echo "Starting Streamlit dashboard..."
	@streamlit run src/dashboard/main.py --server.port 8501

# Supabase operations
supabase-setup:
	@echo "🗄️ Setting up Supabase database..."
	@python setup_supabase.py

supabase-test:
	@echo "🔄 Testing Supabase connection..."
	@python -c "from setup_supabase import check_supabase_connection; check_supabase_connection()"

# dbt operations
dbt-deps:
	@echo "📦 Installing dbt dependencies..."
	@cd dbt_project && dbt deps

dbt-run:
	@echo "🔄 Running dbt transformations..."
	@cd dbt_project && dbt run

dbt-test:
	@echo "🧪 Running dbt tests..."
	@cd dbt_project && dbt test

dbt-docs:
	@echo "📚 Generating dbt documentation..."
	@cd dbt_project && dbt docs generate
	@cd dbt_project && dbt docs serve --port 8080

dbt-clean:
	@echo "🧹 Cleaning dbt artifacts..."
	@cd dbt_project && dbt clean

# Pipeline operations
pipeline:
	@echo "🚀 Running full ETL pipeline..."
	@python src/etl/dbt_runner.py

pipeline-docker:
	@echo "🐳 Running pipeline in Docker..."
	@docker-compose run --rm dbt-runner

# Monitoring
status:
	@echo "📊 Service Status:"
	@docker-compose ps

health:
	@echo "🏥 Health Checks:"
	@curl -s http://localhost:8000/health | jq . || echo "API not responding"
	@curl -s http://localhost:8501 > /dev/null && echo "✅ Streamlit is running" || echo "❌ Streamlit not responding"

# Data operations
extract-sample:
	@echo "📥 Extracting sample data..."
	@python -c "from src.etl.unsplash_client import create_unsplash_client; client = create_unsplash_client(); photos = client.extract_photo_batch(10); print(f'Extracted {len(photos)} photos')"

# Environment setup
env-check:
	@echo "🔍 Checking environment configuration..."
	@python -c "import os; print('✅ DATABASE_URL set' if os.getenv('DATABASE_URL') else '❌ DATABASE_URL missing'); print('✅ SUPABASE_URL set' if os.getenv('SUPABASE_URL') else '❌ SUPABASE_URL missing'); print('✅ UNSPLASH_ACCESS_KEY set' if os.getenv('UNSPLASH_ACCESS_KEY') else '❌ UNSPLASH_ACCESS_KEY missing')"

# Quick start for new users
quickstart: install supabase-setup
	@echo "🎉 Quick start completed!"
	@echo "Run 'make dev' to start the development environment" 