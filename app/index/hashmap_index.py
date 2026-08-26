"""
Hash-map based chunk index for Team B.

The index maps a chunk hash to its stored chunk reference.
"""

from time import perf_counter_ns
from typing import Optional


class HashMapIndex:
    """Hash-map implementation of the Team B chunk hash index."""

    INDEX_VERSION = "v1"

    def __init__(self) -> None:
        self._index: dict[str, str] = {}

    def insert(self, chunk_hash: str, chunk_ref: str) -> None:
        """Insert or update a chunk-hash mapping."""
        if not isinstance(chunk_hash, str) or not chunk_hash:
            raise ValueError("chunk_hash must be a non-empty string")

        if not isinstance(chunk_ref, str) or not chunk_ref:
            raise ValueError("chunk_ref must be a non-empty string")

        self._index[chunk_hash] = chunk_ref

    def lookup(
        self,
        chunk_hash: str,
        index_version: str = INDEX_VERSION,
    ) -> dict:
        """
        Look up a chunk by its hash.

        Returns:
            existing_chunk_ref: matching chunk reference or None
            lookup_time_us: measured lookup duration in microseconds
            cache_hit: True when the hash exists
            index_version: active index version
        """
        if index_version != self.INDEX_VERSION:
            raise ValueError(
                f"INDEX_VERSION_MISMATCH: expected "
                f"{self.INDEX_VERSION}, received {index_version}"
            )

        start = perf_counter_ns()
        chunk_ref: Optional[str] = self._index.get(chunk_hash)
        elapsed_ns = perf_counter_ns() - start

        return {
            "existing_chunk_ref": chunk_ref,
            "lookup_time_us": elapsed_ns / 1000,
            "cache_hit": chunk_ref is not None,
            "index_version": self.INDEX_VERSION,
        }

    def contains(self, chunk_hash: str) -> bool:
        """Return True when a hash exists in the index."""
        return chunk_hash in self._index

    def remove(self, chunk_hash: str) -> bool:
        """Remove a hash and return whether it existed."""
        if chunk_hash not in self._index:
            return False

        del self._index[chunk_hash]
        return True

    def size(self) -> int:
        """Return the number of indexed chunks."""
        return len(self._index)

    def clear(self) -> None:
        """Remove all entries from the index."""
        self._index.clear()

    def get_stats(self) -> dict:
        """Return basic index statistics."""
        return {
            "index_version": self.INDEX_VERSION,
            "entry_count": len(self._index),
        }