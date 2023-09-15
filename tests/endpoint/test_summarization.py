"""Endpoint tests for the summarization router."""
# pylint: disable=redefined-outer-name
import tempfile
from typing import Any

import pytest
import pytest_mock
from fastapi import status, testclient

from . import conftest


class MockElasticResponse:
    def __init__(self):
        self._id = "1"


@pytest.fixture
def mock_openai_response() -> dict[str, Any]:
    """Returns a mock OpenAI response."""
    return {
        "id": "chatcmpl-123",
        "object": "chat.completion",
        "created": 1677652288,
        "model": "gpt-3.5-turbo-0613",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "\n\nHello there, how may I assist you today?",
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 9, "completion_tokens": 12, "total_tokens": 21},
    }


def test_anonymization_endpoint(
    client: testclient.TestClient,
    endpoints: conftest.Endpoints,
    document: tempfile._TemporaryFileWrapper,
) -> None:
    """Tests the anonymization endpoint."""
    form_data = {"docx_file": document}
    expected = "\n".join(
        [
            "clinical summary and impression",
            "Name: [FIRST_NAME] [LAST_NAME]",
            "He/She he/she himself/herself man/woman",
        ]
    )

    response = client.post(endpoints.ANONYMIZE_REPORT, files=form_data)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected


def test_summarization_endpoint(
    mocker: pytest_mock.MockFixture,
    mock_openai_response: dict[str, Any],
    client: testclient.TestClient,
    endpoints: conftest.Endpoints,
) -> None:
    """Tests the summarization endpoint."""
    mocker.patch(
        "ctk_api.microservices.elastic.ElasticClient.search",
        return_value={"hits": {"total": {"value": 0}}},
    )
    mocker.patch(
        "ctk_api.microservices.elastic.ElasticClient.create",
        return_value=MockElasticResponse(),
    )
    mocker.patch(
        "ctk_api.microservices.elastic.ElasticClient.update", return_value=None
    )
    mocker.patch("openai.ChatCompletion.create", return_value=mock_openai_response)
    expected = mock_openai_response["choices"][0]["message"]["content"]

    response = client.post(endpoints.SUMMARIZE_REPORT, json={"text": "Hello there."})

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected
