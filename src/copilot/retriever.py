from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any, Tuple

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer


@dataclass
class RetrievedChunk:
    text: str
    source: str
    score: float


def _chunk_text(text: str, chunk_size: int = 900, overlap: int = 120) -> List[str]:
    text = " ".join(text.split())
    if not text:
        return []
    chunks = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + chunk_size, n)
        chunks.append(text[start:end])
        if end == n:
            break
        start = max(0, end - overlap)
    return chunks


class ContextRetriever:
    """
    RAG retriever that indexes ONLY context/*.md files.
    Uses ChromaDB for persistence.
    """

    def __init__(
        self,
        context_dir: str = "context",
        persist_dir: str = ".chroma_context",
        collection_name: str = "copilot_context",
        embed_model: str = "sentence-transformers/all-MiniLM-L6-v2",
    ):
        self.context_dir = Path(context_dir)
        self.persist_dir = Path(persist_dir)
        self.collection_name = collection_name
        self.embedder = SentenceTransformer(embed_model)

        self.client = chromadb.PersistentClient(
            path=str(self.persist_dir),
            settings=Settings(anonymized_telemetry=False),
        )
        self.col = self.client.get_or_create_collection(name=self.collection_name)

    def build_or_refresh_index(self) -> int:
        if not self.context_dir.exists():
            raise FileNotFoundError(f"Missing context directory: {self.context_dir}")

        # Simple strategy: clear and rebuild (safe for small context packs)
        try:
            self.client.delete_collection(self.collection_name)
        except Exception:
            pass
        self.col = self.client.get_or_create_collection(name=self.collection_name)

        ids: List[str] = []
        docs: List[str] = []
        metas: List[Dict[str, Any]] = []

        for fp in sorted(self.context_dir.glob("*.md")):
            raw = fp.read_text(encoding="utf-8", errors="ignore")
            chunks = _chunk_text(raw, chunk_size=1400, overlap=200)
            for i, ch in enumerate(chunks):
                ids.append(f"{fp.name}::chunk{i}")
                docs.append(ch)
                metas.append({"source": fp.name, "chunk_id": i})

        if not docs:
            raise ValueError(f"No .md files found (or empty) in {self.context_dir}")

        embeddings = self.embedder.encode(docs, normalize_embeddings=True).tolist()

        self.col.add(ids=ids, documents=docs, metadatas=metas, embeddings=embeddings)
        return len(docs)

    def retrieve(self, question: str, top_k: int = 3) -> List[RetrievedChunk]:
        q_emb = self.embedder.encode([question], normalize_embeddings=True).tolist()

        res = self.col.query(
            query_embeddings=q_emb,
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

        out: List[RetrievedChunk] = []
        # Chroma returns distances; for cosine, smaller distance is more similar.
        docs = res.get("documents", [[]])[0]
        metas = res.get("metadatas", [[]])[0]
        dists = res.get("distances", [[]])[0]

        for doc, meta, dist in zip(docs, metas, dists):
            src = (meta or {}).get("source", "unknown")
            # Convert distance to a "score-like" value (roughly)
            score = float(1.0 - dist) if dist is not None else 0.0
            out.append(RetrievedChunk(text=doc, source=src, score=score))

        return out
