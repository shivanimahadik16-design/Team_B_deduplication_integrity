from fastapi import FastAPI

from app.api.routes_integrity import router as integrity_router


app = FastAPI(
    title="Team B Deduplication & Integrity Engine",
    version="1.0.0",
    description="Deduplication and integrity verification service.",
)


app.include_router(integrity_router)