""" Unit tests for the middleware module. """
import logging

import fastapi
import pytest
from fastapi import testclient

from ctk_api.core import middleware

app = fastapi.FastAPI()
app.add_middleware(middleware_class=middleware.RequestLoggerMiddleware)


@app.get("/test/")
def example_route() -> dict[str, str]:
    """
    Test function for the route.

    Returns:
        dict: A dictionary containing a message indicating that the test route was hit.
    """
    return {"message": "Test route"}


client = testclient.TestClient(app)


def test_log_middleware(caplog: pytest.LogCaptureFixture) -> None:
    """Test the log middleware by checking if the log messages are correctly generated."""
    with caplog.at_level(logging.INFO):
        response = client.get("/test/")

    assert response.status_code == 200
    assert "Starting request" in caplog.text
    assert "Finished request" in caplog.text
