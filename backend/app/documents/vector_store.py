"""
BUDDY AI 2.0 — Local Persistent Vector Store & Semantic Embeddings

Architecture & Vector Engine:
  - Zero-Dependency Multilingual Vectorizer:
      - Uses deterministic subword (3-gram and 4-gram) feature hashing to project text into a 128-dimensional space.
      - Provides seamless out-of-the-box support for English, Hindi, and Marathi (Devanagari script)
        without requiring external cloud APIs or bulky PyTorch models.
  - Cosine Similarity Dot-Product Search:
      - Computes L2-normalized dense embeddings, reducing cosine similarity calculations to high-speed numpy dot products.
  - Persistent SQLite Backing:
      - Stores serialized float vectors directly in SQLite's `chunk_vectors` table, ensuring instantaneous
        cold boots without re-embedding files on server restart.
  - Index Synchronization:
      - `rebuild_all_indexes` simultaneously updates the SQLite FTS5 index and dense vector store from approved chunks.
"""

import math
import json
import logging
import zlib
from typing import List, Dict, Any, Optional
import numpy as np

from ..database.repository import repo

logger = logging.getLogger("buddy.vector_store")

VECTOR_DIMENSIONS = 128


class LocalMultilingualVectorizer:
    """
    Fast, completely offline, zero-dependency multilingual text vectorizer.
    Generates normalized dense embedding vectors using subword n-grams,
    supporting English, Hindi, and Marathi (Devanagari script).
    """
    def __init__(self, dimensions: int = VECTOR_DIMENSIONS):
        """
        Initializes the vectorizer with fixed target dimensions.

        Args:
            dimensions: Dimensionality of output embedding space (default: 128).
        """
        self.dimensions = dimensions

    def embed_text(self, text: str) -> List[float]:
        """
        Generates dense vector embeddings using word and character n-gram hashing.
        Applies L2 normalization to enable fast cosine similarity via dot product.

        Args:
            text: Plain text passage or search query.

        Returns:
            List[float]: L2-normalized float embedding list.
        """
        vec = np.zeros(self.dimensions, dtype=np.float32)
        if not text or not text.strip():
            return vec.tolist()

        clean = text.lower().strip()
        tokens = clean.split()

        # Word-level deterministic hashing
        for token in tokens:
            h = zlib.crc32(token.encode("utf-8")) % self.dimensions
            vec[h] += 1.5

        # Subword 3-gram and 4-gram deterministic hashing for robust multilingual semantic capture
        for n in (3, 4):
            for i in range(len(clean) - n + 1):
                ngram = clean[i:i + n]
                h = zlib.crc32(ngram.encode("utf-8")) % self.dimensions
                vec[h] += 0.5

        # L2 Normalization
        norm = np.linalg.norm(vec)
        if norm > 1e-6:
            vec = vec / norm
        return vec.tolist()

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generates dense vector embeddings for multiple text passages in a batch.

        Args:
            texts: List of text passages to embed.

        Returns:
            List[List[float]]: List of L2-normalized dense embedding vectors.
        """
        return [self.embed_text(t) for t in texts]


class LocalVectorStore:
    """
    Lightweight, persistent local vector store backed by SQLite chunk_vectors.
    Rebuildable from approved documents and chunks at any time.
    """
    def __init__(self):
        self.vectorizer = LocalMultilingualVectorizer(dimensions=VECTOR_DIMENSIONS)
        self.indexing_errors: List[str] = []

    def index_chunk(self, chunk_id: int, content: str) -> bool:
        """
        Computes the dense embedding vector for a document chunk and persists it to SQLite.

        Args:
            chunk_id: Unique relational ID of the target document chunk.
            content: Raw textual content of the chunk.

        Returns:
            bool: True if vector was successfully computed and persisted.
        """
        try:
            embedding = self.vectorizer.embed_text(content)
            repo.save_chunk_vector(chunk_id, embedding, model_name="local_multilingual_vectorizer")
            return True
        except Exception as e:
            msg = f"Failed to index chunk {chunk_id}: {str(e)}"
            logger.warning(msg)
            self.indexing_errors.append(msg)
            return False

    def index_document_chunks(self, document_name: str) -> int:
        """
        Indexes all text chunks belonging to a specific document.

        Args:
            document_name: Filename of the target document.

        Returns:
            int: Number of chunks successfully embedded and indexed.
        """
        with repo.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, content FROM document_chunks WHERE document_name = ?", (document_name,))
            rows = cursor.fetchall()

        count = 0
        for r in rows:
            if self.index_chunk(r["id"], r["content"]):
                count += 1
        return count

    def rebuild_all_indexes(self) -> Dict[str, Any]:
        """
        Rebuilds both full-text (FTS5) and semantic vector indexes from scratch
        using approved documents and chunks currently stored in the database.

        Returns:
            Dict[str, Any]: Rebuilding summary report with indexed chunk counts and error logs.
        """
        self.indexing_errors.clear()
        # 1. Sync FTS5
        fts_count = repo.sync_fts_index()

        # 2. Re-index all chunk vectors
        with repo.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, content FROM document_chunks")
            rows = cursor.fetchall()

        vector_count = 0
        for r in rows:
            if self.index_chunk(r["id"], r["content"]):
                vector_count += 1

        return {
            "fts_indexed_chunks": fts_count,
            "vector_indexed_chunks": vector_count,
            "errors": list(self.indexing_errors),
            "status": "success" if not self.indexing_errors else "partial_success"
        }

    def search(self, query: str, top_k: int = 5, threshold: float = 0.15) -> List[Dict[str, Any]]:
        """
        Performs dense vector similarity search across all indexed chunks using numpy dot product.

        Args:
            query: User's search query or topic.
            top_k: Maximum number of closest candidate passages to return (default: 5).
            threshold: Minimum cosine similarity score threshold (default: 0.15).

        Returns:
            List[Dict[str, Any]]: Ranked list of matching chunks with similarity scores and metadata.
        """
        q_vec = np.array(self.vectorizer.embed_text(query), dtype=np.float32)
        q_norm = np.linalg.norm(q_vec)
        if q_norm < 1e-6:
            return []

        all_vectors = repo.get_all_chunk_vectors()
        if not all_vectors:
            return []

        scored: List[Dict[str, Any]] = []
        for item in all_vectors:
            try:
                emb = np.array(json.loads(item["embedding_json"]), dtype=np.float32)
                sim = float(np.dot(q_vec, emb))
                if sim >= threshold:
                    scored.append({
                        "chunk_id": item["chunk_id"],
                        "source": item["document_name"],
                        "page": item["page_number"],
                        "section": item["section_title"],
                        "content": item["content"],
                        "similarity_score": round(sim, 3)
                    })
            except Exception:
                continue

        scored.sort(key=lambda x: x["similarity_score"], reverse=True)
        return scored[:top_k]

    def get_stats(self) -> Dict[str, Any]:
        """
        Retrieves operational statistics about the vector store.

        Returns:
            Dict[str, Any]: Metadata containing vector dimensions, indexed chunk count, and model name.
        """
        all_vectors = repo.get_all_chunk_vectors()
        return {
            "dimensions": self.vectorizer.dimensions,
            "total_vectors": len(all_vectors),
            "model_name": "local_multilingual_vectorizer",
            "recent_errors": len(self.indexing_errors)
        }

    def has_indexed_vectors(self) -> bool:
        """
        Fast check indicating whether any chunk vectors are currently indexed in the store.

        Returns:
            bool: True if at least one vector exists in the store, False otherwise.
        """
        all_vectors = repo.get_all_chunk_vectors()
        return len(all_vectors) > 0

    def clear_indexing_errors(self) -> int:
        """
        Clears the recorded in-memory indexing errors list and returns the cleared count.

        Returns:
            int: Number of cleared error entries.
        """
        count = len(self.indexing_errors)
        self.indexing_errors.clear()
        return count


def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """
    Calculates cosine similarity between two dense float vectors.

    Args:
        vec_a: First float vector list.
        vec_b: Second float vector list.

    Returns:
        float: Cosine similarity in range [-1.0, 1.0], or 0.0 if zero-magnitude.
    """
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0
    arr_a = np.array(vec_a, dtype=np.float32)
    arr_b = np.array(vec_b, dtype=np.float32)
    norm_a = float(np.linalg.norm(arr_a))
    norm_b = float(np.linalg.norm(arr_b))
    if norm_a < 1e-6 or norm_b < 1e-6:
        return 0.0
    return float(np.dot(arr_a, arr_b) / (norm_a * norm_b))


def is_normalized_vector(vec: List[float], tolerance: float = 1e-3) -> bool:
    """
    Validates whether a vector is L2-normalized (magnitude approximately 1.0).

    Args:
        vec: Float vector list.
        tolerance: Allowed deviation from 1.0 (default: 0.001).

    Returns:
        bool: True if Euclidean norm is within tolerance of 1.0.
    """
    if not vec:
        return False
    norm = float(np.linalg.norm(np.array(vec, dtype=np.float32)))
    return abs(norm - 1.0) <= tolerance


vector_store = LocalVectorStore()

