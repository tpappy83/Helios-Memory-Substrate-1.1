"""tests/test_qdrant.py — Qdrant client (mock-path) tests.

Validates that:
- Mock client enforces tenant_id payload partitioning at the SDK boundary
- Cross-tenant search isolation works (Tenant A query never returns Tenant B vectors)
- TenantFilterRequired is raised when tenant_id is missing
- The mock cosine similarity ranks correctly

Real Qdrant integration is NOT exercised here (no live Qdrant in the test env).
Production integration tests are out of scope for the synthetic.
"""
import pytest

from core.qdrant_client import QdrantClient, TenantFilterRequired, VectorPoint


def make_client() -> QdrantClient:
    """Fresh in-memory mock client per test."""
    return QdrantClient(url=None)


def test_mock_path_active_when_no_url():
    c = make_client()
    assert c.real is False


def test_upsert_requires_tenant_id_in_payload():
    c = make_client()
    with pytest.raises(TenantFilterRequired):
        c.upsert("memories", "p1", [0.1, 0.2, 0.3], payload={"content": "no tenant"})


def test_upsert_with_tenant_id_succeeds():
    c = make_client()
    c.upsert("memories", "p1", [0.1, 0.2, 0.3], payload={"tenant_id": "t1", "content": "ok"})
    got = c.get("memories", "p1", tenant_id="t1")
    assert got is not None
    assert got.payload["tenant_id"] == "t1"


def test_search_requires_tenant_id():
    c = make_client()
    c.upsert("memories", "p1", [1.0, 0.0], payload={"tenant_id": "t1"})
    with pytest.raises(TenantFilterRequired):
        c.search("memories", [1.0, 0.0], tenant_id="", top_k=5)


def test_search_isolates_tenants():
    c = make_client()
    # Tenant A has 3 records
    c.upsert("m", "a1", [1.0, 0.0, 0.0], {"tenant_id": "A"})
    c.upsert("m", "a2", [0.9, 0.1, 0.0], {"tenant_id": "A"})
    c.upsert("m", "a3", [0.8, 0.2, 0.0], {"tenant_id": "A"})
    # Tenant B has 2 records, one nearly identical to Tenant A's a1
    c.upsert("m", "b1", [1.0, 0.0, 0.0], {"tenant_id": "B"})
    c.upsert("m", "b2", [0.5, 0.5, 0.0], {"tenant_id": "B"})

    # Tenant A search returns only A's records
    hits_a = c.search("m", [1.0, 0.0, 0.0], tenant_id="A", top_k=10)
    assert len(hits_a) == 3
    assert all(h.payload["tenant_id"] == "A" for h in hits_a)
    # Top result is a1 (exact match)
    assert hits_a[0].id == "a1"
    assert hits_a[0].score == pytest.approx(1.0)

    # Tenant B search returns only B's records (despite a1 being closer to query)
    hits_b = c.search("m", [1.0, 0.0, 0.0], tenant_id="B", top_k=10)
    assert len(hits_b) == 2
    assert all(h.payload["tenant_id"] == "B" for h in hits_b)
    assert hits_b[0].id == "b1"


def test_get_isolates_tenants():
    c = make_client()
    c.upsert("m", "shared_id", [1.0, 0.0], {"tenant_id": "A"})
    # Tenant B asking for "shared_id" should get nothing
    assert c.get("m", "shared_id", tenant_id="B") is None
    # Tenant A gets it
    assert c.get("m", "shared_id", tenant_id="A") is not None


def test_delete_isolates_tenants():
    c = make_client()
    c.upsert("m", "p1", [1.0, 0.0], {"tenant_id": "A"})
    # Tenant B can't delete A's record
    assert c.delete("m", "p1", tenant_id="B") is False
    # Record still exists for A
    assert c.get("m", "p1", tenant_id="A") is not None
    # A deletes successfully
    assert c.delete("m", "p1", tenant_id="A") is True
    # Gone
    assert c.get("m", "p1", tenant_id="A") is None


def test_count_is_per_tenant():
    c = make_client()
    for i in range(5):
        c.upsert("m", f"a{i}", [1.0, 0.0], {"tenant_id": "A"})
    for i in range(3):
        c.upsert("m", f"b{i}", [0.0, 1.0], {"tenant_id": "B"})
    assert c.count("m", tenant_id="A") == 5
    assert c.count("m", tenant_id="B") == 3
    assert c.count("m", tenant_id="C") == 0
