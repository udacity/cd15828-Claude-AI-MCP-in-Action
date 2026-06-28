"""The claims schema catalog exposed as an MCP Resource (claims://schema)."""

from __future__ import annotations

import json
from typing import Any

import pytest

from mcp_governance.schema import CLAIMS_SCHEMA, build_schema_catalog
from mcp_governance.servers import SCHEMA_RESOURCE_URI, build_claims_server
from mcp_governance.services import ClaimsService


async def _read_schema_resource() -> dict[str, Any]:
    server = build_claims_server()
    contents = list(await server.read_resource(SCHEMA_RESOURCE_URI))
    assert len(contents) == 1
    payload = json.loads(contents[0].content)
    assert isinstance(payload, dict)
    return payload


# ---- The resource exists and carries the field catalog ----------------


async def test_resource_is_registered() -> None:
    server = build_claims_server()
    uris = {str(r.uri) for r in await server.list_resources()}
    assert SCHEMA_RESOURCE_URI in uris


async def test_resource_content_is_field_catalog() -> None:
    payload = await _read_schema_resource()
    fields = {f["name"]: f for f in payload["fields"]}
    assert "claim_id" in fields and "status" in fields
    for spec in fields.values():
        assert spec["type"] and spec["description"] and "example" in spec


# ---- Catalog <-> data parity (no drift) -------------------------------


def test_catalog_matches_data_fields_exactly() -> None:
    catalog_fields = {f["name"] for f in build_schema_catalog()["fields"]}
    claims = ClaimsService.from_dir()._claims
    assert claims, "expected committed claim data"
    data_fields = set(claims[0].model_dump().keys())
    for claim in claims:
        assert set(claim.model_dump().keys()) == data_fields  # uniform records
    assert catalog_fields == data_fields  # no field missing, none fabricated


# ---- Catalog is generated from the schema source ----------------------


@pytest.mark.parametrize("spec", CLAIMS_SCHEMA, ids=lambda s: s.name)
def test_each_declared_field_rendered_with_type_and_description(spec: Any) -> None:
    rendered = {f["name"]: f for f in build_schema_catalog()["fields"]}
    assert spec.name in rendered
    assert rendered[spec.name]["type"].strip()
    assert rendered[spec.name]["description"].strip()


def test_status_enum_surfaced_in_catalog() -> None:
    fields = {f["name"]: f for f in build_schema_catalog()["fields"]}
    assert set(fields["status"]["enum"]) == {
        "submitted",
        "under_review",
        "approved",
        "denied",
        "paid",
    }


# ---- The resource reduces exploratory tool calls ----------------------


class CountingClaimsService(ClaimsService):
    """Wraps the real service to count tool-level lookups."""

    def __init__(self) -> None:
        base = ClaimsService.from_dir()
        super().__init__(base._claims)
        self.calls = 0

    def get_claim(self, claim_id: str):  # type: ignore[override]
        self.calls += 1
        return super().get_claim(claim_id)

    def search_claims(self, status=None, min_amount=None):  # type: ignore[override]
        self.calls += 1
        return super().search_claims(status=status, min_amount=min_amount)


def _status_values_from_catalog(catalog: dict[str, Any]) -> set[str]:
    fields = {f["name"]: f for f in catalog["fields"]}
    return set(fields["status"]["enum"])


def _status_values_by_probing(svc: ClaimsService) -> set[str]:
    return {c.status.value for c in svc.search_claims()}


def test_catalog_answers_with_zero_tool_calls() -> None:
    svc = CountingClaimsService()
    # With the resource: the question is answered from catalog content alone.
    values = _status_values_from_catalog(build_schema_catalog())
    assert "under_review" in values
    assert svc.calls == 0

    # Without the resource: the same question forces an exploratory query.
    probed = _status_values_by_probing(svc)
    assert svc.calls >= 1
    assert probed.issubset(values)  # data is consistent with the declared enum
