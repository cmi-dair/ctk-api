"""The controller for the summarization router."""
import functools
import logging
import pathlib

import docx
import fastapi
import openai

from ctk_api.core import config
from ctk_api.routers.summarization import anonymizer, schemas

settings = config.get_settings()
LOGGER_NAME = settings.LOGGER_NAME
OPENAI_API_KEY = settings.OPENAI_API_KEY
OPENAI_CHAT_COMPLETION_MODEL = settings.OPENAI_CHAT_COMPLETION_MODEL
OPENAI_CHAT_COMPLETION_SYSTEM_PROMPT_FILE = (
    settings.OPENAI_CHAT_COMPLETION_SYSTEM_PROMPT_FILE
)

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


def summarize_report(report: schemas.Report) -> str:
    """Summarizes a clinical report.

    Args:
        report: The report to summarize.
        mock: Whether to use the mock summarizer. Useful for testing.

    Returns:
        str: The summarized file.
    """
    logger.info("Summarizing report.")

    system_prompt = get_system_prompt(OPENAI_CHAT_COMPLETION_SYSTEM_PROMPT_FILE)
    response = openai.ChatCompletion.create(
        model=OPENAI_CHAT_COMPLETION_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": report.text},
        ],
    )
    return response["choices"][0]["message"]["content"]


@functools.lru_cache()
def get_system_prompt(filename: str | pathlib.Path):
    """Gets the system prompt for the OpenAI chat completion model.

    Args:
        filename: The filename of the system prompt file.

    Returns:
        str: The system prompt.
    """
    logger.info("Getting system prompt.")
    with open(filename, "r", encoding="utf-8") as file_buffer:
        return file_buffer.read()
