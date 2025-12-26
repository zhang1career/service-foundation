#!/bin/bash

set -e

# Configuration
IMAGE_NAME="service_foundation"
IMAGE_TAG="latest"

echo "🏗️  Building Service Foundation Docker Image..."

# Check if requirements.txt exists
if [ ! -f "requirements.txt" ]; then
    echo "❌ Error: requirements.txt not found"
    echo "   Please ensure requirements.txt exists in the project root"
    exit 1
fi

echo "📦 Using requirements.txt for dependencies"

# Check if manage.py exists
if [ ! -f "manage.py" ]; then
    echo "❌ Error: manage.py not found"
    echo "   Please ensure this is a Django project"
    exit 1
fi

echo "✅ Django project detected"

# Build Docker image
echo "🐳 Building Docker image: $IMAGE_NAME:$IMAGE_TAG"
docker build -t "$IMAGE_NAME:$IMAGE_TAG" .

# Tag with version if provided
if [ ! -z "$1" ]; then
    VERSION_TAG="$1"
    docker tag "$IMAGE_NAME:$IMAGE_TAG" "$IMAGE_NAME:$VERSION_TAG"
    echo "🏷️  Tagged image as: $IMAGE_NAME:$VERSION_TAG"
fi

echo "✅ Docker image built successfully!"
echo "   Image: $IMAGE_NAME:$IMAGE_TAG"
echo ""
echo "🚀 Run with:"
echo "   docker-compose up -d"
