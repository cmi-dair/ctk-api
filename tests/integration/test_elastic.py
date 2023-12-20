"""Integration tests for the Elasticsearch client."""
# mypy: disable-error-code="attr-defined"
# attr-defined is disabled because elastic_client is not recognized as
# a TestClass property.
# pylint: disable=redefined-outer-name
import fastapi
import pytest
from fastapi import status

from ctk_api.microservices import elastic

TEST_INDEX = "test_index"


@pytest.fixture()
def es_document() -> dict[str, str]:
    """Returns a test document.

    Notes:
        This is scoped to functions because something odd is happening
        when this runs on Github Actions, where it gets modified in place.
    """
    return {"test_key": "test_value"}


class TestElastic:
    """Integration tests for the ElasticSearch client."""

    @classmethod
    def setup_class(cls) -> None:
        """Set up the test class by initializing an ElasticSearch client."""
        cls.elastic_client = elastic.ElasticClient()

    def setup_method(self) -> None:
        """Setup for the tests.

        This method deletes the test index from the Elasticsearch cluster to
        ensure a clean slate for each test.
        """
        self.elastic_client.client.options(ignore_status=[400, 404]).indices.delete(
            index=TEST_INDEX,
        )

    @pytest.mark.asyncio()
    async def test_create(self, es_document: dict[str, str]) -> None:
        """Tests creating a document in Elasticsearch."""
        response = await self.elastic_client.create(TEST_INDEX, es_document)

        assert response["_index"] == TEST_INDEX
        assert response["result"] == "created"
        assert response["_id"]

    @pytest.mark.asyncio()
    async def test_search(self, es_document: dict[str, str]) -> None:
        """Tests searching for documents in Elasticsearch."""
        await self.elastic_client.create(TEST_INDEX, es_document)
        self.elastic_client.client.indices.refresh()

        response = await self.elastic_client.search(TEST_INDEX, {"match_all": {}})

        assert response["hits"]["total"]["value"] == 1
        assert (
            response["hits"]["hits"][0]["_source"]["test_key"]
            == es_document["test_key"]
        )

    @pytest.mark.asyncio()
    async def test_read(self, es_document: dict[str, str]) -> None:
        """Tests reading a document from Elasticsearch."""
        document = await self.elastic_client.create(TEST_INDEX, es_document)
        self.elastic_client.client.indices.refresh()

        response = await self.elastic_client.read(TEST_INDEX, document["_id"])

        assert response["_id"] == document["_id"]
        assert response["_source"]["test_key"] == es_document["test_key"]

    @pytest.mark.asyncio()
    async def test_read_not_found(self) -> None:
        """Tests reading a document that doesn't exist from Elasticsearch."""
        with pytest.raises(fastapi.HTTPException) as exc_info:
            await self.elastic_client.read(TEST_INDEX, "not_found")

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio()
    async def test_update(self, es_document: dict[str, str]) -> None:
        """Tests updating a document in Elasticsearch."""
        document = await self.elastic_client.create(TEST_INDEX, es_document)
        self.elastic_client.client.indices.refresh()

        update_response = await self.elastic_client.update(
            TEST_INDEX,
            document["_id"],
            {"test_key": "updated_value"},
        )
        read_response = await self.elastic_client.read(TEST_INDEX, document["_id"])

        assert update_response["_id"] == document["_id"]
        assert read_response["_source"]["test_key"] == "updated_value"

    @pytest.mark.asyncio()
    async def test_update_not_found(self) -> None:
        """Tests updating a document that doesn't exist in Elasticsearch."""
        with pytest.raises(fastapi.HTTPException) as exc_info:
            await self.elastic_client.update(
                TEST_INDEX,
                "not_found",
                {"test_key": "updated_value"},
            )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio()
    async def test_delete(self, es_document: dict[str, str]) -> None:
        """Tests deleting a document from Elasticsearch."""
        document = await self.elastic_client.create(TEST_INDEX, es_document)
        self.elastic_client.client.indices.refresh()

        await self.elastic_client.delete(TEST_INDEX, document["_id"])
        self.elastic_client.client.indices.refresh()
        response = await self.elastic_client.search(TEST_INDEX, {"match_all": {}})

        assert response["hits"]["total"]["value"] == 0

    @pytest.mark.asyncio()
    async def test_delete_not_found(self) -> None:
        """Tests deleting a document that doesn't exist from Elasticsearch."""
        with pytest.raises(fastapi.HTTPException) as exc_info:
            await self.elastic_client.delete(TEST_INDEX, "not_found")

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
