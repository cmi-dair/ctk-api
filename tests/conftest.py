"""Configurations for all tests."""
import tempfile
from typing import Generator

import docx
import pytest


@pytest.fixture
def document() -> Generator[tempfile._TemporaryFileWrapper, None, None]:
    """Generates a new Word document with a title and a paragraph, and returns
    the path to the saved file.

    Returns:
        Generator[tempfile._TemporaryFileWrapper, None, None]: The saved file.
    """
    doc = docx.Document()
    doc.add_heading("Title", 0)
    doc.add_heading("clinical summary and impression", 1)
    doc.add_paragraph("Name: Lea Avatar")
    doc.add_paragraph("He she herself man")

    with tempfile.NamedTemporaryFile(suffix=".docx") as temp_file:
        doc.save(temp_file.name)
        yield temp_file
