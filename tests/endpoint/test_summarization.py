"""Endpoint tests for the summarization router."""
# pylint: disable=redefined-outer-name
import tempfile
from typing import Any

import pytest
import pytest_mock
from fastapi import status, testclient
from pytest_mock import plugin

from . import conftest


@pytest.fixture()
def mock_openai_response(mocker: plugin.MockerFixture) -> dict[str, Any]:
    """Returns a mock OpenAI response."""
    response = {
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
            },
        ],
        "usage": {"prompt_tokens": 9, "completion_tokens": 12, "total_tokens": 21},
    }
    mocker.patch("openai.ChatCompletion.create", return_value=response)
    return response


def test_anonymization_endpoint(
    client: testclient.TestClient,
    endpoints: conftest.Endpoints,
    document: tempfile._TemporaryFileWrapper,
) -> None:
    """Tests the anonymization endpoint."""
    form_data = {"docx_file": document}
    expected = (
        "clinical summary and impression\nName: [FIRST_NAME] [LAST_NAME]\n"
        "He/She he/she himself/herself man/woman"
    )

    response = client.post(endpoints.ANONYMIZE_REPORT, files=form_data)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected


def test_summarization_endpoint_new(
    mocker: plugin.MockerFixture,
    mock_openai_response: dict[str, Any],
    client: testclient.TestClient,
    endpoints: conftest.Endpoints,
) -> None:
    """Tests the summarization endpoint."""
    mocker.patch(
        "ctk_api.routers.summarization.controller._check_for_existing_document",
        return_value=None,
    )
    expected = mock_openai_response["choices"][0]["message"]["content"]

    response = client.post(endpoints.SUMMARIZE_REPORT, json={"text": "Hello there."})

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == expected


def test_summarization_endpoint_exists(
    mocker: pytest_mock.MockFixture,
    client: testclient.TestClient,
    endpoints: conftest.Endpoints,
) -> None:
    """Tests the summarization endpoint when the document already exists."""
    expected = {"summary": {"Hello there.": "Hello there."}}
    mocker.patch(
        "ctk_api.routers.summarization.controller._check_for_existing_document",
        return_value=expected,
    )

    response = client.post(endpoints.SUMMARIZE_REPORT, json={"text": "Hello there."})

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected["summary"]
