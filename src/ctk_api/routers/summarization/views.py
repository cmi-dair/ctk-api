"""View definitions for the summarization router."""
import logging

import fastapi

from ctk_api.core import config
from ctk_api.routers.summarization import controller

settings = config.get_settings()
LOGGER_NAME = settings.LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)

router = fastapi.APIRouter(prefix="/summarization", tags=["Summarization"])


@router.post("/anonymize_report")
async def anonymize_report(
    docx_file: fastapi.UploadFile = fastapi.File(...),
) -> str:
    """POST endpoint for anonymizing a clinical report.

    Args:
        docx_file: The docx file to anonymize.

    Returns:
        str: The anonymized file.
    """
    logger.info("Endpoint: /summarization/anonymize_report")
    return controller.anonymize_report(docx_file)
