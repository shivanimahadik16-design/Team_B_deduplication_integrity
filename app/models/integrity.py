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


class IntegrityVerifyResponse(BaseModel):
    merkle_root: str
    verified: bool
    verified_chunks: list[int]
    corrupted_chunks: list[int]
    verification_latency: float
    algorithm: str