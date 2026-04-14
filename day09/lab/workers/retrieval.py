"""
workers/retrieval.py — Retrieval Worker
Sprint 2: Implement retrieval từ ChromaDB, trả về chunks + sources.

Input (từ AgentState):
    - task: câu hỏi cần retrieve
    - (optional) retrieved_chunks nếu đã có từ trước

Output (vào AgentState):
    - retrieved_chunks: list of {"text", "source", "score", "metadata"}
    - retrieved_sources: list of source filenames
    - worker_io_log: log input/output của worker này

Gọi độc lập để test:
    python workers/retrieval.py
"""

import os
import re

# ─────────────────────────────────────────────
# Worker Contract (xem contracts/worker_contracts.yaml)
# Input:  {"task": str, "top_k": int = 3}
# Output: {"retrieved_chunks": list, "retrieved_sources": list, "error": dict | None}
# ─────────────────────────────────────────────

WORKER_NAME = "retrieval_worker"
DEFAULT_TOP_K = 3
COLLECTION_NAME = "day09_docs"

_EMBED_MODEL = None


def _get_embedding_fn():
    """
    Trả về embedding function offline bằng SentenceTransformer.
    """
    global _EMBED_MODEL
    from sentence_transformers import SentenceTransformer

    if _EMBED_MODEL is None:
        _EMBED_MODEL = SentenceTransformer("all-MiniLM-L6-v2")

    def embed(text: str) -> list:
        return _EMBED_MODEL.encode([text])[0].tolist()

    return embed


def _get_collection():
    """
    Kết nối ChromaDB collection.
    TODO Sprint 2: Đảm bảo collection đã được build từ Step 3 trong README.
    """
    import chromadb
    chroma_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "chroma_db")
    client = chromadb.PersistentClient(path=chroma_path)
    try:
        collection = client.get_collection(COLLECTION_NAME)
    except Exception:
        # Auto-create nếu chưa có data để pipeline vẫn chạy được
        collection = client.get_or_create_collection(
            COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )
        print(f"⚠️  Collection '{COLLECTION_NAME}' chưa có data. Chạy index script trong README trước.")
    return collection


def _tokenize(text: str) -> set:
    return {tok for tok in re.findall(r"\w+", text.lower(), flags=re.UNICODE) if len(tok) > 1}


def _source_boost(query_text: str, source_name: str) -> float:
    q = query_text.lower()
    s = source_name.lower()

    if any(kw in q for kw in ["hoàn tiền", "refund", "flash sale", "store credit", "license"]):
        return 0.35 if "policy_refund_v4" in s else 0.0
    if any(kw in q for kw in ["sla", "p1", "ticket", "escalation", "incident"]):
        return 0.35 if "sla_p1_2026" in s else 0.0
    if any(kw in q for kw in ["access", "cấp quyền", "level", "admin", "contractor"]):
        return 0.35 if "access_control_sop" in s else 0.0
    if any(kw in q for kw in ["remote", "probation", "nghỉ", "hr", "nhân viên"]):
        return 0.35 if "hr_leave_policy" in s else 0.0
    if any(kw in q for kw in ["mật khẩu", "vpn", "helpdesk", "đăng nhập", "faq"]):
        return 0.35 if "it_helpdesk_faq" in s else 0.0
    return 0.0


def _lexical_fallback(query: str, top_k: int = DEFAULT_TOP_K) -> list:
    """Fallback retrieval theo lexical overlap khi vector stack chưa sẵn sàng."""
    docs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "docs")
    if not os.path.isdir(docs_dir):
        return []

    q_tokens = _tokenize(query)
    if not q_tokens:
        return []

    scored = []
    for fname in os.listdir(docs_dir):
        fpath = os.path.join(docs_dir, fname)
        if not os.path.isfile(fpath):
            continue
        try:
            with open(fpath, encoding="utf-8") as f:
                content = f.read().strip()
        except Exception:
            continue

        doc_tokens = _tokenize(content)
        if not doc_tokens:
            continue

        overlap = q_tokens.intersection(doc_tokens)
        overlap_score = len(overlap) / max(1, len(q_tokens))
        boosted_score = overlap_score + _source_boost(query, fname)
        if boosted_score <= 0:
            continue

        snippet = content[:1200]
        scored.append({
            "text": snippet,
            "source": fname,
            "score": round(min(0.95, boosted_score), 4),
            "metadata": {"retrieval": "lexical_fallback"},
        })

    scored.sort(key=lambda item: item["score"], reverse=True)
    return scored[:top_k]


def retrieve_dense(query: str, top_k: int = DEFAULT_TOP_K) -> list:
    """
    Dense retrieval: embed query → query ChromaDB → trả về top_k chunks.

    Returns:
        list of {"text": str, "source": str, "score": float, "metadata": dict}
    """
    if not query.strip():
        return []

    try:
        embed = _get_embedding_fn()
        query_embedding = embed(query)
        collection = _get_collection()
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "distances", "metadatas"]
        )

        docs = (results.get("documents") or [[]])[0]
        dists = (results.get("distances") or [[]])[0]
        metas = (results.get("metadatas") or [[]])[0]

        chunks = []
        for doc, dist, meta in zip(docs, dists, metas):
            score = max(0.0, min(1.0, 1 - float(dist)))
            meta = meta or {}
            chunks.append({
                "text": doc,
                "source": meta.get("source", "unknown"),
                "score": round(score, 4),
                "metadata": meta,
            })
        if chunks:
            return chunks

        return _lexical_fallback(query, top_k=top_k)

    except Exception as e:
        print(f"⚠️  Dense retrieval unavailable ({e}). Falling back to lexical retrieval.")
        return _lexical_fallback(query, top_k=top_k)


def run(state: dict) -> dict:
    """
    Worker entry point — gọi từ graph.py.

    Args:
        state: AgentState dict

    Returns:
        Updated AgentState với retrieved_chunks và retrieved_sources
    """
    task = state.get("task", "")
    top_k = state.get("top_k", state.get("retrieval_top_k", DEFAULT_TOP_K))

    state.setdefault("workers_called", [])
    state.setdefault("history", [])

    state["workers_called"].append(WORKER_NAME)

    # Log worker IO (theo contract)
    worker_io = {
        "worker": WORKER_NAME,
        "input": {"task": task, "top_k": top_k},
        "output": None,
        "error": None,
    }

    try:
        chunks = retrieve_dense(task, top_k=top_k)

        sources = list({c["source"] for c in chunks})

        state["retrieved_chunks"] = chunks
        state["retrieved_sources"] = sources

        worker_io["output"] = {
            "chunks_count": len(chunks),
            "sources": sources,
        }
        state["history"].append(
            f"[{WORKER_NAME}] retrieved {len(chunks)} chunks from {sources}"
        )

    except Exception as e:
        worker_io["error"] = {"code": "RETRIEVAL_FAILED", "reason": str(e)}
        state["retrieved_chunks"] = []
        state["retrieved_sources"] = []
        state["history"].append(f"[{WORKER_NAME}] ERROR: {e}")

    # Ghi worker IO vào state để trace
    state.setdefault("worker_io_logs", []).append(worker_io)

    return state


# ─────────────────────────────────────────────
# Test độc lập
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 50)
    print("Retrieval Worker — Standalone Test")
    print("=" * 50)

    test_queries = [
        "SLA ticket P1 là bao lâu?",
        "Điều kiện được hoàn tiền là gì?",
        "Ai phê duyệt cấp quyền Level 3?",
    ]

    for query in test_queries:
        print(f"\n▶ Query: {query}")
        result = run({"task": query})
        chunks = result.get("retrieved_chunks", [])
        print(f"  Retrieved: {len(chunks)} chunks")
        for c in chunks[:2]:
            print(f"    [{c['score']:.3f}] {c['source']}: {c['text'][:80]}...")
        print(f"  Sources: {result.get('retrieved_sources', [])}")

    print("\n✅ retrieval_worker test done.")
