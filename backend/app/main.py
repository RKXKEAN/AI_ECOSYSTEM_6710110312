from fastapi import FastAPI
from app.api.v1.routers import storage, auth, health, inference, training

app = FastAPI()

app.include_router(storage.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(health.router, prefix="/api/v1")
app.include_router(inference.router, prefix="/api/v1")
app.include_router(training.router, prefix="/api/v1")


@app.get("/health")
def health_check():
    return {"status": "ok"}


