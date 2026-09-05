# Team B API Specification & Integration Reference

This document provides the full API specification for **Team B (Deduplication & Integrity Engine)** in the APNILEAP Smart File Backup System.

---

## Global Headers & Protocols

All requests to Team B accept or return the following standard headers:

| Header | Type | Description | Required |
| :--- | :--- | :--- | :---: |
| `Authorization` | String | `Bearer <token>` service credential when `TEAM_B_API_TOKEN` is set. | Optional (unless token configured) |
| `X-Correlation-ID` | String / UUID | Correlation ID for distributed tracing across Teams A, B, C, and D. | Recommended |
| `X-API-Version` | String | Emitted by Team B on all responses (`v1`). | Response |
| `Content-Type` | String | `application/json; charset=utf-8`. | Yes |

### Response Envelopes

#### Standard Success Envelope
```json
{
  "data": {
    "key": "value"
  },
  "meta": {
    "correlation_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
    "api_version": "v1"
  }
}
```

#### Standard Error Envelope
```json
{
  "error": {
    "code": "HTTP_400",
    "message": "Detailed error message",
    "details": []
  },
  "meta": {
    "correlation_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d"
  }
}
```

---

## 1. Chunking Endpoints

### 1.1 Compute File Chunks
- **Path**: `POST /api/v1/chunks/`
- **Purpose**: Divides a local file into fixed-size or content-defined chunks, computing deterministic hashes.
- **Request Body**:
  ```json
  {
    "chunk_request_id": "req-001",
    "file_id": "file-101",
    "version_ref": "v1.0",
    "file_path": "test_files/sample.txt",
    "chunk_size": 4096,
    "chunk_boundaries": "content-defined",
    "hash_algorithm": "sha256"
  }
  ```
- **Response (`200 OK`)**:
  ```json
  {
    "chunk_request_id": "req-001",
    "file_id": "file-101",
    "version_ref": "v1.0",
    "file_path": "test_files/sample.txt",
    "method": "content_defined",
    "chunk_boundaries": "content_defined",
    "chunk_version": "v1",
    "total_chunks": 5,
    "chunks": [
      {
        "chunk_id": "a90f1d3e-...",
        "chunk_number": 1,
        "offset": 0,
        "size": 4096,
        "hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
      }
    ],
    "coverage_summary": {
      "file_size_bytes": 20000,
      "average_chunk_size": 4000.0,
      "covered_percent": 100.0
    },
    "validation_errors": [],
    "hash_algorithm": "sha256",
    "data": { ... },
    "meta": {
      "correlation_id": "...",
      "api_version": "v1"
    }
  }
  ```

---

### 1.2 Register Chunk (Internal)
- **Path**: `PUT /internal/v1/chunks/{chunkId}`
- **Consumer**: Team C (authoritative metadata manager) / Admin
- **Purpose**: Persist chunk registration in Team B's chunk repository and update the active hash index.
- **Request Body**:
  ```json
  {
    "file_id": "file-101",
    "version_id": "v1",
    "chunk_index": 0,
    "hash_value": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "size_bytes": 4096,
    "metadata": { "author": "system" },
    "expiry_seconds": 3600.0
  }
  ```
- **Response (`200 OK`)**:
  ```json
  {
    "chunk_id": "C001",
    "registered_at": "2026-09-05T17:28:47+00:00",
    "chunk_version": "v1",
    "correlation_id": "...",
    "data": { ... },
    "meta": { "correlation_id": "...", "api_version": "v1" }
  }
  ```

---

### 1.3 Get Chunk Index Coverage
- **Path**: `GET /api/v1/chunks/index`
- **Consumer**: Team D (Dashboard)
- **Purpose**: Retrieve chunk repository summary and coverage status.
- **Response (`200 OK`)**:
  ```json
  {
    "total_chunks": 42,
    "unique_chunks": 42,
    "duplicate_chunks": 0,
    "coverage_percent": 100.0,
    "total_size_bytes": 172032,
    "chunk_version": "v1",
    "chunks": [ ... ],
    "data": { ... },
    "meta": { "correlation_id": "...", "api_version": "v1" }
  }
  ```

---

## 2. Deduplication Endpoints

### 2.1 Compute Deduplication
- **Path**: `POST /api/v1/dedup/compute` (also accessible at `/api/v1/dedup/`)
- **Consumer**: Team C / Team D
- **Purpose**: Chunk the file, compare hashes against live index, calculate delta and savings ratio, and compute Merkle root.
- **Request Body**:
  ```json
  {
    "file_id": "file-101",
    "version": 1,
    "file_path": "test_files/sample.txt",
    "chunk_size": 4096,
    "expected_index_version": "v1",
    "previous_version_reference": "v0.9",
    "optimization_metric": "minimize_delta",
    "hash_algorithm": "sha256"
  }
  ```
- **Response (`200 OK`)**:
  ```json
  {
    "dedup_result_id": "b7ecf522-8302-4f32-840a-ff040529d660",
    "file_id": "file-101",
    "version": 1,
    "total_chunks": 5,
    "unique_chunks": 2,
    "duplicate_chunks": 3,
    "original_size": 20000,
    "delta_size": 8000,
    "savings_ratio": 0.60,
    "algorithm": "sha256",
    "index_version": "v1",
    "algorithm_version": "v1",
    "merkle_root": "6b86b273ff34fce19d6b804eff5a3f5747ada4eaa22f1d49c01e52ddb7875b4b",
    "previous_version_reference": "v0.9",
    "optimization_metric": "minimize_delta",
    "data": { ... },
    "meta": { "correlation_id": "...", "api_version": "v1" }
  }
  ```
- **Errors**:
  - `409 Conflict`: Index version mismatch (`INDEX_VERSION_MISMATCH`).
  - `400 Bad Request`: File not found or unsupported `optimization_metric`.

---

### 2.2 Get Deduplication Result
- **Path**: `GET /api/v1/dedup/{resultId}`
- **Consumer**: Team D
- **Purpose**: Fetch historical deduplication results by `resultId`.
- **Response (`200 OK`)**: Returns the previously computed `DedupResult`.
- **Errors**: `404 Not Found` if `resultId` does not exist.

---

## 3. Index & Cache Endpoints (Internal)

### 3.1 Lookup Hash Index
- **Path**: `GET /internal/v1/hash-index/{key}`
- **Consumer**: Team C / Test harness
- **Purpose**: Directly query the active chunk index for a hash digest.
- **Response (`200 OK`)**:
  ```json
  {
    "existing_chunk_ref": "C001",
    "lookup_time_us": 0.52,
    "cache_hit": true,
    "index_version": "v1",
    "index_statistics": {
      "index_version": "v1",
      "entry_count": 100,
      "cache_hits": 450,
      "cache_misses": 50,
      "cache_hit_rate": 0.90
    },
    "data": { ... },
    "meta": { "correlation_id": "...", "api_version": "v1" }
  }
  ```

---

### 3.2 Invalidate Hash Cache
- **Path**: `POST /internal/v1/hash-cache/invalidate`
- **Consumer**: Team C / Admin
- **Purpose**: Invalidate stale hash-index entries either selectively or in bulk.
- **Request Body**:
  ```json
  {
    "keys": ["hash_1", "hash_2"]
  }
  ```
  *(Omit `keys` or pass `null` to clear the entire cache)*
- **Response (`200 OK`)**:
  ```json
  {
    "invalidated_count": 2,
    "invalidation_time_ms": 0.045,
    "index_statistics": { ... },
    "data": { ... },
    "meta": { "correlation_id": "...", "api_version": "v1" }
  }
  ```

---

## 4. Integrity Verification & Telemetry

### 4.1 Verify Integrity
- **Path**: `POST /api/v1/integrity/verify`
- **Consumer**: Team D / Test harness / Team C
- **Purpose**: Validate data integrity using Merkle tree construction or linear SHA-256 checksums, isolating any corrupted chunks.
- **Request Body**:
  ```json
  {
    "chunk_hashes": [
      "hash_a",
      "hash_b",
      "hash_c"
    ],
    "expected_merkle_root": "6b86b273ff34fce19d6b804eff5a3f5747ada4eaa22f1d49c01e52ddb7875b4b",
    "verification_algorithm": "merkle-tree",
    "expected_chunk_hashes": [
      "hash_a",
      "hash_b_original",
      "hash_c"
    ],
    "benchmark_size_bytes": 12288,
    "repetitions": 10
  }
  ```
- **Response (`200 OK`)**:
  ```json
  {
    "merkle_root": "...",
    "verified": false,
    "verified_chunks": [0, 2],
    "corrupted_chunks": [1],
    "verification_latency": 0.00021,
    "algorithm": "SHA-256 Merkle Tree",
    "time_complexity": "O(n)",
    "space_complexity": "O(n)",
    "benchmark": {
      "size_bytes": 12288,
      "repetitions": 10,
      "total_latency": 0.0018
    },
    "data": { ... },
    "meta": { "correlation_id": "...", "api_version": "v1" }
  }
  ```

---

### 4.2 Deduplication & Index Metrics
- **Path**: `GET /api/v1/metrics/dedup` (also `/api/v1/metrics/benchmark`)
- **Consumer**: Team D
- **Purpose**: Compare live performance and memory usage of HashMap, AVL Tree, and Red-Black Tree.
- **Query Parameters**: `size` (int, default: 1000)
- **Response (`200 OK`)**:
  ```json
  {
    "dataset_size": 1000,
    "results": [
      {
        "index": "HashMap",
        "average_lookup_us": 0.45,
        "p95_lookup_us": 0.50,
        "memory_kib": 123.34
      },
      {
        "index": "AVL",
        "average_lookup_us": 0.48,
        "p95_lookup_us": 0.60,
        "memory_kib": 209.75
      },
      {
        "index": "RedBlack",
        "average_lookup_us": 0.68,
        "p95_lookup_us": 0.90,
        "memory_kib": 217.50
      }
    ],
    "cache": {
      "index_version": "v1",
      "entry_count": 1000,
      "cache_hit_rate": 0.92
    },
    "complexity": {
      "HashMap": { "time": "O(1) average", "space": "O(n)" },
      "AVL": { "time": "O(log n)", "space": "O(n)" },
      "RedBlack": { "time": "O(log n)", "space": "O(n)" }
    },
    "data": { ... },
    "meta": { "correlation_id": "...", "api_version": "v1" }
  }
  ```
