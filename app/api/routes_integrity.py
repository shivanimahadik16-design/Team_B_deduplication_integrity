from fastapi import APIRouter, HTTPException

from app.models.integrity import (
    IntegrityVerifyRequest,
    IntegrityVerifyResponse,
)
from app.services.integrity_service import verify_integrity_service


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
):
    try:
        return verify_integrity_service(
            chunk_hashes=request.chunk_hashes,
            expected_merkle_root=request.expected_merkle_root,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )