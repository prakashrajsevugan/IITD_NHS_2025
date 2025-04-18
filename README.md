# Space Station Cargo Management System

A modern web application for managing cargo on a space station, featuring an animated and attractive UI with space theme.

## Docker Setup

This project is containerized using Docker for easy deployment and consistent runtime environments.

### Prerequisites

- [Docker](https://www.docker.com/get-started) installed on your system
- [Docker Compose](https://docs.docker.com/compose/install/) installed on your system

### Building and Running the Container

1. Clone this repository:
   ```
   git clone <repository-url>
   cd SpaceCargoManager
   ```

2. Build and start the Docker container:
   ```
   docker-compose up --build
   ```

3. Access the application:
   - Open your browser and navigate to `http://localhost:8000`

### Docker Commands Reference

- Start the application in detached mode:
  ```
  docker-compose up -d
  ```

- Stop the application:
  ```
  docker-compose down
  ```

- View logs:
  ```
  docker-compose logs -f
  ```

- Rebuild the container after changes:
  ```
  docker-compose up --build
  ```

## Project Structure

```
SpaceCargoManager/
├── backend/                # Backend FastAPI application
│   ├── app/                # Application code
│   │   ├── static/         # Frontend static files (HTML, CSS, JS)
│   │   ├── main.py         # Main FastAPI application
│   │   └── ...             # Other backend modules
│   ├── Dockerfile          # Backend Docker configuration
│   └── requirements.txt    # Python dependencies
├── docker-compose.yml      # Docker Compose configuration
└── space_cargo.db          # SQLite database file
```

## Features

- Modern, animated UI with space theme
- Cargo management and tracking
- Waste management system
- Time simulation for mission planning
- Interactive dashboard with real-time updates

## API Endpoints

- `/api/test` - Test endpoint to verify API connectivity
- `/api/simulation/status` - Get current mission date and days since start
- `/api/simulate/day` - Get current simulation date

## Development

For development purposes, you can mount your local directories as volumes in the docker-compose.yml file to see changes in real-time without rebuilding the container.

## License

[MIT License](LICENSE)
#   I I T D _ N H S _ 2 0 2 5  
 