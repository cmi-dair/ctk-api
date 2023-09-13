"""This module contains fixtures and configurations for testing the endpoints of
the CTK API.
"""

import enum

import pytest
from fastapi import testclient

from ctk_api import main

API_ROOT = "/api/v1"


class Endpoints(str, enum.Enum):
    """Enum class that represents the available endpoints for the API."""

    ANONYMIZE_REPORT = f"{API_ROOT}/summarization/anonymize_report"
    SUMMARIZE_REPORT = f"{API_ROOT}/summarization/summarize_report"


@pytest.fixture
def endpoints() -> type[Endpoints]:
    """Returns the Endpoints enum class."""
    return Endpoints


@pytest.fixture
def client() -> testclient.TestClient:
    """Returns a test client for the API."""
    return testclient.TestClient(main.app)
