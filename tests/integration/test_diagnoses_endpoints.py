"""Tests the diagnoses endpoints."""
import pytest
from fastapi import status, testclient

from ctk_api.microservices import elastic

from . import conftest


def is_hexadecimal(string: str) -> bool:
    """Returns whether the string is hexadecimal.

    Args:
        string: The string to check.

    Returns:
        Whether the string is hexadecimal.
    """
    try:
        int(string, 16)
    except ValueError:
        return False
    return True


@pytest.mark.asyncio()
async def test_get_diagnoses_endpoint(
    client: testclient.TestClient,
    elastic_client: elastic.ElasticClient,
    endpoints: conftest.Endpoints,
) -> None:
    """Tests the anonymization endpoint."""
    diagnosis = {"text": "test_text", "children": []}
    client.post(endpoints.POST_DIAGNOSIS_ROOT, json=diagnosis)
    elastic_client.client.indices.refresh()

    response = client.get(endpoints.GET_DIAGNOSES)

    assert response.status_code == status.HTTP_200_OK
    assert diagnosis in response.json()


@pytest.mark.asyncio()
async def test_create_diagnosis_root(
    endpoints: conftest.Endpoints,
    client: testclient.TestClient,
) -> None:
    """Tests creating a root diagnosis."""
    diagnosis = {"text": "test_text", "children": []}

    response = client.post(endpoints.POST_DIAGNOSIS_ROOT, json=diagnosis)

    assert response.status_code == status.HTTP_201_CREATED
    assert is_hexadecimal(response.json()["_id"])


@pytest.mark.asyncio()
async def test_create_diagnosis_node(
    endpoints: conftest.Endpoints,
    client: testclient.TestClient,
) -> None:
    """Tests creating a child diagnosis."""
    diagnosis_parent = {"text": "test_text_parent", "children": []}
    diagnosis_child = {"text": "test_text_child", "children": []}
    response_parent = client.post(endpoints.POST_DIAGNOSIS_ROOT, json=diagnosis_parent)
    response_child = client.post(
        endpoints.POST_DIAGNOSIS_NODE.format(
            diagnosis_id=response_parent.json()["_id"],
        ),
        json=diagnosis_child,
    )

    assert response_child.status_code == status.HTTP_201_CREATED
    assert is_hexadecimal(response_child.json()["_id"])


@pytest.mark.asyncio()
async def test_patch_diagnosis_node(
    endpoints: conftest.Endpoints,
    client: testclient.TestClient,
) -> None:
    """Tests patching a diagnosis."""
    diagnosis = {"text": "test_text", "children": []}
    response_parent = client.post(endpoints.POST_DIAGNOSIS_ROOT, json=diagnosis)

    response = client.patch(
        endpoints.PATCH_DIAGNOSIS.format(
            diagnosis_id=response_parent.json()["_id"],
        ),
        json={"text": "test_text_updated"},
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["_id"] == response_parent.json()["_id"]
    assert response.json()["result"] == "updated"


@pytest.mark.asyncio()
async def test_delete_diagnosis_node(
    endpoints: conftest.Endpoints,
    client: testclient.TestClient,
) -> None:
    """Tests deleting a diagnosis."""
    diagnosis = {"text": "test_text", "children": []}
    response_parent = client.post(endpoints.POST_DIAGNOSIS_ROOT, json=diagnosis)

    response = client.delete(
        endpoints.DELETE_DIAGNOSIS.format(
            diagnosis_id=response_parent.json()["_id"],
        ),
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT
