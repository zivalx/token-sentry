@echo off
REM token-sentry - Windows run script

if "%1"=="build" (
    echo Building Docker containers...
    docker-compose build
    goto :eof
)

if "%1"=="up" (
    echo Starting all services...
    docker-compose up
    goto :eof
)

if "%1"=="up-build" (
    echo Building and starting all services...
    docker-compose up --build
    goto :eof
)

if "%1"=="down" (
    echo Stopping all services...
    docker-compose down
    goto :eof
)

if "%1"=="logs" (
    echo Showing logs...
    docker-compose logs -f
    goto :eof
)

if "%1"=="test" (
    echo Running backend tests...
    cd backend
    pytest tests -v
    cd ..
    goto :eof
)

if "%1"=="clean" (
    echo Cleaning up...
    docker-compose down -v --rmi all
    goto :eof
)

echo Usage: run.bat [command]
echo.
echo Available commands:
echo   build       - Build Docker containers
echo   up          - Start all services
echo   up-build    - Build and start all services
echo   down        - Stop all services
echo   logs        - View logs
echo   test        - Run backend tests
echo   clean       - Remove containers and images
