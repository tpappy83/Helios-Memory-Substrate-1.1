"""core/qdrant_client.py — Helios v0.3 vector index with multi-tenant payload partitioning.

Per Crucible §3 of the research blueprint:
- Qdrant payload partitioning with `is_tenant=true` keyword index on tenant_id
- Tenant filter is INJECTED at the SDK boundary, not at the application call site
  (too easy to forget at the call site)
- This module raises if a query/upsert is attempted without a tenant_id filter

This is the QDRANT-LAYER abstraction. Real Qdrant deployment activates when
QDRANT_URL is set in the environment; otherwise a deterministic in-memory mock is
used (for tests and local-first development without external deps).

**Wedge violation flag:** activating this module against real Qdrant violates
Helios wedge #2 (no vector DB dependency). The mock path preserves the wedge for
single-tenant local-first; the production path is explicitly v0.3+ territory.

Public API:
- `QdrantClient.upsert(collection, point_id, vector, payload)` — single upsert
- `QdrantClient.upsert_batch(collection, points)` — batch
- `QdrantClient.search(collection, query_vector, tenant_id, top_k)` — tenant-scoped
- `QdrantClient.delete(collection, point_id, tenant_id)` — namespace-gated delete
- `QdrantClient.count(collection, tenant_id)` — per-tenant count

All search/delete operations REQUIRE tenant_id. There is no escape hatch.
"""
from __future__ import annotations

import math
import os
from dataclasses import dataclass, field
from typing import Optional


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    if len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    if na < 1e-9 or nb < 1e-9:
        return 0.0
    return dot / (na * nb)


@dataclass
class VectorPoint:
    """A single vector record. Payload MUST contain tenant_id."""
    id:      str
    vector:  list[float]
    payload: dict
    score:   Optional[float] = None    # populated by search


class TenantFilterRequired(Exception):
    """Raised when a vector operation is attempted without a tenant_id filter."""


class QdrantClient:
    """Thin wrapper over Qdrant with tenant-payload-partitioning enforced.

    Two modes:
    - REAL: when QDRANT_URL env var is set; uses qdrant-client Python package
    - MOCK: in-memory dict-of-dicts; deterministic for tests; no external deps

    The mode is selected at construction time. Tests in this synthetic ship use
    the MOCK path; real deployment sets QDRANT_URL + QDRANT_API_KEY in env.
    """

    def __init__(self, url: Optional[str] = None, api_key: Optional[str] = None) -> None:
        self.url = url or os.environ.get("QDRANT_URL")
        self.api_key = api_key or os.environ.get("QDRANT_API_KEY")
        self.real = bool(self.url)
        if self.real:
            try:
                from qdrant_client import QdrantClient as RealClient
                self._real = RealClient(url=self.url, api_key=self.api_key)
            except ImportError as exc:
                raise RuntimeError(
                    "QDRANT_URL set but qdrant-client not installed. "
                    "Add `qdrant-client` to requirements.txt, or unset QDRANT_URL "
                    "to use the in-memory mock path."
                ) from exc
        else:
            # Mock storage: {collection: {point_id: VectorPoint}}
            self._mock: dict[str, dict[str, VectorPoint]] = {}

    # ─── Collection management ──────────────────────────────────────

    def ensure_collection(self, name: str, vector_size: int = 1536) -> None:
        """Create the collection if it doesn't exist (vector_size hint for real Qdrant)."""
        if self.real:
            from qdrant_client.models import Distance, VectorParams
            cols = {c.name for c in self._real.get_collections().collections}
            if name not in cols:
                self._real.create_collection(
                    collection_name=name,
                    vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
                )
                # Create the tenant_id keyword index for payload partitioning
                self._real.create_payload_index(
                    collection_name=name,
                    field_name="tenant_id",
                    field_schema="keyword",
                )
        else:
            self._mock.setdefault(name, {})

    # ─── Write operations ──────────────────────────────────────────

    def upsert(
        self,
        collection: str,
        point_id: str,
        vector: list[float],
        payload: dict,
    ) -> None:
        """Insert or update a single vector point. Payload MUST contain tenant_id."""
        if "tenant_id" not in payload:
            raise TenantFilterRequired(
                "payload must contain tenant_id for multi-tenant isolation"
            )
        self.ensure_collection(collection, vector_size=len(vector))
        if self.real:
            from qdrant_client.models import PointStruct
            self._real.upsert(
                collection_name=collection,
                points=[PointStruct(id=point_id, vector=vector, payload=payload)],
            )
        else:
            self._mock.setdefault(collection, {})[point_id] = VectorPoint(
                id=point_id, vector=list(vector), payload=dict(payload),
            )

    def upsert_batch(self, collection: str, points: list[VectorPoint]) -> None:
        for p in points:
            self.upsert(collection, p.id, p.vector, p.payload)

    # ─── Read operations ───────────────────────────────────────────

    def search(
        self,
        collection: str,
        query_vector: list[float],
        tenant_id: str,
        top_k: int = 10,
    ) -> list[VectorPoint]:
        """Search restricted to records with payload.tenant_id == tenant_id.

        Tenant filter is REQUIRED. There is no escape hatch.
        """
        if not tenant_id:
            raise TenantFilterRequired("tenant_id must be provided for search")
        if self.real:
            from qdrant_client.models import Filter, FieldCondition, MatchValue
            hits = self._real.search(
                collection_name=collection,
                query_vector=query_vector,
                query_filter=Filter(
                    must=[FieldCondition(key="tenant_id", match=MatchValue(value=tenant_id))]
                ),
                limit=top_k,
            )
            return [
                VectorPoint(
                    id=str(h.id), vector=[], payload=h.payload, score=h.score,
                )
                for h in hits
            ]
        else:
            results: list[VectorPoint] = []
            for point in self._mock.get(collection, {}).values():
                if point.payload.get("tenant_id") != tenant_id:
                    continue
                score = _cosine_similarity(point.vector, query_vector)
                results.append(VectorPoint(
                    id=point.id, vector=point.vector,
                    payload=dict(point.payload), score=score,
                ))
            results.sort(key=lambda p: p.score or 0, reverse=True)
            return results[:top_k]

    def get(
        self,
        collection: str,
        point_id: str,
        tenant_id: str,
    ) -> Optional[VectorPoint]:
        """Get a single point, tenant-gated. Returns None if not found or wrong tenant."""
        if not tenant_id:
            raise TenantFilterRequired("tenant_id must be provided for get")
        if self.real:
            from qdrant_client.models import Filter, FieldCondition, MatchValue
            hits = self._real.retrieve(
                collection_name=collection,
                ids=[point_id],
                with_payload=True,
                with_vectors=False,
            )
            for h in hits:
                if h.payload.get("tenant_id") == tenant_id:
                    return VectorPoint(id=str(h.id), vector=[], payload=h.payload)
            return None
        else:
            p = self._mock.get(collection, {}).get(point_id)
            if p is None or p.payload.get("tenant_id") != tenant_id:
                return None
            return VectorPoint(id=p.id, vector=p.vector, payload=dict(p.payload))

    def delete(
        self,
        collection: str,
        point_id: str,
        tenant_id: str,
    ) -> bool:
        """Delete a point, tenant-gated. Returns True if deleted."""
        if not tenant_id:
            raise TenantFilterRequired("tenant_id must be provided for delete")
        if self.real:
            from qdrant_client.models import Filter, FieldCondition, MatchValue, FilterSelector
            # Real qdrant doesn't have AND-id-and-filter in one call cleanly;
            # do a retrieve-then-delete-if-matches pattern.
            existing = self.get(collection, point_id, tenant_id)
            if existing is None:
                return False
            self._real.delete(collection_name=collection, points_selector=[point_id])
            return True
        else:
            store = self._mock.get(collection, {})
            p = store.get(point_id)
            if p is None or p.payload.get("tenant_id") != tenant_id:
                return False
            del store[point_id]
            return True

    def count(self, collection: str, tenant_id: str) -> int:
        """Count records in the collection scoped to tenant_id."""
        if not tenant_id:
            raise TenantFilterRequired("tenant_id must be provided for count")
        if self.real:
            from qdrant_client.models import Filter, FieldCondition, MatchValue
            result = self._real.count(
                collection_name=collection,
                count_filter=Filter(
                    must=[FieldCondition(key="tenant_id", match=MatchValue(value=tenant_id))]
                ),
            )
            return result.count
        else:
            return sum(
                1 for p in self._mock.get(collection, {}).values()
                if p.payload.get("tenant_id") == tenant_id
            )


# ─── Module-level singleton (lazy) ───────────────────────────────────

_singleton: Optional[QdrantClient] = None
def get_client() -> QdrantClient:
    """Return the process-wide QdrantClient. Constructs on first call."""
    global _singleton
    if _singleton is None:
        _singleton = QdrantClient()
    return _singleton
