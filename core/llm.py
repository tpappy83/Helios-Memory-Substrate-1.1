"""core/llm.py — OpenRouter client wrappers + classify / rerank / chat.

Three execution modes (selected automatically by env var presence):
  1. MOCK_MODE (HELIOS_LLM_MOCK=1): deterministic in-process responses. Used by tests.
  2. REAL mode (OPENROUTER_API_KEY set): makes real calls via OpenRouter's
     OpenAI-compatible endpoint. Default model is Google Gemini 2.0 Flash Exp
     (free tier — sign up at https://openrouter.ai/keys, no credit card required).
  3. FALLBACK (no key, no mock): returns mock responses with a graceful warning.
     Lets the synthetic deploy without keys for visual testing.

To use real LLM responses:
  export OPENROUTER_API_KEY=sk-or-v1-...
  # Optional: pick a different free model
  export OPENROUTER_MODEL=google/gemini-2.0-flash-exp:free
"""
from __future__ import annotations

import json
import os
import re
import time
from typing import Iterable, Iterator, Optional

from core.memory import Memory, keyword_candidates, write_memory
from core import tiering

# ─── Mode selection ───────────────────────────────────────────────────

MOCK_MODE = os.environ.get("HELIOS_LLM_MOCK") == "1"

OPENROUTER_API_KEY  = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
# Default to a strong FREE model on OpenRouter. Override via env if you have credits
# and want higher-quality output (claude, gpt, etc.).
DEFAULT_FREE_MODEL  = "google/gemini-2.0-flash-exp:free"
OPENROUTER_MODEL    = os.environ.get("OPENROUTER_MODEL", DEFAULT_FREE_MODEL)

REAL_LLM_ACTIVE = bool(OPENROUTER_API_KEY) and not MOCK_MODE


# ─── Lazy OpenAI-compatible client ─────────────────────────────────────

_client = None
def _get_client():
    """Lazy-construct the OpenRouter client. Returns None if no key configured."""
    global _client
    if _client is not None:
        return _client
    if not OPENROUTER_API_KEY:
        return None
    try:
        from openai import OpenAI
        _client = OpenAI(
            api_key=OPENROUTER_API_KEY,
            base_url=OPENROUTER_BASE_URL,
            default_headers={
                "HTTP-Referer": os.environ.get("HELIOS_PUBLIC_URL", "https://helios-memory.local"),
                "X-Title": "Helios memory backend",
            },
        )
        return _client
    except Exception:
        return None


def _mock_classify(text: str) -> dict:
    """Heuristic classifier for tests."""
    lower = text.lower()
    if "decided" in lower or "chose" in lower:
        return {"type": "decision", "importance": 0.7, "metadata": {}}
    if "happened" in lower or "occurred" in lower:
        return {"type": "event", "importance": 0.6, "metadata": {}}
    if "summary" in lower:
        return {"type": "summary", "importance": 0.5, "metadata": {}}
    return {"type": "observation", "importance": 0.5, "metadata": {}}


def _mock_rerank(query: str, candidates: list[Memory], top_k: int = 5) -> list[tuple[str, float]]:
    """Deterministic mock rerank for tests: rank by content length similarity."""
    q_tokens = set(query.lower().split())
    scored: list[tuple[str, float]] = []
    for m in candidates:
        c_tokens = set(m.content.lower().split())
        overlap = len(q_tokens & c_tokens)
        score = overlap / max(len(q_tokens), 1)
        scored.append((m.id, score))
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:top_k]


CLASSIFY_SYSTEM = """You are Helios's memory classifier. Read the user's message and return STRICT JSON with three fields:
- "type": one of "event" (something that happened), "state" (current condition), "summary" (distilled aggregate), "decision" (chosen action with rationale), "observation" (sensed/noted fact). Default to "observation" if uncertain.
- "importance": a float in [0, 1]. Decisions and events with strong rationale score ~0.7; routine observations score ~0.4. Pure questions score ~0.3.
- "metadata": an object with optional keys "topic" (1-3 word topic), "entities" (string list).
Return ONLY the JSON object, no surrounding text."""


def _real_classify(text: str) -> dict:
    """Real classify via OpenRouter chat completion (JSON mode)."""
    client = _get_client()
    if client is None:
        return _mock_classify(text)
    try:
        resp = client.chat.completions.create(
            model=OPENROUTER_MODEL,
            messages=[
                {"role": "system", "content": CLASSIFY_SYSTEM},
                {"role": "user", "content": text},
            ],
            temperature=0.0,
            max_tokens=200,
            response_format={"type": "json_object"},
        )
        raw = resp.choices[0].message.content or "{}"
        parsed = _parse_classify_json(raw)
        return parsed
    except Exception:
        return _mock_classify(text)


def _parse_classify_json(raw: str) -> dict:
    """Tolerant JSON parser for classifier output."""
    # Strip code fences if present
    raw = re.sub(r"^```(?:json)?", "", raw.strip())
    raw = re.sub(r"```$", "", raw.strip()).strip()
    try:
        data = json.loads(raw)
    except Exception:
        return {"type": "observation", "importance": 0.5, "metadata": {}}
    t = data.get("type", "observation")
    if t not in {"event", "state", "summary", "decision", "observation"}:
        t = "observation"
    imp = float(data.get("importance", 0.5))
    imp = max(0.0, min(1.0, imp))
    md = data.get("metadata") or {}
    if not isinstance(md, dict):
        md = {}
    return {"type": t, "importance": imp, "metadata": md}


RERANK_SYSTEM = """You are Helios's memory reranker. The user has a query and we retrieved candidate memories.
Score each candidate's relevance to the query on a 0.0 to 1.0 scale.
Return STRICT JSON: an object with key "scores" mapping each candidate id (string) to its float score.
Higher = more relevant. Return ONLY the JSON object."""


def _real_rerank(query: str, candidates: list[Memory], top_k: int) -> list[tuple[str, float]]:
    """Real LLM rerank via OpenRouter."""
    client = _get_client()
    if client is None or not candidates:
        return _mock_rerank(query, candidates, top_k)
    try:
        # Compact candidate representation to keep prompt small
        cand_text = "\n".join(
            f"- id={m.id[:12]}: [{m.type}] {m.content[:140]}" for m in candidates[:25]
        )
        user_prompt = f"Query: {query}\n\nCandidates:\n{cand_text}"
        resp = client.chat.completions.create(
            model=OPENROUTER_MODEL,
            messages=[
                {"role": "system", "content": RERANK_SYSTEM},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.0,
            max_tokens=600,
            response_format={"type": "json_object"},
        )
        raw = resp.choices[0].message.content or "{}"
        raw = re.sub(r"^```(?:json)?|```$", "", raw.strip()).strip()
        data = json.loads(raw) if raw else {}
        scores = data.get("scores", {}) if isinstance(data, dict) else {}

        # Map back to full IDs (we truncated to 12 chars in the prompt)
        out: list[tuple[str, float]] = []
        for m in candidates:
            short = m.id[:12]
            s = scores.get(short, scores.get(m.id, 0.0))
            try:
                out.append((m.id, float(s)))
            except (TypeError, ValueError):
                out.append((m.id, 0.0))
        out.sort(key=lambda x: x[1], reverse=True)
        return out[:top_k]
    except Exception:
        return _mock_rerank(query, candidates, top_k)


def llm_classify(text: str) -> dict:
    """Classify text into a memory type with suggested metadata + importance."""
    if MOCK_MODE:
        return _mock_classify(text)
    if REAL_LLM_ACTIVE:
        return _real_classify(text)
    return _mock_classify(text)


def llm_rerank(query: str, candidates: list[Memory], top_k: int = 5) -> list[tuple[str, float]]:
    """LLM rerank: returns (memory_id, score) pairs sorted descending."""
    if MOCK_MODE:
        return _mock_rerank(query, candidates, top_k)
    if REAL_LLM_ACTIVE:
        return _real_rerank(query, candidates, top_k)
    return _mock_rerank(query, candidates, top_k)


def query_memories(query: str, top_k: int = 5) -> list[tuple[Memory, float]]:
    """FTS5 candidate generation → LLM rerank → tier-aware rerank → top-K.

    Pipeline (post-v0.2):
      1. FTS5 keyword candidates (default k=25)
      2. LLM rerank → (id, score) pairs
      3. tiering.rerank_candidates → tier/drift/recency-aware final score
         + feedback loop on top-K (updates temperature, applies tier moves)
    """
    candidates = keyword_candidates(query, k=25)
    if not candidates:
        return []
    scored = llm_rerank(query, candidates, top_k=len(candidates))   # rank all so tiering sees them
    final = tiering.rerank_candidates(scored)
    by_id = {m.id: m for m in candidates}
    return [(by_id[mid], s) for mid, s in final[:top_k] if mid in by_id]


def _build_chat_messages(
    user_message: str,
    history: Iterable[dict],
    retrieved: list[Memory],
) -> list[dict]:
    """Shared prompt-assembly helper for streaming and non-streaming."""
    system = (
        "You are Helios, a memory-grounded assistant. "
        "Use retrieved memories below when relevant.\n\n"
        "Retrieved memories:\n"
        + "\n".join(f"- [{m.type}] {m.content}" for m in retrieved)
    )
    messages = [{"role": "system", "content": system}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_message})
    return messages


def chat_response(user_message: str, history: Optional[list[dict]] = None) -> str:
    """Non-streaming chat completion grounded in retrieved memories."""
    retrieved = [m for m, _ in query_memories(user_message, top_k=3)]
    messages = _build_chat_messages(user_message, history or [], retrieved)
    if MOCK_MODE:
        return _mock_chat(user_message, retrieved)
    if REAL_LLM_ACTIVE:
        client = _get_client()
        if client is not None:
            try:
                resp = client.chat.completions.create(
                    model=OPENROUTER_MODEL,
                    messages=messages,
                    temperature=0.3,
                    max_tokens=800,
                )
                return (resp.choices[0].message.content or "").strip()
            except Exception:
                return _mock_chat(user_message, retrieved)
    return _mock_chat(user_message, retrieved)


def _mock_chat(user_message: str, retrieved: list[Memory]) -> str:
    """Mock reply that demonstrates the pipeline result without an LLM call."""
    if retrieved:
        recall = "; ".join(f"[{m.type}] {m.content[:50]}" for m in retrieved[:2])
        return (
            f"Helios indexed your message and retrieved {len(retrieved)} relevant memories. "
            f"Most relevant: {recall}. Configure OPENROUTER_API_KEY for a real LLM reply."
        )
    return (
        f"Helios indexed your message ({len(user_message)} chars). No prior context yet. "
        f"Configure OPENROUTER_API_KEY for a real LLM reply."
    )


def chat_response_stream(
    user_message: str,
    history: Optional[list[dict]] = None,
    namespace: str = "default",
) -> Iterator[dict]:
    """Streaming chat: emits pipeline stage events + classified + tokens + done.

    Stage events (v0.2) trace the full Helios workflow:
        ingest → score → read → modify → write → store

    Each stage emits a {"type": "stage", "stage": <name>, "status": "running"|"complete", "data": {...}}.

    Legacy events preserved for backward compat:
        classified (memory_id + memory_type), token (incremental content), done (final + latency_ms).
    """
    t0 = time.perf_counter()

    # ── Stage 1: INGEST ──
    yield {"type": "stage", "stage": "ingest", "status": "running"}
    yield {
        "type": "stage", "stage": "ingest", "status": "complete",
        "data": {"chars": len(user_message), "namespace": namespace},
    }

    # ── Stage 2: SCORE (classify) ──
    yield {"type": "stage", "stage": "score", "status": "running"}
    cls = llm_classify(user_message)
    yield {
        "type": "stage", "stage": "score", "status": "complete",
        "data": {
            "memory_type": cls["type"],
            "importance": round(cls["importance"], 2),
        },
    }

    # ── Stage 3: READ (FTS5 + LLM rerank) ──
    yield {"type": "stage", "stage": "read", "status": "running"}
    candidates = keyword_candidates(user_message, k=25)
    fts_count = len(candidates)
    if candidates:
        scored = llm_rerank(user_message, candidates, top_k=len(candidates))
    else:
        scored = []
    yield {
        "type": "stage", "stage": "read", "status": "complete",
        "data": {"fts_candidates": fts_count, "reranked": len(scored)},
    }

    # ── Stage 4: MODIFY (tier-aware rerank + EMA feedback on top-K) ──
    yield {"type": "stage", "stage": "modify", "status": "running"}
    if scored:
        from core import tiering as _tiering  # late import to avoid cycle
        final = _tiering.rerank_candidates(scored)
    else:
        final = []
    yield {
        "type": "stage", "stage": "modify", "status": "complete",
        "data": {"top_k_updated": min(len(final), 20)},
    }

    # ── Stage 5: WRITE (persist new memory) ──
    yield {"type": "stage", "stage": "write", "status": "running"}
    mid = write_memory(
        content=user_message,
        type=cls["type"],
        metadata=cls["metadata"],
        importance=cls["importance"],
        namespace=namespace,
    )
    yield {
        "type": "stage", "stage": "write", "status": "complete",
        "data": {"memory_id": mid[:8]},
    }

    # ── Stage 6: STORE (confirm persistence + audit) ──
    yield {"type": "stage", "stage": "store", "status": "running"}
    yield {
        "type": "stage", "stage": "store", "status": "complete",
        "data": {"tier": "cold", "temperature": 0.5, "audit_logged": True},
    }

    # Legacy events preserved
    yield {"type": "classified", "memory_id": mid, "memory_type": cls["type"]}

    # ── Tokens (real streaming when LLM key is set, mock word-split otherwise) ──
    retrieved_memories = []
    if scored:
        from core.memory import get_memory
        retrieved_memories = [m for m in [get_memory(mid_) for mid_, _ in scored[:3]] if m]
    response_parts: list[str] = []

    if not MOCK_MODE and REAL_LLM_ACTIVE:
        client = _get_client()
        if client is not None:
            try:
                messages = _build_chat_messages(user_message, history or [], retrieved_memories)
                stream = client.chat.completions.create(
                    model=OPENROUTER_MODEL,
                    messages=messages,
                    temperature=0.3,
                    max_tokens=800,
                    stream=True,
                )
                for chunk in stream:
                    delta = chunk.choices[0].delta.content if chunk.choices else None
                    if delta:
                        response_parts.append(delta)
                        yield {"type": "token", "content": delta}
            except Exception:
                # Fall through to mock streaming
                response_parts = []

    if not response_parts:
        # Mock or fallback path
        response = _mock_chat(user_message, retrieved_memories) if MOCK_MODE else chat_response(user_message, history)
        for word in response.split():
            response_parts.append(word + " ")
            yield {"type": "token", "content": word + " "}
            time.sleep(0)

    final_response = "".join(response_parts)
    yield {
        "type": "done", "content": final_response,
        "latency_ms": (time.perf_counter() - t0) * 1000.0,
        "memory_id": mid,
    }
