"""Controller for the diagnoses endpoint."""
import json
import logging
from typing import Union

from ctk_api.core import config

settings = config.get_settings()

LOGGER_NAME = settings.LOGGER_NAME
DIAGNOSES_FILE = settings.DIAGNOSES_FILE
logger = logging.getLogger(LOGGER_NAME)

RecursiveDict = dict[str, Union[str, "RecursiveDict"]]


def get_diagnoses() -> list[RecursiveDict]:
    """Gets the dictionary of diagnoses.

    Returns:
        The dictionary of diagnoses.
    """
    logger.debug("Getting diagnoses.")
    with open(DIAGNOSES_FILE, "r", encoding="utf-8") as file:
        diagnoses = json.load(file)

    return diagnoses
