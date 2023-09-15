"""View definitions for the summarization router."""
import logging

import fastapi

from ctk_api.core import config
from ctk_api.microservices import elastic
from ctk_api.routers.summarization import controller, schemas

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


@router.post("/summarize_report")
async def summarize_report(
    report: schemas.Report,
    elastic_client: elastic.ElasticClient = fastapi.Depends(elastic.ElasticClient),
) -> str:
    """POST endpoint for summarizing a clinical report.

    Args:
        report: The report to summarize.
        elastic_client: The Elasticsearch client.

    Returns:
        str: The summarized file.
    """
    logger.info("Endpoint: /summarization/summarize_report")
    return controller.summarize_report(report, elastic_client)
