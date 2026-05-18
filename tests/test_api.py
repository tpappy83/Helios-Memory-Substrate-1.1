"""tests/test_api.py — FastAPI surface smoke tests (v0.2 additions)."""
from fastapi.testclient import TestClient

from api import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_stats_endpoint():
    r = client.get("/stats")
    assert r.status_code == 200
    data = r.json()
    assert data["schema_version"] == 3
    assert "tier_distribution" in data
    assert "reranker_weights" in data
    assert data["reranker_weights"]["similarity"] == 0.55


def test_create_and_get_memory_with_namespace():
    r = client.post("/memory", json={"content": "test memory"}, headers={"X-Namespace": "tenant1"})
    assert r.status_code == 201
    mid = r.json()["id"]
    assert r.json()["namespace"] == "tenant1"
    assert r.json()["tier"] == "cold"

    # Get by id in same namespace → 200
    r = client.get(f"/memory/{mid}", headers={"X-Namespace": "tenant1"})
    assert r.status_code == 200

    # Get by id in wrong namespace → 404
    r = client.get(f"/memory/{mid}", headers={"X-Namespace": "tenant2"})
    assert r.status_code == 404


def test_delete_memory_namespace_gated():
    r = client.post("/memory", json={"content": "to delete"}, headers={"X-Namespace": "tenant1"})
    mid = r.json()["id"]

    # Wrong namespace → 404
    r = client.delete(f"/memory/{mid}", headers={"X-Namespace": "tenant2"})
    assert r.status_code == 404

    # Right namespace → 204
    r = client.delete(f"/memory/{mid}", headers={"X-Namespace": "tenant1"})
    assert r.status_code == 204


def test_batch_ingest():
    items = [
        {"content": "item 1", "importance": 0.3},
        {"content": "item 2", "importance": 0.7},
        {"content": "item 3", "type": "decision"},
    ]
    r = client.post("/memory/batch", json=items, headers={"X-Namespace": "batch_test"})
    assert r.status_code == 201
    data = r.json()
    assert data["success_count"] == 3
    assert data["error_count"] == 0
    assert "latency_ms" in data and data["latency_ms"] >= 0


def test_patch_config_retrieval():
    r = client.patch("/config/retrieval", json={"w_similarity": 0.6, "w_recency": 0.15})
    assert r.status_code == 200
    weights = r.json()["weights"]
    assert weights["similarity"] == 0.6
    assert weights["recency"] == 0.15
    # Reset
    client.patch("/config/retrieval", json={"w_similarity": 0.55, "w_recency": 0.10})


def test_chat_with_latency_ms():
    r = client.post("/chat", json={"message": "hello", "session_id": "test"})
    assert r.status_code == 200
    data = r.json()
    assert "latency_ms" in data
    assert data["latency_ms"] >= 0


def test_audit_log_endpoint():
    # Trigger an audit entry via memory write
    client.post("/memory", json={"content": "audit me"}, headers={"X-Namespace": "audit_test"})

    r = client.get("/audit", headers={"X-Namespace": "audit_test"})
    assert r.status_code == 200
    data = r.json()
    assert data["count"] >= 1
    assert data["entries"][0]["action"] == "memory.write"


def test_events_alias():
    # Events endpoint reshapes audit entries
    client.post("/memory", json={"content": "event source"}, headers={"X-Namespace": "events_test"})

    r = client.get("/events", headers={"X-Namespace": "events_test"})
    assert r.status_code == 200
    events = r.json()
    assert len(events) >= 1
    assert events[0]["type"] == "write"   # "memory.write" → "write"


def test_chat_stream_emits_pipeline_stages():
    """/chat/stream emits all 6 pipeline stage events per the v0.2 workflow."""
    with client.stream(
        "POST", "/chat/stream",
        json={"message": "I decided to ship Helios v0.2", "session_id": "stream_test"},
    ) as resp:
        assert resp.status_code == 200
        events = []
        for chunk in resp.iter_text():
            for block in chunk.split("\n\n"):
                if not block.strip():
                    continue
                for line in block.split("\n"):
                    if line.startswith("data: "):
                        import json as _json
                        events.append(_json.loads(line[6:]))

    # Extract all stage events
    stages = [e for e in events if e.get("type") == "stage"]
    stage_names_complete = {e["stage"] for e in stages if e.get("status") == "complete"}
    assert stage_names_complete == {"ingest", "score", "read", "modify", "write", "store"}, \
        f"missing stages: {stage_names_complete}"

    # Score stage carries classification
    score_complete = next(e for e in stages if e["stage"] == "score" and e["status"] == "complete")
    assert score_complete["data"]["memory_type"] == "decision"

    # Write stage carries memory_id
    write_complete = next(e for e in stages if e["stage"] == "write" and e["status"] == "complete")
    assert "memory_id" in write_complete["data"]

    # Done event carries latency_ms
    done = next(e for e in events if e.get("type") == "done")
    assert "latency_ms" in done and done["latency_ms"] >= 0
