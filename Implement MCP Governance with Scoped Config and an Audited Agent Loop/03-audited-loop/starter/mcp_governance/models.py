"""Domain models for the claims and policy systems of record."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel


class ClaimStatus(StrEnum):
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    DENIED = "denied"
    PAID = "paid"


class IncidentType(StrEnum):
    AUTO_COLLISION = "auto_collision"
    PROPERTY_DAMAGE = "property_damage"
    THEFT = "theft"
    LIABILITY = "liability"
    WATER_DAMAGE = "water_damage"


class PolicyType(StrEnum):
    AUTO = "auto"
    HOME = "home"
    LIFE = "life"
    UMBRELLA = "umbrella"


class PolicyStatus(StrEnum):
    ACTIVE = "active"
    LAPSED = "lapsed"
    CANCELLED = "cancelled"


class Claim(BaseModel):
    """One claim record. Field names are the single source of truth the schema catalog
    (``claims://schema``) must agree with -- the parity test enforces that."""

    claim_id: str
    policy_id: str
    claimant_name: str
    status: ClaimStatus
    incident_type: IncidentType
    amount: float
    filed_date: str
    adjuster: str


class Policy(BaseModel):
    policy_id: str
    holder_name: str
    policy_type: PolicyType
    coverage_limit: int
    deductible: int
    status: PolicyStatus
    effective_date: str
