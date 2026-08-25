import hashlib


def content_defined_chunks(
    file_path,
    min_size=2048,
    avg_size=4096,
    max_size=8192
):
    """
    Split a file into content-defined chunks.

    Chunk boundaries are determined using a rolling hash,
    rather than a fixed number of bytes.
    """

    with open(file_path, "rb") as file:
        data = file.read()

    chunks = []
    offset = 0
    chunk_start = 0

    # Mask controls the average chunk size.
    mask = avg_size - 1

    for i in range(len(data)):
        current_size = i - chunk_start + 1

        # Do not create a boundary before minimum size.
        if current_size < min_size:
            continue

        # Force a boundary at maximum size.
        if current_size >= max_size:
            chunk_data = data[chunk_start:i + 1]

            chunks.append({
                "chunk_id": f"C{len(chunks) + 1:03d}",
                "offset": chunk_start,
                "size": len(chunk_data),
                "hash": hashlib.sha256(chunk_data).hexdigest()
            })

            chunk_start = i + 1
            continue

        # Simple rolling/content-dependent hash.
        window = data[max(chunk_start, i - 63):i + 1]

        hash_value = 0
        for byte in window:
            hash_value = ((hash_value << 5) - hash_value + byte) & 0xFFFFFFFF

        # Content determines whether a boundary occurs.
        if (hash_value & mask) == 0:
            chunk_data = data[chunk_start:i + 1]

            chunks.append({
                "chunk_id": f"C{len(chunks) + 1:03d}",
                "offset": chunk_start,
                "size": len(chunk_data),
                "hash": hashlib.sha256(chunk_data).hexdigest()
            })

            chunk_start = i + 1

    # Store remaining data as the final chunk.
    if chunk_start < len(data):
        chunk_data = data[chunk_start:]

        chunks.append({
            "chunk_id": f"C{len(chunks) + 1:03d}",
            "offset": chunk_start,
            "size": len(chunk_data),
            "hash": hashlib.sha256(chunk_data).hexdigest()
        })

    return chunks


if __name__ == "__main__":
    file_path = "test_files/sample.txt"

    chunks = content_defined_chunks(file_path)

    print("Content-Defined Chunking")
    print("=" * 60)
    print(f"File       : {file_path}")
    print(f"Min size   : 2048 bytes (2 KB)")
    print(f"Avg size   : 4096 bytes (4 KB)")
    print(f"Max size   : 8192 bytes (8 KB)")
    print(f"Total chunks: {len(chunks)}")
    print("=" * 60)

    for chunk in chunks:
        print(
            f"{chunk['chunk_id']} | "
            f"Offset: {chunk['offset']} | "
            f"Size: {chunk['size']} bytes"
        )