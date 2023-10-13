"""View definitions for the diagnoses router."""
import logging
from typing import Any

import fastapi

from ctk_api.core import config
from ctk_api.routers.diagnoses import controller

settings = config.get_settings()
LOGGER_NAME = settings.LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)

router = fastapi.APIRouter(prefix="/diagnoses", tags=["diagnoses"])


@router.get("")
async def get_diagnoses() -> list[dict[str, Any]]:
    """Gets the dictionary of diagnoses.

    Returns:
        The dictionary of diagnoses.
    """
    logger.debug("Getting diagnoses.")
    return controller.get_diagnoses()
