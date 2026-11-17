from fastapi import FastAPI

app = FastAPI(title="Fabric Audit API")


@app.get("/healthz")
def health_check() -> dict[str, str]:
    return {"status": "healthy"}
