"""The model proposes a report; independent code verifies its citations."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field


class Reference(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    source: str
    line_start: int = Field(ge=1)
    line_end: int = Field(ge=1)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    excerpt: str


class Claim(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    title: str
    status: Literal["supported", "contradicted", "unknown"]
    rationale: str
    evidence_refs: list[str] = Field(min_length=1)


FindingText = Annotated[str, Field(min_length=20)]


class HandoffReport(BaseModel):
    model_config = ConfigDict(extra="forbid")
    claims: list[Claim] = Field(min_length=1)
    unknowns: list[FindingText]
    risks: list[FindingText]
    references: list[Reference] = Field(min_length=1)


def report_schema_for_checks(checks: list[dict]) -> dict:
    """Constrain visibility from actual observations, without supplying a report."""
    schema = HandoffReport.model_json_schema()
    classifications = {check["classification"] for check in checks}
    if "unknown" in classifications:
        schema["properties"]["unknowns"]["minItems"] = 1
    if "contradicted" in classifications:
        schema["properties"]["risks"]["minItems"] = 1
    return schema
