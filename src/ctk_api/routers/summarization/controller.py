"""The controller for the summarization router."""
import logging

import docx
import fastapi

from ctk_api.core import config
from ctk_api.routers.summarization import anonymizer

settings = config.get_settings()
LOGGER_NAME = settings.LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)


def anonymize_report(docx_file: fastapi.UploadFile) -> str:
    """Anonymizes a clinical report. This function is specific
    to the file format used by HBN's clinical reports and will not work for
    other file formats.

    Args:
        docx_file: The report's docx file to anonymize.

    Returns:
        str: The anonymized file.
    """
    logger.info("Anonymizing report.")
    document = docx.Document(docx_file.file)
    first_name, last_name = anonymizer.get_patient_name(document)
    paragraphs = anonymizer.get_diagnostic_paragraphs(document)
    anonymized_paragraphs = anonymizer.anonymize_paragraphs(
        paragraphs, first_name, last_name
    )
    anonymized_text = "\n".join([p.text for p in anonymized_paragraphs])
    return anonymized_text
