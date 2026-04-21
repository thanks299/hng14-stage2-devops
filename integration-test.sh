#!/bin/bash
set -e

echo "=========================================="
echo "Starting integration tests"
echo "=========================================="

# Function to check if a service is responding
check_service() {
    local url=$1
    local name=$2
    local max_attempts=30
    local attempt=1
    
    echo "Waiting for $name to be ready..."
    while [ $attempt -le $max_attempts ]; do
        if curl -sf "$url" > /dev/null 2>&1; then
            echo "✓ $name is ready (attempt $attempt)"
            return 0
        fi
        echo "  Attempt $attempt/$max_attempts: $name not ready yet..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo "✗ $name failed to become ready within timeout"
    return 1
}

# Wait for containers to start
echo ""
echo "Step 1: Waiting for containers to start..."
sleep 20

# Check API health
check_service "http://localhost:8000/health" "API" || exit 1

# Check frontend health
check_service "http://localhost:3000/health" "Frontend" || exit 1

# Submit a job
echo ""
echo "Step 2: Submitting a test job..."
RESPONSE=$(curl -s -X POST http://localhost:3000/submit)
echo "Response: $RESPONSE"

JOB_ID=$(echo "$RESPONSE" | jq -r '.job_id')
if [ -z "$JOB_ID" ] || [ "$JOB_ID" = "null" ]; then
    echo "✗ Failed to get job ID from response"
    exit 1
fi
echo "✓ Job created with ID: $JOB_ID"

# Poll for job completion
echo ""
echo "Step 3: Waiting for job to complete..."
MAX_ATTEMPTS=60
ATTEMPT=1
COMPLETED=false

while [ $ATTEMPT -le $MAX_ATTEMPTS ]; do
    STATUS_RESPONSE=$(curl -s http://localhost:3000/status/$JOB_ID)
    STATUS=$(echo "$STATUS_RESPONSE" | jq -r '.status')
    
    echo "  Attempt $ATTEMPT/$MAX_ATTEMPTS: Job status = $STATUS"
    
    if [ "$STATUS" = "completed" ]; then
        COMPLETED=true
        echo "✓ Job completed successfully!"
        break
    elif [ "$STATUS" = "failed" ]; then
        echo "✗ Job failed!"
        exit 1
    fi
    
    ATTEMPT=$((ATTEMPT + 1))
    sleep 2
done

if [ "$COMPLETED" = false ]; then
    echo "✗ Job did not complete within timeout"
    echo ""
    echo "Debug information:"
    echo "Worker logs:"
    docker logs job-queue-worker --tail 50 2>&1 || echo "Worker not running"
    exit 1
fi

echo ""
echo "=========================================="
echo "All integration tests passed! ✓"
echo "=========================================="
