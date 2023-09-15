import pytest

from ctk_api.microservices import elastic


@pytest.fixture
def elastic_client() -> elastic.ElasticClient:
    """Returns an instance of the Elasticsearch client."""
    return elastic.get_elastic_client()


def test_create(elastic_client: elastic.ElasticClient) -> None:
    """Tests creating a document in Elasticsearch."""
    index = "test_index"
    document = {"test_key": "test_value"}

    response = elastic_client.create(index, document)

    assert response["_index"] == index
    assert response["result"] == "created"
    assert response["_id"]
