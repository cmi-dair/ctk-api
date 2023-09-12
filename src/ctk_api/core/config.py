"""Settings for the API."""
import functools
import logging

import pydantic
import pydantic_settings


class Settings(pydantic_settings.BaseSettings):  # type: ignore[valid-type, misc]
    """Settings for the API."""

    LOGGER_NAME: str = pydantic.Field("Clinician Toolkit API")

    ENVIRONMENT: str = pydantic.Field(
        "development", json_schema_extra={"env": "CTK_API_ENVIRONMENT"}
    )


@functools.lru_cache()
def get_settings() -> Settings:
    """Cached fetcher for the API settings.

    Returns:
        The settings for the API.
    """

    return Settings()  # type: ignore[call-arg]


def initialize_logger() -> None:
    """Initializes the logger for the API."""
    settings = get_settings()
    logger = logging.getLogger(settings.LOGGER_NAME)
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)s - %(funcName)s - %(message)s"
    )

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)
