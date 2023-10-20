"""This module contains fixtures and configurations for testing the endpoints of
the CTK API.
"""
import enum

import pytest
from fastapi import testclient
from pytest_mock import plugin

from ctk_api import main

API_ROOT = "/api/v1"


class Endpoints(str, enum.Enum):
    """Enum class that represents the available endpoints for the API."""

    ANONYMIZE_REPORT = f"{API_ROOT}/summarization/anonymize_report"
    SUMMARIZE_REPORT = f"{API_ROOT}/summarization/summarize_report"
    DIAGNOSES = f"{API_ROOT}/diagnoses"


@pytest.fixture
def endpoints() -> type[Endpoints]:
    """Returns the Endpoints enum class."""
    return Endpoints


@pytest.fixture
def client(mocker: plugin.MockerFixture) -> testclient.TestClient:
    """Returns a test client for the API."""
    mocker.patch("ctk_api.microservices.elastic.ElasticClient._create_default_indices")
    mocker.patch("ctk_api.microservices.elastic.ElasticClient.create")
    mocker.patch("ctk_api.microservices.elastic.ElasticClient.update")
    return testclient.TestClient(main.app)
