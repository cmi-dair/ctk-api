"""Controller for the diagnoses endpoint."""
import logging
from typing import Any

from ctk_api.core import config
from ctk_api.microservices import elastic
from ctk_api.routers.diagnoses import schemas

settings = config.get_settings()

LOGGER_NAME = settings.LOGGER_NAME
DIAGNOSES_FILE = settings.DIAGNOSES_FILE
ELASTIC_DIAGNOSES_INDEX = settings.ELASTIC_DIAGNOSES_INDEX
logger = logging.getLogger(LOGGER_NAME)


async def get_diagnoses(
    elastic_client: elastic.ElasticClient,
) -> list[schemas.DiagnosisNode]:
    """Gets the dictionary of diagnoses.

    Returns:
        The dictionary of diagnoses.
    """
    logger.debug("Getting diagnoses.")
    docs = await elastic_client.search(
        ELASTIC_DIAGNOSES_INDEX,
        {"match_all": {}},
    )
    return [schemas.DiagnosisNode(**doc["_source"]) for doc in docs["hits"]["hits"]]


async def create_diagnosis_root(
    diagnosis: schemas.DiagnosisNode,
    elastic_client: elastic.ElasticClient,
) -> dict[str, Any]:
    """Creates a new diagnosis at the root level.

    Args:
        diagnosis: The diagnosis to create.
        elastic_client: The Elasticsearch client.

    Returns:
        The created diagnosis.
    """
    logger.debug("Creating diagnosis.")
    elastic_response = await elastic_client.create(
        ELASTIC_DIAGNOSES_INDEX,
        diagnosis.model_dump(),
    )
    return dict(elastic_response.body)


async def create_diagnosis_node(
    diagnosis: schemas.DiagnosisNode,
    elastic_client: elastic.ElasticClient,
    identifier: str,
) -> dict[str, Any]:
    """Creates a new diagnosis node.

    Args:
        diagnosis: The diagnosis to create.
        elastic_client: The Elasticsearch client.
        identifier: The identifier of the parent diagnosis node.

    Returns:
        The created diagnosis.
    """
    logger.debug("Creating diagnosis.")
    doc = await elastic_client.read(ELASTIC_DIAGNOSES_INDEX, identifier)
    new_doc = doc["_source"]
    new_doc["children"].append(diagnosis.model_dump())
    elastic_response = await elastic_client.update(
        ELASTIC_DIAGNOSES_INDEX,
        doc["_id"],
        new_doc,
    )
    return dict(elastic_response.body)


async def patch_diagnosis_node(
    identifier: str,
    updated_node: schemas.UpdateDiagnosisNode,
    elastic_client: elastic.ElasticClient,
) -> dict[str, Any]:
    """Patches a diagnosis.

    Args:
        identifier: The identifier of the diagnosis to patch.
        updated_node: The updated diagnosis.
        elastic_client: The Elasticsearch client.

    Returns:
        The patched diagnosis.
    """
    logger.debug("Patching diagnosis.")
    doc = await elastic_client.read(ELASTIC_DIAGNOSES_INDEX, identifier)
    new_doc = doc["_source"]
    new_doc.update({"text": updated_node.text})
    elastic_response = await elastic_client.update(
        ELASTIC_DIAGNOSES_INDEX,
        doc["_id"],
        new_doc,
    )
    return dict(elastic_response.body)


async def delete_diagnosis_node(
    identifier: str,
    elastic_client: elastic.ElasticClient,
) -> None:
    """Deletes a diagnosis.

    Args:
        identifier: The identifier of the diagnosis to delete.
        elastic_client: The Elasticsearch client.
    """
    logger.debug("Deleting diagnosis.")
    await elastic_client.delete(ELASTIC_DIAGNOSES_INDEX, identifier)
