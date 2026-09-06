"""FastAPI application entrypoint — health + Retell tool webhooks."""

from fastapi import FastAPI

from app.api.retell_webhooks import router as retell_router

app = FastAPI(title="Summit Air Voice Agent", version="0.1.0")
app.include_router(retell_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
