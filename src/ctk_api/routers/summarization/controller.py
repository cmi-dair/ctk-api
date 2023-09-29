"""The controller for the summarization router."""
import functools
import json
import logging
import pathlib
from typing import Any

import docx
import fastapi
import openai
from fastapi import status

from ctk_api.core import config
from ctk_api.microservices import elastic
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


def summarize_report(
    report: schemas.Report, elastic_client: elastic.ElasticClient
) -> str:
    """Summarizes a clinical report by sending it to OpenAI. Both the
    report and the summary are stored in Elasticsearch for caching and
    auditing.

    Args:
        report: The report to summarize.
        elastic_client: The Elasticsearch client.

    Returns:
        str: The summarized file.
    """
    logger.info("Checking if request was made before.")
    existing_document = _check_for_existing_document(report, elastic_client)

    if existing_document:
        return fastapi.Response(
            json.dumps(existing_document["summary"]), status_code=status.HTTP_200_OK
        )

    logger.debug("Creating request document.")
    document = elastic_client.create(
        index="summarization",
        document={"report": report.text},
    )

    logger.debug(
        "Sending report %s to OpenAI.",
        document["_id"],
    )
    system_prompt = get_system_prompt(OPENAI_CHAT_COMPLETION_SYSTEM_PROMPT_FILE)

    response = openai.ChatCompletion.create(
        model=OPENAI_CHAT_COMPLETION_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": report.text},
        ],
    )

    logger.debug(
        "Saving response for report %s from OpenAI.",
        document["_id"],
    )
    response_text = response["choices"][0]["message"]["content"]
    elastic_client.update(
        index="summarization",
        document_id=document["_id"],
        document={"summary": response_text},
    )

    return fastapi.Response(
        json.dumps(response_text),
        status_code=status.HTTP_201_CREATED,
    )


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


def _check_for_existing_document(
    report: schemas.Report, elastic_client: elastic.ElasticClient
) -> dict[str, Any] | None:
    """Checks if a document already exists in Elasticsearch for the given
    report.

    Args:
        report: The report to check for.
        elastic_client: The Elasticsearch client.

    Returns:
        dict[str, Any] | None: The existing document if it exists, else None.
    """
    query = {"match_phrase": {"report": report.text}}
    existing_document = elastic_client.search(index="summarization", query=query)

    if existing_document["hits"]["total"]["value"] == 0:
        logger.debug("Request was not made before.")
        return None
    if existing_document["hits"]["total"]["value"] == 1:
        logger.debug("Request was made before.")
        return existing_document["hits"]["hits"][0]["_source"]

    logger.error("More than one document was found for the request.")
    raise fastapi.HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="More than one document was found for the request.",
    )
