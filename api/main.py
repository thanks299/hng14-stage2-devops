from fastapi import FastAPI, HTTPException
import redis
import uuid
import os
import logging
from contextlib import asynccontextmanager
import time

# Configure logging
logging.basicConfig(level=os.getenv('LOG_LEVEL', 'INFO'))
logger = logging.getLogger(__name__)

# Environment variables with defaults
REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)

# Redis connection with retry
def get_redis_connection():
    retries = 5
    while retries > 0:
        try:
            r = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                db=REDIS_DB,
                password=REDIS_PASSWORD,
                decode_responses=True,
                socket_connect_timeout=5
            )
            r.ping()
            logger.info(f"Connected to Redis at {REDIS_HOST}:{REDIS_PORT}")
            return r
        except redis.ConnectionError as e:
            retries -= 1
            logger.warning(f"Redis connection failed, retries left: {retries}")
            time.sleep(2)
    raise Exception("Could not connect to Redis")

r = get_redis_connection()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("API Service Starting...")
    yield
    # Shutdown
    logger.info("API Service Shutting down...")

app = FastAPI(lifespan=lifespan)

@app.get("/health")
async def health_check():
    """Health check endpoint for container orchestration"""
    try:
        r.ping()
        return {"status": "healthy", "redis": "connected"}
    except redis.ConnectionError:
        raise HTTPException(status_code=503, detail="Redis connection failed")

@app.post("/jobs")
async def create_job():
    try:
        job_id = str(uuid.uuid4())
        r.lpush("job", job_id)
        r.hset(f"job:{job_id}", "status", "queued")
        logger.info(f"Job created: {job_id}")
        return {"job_id": job_id}
    except Exception as e:
        logger.error(f"Failed to create job: {e}")
        raise HTTPException(status_code=500, detail="Failed to create job")

@app.get("/jobs/{job_id}")
async def get_job(job_id: str):
    try:
        status = r.hget(f"job:{job_id}", "status")
        if not status:
            raise HTTPException(status_code=404, detail="Job not found")
        return {"job_id": job_id, "status": status}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve job status")
