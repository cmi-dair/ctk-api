"""Main entrypoint for the API."""
import logging

import fastapi
from fastapi.middleware import cors

from ctk_api.core import config
from ctk_api.routers.summarization import views as summarization_views

settings = config.get_settings()
LOGGER_NAME = settings.LOGGER_NAME

config.initialize_logger()
logger = logging.getLogger(LOGGER_NAME)

logger.info("Initializing API routes.")
api_router = fastapi.APIRouter(prefix="/api/v1")
api_router.include_router(summarization_views.router)

logger.info("Starting API.")
app = fastapi.FastAPI()
app.include_router(api_router)

logger.info("Adding CORS middleware.")
app.add_middleware(
    cors.CORSMiddleware,
    allow_origins="*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
