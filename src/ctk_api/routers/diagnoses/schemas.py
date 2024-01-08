"""Schemas for the diagnoses endpoints."""

import pydantic


class DiagnosisNode(pydantic.BaseModel):
    """Represents node in the diagnoses tree.

    Attributes:
        text (str): The text of the diagnosis.
        children (list[DiagnosisNode]): The subclasses of the diagnosis.
        header (bool): Whether the diagnosis is a header. Dependent on
            whether the dliagnosis has any subclasses.
    """

    model_config = pydantic.ConfigDict(from_attributes=True)

    text: str = pydantic.Field(
        ...,
        json_schema_extra={
            "example": "Autism Spectrum Disorder",
            "description": "The text of the diagnosis.",
        },
    )
    children: list["DiagnosisNode"] = pydantic.Field(
        [],
        json_schema_extra={
            "description": "The subclasses of the diagnosis.",
        },
    )


class UpdateDiagnosisNode(pydantic.BaseModel):
    """Updates a node in the diagnoses tree.

    Attributes:
        text (str): The text of the diagnosis.
    """

    model_config = pydantic.ConfigDict(from_attributes=True)

    text: str = pydantic.Field(
        ...,
        json_schema_extra={
            "example": "Autism Spectrum Disorder",
            "description": "The text of the diagnosis.",
        },
    )
