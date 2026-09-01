import time

from app.merkle.tree import build_merkle_root


def verify_integrity(
    chunk_hashes: list[str],
    expected_merkle_root: str
) -> dict:
    """
    Verify the integrity of ordered chunk hashes.

    Returns the calculated Merkle root, verification status,
    verified chunks, corrupted chunks, latency, and algorithm.
    """

    start_time = time.perf_counter()

    if not chunk_hashes:
        raise ValueError("chunk_hashes cannot be empty")

    if not expected_merkle_root:
        raise ValueError("expected_merkle_root cannot be empty")

    current_merkle_root = build_merkle_root(chunk_hashes)

    is_verified = current_merkle_root == expected_merkle_root

    if is_verified:
        verified_chunks = list(range(len(chunk_hashes)))
        corrupted_chunks = []
    else:
        verified_chunks = []
        corrupted_chunks = list(range(len(chunk_hashes)))

    verification_latency = time.perf_counter() - start_time

    return {
        "merkle_root": current_merkle_root,
        "verified": is_verified,
        "verified_chunks": verified_chunks,
        "corrupted_chunks": corrupted_chunks,
        "verification_latency": verification_latency,
        "algorithm": "SHA-256 Merkle Tree"
    }