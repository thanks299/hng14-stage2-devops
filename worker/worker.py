import redis
import time
import os
import signal
import logging
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

# Configure logging
logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Environment variables
REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)
WORKER_POLL_INTERVAL = int(os.getenv('WORKER_POLL_INTERVAL', 5))
HEALTH_PORT = int(os.getenv('HEALTH_PORT', 8080))

running = True

def get_redis_connection():
    """Create Redis connection with retry logic"""
    retries = 5
    while retries > 0 and running:
        try:
            r = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                db=REDIS_DB,
                password=REDIS_PASSWORD,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_keepalive=True
            )
            r.ping()
            logger.info(f"Connected to Redis at {REDIS_HOST}:{REDIS_PORT}")
            return r
        except redis.ConnectionError as e:
            retries -= 1
            logger.warning(f"Redis connection failed ({retries} retries left): {e}")
            time.sleep(3)
    logger.error("Could not connect to Redis after retries")
    return None

def process_job(job_id):
    """Process a single job"""
    try:
        logger.info(f"Processing job {job_id}")
        time.sleep(2)  # simulate work
        r = get_redis_connection()
        if r:
            r.hset(f"job:{job_id}", "status", "completed")
            logger.info(f"Completed job {job_id}")
        else:
            logger.error(f"No Redis connection for job {job_id}")
    except Exception as e:
        logger.error(f"Error processing job {job_id}: {e}")
        # Mark as failed if needed
        r = get_redis_connection()
        if r:
            r.hset(f"job:{job_id}", "status", "failed")

class HealthHandler(BaseHTTPRequestHandler):
    """Health check endpoint for the worker"""
    
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status": "healthy", "service": "worker"}')
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        # Suppress health check logs
        pass

def start_health_server():
    """Start a simple HTTP server for health checks"""
    server = HTTPServer(('0.0.0.0', HEALTH_PORT), HealthHandler)
    logger.info(f"Health server running on port {HEALTH_PORT}")
    server.serve_forever()

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    global running
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    running = False
    # Give time for current job to complete
    time.sleep(2)
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

# Start health check server in background
health_thread = threading.Thread(target=start_health_server, daemon=True)
health_thread.start()

# Main worker loop
logger.info("Worker started, waiting for jobs...")
redis_client = get_redis_connection()

while running:
    try:
        if not redis_client:
            logger.warning("Reconnecting to Redis...")
            redis_client = get_redis_connection()
            if not redis_client:
                time.sleep(5)
                continue
        
        # Use brpop with timeout to allow checking running flag
        result = redis_client.brpop("job", timeout=WORKER_POLL_INTERVAL)
        
        if result and running:
            _, job_id = result
            logger.info(f"Picked up job: {job_id}")
            process_job(job_id)
            
    except redis.ConnectionError as e:
        logger.error(f"Redis connection error: {e}")
        redis_client = None
        time.sleep(5)
    except Exception as e:
        logger.error(f"Unexpected error in worker loop: {e}")
        time.sleep(1)

logger.info("Worker stopped")
