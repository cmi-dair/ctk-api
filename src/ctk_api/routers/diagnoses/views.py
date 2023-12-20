"""View definitions for the diagnoses router."""
import logging
from typing import Any

import fastapi
from fastapi import status

from ctk_api.core import config
from ctk_api.microservices import elastic
from ctk_api.routers.diagnoses import controller, schemas

settings = config.get_settings()
LOGGER_NAME = settings.LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)

router = fastapi.APIRouter(prefix="/diagnoses", tags=["diagnoses"])


@router.get(
    "",
    description="Gets the dictionary of diagnoses.",
    status_code=status.HTTP_200_OK,
)
async def get_diagnoses(
    elastic_client: elastic.ElasticClient = fastapi.Depends(elastic.ElasticClient),
) -> list[schemas.DiagnosisNode]:
    """Gets the dictionary of diagnoses.

    Returns:
        The dictionary of diagnoses.
    """
    logger.debug("Getting diagnoses.")
    diagnoses = await controller.get_diagnoses(elastic_client)
    logger.debug("Got diagnoses.")
    return diagnoses


@router.post(
    "",
    summary="Creates a new diagnosis root node.",
    description="Creates a new diagnosis root node.",
    status_code=status.HTTP_201_CREATED,
)
async def create_diagnosis_root(
    diagnosis: schemas.DiagnosisNode,
    elastic_client: elastic.ElasticClient = fastapi.Depends(elastic.ElasticClient),
) -> dict[str, Any]:
    """Creates a new diagnosis root node.

    Args:
        diagnosis: The diagnosis to create.
        elastic_client: The Elasticsearch client.

    Returns:
        The created diagnosis.
    """
    logger.debug("Creating diagnosis root.")
    response = await controller.create_diagnosis_root(diagnosis, elastic_client)
    logger.debug("Created diagnosis root.")
    return response


@router.post(
    "/{diagnosis_id}",
    summary="Creates a new node in the diagnosis tree.",
    description="""Creates a new diagnosis node. Provide the identifier of the parent
    diagnosis node to create a child node, or no identifier for a root node.""",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "description": "The parent diagnosis node was not found.",
        },
    },
)
async def create_diagnosis_node(
    diagnosis: schemas.DiagnosisNode,
    diagnosis_id: str = fastapi.Path(
        description="""The identifier of the parent diagnosis node.
            Leave blank to create a root node.""",
    ),
    elastic_client: elastic.ElasticClient = fastapi.Depends(elastic.ElasticClient),
) -> dict[str, Any]:
    """Creates a new diagnosis.

    Args:
        diagnosis: The diagnosis to create.
        diagnosis_id: The identifier of the parent diagnosis node. If
            None, the diagnosis is created as a root node.
        elastic_client: The Elasticsearch client.

    Returns:
        The created diagnosis.
    """
    logger.debug("Creating diagnosis.")
    response = await controller.create_diagnosis_node(
        diagnosis,
        elastic_client,
        diagnosis_id,
    )
    logger.debug("Created diagnosis.")
    return response


@router.patch(
    "/{diagnosis_id}",
    summary="Updates the text of a diagnosis.",
    description="Updates the text of a diagnosis selected by its identifier.",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "description": "The diagnosis was not found.",
        },
    },
)
async def patch_diagnosis_node(
    update_schema: schemas.UpdateDiagnosisNode,
    diagnosis_id: str = fastapi.Path(
        description="The identifier of the diagnosis to update.",
    ),
    elastic_client: elastic.ElasticClient = fastapi.Depends(elastic.ElasticClient),
) -> dict[str, Any]:
    """Updates a diagnosis.

    Args:
        update_schema: The new text of the diagnosis.
        diagnosis_id: The ID of the diagnosis to update.
        elastic_client: The Elasticsearch client.

    Returns:
        The updated diagnosis.
    """
    logger.debug("Updating diagnosis.")
    response = await controller.patch_diagnosis_node(
        diagnosis_id,
        update_schema,
        elastic_client,
    )
    logger.debug("Updated diagnosis.")
    return response


@router.delete(
    "/{diagnosis_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deletes a diagnosis.",
    description="Deletes a diagnosis selected by its identifier.",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "description": "The diagnosis was not found.",
        },
    },
)
async def delete_diagnosis_node(
    diagnosis_id: str,
    elastic_client: elastic.ElasticClient = fastapi.Depends(elastic.ElasticClient),
) -> None:
    """Deletes a diagnosis.

    Args:
        diagnosis_id: The ID of the diagnosis to delete.
        elastic_client: The Elasticsearch client.
    """
    logger.debug("Deleting diagnosis.")
    await controller.delete_diagnosis_node(diagnosis_id, elastic_client)
    logger.debug("Deleted diagnosis.")
