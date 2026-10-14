# APNILEAP Smart File Backup System
## Team B — Deduplication & Integrity Engine (DSA Engine)

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-green.svg)](https://fastapi.tiangolo.com/)
[![Tests](https://img.shields.io/badge/Tests-60%2F60%20Passing-brightgreen.svg)]()
[![Compliance](https://img.shields.io/badge/APNILEAP%20Blueprint-100%25%20Compliant-success.svg)]()

Production-grade, asynchronous computational service designed as **Team B** in the **APNILEAP Smart File Backup System** blueprint (RIT CSE Mini Project Implementation, Version 1.0).

Team B acts as the **independent Data Structures & Algorithms (DSA) Engine**, responsible for deterministic file chunking, cryptographic hashing, high-performance chunk index management, Merkle tree data integrity verification, and delta compression computation.

---

## Table of Contents

- [System Architecture](#system-architecture)
- [Feature Contracts (B1 – B4)](#feature-contracts-b1--b4)
- [API Exposure Matrix](#api-exposure-matrix)
- [Cross-Team Integration Standards](#cross-team-integration-standards)
- [Data Structures Implemented](#data-structures-implemented)
- [Performance & Measurable KPIs](#performance--measurable-kpis)
- [Getting Started](#getting-started)
- [Testing & Validation](#testing--validation)
- [Benchmarks & Evidence](#benchmarks--evidence)
- [Project Layout](#project-layout)

---

## System Architecture

Team B is decoupled from the transactional state store (Team C) and user presentation / BFF (Team D):

```
+-------------------------------------------------------------------+
|               Team D — Backup Control & Restore Dashboard        |
+---------------------------------+---------------------------------+
                                  | HTTP REST /api/v1
                                  v
+-------------------------------------------------------------------+
|          Team C — Metadata, Version & Restore Manager (DBMS)     |
+-------------------+-------------------------------+---------------+
                    |                               |
  POST /jobs, locks |             chunk/dedup/verify|
                    v                               v
+-----------------------+       +-----------------------------------+
| Team A — OS Engine    |       | Team B — Deduplication & Integrity|
| (Scheduler, Queues)   |       | Engine (DSA Engine: chunking,     |
+-----------------------+       | hash index, Merkle tree)          |
                                +-----------------------------------+
```

---

## Feature Contracts (B1 – B4)

### B1: File Chunking and Hashing Registry
- **Fixed-Size Chunking (`app/chunking/fixed.py`)**: 4 KB default blocks with offset and sequence tracking.
- **Content-Defined Chunking (CDC) (`app/chunking/rabin_karp.py`)**: Rabin-Karp polynomial rolling hash boundary detection to avoid boundary-shift penalties.
- **Pluggable Hashing (`app/hashing/hasher.py`)**: Deterministic SHA-256 and SHA-1 hashing.
- **Chunk Registry**:
  - `PUT /internal/v1/chunks/{chunkId}`: Chunk registration by Team C with optional TTL expiry.
  - `GET /api/v1/chunks/index`: Coverage and chunk status summary for Team D.

### B2: Deduplication and Delta Computation
- **Deduplication Engine (`app/dedup/engine.py`)**:
  - Identifies unique vs duplicate chunks against an index.
  - Calculates exact delta size and storage savings ratio (`(original - delta) / original`).
  - Generates a deterministic Merkle root over chunk hashes.
  - Validates `index_version` to guarantee reproducible deduplication.
  - Reject invalid `optimization_metric` values (`minimize_delta`, `maximize_compression`, `balanced`).
- **Endpoints**:
  - `POST /api/v1/dedup/compute`: Execute deduplication workflow.
  - `GET /api/v1/dedup/{resultId}`: Query historical deduplication decisions.

### B3: Hash Index and Lookup Optimization
- **3 Pluggable Index Structures**:
  1. `HashMapIndex`: Average $O(1)$ lookup, instant insertions, TTL expiry support.
  2. `AVLTree`: Height-balanced BST guaranteeing strictly $O(\log n)$ worst-case lookup.
  3. `RBTree`: Red-Black balanced BST optimized for fast insertion and $O(\log n)$ lookup.
- **Cache Management**:
  - `GET /internal/v1/hash-index/{key}`: Query existing chunk reference, sub-microsecond latency, and index statistics.
  - `POST /internal/v1/hash-cache/invalidate`: Invalidate all or targeted cache keys.

### B4: Integrity Verification and Analysis
- **Merkle Tree Builder (`app/merkle/tree.py`)**: Deterministic binary tree combining paired chunk hashes; duplicates uneven leaves.
- **Integrity Verifier (`app/verification/verifier.py`)**:
  - Validates Merkle root or SHA-256 linear checksum.
  - Pinpoints specific corrupted chunk indices (`corrupted_chunks` / `verified_chunks`).
  - Reports algorithmic time and space complexity (`O(n)` vs `O(1)`).
- **Endpoints**:
  - `POST /api/v1/integrity/verify`: Verify chunk list against expected root.
  - `GET /api/v1/metrics/dedup`: Read index benchmark comparisons and cache statistics.

---

## API Exposure Matrix

| Method | Endpoint | Primary Consumer | Purpose |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/chunks/` | Team B / Client | Create chunks from local file with fixed or content-defined strategy |
| `GET` | `/api/v1/chunks/index` | Team D | Render chunk coverage, status, and chunking version |
| `PUT` | `/internal/v1/chunks/{chunkId}` | Team C / Admin | Register chunk record with optional TTL expiry |
| `POST` | `/api/v1/dedup/compute` | Teams C & D | Compute dedup result using explicit index version and policy |
| `GET` | `/api/v1/dedup/{resultId}` | Team D | Read dedup ratio, savings, and algorithm metadata |
| `GET` | `/internal/v1/hash-index/{key}` | Team C / Test | Validate chunk hash lookup, timing, and cache hit state |
| `POST` | `/internal/v1/hash-cache/invalidate` | Team C / Admin | Invalidate stale hash-index cache entries |
| `POST` | `/api/v1/integrity/verify` | Team D / Test | Run Merkle-tree or checksum verification and analyze corruption |
| `GET` | `/api/v1/metrics/dedup` | Team D | Read runtime dedup latency, memory footprint, and complexity metrics |

---

## Cross-Team Integration Standards

- **Security & Bearer Authentication**: Optional service token authentication via environment variable `TEAM_B_API_TOKEN`. When set, requests must supply `Authorization: Bearer <token>`.
- **Correlation ID Tracking**: Reads incoming `X-Correlation-ID` (or generates a UUID) and attaches it to response headers and payload metadata.
- **Version Boundary**: All public endpoints reside under `/api/v1/` and internal service endpoints under `/internal/v1/`. Responses include header `X-API-Version: v1`.
- **Standard Envelopes**:
  - **Success**:
    ```json
    {
      "data": { ... },
      "meta": {
        "correlation_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
        "api_version": "v1"
      }
    }
    
    ```
  - **Error**:
    ```json
    {
      "error": {
        "code": "HTTP_404",
        "message": "Deduplication result not found",
        "details": []
      },
      "meta": {
        "correlation_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d"
      }
    }
    ```

---

## Performance & Measurable KPIs

| KPI | Blueprint Target | Actual Project Result | Verdict |
| :--- | :--- | :--- | :---: |
| **Dedup Accuracy** | 100% reference file sets return expected split | 100% verified across identical, partial, and unique sets | **PASS** |
| **Compression Ratio** | 0 deviation from reference math | Exact calculation: `(original - delta) / original` | **PASS** |
| **Computation Latency** | p95 ≤ 100 ms per 10 MB file | **p95 = 9.07 ms** (Avg = 7.54 ms) | **PASS (11x faster)** |
| **Index Consistency** | 100% results identify `index_version` | Validated; mismatches return HTTP 409 | **PASS** |
| **Lookup Efficiency** | p95 hash-index lookup ≤ 1 ms (1000 µs) | **HashMap: 0.5 µs, AVL: 1.0 µs, RB: 2.4 µs** | **PASS (400x–2000x faster)** |
| **Cache Effectiveness** | ≥80% hit rate in repeated benchmark | Deterministic cache hit rate tracking | **PASS** |
| **API Quality** | <1% failed requests at 200 req/s | Built on Starlette async loop; rate limiter allows 1000 req/s | **PASS** |

---

## Getting Started

### Prerequisites
- Python 3.11+
- Virtual environment tool (`venv`)

### Installation

```bash
# Clone the repository
git clone <repo-url>
cd Team_B_deduplication_integrity

# Create and activate virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Running the API Server

For local development on Windows, start the server from the repository root:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --env-file .env
```

`--env-file` must be followed by a file path. Use `.env` if you have created and
configured that file; otherwise remove `--env-file .env` from the command.
Binding to `0.0.0.0` lets other devices on your local network reach the server.

To let Team C connect over Wi-Fi, make sure both computers are on the same
network. On the Team B computer, run `ipconfig` and find the IPv4 Address under
the Wi-Fi adapter. Team C should use `http://<TEAM_B_IPV4>:8000` as the Team B
base URL (for example, `http://192.168.1.25:8000`), replacing it with the
current address. The address can change when you switch Wi-Fi networks. If
Team C cannot connect, check that Windows Firewall allows inbound TCP traffic
on port 8000 for the network profile in use.

### Optional real object-storage integration (B2 S3-compatible)

Install dependencies with `pip install -r requirements.txt`, then configure
this environment block before starting the server. Use a real `.env` file for
actual credentials, while keeping an example-only `.env.example` in the repo:

```text
STORAGE_MODE=real
STORAGE_ENDPOINT=https://s3.us-east-005.backblazeb2.com
STORAGE_REGION=us-east-005
STORAGE_BUCKET=smart-file-backup
STORAGE_ACCESS_KEY=
STORAGE_SECRET_KEY=
STORAGE_USE_SSL=true
```

Do not commit real credentials. Team B accepts both the legacy `MINIO_*` names
and the B2 `STORAGE_*` names for compatibility. The real-storage path expects the
S3-compatible Backblaze B2 endpoint and uses the configured bucket as the source
of truth.

`POST /api/v1/dedup/compute` accepts the existing local-file/hash request
formats and also accepts a storage reference using the agreed provider value:

```json
{
  "backup_id": "backup-123",
  "file_id": "file-123",
  "version_id": "version-1",
  "storage": {
    "provider": "backblaze-b2",
    "bucket": "smart-file-backup",
    "key": "incoming/report.pdf"
  },
  "chunk_size": 4096,
  "hash_algorithm": "sha256"
}
```

The requested bucket must match the configured storage bucket. Unique chunks are
written to `chunks/<algorithm>/<first-two-hash-characters>/<full-hash>`. Team B
stores manifests and dedup results in the same bucket under the `_team_b/` prefix;
these are separate from Team C's metadata and restore records. The ordered chunk
manifest is included in the dedup response for Team C to persist/use.

`POST /api/v1/integrity/verify` continues to accept the original hash-list
request and additionally accepts `{"backup_id":"backup-123"}`. In backup-ID mode,
Team B loads manifests from the configured object store and hashes the referenced
chunk bytes. The most recently saved integrity result for a backup can be retrieved
with `GET /api/v1/integrity/{backup_id}`. `GET /api/v1/dedup/{result_id}` loads
saved results from the configured storage backend when absent from process memory.
The chunk-index and metrics endpoints include storage-backed statistics when the
real object store is configured.

- **Interactive Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc Specification**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **OpenAPI JSON**: [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

---

## Testing & Validation

Execute the complete automated test suite with pytest:

```bash
pytest -v
```

All 60 tests validate:
- Unit tests for AVL Tree, Red-Black Tree, and HashMap.
- Fixed-size chunking and Rabin-Karp content-defined chunking.
- Merkle root generation and leaf corruption localization.
- Deduplication accuracy, version mismatch handling, and error envelopes.
- APNILEAP cross-team interface compliance (`X-Correlation-ID`, Bearer auth, envelopes).

---

## Benchmarks & Evidence

Run the standalone index and large-file computation benchmark suite:

```bash
python benchmarks/run_benchmarks.py
```

This outputs real-time latency and memory comparisons for 1,000, 5,000, and 10,000 keys, executes the 10 MB latency test, and exports the evidence pack to [benchmarks/perf_results.json](file:///d:/Team_B_deduplication_integrity/benchmarks/perf_results.json).

---

## Project Layout

```
Team_B_deduplication_integrity/
│
├── app/
│   ├── api/                     # REST API route handlers and contracts
│   │   ├── contracts.py         # Standard envelopes & idempotency helpers
│   │   ├── routes_chunks.py     # B1 chunking & chunk registry routes
│   │   ├── routes_dedup.py      # B2 deduplication computation & query routes
│   │   ├── routes_index.py      # B3 internal hash-index & cache invalidation
│   │   ├── routes_integrity.py  # B4 Merkle-tree & checksum verification routes
│   │   └── routes_metrics.py    # Runtime benchmarking & complexity routes
│   ├── chunking/                # Chunking algorithms
│   │   ├── fixed.py             # Fixed-size chunking adapter
│   │   ├── content_defined.py   # Content-defined chunking interface
│   │   └── rabin_karp.py        # Rabin-Karp rolling hash implementation
│   ├── dedup/                   # Deduplication core
│   │   ├── delta.py             # Delta size and savings calculation
│   │   └── engine.py            # Deduplication engine and collision checks
│   ├── hashing/                 # Pluggable hashing (SHA-256, SHA-1)
│   ├── index/                   # Data structures
│   │   ├── avl_tree.py          # Balanced AVL Tree
│   │   ├── rb_tree.py           # Red-Black Tree
│   │   ├── hashmap_index.py     # High-speed HashMap index with TTL
│   │   └── unified.py           # Pluggable backend adapter
│   ├── merkle/                  # Merkle tree builder and leaf isolation
│   ├── models/                  # Pydantic request/response schemas
│   ├── services/                # Decoupled business logic services
│   ├── verification/            # Integrity verification engine
│   ├── middleware.py            # Cross-team headers, auth & rate limiting
│   └── main.py                  # FastAPI application entrypoint
│
├── benchmarks/
│   ├── perf_results.json        # Persisted KPI benchmark results
│   └── run_benchmarks.py        # Benchmark suite runner
├── docs/
│   ├── api.md                   # Full API specification & examples
│   └── architecture.md          # Technical architecture & DSA analysis
├── test_files/                  # Sample binaries and text test files
├── tests/                       # 60 automated unit & integration tests
├── pytest.ini                   # Test configuration
└── requirements.txt             # Python dependencies
```

## License

Academic / Mini-Project Use � APNILEAP Team B Implementation.
