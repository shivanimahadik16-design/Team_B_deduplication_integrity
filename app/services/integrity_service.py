from app.verification.verifier import verify_integrity


def verify_integrity_service(
    chunk_hashes: list[str],
    expected_merkle_root: str
) -> dict:
    """
    Service layer for integrity verification.

    Keeps the API route separate from the verification algorithm.
    """
    return verify_integrity(
        chunk_hashes=chunk_hashes,
        expected_merkle_root=expected_merkle_root
    )