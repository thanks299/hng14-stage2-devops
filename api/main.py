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

# Global variable for Redis connection
redis_client = None


def get_redis_connection():
    """Create Redis connection with retry logic"""
    global redis_client
    if redis_client is not None:
        try:
            redis_client.ping()
            return redis_client
        except redis.ConnectionError:
            redis_client = None
    
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
            redis_client = r
            return redis_client
        except redis.ConnectionError:
            retries -= 1
            logger.warning(f"Redis connection failed, retries left: {retries}")
            time.sleep(2)
    raise redis.ConnectionError("Could not connect to Redis")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events"""
    # Startup
    logger.info("API Service Starting...")
    # Initialize Redis connection
    try:
        get_redis_connection()
        logger.info("Redis connection established")
    except Exception as e:
        logger.error(f"Failed to connect to Redis at startup: {e}")
    yield
    # Shutdown
    logger.info("API Service Shutting down...")


app = FastAPI(lifespan=lifespan)


@app.get("/health", responses={503: {"description": "Redis connection failed"}})
async def health_check():
    """Health check endpoint for container orchestration"""
    try:
        r = get_redis_connection()
        r.ping()
        return {"status": "healthy", "redis": "connected"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Redis connection failed")


@app.post("/jobs", responses={500: {"description": "Failed to create job"}})
async def create_job():
    """Create a new job"""
    try:
        r = get_redis_connection()
        job_id = str(uuid.uuid4())
        r.lpush("job", job_id)
        r.hset(f"job:{job_id}", "status", "queued")
        logger.info(f"Job created: {job_id}")
        return {"job_id": job_id}
    except Exception as e:
        logger.error(f"Failed to create job: {e}")
        raise HTTPException(status_code=500, detail="Failed to create job")


@app.get("/jobs/{job_id}", responses={404: {"description": "Job not found"}, 500: {"description": "Failed to retrieve job status"}})
async def get_job(job_id: str):
    """Get job status by ID"""
    try:
        r = get_redis_connection()
        status = r.hget(f"job:{job_id}", "status")
        if not status:
            raise HTTPException(status_code=404, detail="Job not found")
        return {"job_id": job_id, "status": status}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve job status")
