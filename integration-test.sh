#!/bin/bash

# Integration test script for job processing system
set -e

echo "Starting integration tests..."

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 30

# Test health endpoints
echo "Testing health endpoints..."
curl -f http://localhost:3000/health || exit 1
curl -f http://localhost:8000/health || exit 1

# Submit a job
echo "Submitting test job..."
RESPONSE=$(curl -s -X POST http://localhost:3000/submit)
JOB_ID=$(echo $RESPONSE | jq -r '.job_id')

if [ -z "$JOB_ID" ] || [ "$JOB_ID" = "null" ]; then
    echo "Failed to create job"
    exit 1
fi

echo "Job ID: $JOB_ID"

# Poll for job completion (timeout after 60 seconds)
TIMEOUT=60
START_TIME=$(date +%s)

while true; do
    CURRENT_TIME=$(date +%s)
    ELAPSED=$((CURRENT_TIME - START_TIME))
    
    if [ $ELAPSED -gt $TIMEOUT ]; then
        echo "Job did not complete within ${TIMEOUT} seconds"
        exit 1
    fi
    
    STATUS=$(curl -s http://localhost:3000/status/$JOB_ID | jq -r '.status')
    echo "Job status: $STATUS (elapsed: ${ELAPSED}s)"
    
    if [ "$STATUS" = "completed" ]; then
        echo "✅ Job completed successfully!"
        exit 0
    elif [ "$STATUS" = "failed" ]; then
        echo "❌ Job failed!"
        exit 1
    fi
    
    sleep 2
done
