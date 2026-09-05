from pydantic import BaseModel, Field


class IntegrityVerifyRequest(BaseModel):
    chunk_hashes: list[str] = Field(
        ...,
        min_length=1,
        description="Ordered SHA-256 hashes of the file chunks"
    )
    expected_merkle_root: str = Field(
        ...,
        min_length=64,
        max_length=64,
        description="Original Merkle root"
    )
    verification_algorithm: str = Field(
        default="merkle-tree",
        pattern="^(merkle-tree|checksum)$",
    )
    expected_chunk_hashes: list[str] | None = None
    benchmark_size_bytes: int = Field(default=0, ge=0)
    repetitions: int = Field(default=1, ge=1, le=1000)


class IntegrityVerifyResponse(BaseModel):
    merkle_root: str
    verified: bool
    verified_chunks: list[int]
    corrupted_chunks: list[int]
    verification_latency: float
    algorithm: str
    time_complexity: str = "O(n)"
    space_complexity: str = "O(n)"
    benchmark: dict = {}
    data: dict | None = None
    meta: dict | None = None