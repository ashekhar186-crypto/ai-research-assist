"""
app/vector_store/faiss_store.py
────────────────────────────────
FAISS-based vector store for semantic paper search.

Libraries:
  - faiss-cpu: pip install faiss-cpu
    Facebook AI Similarity Search. Stores text embeddings as vectors
    and performs fast nearest-neighbor search.
  - sentence-transformers: pip install sentence-transformers
    Converts text into numerical vectors (embeddings).
    Model: all-MiniLM-L6-v2 (384 dimensions, fast and accurate)
  - numpy: pip install numpy  (required by FAISS)

HOW VECTOR SEARCH WORKS:
  1. Text → Embedding model → 384-dimension float vector
  2. Vectors stored in FAISS index file on disk
  3. On search: query → vector → find N nearest vectors → return texts
  4. "Nearest" = semantically similar (not keyword match!)
"""

import os
import json
import pickle
import numpy as np
from typing import List, Dict, Any, Optional, Tuple

import faiss
from sentence_transformers import SentenceTransformer

from app.core.config import get_settings

settings = get_settings()


class FAISSVectorStore:
    """
    FAISS vector store with a simple metadata store (JSON file).
    Each 'paper' gets its own namespace (index) so results can be
    filtered per paper or per project.
    """

    def __init__(self):
        self.model = SentenceTransformer(settings.EMBEDDING_MODEL)
        self.dimension = settings.EMBEDDING_DIMENSION
        self.index_path = settings.FAISS_INDEX_PATH
        os.makedirs(self.index_path, exist_ok=True)

        # Global index holds ALL papers' chunks
        self.global_index_file = os.path.join(self.index_path, "global.index")
        self.metadata_file = os.path.join(self.index_path, "metadata.json")

        # Load or create the FAISS index
        self._index = self._load_or_create_index()
        self._metadata: List[Dict] = self._load_metadata()

    # ── Index Management ──────────────────────────────────────────────────────

    def _load_or_create_index(self) -> faiss.IndexFlatL2:
        """Load existing FAISS index from disk, or create a new one."""
        if os.path.exists(self.global_index_file):
            return faiss.read_index(self.global_index_file)
        # IndexFlatL2: exact L2 (Euclidean) distance search
        # For production with millions of vectors, use IndexIVFFlat instead
        return faiss.IndexFlatL2(self.dimension)

    def _load_metadata(self) -> List[Dict]:
        """Load metadata JSON (parallel array to FAISS vectors)."""
        if os.path.exists(self.metadata_file):
            with open(self.metadata_file, "r") as f:
                return json.load(f)
        return []

    def _save_index(self):
        """Persist FAISS index and metadata to disk."""
        faiss.write_index(self._index, self.global_index_file)
        with open(self.metadata_file, "w") as f:
            json.dump(self._metadata, f)

    # ── Core Operations ───────────────────────────────────────────────────────

    def add_texts(
        self,
        texts: List[str],
        paper_id: str,
        paper_title: str = "",
        chunk_metadata: Optional[List[Dict]] = None,
    ) -> List[int]:
        """
        Embed a list of text chunks and add them to the FAISS index.

        Args:
            texts: List of text chunks to embed
            paper_id: UUID of the paper these chunks belong to
            paper_title: Paper title for metadata
            chunk_metadata: Optional extra metadata per chunk

        Returns:
            List of integer IDs assigned by FAISS
        """
        if not texts:
            return []

        # Convert texts to embedding vectors
        # model.encode returns numpy array of shape (N, dimension)
        embeddings = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=False)

        # FAISS requires float32
        embeddings = embeddings.astype(np.float32)

        # Add to index (FAISS auto-assigns integer IDs starting from 0)
        start_id = self._index.ntotal
        self._index.add(embeddings)

        # Store metadata for each chunk (parallel to FAISS vectors)
        for i, text in enumerate(texts):
            meta = {
                "faiss_id": start_id + i,
                "paper_id": paper_id,
                "paper_title": paper_title,
                "text": text,
                "chunk_index": i,
            }
            if chunk_metadata and i < len(chunk_metadata):
                meta.update(chunk_metadata[i])
            self._metadata.append(meta)

        self._save_index()
        return list(range(start_id, start_id + len(texts)))

    def search(
        self,
        query: str,
        top_k: int = 10,
        paper_id: Optional[str] = None,
        project_paper_ids: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Semantic search: find the top_k most similar chunks to query.

        Args:
            query: Natural language search query
            top_k: Number of results to return
            paper_id: If set, only return chunks from this paper
            project_paper_ids: If set, only return chunks from these papers

        Returns:
            List of dicts with keys: text, paper_id, paper_title, score, faiss_id
        """
        if self._index.ntotal == 0:
            return []

        # Embed the query
        query_vector = self.model.encode([query], convert_to_numpy=True).astype(np.float32)

        # Search FAISS — returns (distances, indices) arrays of shape (1, top_k)
        # We over-fetch (top_k * 5) to allow filtering by paper_id
        fetch_k = min(top_k * 5, self._index.ntotal)
        distances, indices = self._index.search(query_vector, fetch_k)

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx == -1:   # FAISS returns -1 for empty slots
                continue
            if idx >= len(self._metadata):
                continue

            meta = self._metadata[idx]

            # Apply filters
            if paper_id and meta.get("paper_id") != paper_id:
                continue
            if project_paper_ids and meta.get("paper_id") not in project_paper_ids:
                continue

            results.append({
                "text": meta["text"],
                "paper_id": meta["paper_id"],
                "paper_title": meta.get("paper_title", ""),
                "chunk_index": meta.get("chunk_index", 0),
                "score": float(dist),          # Lower L2 distance = more similar
                "faiss_id": int(idx),
            })

            if len(results) >= top_k:
                break

        return results

    def delete_paper(self, paper_id: str):
        """
        Remove all chunks for a paper from the metadata.
        Note: FAISS IndexFlatL2 doesn't support removal, so we mark
        as deleted and rebuild the index periodically.
        """
        self._metadata = [m for m in self._metadata if m.get("paper_id") != paper_id]
        self._save_index()

    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 100) -> List[str]:
        """
        Split a long text into overlapping chunks for embedding.
        Overlap ensures context isn't lost at chunk boundaries.

        Args:
            text: Input text
            chunk_size: Characters per chunk
            overlap: Characters of overlap between adjacent chunks

        Returns:
            List of text chunk strings
        """
        if len(text) <= chunk_size:
            return [text]

        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk.strip())
            start += chunk_size - overlap

        return [c for c in chunks if len(c) > 50]  # Filter tiny chunks


# ── Singleton Instance ────────────────────────────────────────────────────────
_vector_store: Optional[FAISSVectorStore] = None


def get_vector_store() -> FAISSVectorStore:
    """Returns the singleton FAISSVectorStore. Thread-safe for single process."""
    global _vector_store
    if _vector_store is None:
        _vector_store = FAISSVectorStore()
    return _vector_store