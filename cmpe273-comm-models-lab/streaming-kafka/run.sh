#!/bin/bash
# Build and run Kafka streaming tests

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "======================================"
echo "Kafka Streaming - Part C"
echo "======================================"
echo ""

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "Error: docker-compose is not installed"
    exit 1
fi

# Check if docker is running
if ! docker ps > /dev/null 2>&1; then
    echo "Error: Docker daemon is not running"
    exit 1
fi

# Parse arguments
BUILD=false
UP=false
TEST=false
DOWN=false
LOGS=false

if [ $# -eq 0 ]; then
    # Default: build, up, test
    BUILD=true
    UP=true
    TEST=true
else
    case "$1" in
        build)
            BUILD=true
            ;;
        up)
            UP=true
            ;;
        test)
            TEST=true
            ;;
        down)
            DOWN=true
            ;;
        logs)
            LOGS=true
            ;;
        all)
            BUILD=true
            UP=true
            TEST=true
            ;;
        clean)
            BUILD=true
            UP=true
            DOWN=true
            ;;
        *)
            echo "Usage: $0 [build|up|test|down|logs|all|clean]"
            echo ""
            echo "Commands:"
            echo "  build    - Build Docker images"
            echo "  up       - Start services"
            echo "  test     - Run test suite"
            echo "  down     - Stop and remove containers"
            echo "  logs     - View live logs"
            echo "  all      - Build, start, and test (default)"
            echo "  clean    - Remove all containers and volumes"
            exit 0
            ;;
    esac
fi

# Build images
if [ "$BUILD" = true ]; then
    echo "Building Docker images..."
    docker-compose build --no-cache
    echo "✓ Images built successfully"
    echo ""
fi

# Start services
if [ "$UP" = true ]; then
    echo "Starting services..."
    docker-compose up -d
    
    echo "Waiting for Kafka to be ready..."
    for i in {1..30}; do
        if docker logs kafka 2>&1 | grep -q "started SocketServer"; then
            echo "✓ Kafka is ready"
            break
        fi
        echo "  Waiting... ($i/30)"
        sleep 2
    done
    
    echo "Waiting for services to be healthy..."
    sleep 5
    echo "✓ Services started successfully"
    echo ""
fi

# Run tests
if [ "$TEST" = true ]; then
    echo "Running test suite..."
    docker-compose run --rm tests
    echo ""
    echo "✓ Tests completed"
    
    # Show test report location
    if [ -f /tmp/kafka_test_report.txt ]; then
        echo ""
        echo "Test report saved to: /tmp/kafka_test_report.txt"
        echo ""
        echo "Report contents:"
        echo "---"
        cat /tmp/kafka_test_report.txt
        echo "---"
    fi
fi

# Show logs
if [ "$LOGS" = true ]; then
    echo "Showing live logs (Ctrl+C to stop)..."
    docker-compose logs -f
fi

# Stop services
if [ "$DOWN" = true ]; then
    echo "Stopping services..."
    docker-compose down
    
    if [ "$BUILD" = false ] && [ "$UP" = false ] && [ "$TEST" = false ]; then
        # Only cleanup if user explicitly asked for 'down'
        echo "Removing volumes..."
        docker-compose down -v
        echo "✓ Services stopped and cleaned up"
    else
        echo "✓ Services stopped"
    fi
fi

echo ""
echo "======================================"
echo "Done!"
echo "======================================"
