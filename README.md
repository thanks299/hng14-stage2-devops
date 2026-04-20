# HNG14 Stage 2 DevOps Task - Microservices Job Processing System

## Overview
This is a containerized job processing system consisting of three microservices:
- **Frontend** (Node.js/Express) - User interface for job submission and tracking
- **API** (Python/FastAPI) - Job creation and status endpoints
- **Worker** (Python) - Background job processor using Redis queue
- **Redis** - Message broker and state storage

## Prerequisites
- Docker Desktop 20.10+
- Docker Compose v2
- Git
- 4GB RAM available

## Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/hng14-stage2-devops.git
cd hng14-stage2-devops
2. Set up environment variables
bash
cp .env.example .env
# Edit .env if needed (defaults work for local development)
3. Build and run with Docker Compose
bash
docker-compose up --build
4. Test the application
bash
# Submit a job
curl -X POST http://localhost:3000/submit

# Check job status (replace JOB_ID)
curl http://localhost:3000/status/JOB_ID

# Health checks
curl http://localhost:3000/health
curl http://localhost:8000/health
5. Stop everything
bash
docker-compose down
# Remove volumes to reset data
docker-compose down -v
What a Successful Startup Looks Like
✅ All 4 containers running (redis, api, worker, frontend)
✅ Frontend accessible at http://localhost:3000
✅ API health endpoint returns {"status":"healthy"}
✅ Worker connects to Redis and processes jobs
✅ No errors in container logs

CI/CD Pipeline
The GitHub Actions pipeline runs automatically on push:

Lint - Python (flake8), JavaScript (eslint), Dockerfiles (hadolint)

Test - Unit tests with pytest and coverage reporting

Build - Multi-stage Docker builds for all services

Security Scan - Trivy vulnerability scanning (fails on CRITICAL)

Integration Test - End-to-end job submission and completion test

Deploy - Rolling update (main branch only)

Architecture
texts
                    ┌─────────────┐
                    │   Browser   │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  Frontend   │
                    │   :3000     │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │     API     │
                    │   :8000     │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │    Redis    │
                    │   :6379     │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │   Worker    │
                    └─────────────┘
Troubleshooting
Redis connection errors
bash
# Check Redis is healthy
docker-compose ps
docker logs job-queue-redis
Worker not processing jobs
bash
# Check worker logs
docker logs job-queue-worker
# Verify Redis queue
docker exec job-queue-redis redis-cli LRANGE job 0 -1
Port conflicts
Change ports in docker-compose.yml or .env file

License
This project is for HNG14 DevOps Stage 2 assessment.

Author
[Your Name]
EOF

text

## Step 12: Push to GitHub

Now push everything to your fork:

```bash
# Add all changes
git add .

# Commit with meaningful message
git commit -m "Complete containerization and CI/CD pipeline setup

- Fixed all bugs in API, Frontend, and Worker services
- Added health check endpoints
- Implemented environment variable configuration
- Created production Dockerfiles with multi-stage builds
- Added docker-compose with health checks and resource limits
- Implemented GitHub Actions CI/CD pipeline
- Added unit tests with pytest
- Added Trivy security scanning
- Created comprehensive documentation"

# Push to your fork
git push origin main