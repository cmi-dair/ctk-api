"""View definitions for the summarization router."""
import logging

import fastapi
from fastapi import responses

from ctk_api.core import config
from ctk_api.microservices import elastic
from ctk_api.routers.summarization import controller, schemas

settings = config.get_settings()
LOGGER_NAME = settings.LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)

router = fastapi.APIRouter(prefix="/summarization", tags=["summarization"])


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
    logger.debug("Anonymizing report.")
    response = controller.anonymize_report(docx_file)
    logger.debug("Anonymized report.")
    return response


@router.post("/summarize_report")
async def summarize_report(
    report: schemas.Report,
    elastic_client: elastic.ElasticClient = fastapi.Depends(elastic.ElasticClient),
    background_tasks: fastapi.BackgroundTasks = fastapi.BackgroundTasks(),
) -> responses.FileResponse:
    """POST endpoint for summarizing a clinical report.

    Args:
        report: The report to summarize.
        elastic_client: The Elasticsearch client.
        background_tasks: The background tasks to run.

    Returns:
        str: The summarized file.
    """
    logger.debug("Summarizing report.")
    response = await controller.summarize_report(
        report,
        elastic_client,
        background_tasks,
    )
    logger.debug("Summarized report.")
    return response
