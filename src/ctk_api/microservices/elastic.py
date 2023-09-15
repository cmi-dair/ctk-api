""" A client for interacting with Elasticsearch.

This module contains a client for interacting with Elasticsearch. It also
contains a getter function that is intended to be used as a dependency in
FastAPI.
"""
import logging
import uuid
from datetime import datetime
from typing import Any

import elastic_transport
import elasticsearch
import fastapi
import pydantic
from fastapi import status

from ctk_api.core import config

settings = config.get_settings()
ELASTIC_URL = settings.ELASTIC_URL
ELASTIC_PASSWORD = settings.ELASTIC_PASSWORD
LOGGER_NAME = settings.LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)


class ElasticClient:
    """A client for interacting with Elasticsearch.

    Attributes:
        url: The URL of the Elasticsearch instance.
        password: The password to use when connecting to the Elasticsearch instance.
        client: The Elasticsearch client instance.
    """

    def __init__(
        self,
        url: pydantic.AnyHttpUrl | str = ELASTIC_URL,
        password: pydantic.SecretStr = ELASTIC_PASSWORD,
    ):
        self.url = str(url)
        self.client = elasticsearch.Elasticsearch(
            self.url,
            basic_auth=(
                "elastic",
                password.get_secret_value(),  # pylint: disable=no-member
            ),
        )

    def create(
        self, index: str, document: dict[str, Any]
    ) -> elastic_transport.ObjectApiResponse:
        """Creates a document in the specified index.

        Args:
            index: The index to create the document in.
            body: The document to create.

        Returns:
            The response from Elasticsearch.

        Notes:
            The document will be timestamped with the current time.
            As such, the document should not already have a `created_at` or
            `modified_at` field.
        """
        logger.debug("Creating document in Elasticsearch.")
        if "created_at" in document or "modified_at" in document:
            raise fastapi.HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Document should not already have a 'created_at' or 'modified_at' field.",
            )
        now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        document["created_at"] = now
        document["mofidied_at"] = now
        document_id = uuid.uuid4().hex
        return self.client.create(id=document_id, index=index, document=document)

    def read(self, index: str, document_id: str) -> elastic_transport.ObjectApiResponse:
        """Reads a document from the specified index.

        Args:
            index: The index to read the document from.
            document_id: The ID of the document to read.

        Returns:
            The response from Elasticsearch.
        """
        logger.debug("Reading document from Elasticsearch.")
        return self.client.get(index=index, id=document_id)

    def update(
        self, index: str, document_id: str, document: dict[str, Any]
    ) -> elastic_transport.ObjectApiResponse:
        """Updates a document in the specified index.

        Args:
            index: The index to update the document in.
            document_id: The ID of the document to update.
            body: The document to update.

        Returns:
            The response from Elasticsearch.
        """
        logger.debug("Updating document in Elasticsearch.")
        if "created_at" in document:
            raise fastapi.HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Document should not already have a 'created_at' field.",
            )
        document["modified_at"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        return self.client.update(index=index, id=document_id, doc=document)

    def delete(self, index: str, document_id: str) -> None:
        """Deletes a document from the specified index.

        Args:
            index: The index to delete the document from.
            document_id: The ID of the document to delete.
        """
        logger.debug("Deleting document from Elasticsearch.")
        self.client.delete(index=index, id=document_id)

    def search(
        self, index: str, query: dict[str, Any]
    ) -> elastic_transport.ObjectApiResponse:
        """Searches the specified index.

        Args:
            index: The index to search.
            query: The query to search with.

        Returns:
            The response from Elasticsearch.
        """
        logger.debug("Searching Elasticsearch.")
        return self.client.search(index=index, query=query)

    def close(self) -> None:
        """Closes the Elasticsearch client."""
        logger.debug("Closing Elasticsearch client.")
        self.client.close()


def get_elastic_client() -> ElasticClient:
    """Creates an instance of the Elasticsearch client.

    Returns:
        An instance of the Elasticsearch client.

    Notes:
        This function is used as a dependency in FastAPI.
    """
    logger.info("Creating Elasticsearch client.")
    return ElasticClient()
