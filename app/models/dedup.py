from pydantic import BaseModel, Field


class DedupResult(BaseModel):
    """
    Result produced by the deduplication engine.
    """

    dedup_result_id: str
    file_id: str
    version: int

    total_chunks: int = Field(ge=0)
    unique_chunks: int = Field(ge=0)
    duplicate_chunks: int = Field(ge=0)

    original_size: int = Field(ge=0)
    delta_size: int = Field(ge=0)

    savings_ratio: float = Field(ge=0.0, le=1.0)

    algorithm: str
    index_version: str