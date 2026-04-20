# Build and start all services
docker-compose up --build

# In another terminal, test the application
# Submit a job
curl -X POST http://localhost:3000/submit

# Check job status (replace JOB_ID with actual ID)
curl http://localhost:3000/status/JOB_ID

# Check service health
curl http://localhost:3000/health

# Stop all containers
docker-compose down

# Stop and remove volumes (cleans Redis data)
docker-compose down -v

docker-compose up --build