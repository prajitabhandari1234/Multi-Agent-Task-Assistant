# Import logging first
import logging


# Configure logging before importing application modules
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    force=True
)


# Import FastAPI after logging configuration
from fastapi import FastAPI

# Import normal task routes
from api.routes import router as task_router

# Import AI agent routes
from api.agent_routes import router as agent_router

# Import multi-agent workflow routes
from api.workflow_routes import router as workflow_router


# Create a logger for this module
logger = logging.getLogger(__name__)


# Create the FastAPI application
app = FastAPI(
    title="Multi-Agent Task Assistant",
    description="COIT12204 Multi-Agent Task Assistant",
    version="2.0.0"
)


# Register normal task routes
app.include_router(task_router)

# Register AI agent routes
app.include_router(agent_router)

# Register multi-agent workflow routes
app.include_router(workflow_router)


# Log application startup
@app.on_event("startup")
def startup_event():
    logger.info(
        "Multi-Agent Task Assistant application started"
    )


# Root endpoint
@app.get("/")
def root():
    return {
        "message": "Multi-Agent Task Assistant API"
    }