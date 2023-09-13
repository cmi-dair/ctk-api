"""This module contains the anonymization logic for clinical reports."""

import logging
import re

import docx
import fastapi
from docx.text import paragraph as docx_paragraph
from fastapi import status

from ctk_api.core import config

settings = config.get_settings()
LOGGER_NAME = settings.LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)

PARAGRAPHS_OF_INTEREST = {
    "clinical summary and impression",
    "mental health assessment",
    "dsm-5 diagnostic summary",
}

PRONOUN_REPLACEMENTS = {
    ("he", "he/she"),
    ("she", "he/she"),
    ("his", "his/her"),
    ("her", "his/her"),
    ("him", "him/her"),
    ("himself", "himself/herself"),
    ("herself", "himself/herself"),
}

GENDER_REPLACEMENTS = {
    ("man", "man/woman"),
    ("woman", "man/woman"),
    ("boy", "boy/girl"),
    ("girl", "bow/girl"),
    ("son", "son/daughter"),
    ("daughter", "son/daughter"),
}


def get_patient_name(document: docx.Document) -> tuple[str, str]:
    """Extracts the patient's name from a clinical report.

    Args:
        document: The clinical report.

    Returns:
        first_name: The patient's first name.
        last_name: The patient's last name.
    """
    logger.debug("Extracting patient name.")
    for paragraph in document.paragraphs:
        if paragraph.text.startswith("Name: "):
            first_name = paragraph.text.split(" ")[1]
            last_name = " ".join(paragraph.text.split(" ")[2:])
            return first_name, last_name

    raise fastapi.HTTPException(
        status.HTTP_400_BAD_REQUEST, detail="Patient name not found."
    )


def get_diagnostic_paragraphs(
    document: docx.Document,
) -> list[docx_paragraph.Paragraph]:
    """Extracts the diagnostic paragraphs from a clinical report.

    Args:
        document: The clinical report.

    Returns:
        list: The diagnostic paragraphs.

    Notes:
        This function relies on the fact that the paragraphs of interest are the
        lowest level headings. If this changes, more complicated logic will be
        necessary.
    """
    logger.debug("Extracting diagnostic paragraphs.")
    paragraphs = []
    retain_this = False
    for paragraph in document.paragraphs:
        if paragraph.style.name.startswith("Heading"):
            sanitized_text = paragraph.text.lower().strip()
            retain_this = sanitized_text in PARAGRAPHS_OF_INTEREST
        if retain_this:
            paragraphs.append(paragraph)
    return paragraphs


def anonymize_paragraphs(
    paragraphs: list[docx_paragraph.Paragraph],
    first_name: str,
    last_name: str,
) -> list[docx_paragraph.Paragraph]:
    """Anonymizes the paragraphs of a clinical report.

    Args:
        paragraphs: The paragraphs to anonymize.
        first_name: The patient's first name.
        last_name: The patient's last name.

    Returns:
        list: The anonymized paragraphs.
    """
    logger.debug("Anonymizing paragraphs.")
    return [_anonymize_paragraph(p, first_name, last_name) for p in paragraphs]


def _anonymize_paragraph(
    paragraph: docx_paragraph.Paragraph, first_name: str, last_name: str
) -> docx_paragraph.Paragraph:
    """Anonymizes a single paragraph of a clinical report.

    Args:
        paragraph: The paragraph to anonymize.
        first_name: The patient's first name.
        last_name: The patient's last name.

    Returns:
        paragraph: The anonymized paragraph.
    """
    logger.debug("Anonymizing paragraph.")
    text = paragraph.text
    text = _find_and_replace(text, first_name, "[FIRST_NAME]")
    text = _find_and_replace(text, last_name, "[LAST_NAME]")
    for pronoun, replacement in PRONOUN_REPLACEMENTS:
        text = _find_and_replace(text, pronoun, replacement, match_case=True)
    for gender, replacement in GENDER_REPLACEMENTS:
        text = _find_and_replace(text, gender, replacement, match_case=True)

    paragraph.text = text
    return paragraph


def _find_and_replace(
    text: str, target: str, replacement: str, match_case: bool = False
) -> str:
    """Anonymizes the patient's pronouns in a paragraph.

    Args:
        text: The paragraph text, must be a complete word or words.
        target: The text to replace.
        replacement: The text to replace with. If multiple options are provided
            separated by a "/", all words after a "/" will be capitalized.
        match_case: Whether to match the case of the target.

    Returns:
        text: The anonymized paragraph text.

    """
    logger.debug("Finding and replacing.")

    def make_regex_pattern(target: str):
        return r"(?<!\/)\b" + target + r"\b(?!\/)"

    pattern = make_regex_pattern(target)
    if not match_case:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    else:
        text = re.sub(pattern, replacement, text)
        capitalized_replacements = "/".join(
            [replace.capitalize() for replace in replacement.split("/")]
        )
        pattern_capitalize = make_regex_pattern(target.capitalize())
        text = re.sub(pattern_capitalize, capitalized_replacements, text)
    return text
