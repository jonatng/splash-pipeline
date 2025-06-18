#!/bin/bash

# Splash Visual Trends Analytics Setup Script

set -e

echo "🚀 Setting up Splash Visual Trends Analytics..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp env.example .env
    echo "✅ .env file created. Please edit it with your Unsplash API key."
    echo ""
    echo "To get your Unsplash API key:"
    echo "1. Go to https://unsplash.com/developers"
    echo "2. Create a new application"
    echo "3. Copy the Access Key"
    echo "4. Edit .env file and set UNSPLASH_ACCESS_KEY=your_key_here"
    echo ""
    read -p "Press Enter after you've updated the .env file..."
fi

# Check if UNSPLASH_ACCESS_KEY is set
if ! grep -q "UNSPLASH_ACCESS_KEY=.*[^=]" .env; then
    echo "❌ UNSPLASH_ACCESS_KEY is not set in .env file."
    echo "Please edit .env and add your Unsplash API key."
    exit 1
fi

# Create data directories
echo "📁 Creating data directories..."
mkdir -p data/lake data/warehouse logs

# Generate Airflow Fernet key if not set
if ! grep -q "AIRFLOW__CORE__FERNET_KEY=.*[^=]" .env; then
    echo "🔑 Generating Airflow Fernet key..."
    FERNET_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
    sed -i "s/AIRFLOW__CORE__FERNET_KEY=.*/AIRFLOW__CORE__FERNET_KEY=$FERNET_KEY/" .env
fi

# Build and start services
echo "🐳 Building and starting Docker services..."
docker-compose up -d --build

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 30

# Check service health
echo "🏥 Checking service health..."

# Check PostgreSQL
if docker-compose exec -T postgres pg_isready -U splash_user -d splash_analytics > /dev/null 2>&1; then
    echo "✅ PostgreSQL is ready"
else
    echo "❌ PostgreSQL is not ready"
fi

# Check API
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ FastAPI is ready"
else
    echo "⚠️  FastAPI is starting up..."
fi

# Check Streamlit
if curl -s http://localhost:8501 > /dev/null 2>&1; then
    echo "✅ Streamlit is ready"
else
    echo "⚠️  Streamlit is starting up..."
fi

echo ""
echo "🎉 Setup complete! Your applications are available at:"
echo ""
echo "📊 Streamlit Dashboard: http://localhost:8501"
echo "🔧 FastAPI Documentation: http://localhost:8000/docs"
echo "⚙️  Airflow Web UI: http://localhost:8080 (admin/admin)"
echo ""
echo "📚 Check the README.md for more information."
echo ""
echo "To view logs: docker-compose logs -f"
echo "To stop services: docker-compose down" 