"""
FastAPI Application Entry Point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.config import get_settings
from app.api.routes import router as api_router
from app.utils.logger import setup_logger

# Setup logging
setup_logger()
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info(f"Starting {settings.API_TITLE} v{settings.VERSION}")
    logger.info(f"Model API URL: {settings.MODEL_API_URL}")
    logger.info(f"GitLab URL: {settings.GITLAB_URL}")
    logger.info(f"Default CLI Agent: {settings.DEFAULT_CLI_AGENT}")
    logger.info(f"Work Directory: {settings.WORK_DIR}")
    
    # Verify CLI tools availability
    from app.dependencies import get_review_service_instance
    try:
        review_service = get_review_service_instance()
        health = await review_service.health_check()
        logger.info(f"Cline CLI available: {health.get('cline_available', False)}")
        logger.info(f"Qwen Code CLI available: {health.get('qwen_available', False)}")
        logger.info(f"Model API connected: {health.get('model_api_connected', False)}")
    except Exception as e:
        logger.error(f"Health check failed during startup: {str(e)}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application")


# Create FastAPI app
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.VERSION,
    description=settings.API_DESCRIPTION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": settings.API_TITLE,
        "version": settings.VERSION,
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check_simple():
    """Simple health check (without dependencies check)"""
    return {
        "status": "healthy",
        "version": settings.VERSION
    }
