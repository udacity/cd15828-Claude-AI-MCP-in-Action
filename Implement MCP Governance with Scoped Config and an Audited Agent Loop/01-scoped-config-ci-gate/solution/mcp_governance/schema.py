"""The claims-record schema as a **single source of truth**.

The ``claims://schema`` MCP resource is *derived* from ``CLAIMS_SCHEMA`` -- it is
never hand-maintained as a second copy. A parity test asserts these field names match the
keys actually present in ``data/claims`` so the catalog can't drift from the data.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from mcp_governance.models import ClaimStatus, IncidentType


class FieldSpec(BaseModel):
    """One field in the claims schema catalog."""

    name: str
    type: str
    description: str
    example: Any
    enum: list[str] | None = None


CLAIMS_SCHEMA: list[FieldSpec] = [
    FieldSpec(
        name="claim_id",
        type="string",
        description="Unique claim identifier, format CLM-#####.",
        example="CLM-10001",
    ),
    FieldSpec(
        name="policy_id",
        type="string",
        description="Identifier of the policy this claim is filed against; "
        "a foreign key resolvable via the policy-lookup server.",
        example="POL-5001",
    ),
    FieldSpec(
        name="claimant_name",
        type="string",
        description="Full legal name of the claimant (PII -- never log in cleartext).",
        example="Margaret A. Donnelly",
    ),
    FieldSpec(
        name="status",
        type="string",
        description="Current workflow status of the claim.",
        example="under_review",
        enum=[s.value for s in ClaimStatus],
    ),
    FieldSpec(
        name="incident_type",
        type="string",
        description="Category of the insured incident.",
        example="auto_collision",
        enum=[t.value for t in IncidentType],
    ),
    FieldSpec(
        name="amount",
        type="number",
        description="Claimed amount in US dollars.",
        example=8450.0,
    ),
    FieldSpec(
        name="filed_date",
        type="string",
        description="Date the claim was filed, ISO-8601 date (YYYY-MM-DD).",
        example="2024-04-12",
    ),
    FieldSpec(
        name="adjuster",
        type="string",
        description="Name of the assigned claims adjuster.",
        example="Karen Liu",
    ),
]


def build_schema_catalog() -> dict[str, Any]:
    """Render the schema source into the content-catalog payload exposed at
    ``claims://schema``. Derived from :data:`CLAIMS_SCHEMA`, never duplicated."""
    # TODO (LO-3): return the content-catalog payload, DERIVED from CLAIMS_SCHEMA (never a
    #   hand-maintained second copy -- a parity test checks it against the data). Include:
    #     - "resource": the resource URI "claims://schema"
    #     - "description": a one-line "read this to discover fields without exploratory calls"
    #     - "fields": one rendered entry per spec in CLAIMS_SCHEMA (spec.model_dump,
    #                 dropping None so a field without an enum omits the key)
    raise NotImplementedError
