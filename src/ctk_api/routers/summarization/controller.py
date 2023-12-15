"""The controller for the summarization router."""
import functools
import json
import logging
import pathlib
import tempfile
from typing import Any, Literal

import docx
import fastapi
import openai
import pypandoc
import yaml
from fastapi import responses, status

from ctk_api.core import config
from ctk_api.microservices import elastic
from ctk_api.routers.summarization import anonymizer, schemas

settings = config.get_settings()
LOGGER_NAME = settings.LOGGER_NAME
OPENAI_API_KEY = settings.OPENAI_API_KEY
OPENAI_CHAT_COMPLETION_MODEL = settings.OPENAI_CHAT_COMPLETION_MODEL
OPENAI_CHAT_COMPLETION_PROMPT_FILE = settings.OPENAI_CHAT_COMPLETION_PROMPT_FILE

logger = logging.getLogger(LOGGER_NAME)


def anonymize_report(docx_file: fastapi.UploadFile) -> str:
    """Anonymizes a clinical report.

    Args:
        docx_file: The report's docx file to anonymize.

    Returns:
        str: The anonymized file.

    Notes:
        This function is specific to the file format used by HBN's clinical
        reports and will not work for other file formats.
    """
    logger.info("Anonymizing report.")
    document = docx.Document(docx_file.file)
    first_name, last_name = anonymizer.get_patient_name(document)
    paragraphs = anonymizer.get_diagnostic_paragraphs(document)
    anonymized_paragraphs = anonymizer.anonymize_paragraphs(
        paragraphs,
        first_name,
        last_name,
    )
    return "\n".join([p.text for p in anonymized_paragraphs])


def summarize_report(
    report: schemas.Report,
    elastic_client: elastic.ElasticClient,
    background_tasks: fastapi.BackgroundTasks,
) -> fastapi.Response:
    """Summarizes a clinical report.

    Clinical reports are sent to OpenAI. Both the report and the summary are
    stored in Elasticsearch for caching and auditing.

    Args:
        report: The report to summarize.
        elastic_client: The Elasticsearch client.
        background_tasks: The background tasks to run.

    Returns:
        str: The summarized file.
    """
    logger.info("Checking if request was made before.")
    existing_document = _check_for_existing_document(report, elastic_client)

    if existing_document and "summary" in existing_document:
        return fastapi.Response(
            json.dumps(existing_document["summary"]),
            status_code=status.HTTP_200_OK,
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
    system_prompt = get_prompt("system", "summarize_clinical_report")

    client = openai.OpenAI(api_key=OPENAI_API_KEY.get_secret_value())
    response = client.chat.completions.create(
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
    response_text = response.choices[0].message.content
    elastic_client.update(
        index="summarization",
        document_id=document["_id"],
        document={"summary": response_text},
    )

    logger.debug("Converting response to docx.")
    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as output_file:
        _markdown_text_to_docx_file(response_text, output_file.name)

    background_tasks.add_task(_remove_file, output_file.name)
    return responses.FileResponse(
        output_file.name,
        filename="summary.docx",
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        background=background_tasks,
        status_code=status.HTTP_201_CREATED,
    )


@functools.lru_cache
def get_prompt(category: Literal["system", "user"], name: str) -> str:
    """Gets the system prompt for the OpenAI chat completion model.

    Args:
        category: The type of prompt to get.
        name: The name of the prompt to get.

    Returns:
        str: The system prompt.
    """
    logger.debug("Getting %s prompt: %s.", category, name)
    with OPENAI_CHAT_COMPLETION_PROMPT_FILE.open("r") as file:
        prompts = yaml.safe_load(file)
    return prompts[category][name]


def _check_for_existing_document(
    report: schemas.Report,
    elastic_client: elastic.ElasticClient,
) -> dict[str, Any] | None:
    """Checks if a document already exists in Elasticsearch.

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


def _remove_file(filename: str | pathlib.Path) -> None:
    """Removes a file.

    Args:
        filename: The filename of the file to remove.
    """
    logger.debug("Removing file %s.", filename)
    pathlib.Path(filename).unlink()


def _markdown_text_to_docx_file(
    markdown_text: str,
    output_file: str | pathlib.Path,
) -> None:
    """Converts markdown text to a docx file.

    Args:
        markdown_text: The markdown text to convert.
        output_file: The output file.
    """
    with tempfile.NamedTemporaryFile(suffix=".md") as markdown_file:
        markdown_file.write(markdown_text.encode("utf-8"))
        markdown_file.seek(0)
        pypandoc.convert_file(markdown_file.name, "docx", outputfile=str(output_file))
