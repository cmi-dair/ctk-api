""" Integration tests for the Elasticsearch client. """
# mypy: disable-error-code="attr-defined"
# attr-defined is disabled because elastic_client is not recognized as
# a TestClass property.
from ctk_api.microservices import elastic

TEST_INDEX = "test_index"


class TestElastic:
    @classmethod
    def setup_class(cls) -> None:
        cls.elastic_client = elastic.get_elastic_client()

    def setup_method(self) -> None:
        self.elastic_client.client.options(ignore_status=[400, 404]).indices.delete(
            index=TEST_INDEX
        )

    @property
    def document(self) -> dict[str, str]:
        """Returns the document to use for the test."""
        return {"test_key": "test_value"}

    def test_create(self) -> None:
        """Tests creating a document in Elasticsearch."""
        response = self.elastic_client.create(TEST_INDEX, self.document)

        assert response["_index"] == TEST_INDEX
        assert response["result"] == "created"
        assert response["_id"]

    def test_search(self) -> None:
        """Tests searching for documents in Elasticsearch."""
        self.elastic_client.create(TEST_INDEX, self.document)
        self.elastic_client.client.indices.refresh()

        response = self.elastic_client.search(TEST_INDEX, {"match_all": {}})

        assert response["hits"]["total"]["value"] == 1
        assert (
            response["hits"]["hits"][0]["_source"]["test_key"]
            == self.document["test_key"]
        )

    def test_read(self) -> None:
        """Tests reading a document from Elasticsearch."""
        document_id = self.elastic_client.create(TEST_INDEX, self.document)["_id"]
        self.elastic_client.client.indices.refresh()

        response = self.elastic_client.read(TEST_INDEX, document_id)

        assert response["_id"] == document_id
        assert response["_source"]["test_key"] == self.document["test_key"]

    def test_update(self) -> None:
        """Tests updating a document in Elasticsearch."""
        document_id = self.elastic_client.create(TEST_INDEX, self.document)["_id"]
        self.elastic_client.client.indices.refresh()

        update_response = self.elastic_client.update(
            TEST_INDEX, document_id, {"test_key": "updated_value"}
        )
        read_response = self.elastic_client.read(TEST_INDEX, document_id)

        assert update_response["_id"] == document_id
        assert read_response["_source"]["test_key"] == "updated_value"

    def test_delete(self) -> None:
        """Tests deleting a document from Elasticsearch."""
        document_id = self.elastic_client.create(TEST_INDEX, self.document)["_id"]
        self.elastic_client.client.indices.refresh()

        self.elastic_client.delete(TEST_INDEX, document_id)
        self.elastic_client.client.indices.refresh()
        response = self.elastic_client.search(TEST_INDEX, {"match_all": {}})

        assert response["hits"]["total"]["value"] == 0
