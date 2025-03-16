#!/bin/bash

# Create a directory for Docker files
mkdir -p docker_files

# Copy Docker-related files to the directory
cp Dockerfile docker_files/
cp docker-compose.yml docker_files/
cp docker-deploy.sh docker_files/
cp .dockerignore docker_files/

# Make the deploy script executable
chmod +x docker_files/docker-deploy.sh

# Create a tar archive
tar -czf docker_files.tar.gz docker_files

# Clean up
rm -rf docker_files

echo "Docker files have been archived to docker_files.tar.gz"
echo "You can now download this file from the Replit Files panel"