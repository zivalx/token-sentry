#!/bin/bash
# TokenHealth - Unix run script

set -e

case "$1" in
  build)
    echo "Building Docker containers..."
    docker-compose build
    ;;
  up)
    echo "Starting all services..."
    DEMO_MODE=true docker-compose up
    ;;
  up-build)
    echo "Building and starting all services..."
    DEMO_MODE=true docker-compose up --build
    ;;
  down)
    echo "Stopping all services..."
    docker-compose down
    ;;
  logs)
    echo "Showing logs..."
    docker-compose logs -f
    ;;
  test)
    echo "Running tests..."
    cd backend
    pytest test_app.py -v
    cd ..
    ;;
  clean)
    echo "Cleaning up..."
    docker-compose down -v --rmi all
    ;;
  *)
    echo "Usage: ./run.sh [command]"
    echo ""
    echo "Available commands:"
    echo "  build       - Build Docker containers"
    echo "  up          - Start all services"
    echo "  up-build    - Build and start all services"
    echo "  down        - Stop all services"
    echo "  logs        - View logs"
    echo "  test        - Run backend tests"
    echo "  clean       - Remove containers and images"
    exit 1
    ;;
esac
