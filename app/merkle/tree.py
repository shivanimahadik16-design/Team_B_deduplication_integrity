import hashlib


def sha256(data: str) -> str:
    """Return the SHA-256 hexadecimal digest of a string."""
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def build_merkle_root(chunk_hashes: list[str]) -> str:
    """
    Build a Merkle tree from ordered chunk hashes.

    If a level has an odd number of hashes,
    the last hash is duplicated.
    """
    if not chunk_hashes:
        raise ValueError("chunk_hashes cannot be empty")

    current_level = chunk_hashes.copy()

    while len(current_level) > 1:
        if len(current_level) % 2 != 0:
            current_level.append(current_level[-1])

        next_level = []

        for i in range(0, len(current_level), 2):
            combined = current_level[i] + current_level[i + 1]
            parent_hash = sha256(combined)
            next_level.append(parent_hash)

        current_level = next_level

    return current_level[0]