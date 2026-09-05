from fastapi import APIRouter, Header, HTTPException

from app.models.integrity import (
    IntegrityVerifyRequest,
    IntegrityVerifyResponse,
)
from app.services.integrity_service import verify_integrity_service
from app.api.contracts import success_envelope


router = APIRouter(
    prefix="/api/v1/integrity",
    tags=["Integrity"],
)


@router.post(
    "/verify",
    response_model=IntegrityVerifyResponse,
)
def verify_integrity_endpoint(
    request: IntegrityVerifyRequest,
    x_correlation_id: str | None = Header(default=None),
):
    try:
        response = verify_integrity_service(
            chunk_hashes=request.chunk_hashes,
            expected_merkle_root=request.expected_merkle_root,
            verification_algorithm=request.verification_algorithm,
            expected_chunk_hashes=request.expected_chunk_hashes,
            repetitions=request.repetitions,
            benchmark_size_bytes=request.benchmark_size_bytes,
        )
        return success_envelope(response, x_correlation_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )