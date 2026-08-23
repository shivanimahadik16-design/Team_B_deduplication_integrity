from typing import Any
from uuid import uuid4

from app.dedup.delta import (
    calculate_delta_size,
    calculate_savings_ratio,
)
from app.models.dedup import DedupResult


class IndexVersionMismatchError(Exception):
    """
    Raised when the requested index version does not match
    the currently selected index.
    """

    pass


class DeduplicationEngine:
    """
    Core deduplication engine.

    Responsibilities:
    1. Receive ordered chunks.
    2. Look up each chunk hash in the hash index.
    3. Identify duplicate and unique chunks.
    4. Calculate delta size.
    5. Calculate storage savings.
    6. Produce DedupResult.
    """

    def __init__(self, index):
        self.index = index

    def compute(
        self,
        file_id: str,
        version: int,
        chunks: list[Any],
        algorithm: str = "sha256",
        expected_index_version: str | None = None,
    ) -> DedupResult:

        # ---------------------------------------------
        # 1. Validate index version
        # ---------------------------------------------

        actual_index_version = self.index.index_version

        if (
            expected_index_version is not None
            and expected_index_version != actual_index_version
        ):
            raise IndexVersionMismatchError(
                f"Index version mismatch: "
                f"expected={expected_index_version}, "
                f"actual={actual_index_version}"
            )

        # ---------------------------------------------
        # 2. Process chunks
        # ---------------------------------------------

        unique_chunks = 0
        duplicate_chunks = 0

        unique_chunk_sizes = []

        for chunk in chunks:

            chunk_hash = self._get_chunk_hash(chunk)
            chunk_size = self._get_chunk_size(chunk)

            existing_chunk = self.index.search(chunk_hash)

            if existing_chunk is not None:

                # Existing hash means this chunk
                # can be reused.
                duplicate_chunks += 1

            else:

                # New hash means new data must be stored.
                unique_chunks += 1

                unique_chunk_sizes.append(chunk_size)

                self.index.insert(
                    chunk_hash,
                    chunk,
                )

        # ---------------------------------------------
        # 3. File statistics
        # ---------------------------------------------

        total_chunks = len(chunks)

        original_size = sum(
            self._get_chunk_size(chunk)
            for chunk in chunks
        )

        # ---------------------------------------------
        # 4. Delta size
        # ---------------------------------------------

        delta_size = calculate_delta_size(
            unique_chunk_sizes
        )

        # ---------------------------------------------
        # 5. Savings ratio
        # ---------------------------------------------

        savings_ratio = calculate_savings_ratio(
            original_size,
            delta_size,
        )

        # ---------------------------------------------
        # 6. Create result
        # ---------------------------------------------

        return DedupResult(
            dedup_result_id=str(uuid4()),
            file_id=file_id,
            version=version,

            total_chunks=total_chunks,
            unique_chunks=unique_chunks,
            duplicate_chunks=duplicate_chunks,

            original_size=original_size,
            delta_size=delta_size,

            savings_ratio=savings_ratio,

            algorithm=algorithm,
            index_version=actual_index_version,
        )

    # =================================================
    # Helper methods
    # =================================================

    @staticmethod
    def _get_chunk_hash(chunk: Any) -> str:

        if hasattr(chunk, "hash"):
            chunk_hash = chunk.hash

        elif isinstance(chunk, dict):
            chunk_hash = chunk.get("hash")

        else:
            raise TypeError(
                "Chunk must provide a hash field"
            )

        if not chunk_hash:
            raise ValueError(
                "Chunk hash cannot be empty"
            )

        return str(chunk_hash)

    @staticmethod
    def _get_chunk_size(chunk: Any) -> int:

        if hasattr(chunk, "size"):
            size = chunk.size

        elif isinstance(chunk, dict):
            size = chunk.get("size")

        else:
            raise TypeError(
                "Chunk must provide a size field"
            )

        if size is None:
            raise ValueError(
                "Chunk size is required"
            )

        size = int(size)

        if size < 0:
            raise ValueError(
                "Chunk size cannot be negative"
            )

        return size