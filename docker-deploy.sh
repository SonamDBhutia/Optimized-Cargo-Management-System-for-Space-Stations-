#!/bin/bash

# Exit on error
set -e

# Build and start Docker containers
echo "Building and starting Docker containers..."
docker-compose up -d --build

# Wait for database to be ready
echo "Waiting for database to be ready..."
sleep 10

# Initialize the database
echo "Initializing the database..."
docker-compose exec web python -c "from database import initialize_db; initialize_db()"

echo "Deployment completed successfully!"
echo "The application is now running at http://localhost:5000"