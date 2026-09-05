from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from app.chunking.fixed import fixed_size_chunks
from app.dedup.engine import (
    DeduplicationEngine,
    IndexVersionMismatchError,
)
from app.index.hashmap_index import HashMapIndex
from app.hashing.hasher import Hasher
from app.api.contracts import success_envelope


router = APIRouter(
    prefix="/api/v1/dedup",
    tags=["Deduplication"],
)


dedup_results: dict[str, dict] = {}


class DedupRequest(BaseModel):
    file_id: str
    version: int = 1
    file_path: str | None = None
    chunk_hashes: list[str] | None = None
    chunk_size: int = 4096
    expected_index_version: str | None = None
    previous_version_reference: str | None = None
    optimization_metric: str = "minimize_delta"
    hash_algorithm: str = "sha256"


# Create the index once while the server is running.
# This allows duplicate chunks to be detected across requests.
index = HashMapIndex()

dedup_engine = DeduplicationEngine(index)


@router.post("/")
@router.post("/compute")
def deduplicate_file(
    request: DedupRequest,
    x_correlation_id: str | None = Header(default=None),
):
    try:
        if request.optimization_metric not in {
            "minimize_delta",
            "maximize_compression",
            "balanced",
        }:
            raise ValueError("unsupported optimization_metric")

        hasher = Hasher(request.hash_algorithm)

        if request.file_path:
            chunks = fixed_size_chunks(
                request.file_path,
                request.chunk_size,
            )
            for chunk in chunks:
                chunk["hash"] = hasher.hash(chunk["data"])
        elif request.chunk_hashes:
            chunks = [
                {
                    "chunk_id": f"C{idx + 1:03d}",
                    "hash": chash,
                    "size": request.chunk_size,
                }
                for idx, chash in enumerate(request.chunk_hashes)
            ]
        else:
            raise ValueError("Either file_path or chunk_hashes must be provided")

        # Run deduplication
        result = dedup_engine.compute(
            file_id=request.file_id,
            version=request.version,
            chunks=chunks,
            algorithm=request.hash_algorithm,
            expected_index_version=request.expected_index_version,
            previous_version_reference=request.previous_version_reference,
            optimization_metric=request.optimization_metric,
        )

        result_data = result.model_dump()
        result_data["previous_version_reference"] = request.previous_version_reference
        result_data["optimization_metric"] = request.optimization_metric
        dedup_results[result.dedup_result_id] = result_data
        return success_envelope(result_data, x_correlation_id)

    except IndexVersionMismatchError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        )

    except (FileNotFoundError, ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@router.get("/{result_id}")
def get_dedup_result(
    result_id: str,
    x_correlation_id: str | None = Header(default=None),
):
    result = dedup_results.get(result_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Deduplication result not found")

    return success_envelope(result, x_correlation_id)