from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, HttpUrl, field_validator


ValidationStatus = Literal[
    "Supported",
    "Partially supported",
    "Conflicting evidence",
    "Insufficient evidence",
    "Outdated source",
    "Model inference",
]


class SourceRecord(BaseModel):
    title: str = "Untitled source"
    url: str
    source_type: str = "other"
    publication_date: str | None = None
    reliability_score: float = Field(default=0.50, ge=0.0, le=1.0)


class EvidenceClaim(BaseModel):
    claim: str
    category: str
    evidence_excerpt: str = ""
    source_title: str = ""
    source_url: str = ""
    source_type: str = "other"
    publication_date: str | None = None
    confidence_score: float = Field(default=0.50, ge=0.0, le=1.0)
    validation_status: ValidationStatus = "Insufficient evidence"
    analyst_note: str = ""

    @field_validator("claim", "category")
    @classmethod
    def must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Field cannot be blank")
        return value


class DiligenceOutput(BaseModel):
    company: str
    objective: str
    executive_summary: str
    claims: list[EvidenceClaim]
    key_risks: list[str] = []
    open_questions: list[str] = []
    methodology_note: str = (
        "AI-assisted research output. Every material conclusion should be reviewed "
        "against its cited source before external use."
    )
