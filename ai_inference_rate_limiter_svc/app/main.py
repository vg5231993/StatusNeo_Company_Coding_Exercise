import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status
from redis.exceptions import ConnectionError

from .limiter import DistributedRateLimiter
from .models import LimitCheckRequest
from .config import settings

logger = logging.getLogger(__name__)
logging.basicConfig(level=settings.LOG_LEVEL.upper())

#Global Variable to store the Rate Limitter
RATE_LIMITER: DistributedRateLimiter = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles startup (resource allocation) and shutdown."""
    global RATE_LIMITER
    logger.info("Application starting: Initializing Rate Limiter...")
    try:
        # Instantiate the limiter which will connect to Redis and load the Lua script
        RATE_LIMITER = DistributedRateLimiter()
        logger.info("Rate Limiter is ready.")
    except ConnectionError as e:
        logger.critical(f"Rate Limiter failed to initialize: {e}")
        RATE_LIMITER = None
    
    yield # Application serves requests here

app = FastAPI(
    title="AI Inference Rate Limiter Service",
    description="Protects GPU resources using a distributed Sliding Window Log",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    if RATE_LIMITER is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Redis svc failed to initialize.")
    
    try:
        RATE_LIMITER.redis_client.ping()
        return {"status": "ok", "dependencies": "redis_ok"}
    except ConnectionError:
        logger.error("Health check failed Redis svc is unreachable.")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Redis connection failed.")


@app.post("/api/v1/inference/allow")
async def check_rate_limit(request: LimitCheckRequest):
    if RATE_LIMITER is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Rate Limiter svc is unavailable.")

    limit = request.max_limit if request.max_limit is not None else settings.DEFAULT_MAX_REQUESTS
    
    if RATE_LIMITER.allow(request.user_id, request.model_id, max_limit=limit):
        logger.info(f"Allowed: {request.user_id}/{request.model_id}")
        return {"status": "ok", "message": "Request allowed to proceed to inference."}
    else:
        logger.warning(f"Rejected: {request.user_id}/{request.model_id}. Limit ({limit}) exceeded.")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS, 
            detail=f"Rate limit exceeded: {limit} requests per {settings.WINDOW_DURATION_SECONDS // 60} minutes for {request.model_id}."
        )