"""app.py — Helios Streamlit chat UI (port 8501).

Talks to core.* directly. Token streaming via st.write_stream.
Sidebar additions (v0.2): reranker weight tuning, namespace selector.
"""
from __future__ import annotations

import time

import requests
import streamlit as st

from core.db import init_schema
from core import memory as memory_mod
from core import llm as llm_mod
from core import tiering

st.set_page_config(page_title="Helios", page_icon="◉", layout="wide")

init_schema()

if "session_id" not in st.session_state:
    st.session_state.session_id = "default"
if "namespace" not in st.session_state:
    st.session_state.namespace = "default"


# ─── Sidebar: namespace selector (v0.2) ──────────────────────────

with st.sidebar.expander("Namespace", expanded=False):
    ns = st.text_input(
        "Memory namespace",
        value=st.session_state.namespace,
        help="All memory writes/reads in this session are scoped to this namespace.",
    )
    st.session_state.namespace = ns
    st.caption(f"Current: `{ns}`")


# ─── Sidebar: reranker tuning (v0.2) ─────────────────────────────

with st.sidebar.expander("Reranker weights", expanded=False):
    w_sim   = st.slider("Similarity", 0.0, 1.0, tiering.W_SIMILARITY, 0.01, key="ws")
    w_val   = st.slider("Value",      0.0, 1.0, tiering.W_VALUE,      0.01, key="wv")
    w_rec   = st.slider("Recency",    0.0, 1.0, tiering.W_RECENCY,    0.01, key="wr")
    w_tier  = st.slider("Tier",       0.0, 1.0, tiering.W_TIER,       0.01, key="wt")
    w_drift = st.slider("Drift",      0.0, 0.5, tiering.W_DRIFT,      0.01, key="wd")

    total = w_sim + w_val + w_rec + w_tier
    sigma_ok = abs(total - 1.0) < 0.05
    st.caption(
        f"Σ(sim+val+rec+tier) = {total:.2f} "
        f"{'(balanced)' if sigma_ok else '(skewed — unconstrained)'}"
    )
    st.code(
        f"score = sim*{w_sim:.2f} + val*{w_val:.2f} "
        f"+ rec*{w_rec:.2f} + tier*{w_tier:.2f} - drift*{w_drift:.2f}",
        language="python",
    )
    if st.button("Apply", key="apply_weights"):
        try:
            resp = requests.patch(
                "http://localhost:8000/config/retrieval",
                json={
                    "w_similarity": w_sim, "w_value": w_val,
                    "w_recency": w_rec, "w_tier": w_tier, "w_drift": w_drift,
                },
                timeout=2,
            )
            if resp.status_code == 200:
                st.success("Weights updated")
            else:
                st.error(f"Update failed: {resp.status_code}")
        except Exception as exc:
            st.error(f"Connection error: {exc}")


# ─── Sidebar: recent memories preview ────────────────────────────

with st.sidebar:
    st.subheader("Recent memories")
    for m in memory_mod.list_recent(limit=5):
        st.text(f"[{m.type}] {m.content[:60]}")


# ─── Main chat ────────────────────────────────────────────────────

st.title("Helios — memory-grounded chat")
st.caption("FTS5 + LLM rerank + tier-aware reranker. No vector DB.")

history = memory_mod.list_session(st.session_state.session_id, limit=50)
for msg in history:
    with st.chat_message(msg.role):
        st.write(msg.content)

if prompt := st.chat_input("Ask Helios..."):
    memory_mod.write_chat(st.session_state.session_id, "user", prompt)
    with st.chat_message("user"):
        st.write(prompt)
    with st.chat_message("assistant"):
        t0 = time.perf_counter()
        reply = llm_mod.chat_response(prompt)
        latency_ms = (time.perf_counter() - t0) * 1000.0
        st.write(reply)
        st.caption(f"{latency_ms:.0f}ms · namespace=`{st.session_state.namespace}`")
        memory_mod.write_chat(st.session_state.session_id, "assistant", reply)
