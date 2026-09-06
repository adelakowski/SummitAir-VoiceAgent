"""FastAPI application entrypoint — health check."""

from fastapi import FastAPI

app = FastAPI(title="Summit Air Voice Agent", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
