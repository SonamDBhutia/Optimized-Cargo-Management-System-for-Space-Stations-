# Space Station Cargo Management System

A comprehensive solution for organizing, tracking, and managing cargo aboard a space station using advanced spatial algorithms.

## Features

- **3D Space Optimization**: Efficiently utilizes limited storage space using octree data structure
- **Intelligent Item Placement**: Suggests optimal placement locations for new items
- **Retrieval Path Planning**: Computes the easiest retrieval path for items
- **Expiry Tracking**: Monitors item expiration dates and usage limits
- **Waste Management**: Identifies and manages waste items for return shipments
- **Time Simulation**: Forecasts future inventory states based on expected consumption
- **Visualization**: 3D visualization of containers and their contents

## Technology Stack

- **Backend**: Flask, SQLAlchemy, PostgreSQL
- **Algorithms**: Custom octree implementation for spatial queries
- **Frontend**: Bootstrap, Three.js for 3D visualization
- **Deployment**: Gunicorn

## System Architecture

The system is organized into several key components:

1. **Database Layer**: PostgreSQL with SQLAlchemy ORM
   - Models for Zones, Containers, Items, and Usage Logs

2. **Spatial Algorithm**: Octree-based spatial partitioning
   - Efficient collision detection
   - Finding optimal placements
   - Computing retrieval paths

3. **API Layer**: REST endpoints for all operations
   - Item management
   - Container operations
   - Retrieval planning
   - Waste processing

4. **User Interface**: Web-based dashboard
   - Overview statistics
   - 3D container visualization
   - Item management forms
   - Simulation controls

5. **Time Simulation**: Time advancement and forecasting
   - Expiry prediction
   - Usage pattern analysis

## Getting Started

### Prerequisites

- Python 3.11
- PostgreSQL database

### Installation (Standard)

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Set up environment variables:
   ```
   DATABASE_URL=postgresql://username:password@localhost/dbname
   ```
4. Initialize the database:
   ```
   python -c "from database import initialize_db; initialize_db()"
   ```
5. Run the application:
   ```
   gunicorn --bind 0.0.0.0:5000 main:app
   ```

### Docker Deployment

The application can also be deployed using Docker and Docker Compose:

#### Prerequisites
- Docker
- Docker Compose

#### Deployment Steps

1. Clone the repository
2. Run the deployment script:
   ```
   ./docker-deploy.sh
   ```
   
   Or manually:
   ```
   docker-compose up -d --build
   docker-compose exec web python -c "from database import initialize_db; initialize_db()"
   ```

3. Access the application at http://localhost:5000

#### Environment Variables

These can be configured in the `docker-compose.yml` file:

- `DATABASE_URL`: Database connection string
- `SESSION_SECRET`: Secret key for session management

## Usage Guide

### Adding New Items

1. Navigate to the Items page
2. Click "Add New Item"
3. Fill in item details (dimensions, mass, priority, etc.)
4. The system will suggest optimal placement

### Retrieving Items

1. Use the search function to find an item
2. View the retrieval steps required
3. Confirm retrieval

### Waste Management

1. Navigate to the Waste Management page
2. Review items marked as waste
3. Prepare items for return shipment

### Time Simulation

1. Navigate to the Simulation page
2. Advance time to simulate days passing
3. View forecasts for expiry and usage

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.